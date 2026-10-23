from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
from typing import Mapping
import uuid

from .alma_gate import POLICY_SHA256, POLICY_VERSION, AlmaGate, candidate_to_finding
from .alma_gate_v11 import (
    POLICY_SHA256 as POLICY_SHA256_V11,
    POLICY_VERSION as POLICY_VERSION_V11,
    AlmaGateV11,
)
from .alma_gate_v12 import (
    POLICY_SHA256 as POLICY_SHA256_V12,
    POLICY_VERSION as POLICY_VERSION_V12,
    AlmaGateV12,
)
from .alma_gate_v13 import (
    POLICY_SHA256 as POLICY_SHA256_V13,
    POLICY_VERSION as POLICY_VERSION_V13,
    AlmaGateV13,
)
from .alma_gate_v14 import (
    POLICY_SHA256 as POLICY_SHA256_V14,
    POLICY_VERSION as POLICY_VERSION_V14,
    AlmaGateV14,
)
from .alma_gate_v141 import (
    POLICY_SHA256 as POLICY_SHA256_V141,
    POLICY_VERSION as POLICY_VERSION_V141,
    AlmaGateV141,
)
from .alma_gate_v150 import (
    POLICY_SHA256 as POLICY_SHA256_V150,
    POLICY_VERSION as POLICY_VERSION_V150,
    AlmaGateV150,
)
from .base_reviewer import BaseReviewer, Candidate
from .diff_parser import parse_unified_diff
from .llm_reviewer import LLMReviewer, RealLLMRefused
from .run_ledger import (
    RunLedger,
    RunLedgerError,
    record_candidates,
    record_gate_decisions,
    record_session_close,
    record_session_error,
    record_session_open,
    record_spend,
)
from .llm_reviewer_v2 import LLMReviewerV2
from .llm_reviewer_v21 import LLMReviewerV21
from .llm_reviewer_v22 import LLMReviewerV22
from .llm_reviewer_v23 import LLMReviewerV23
from .llm_reviewer_v24 import LLMReviewerV24
from .llm_reviewer_v25 import LLMReviewerV25
from .llm_reviewer_v26 import LLMReviewerV26


# Backwards-compatible name: the mock-first package raised this when
# backend=llm was requested.  It is now the refusal error of the real,
# flag-guarded adapter (agent/llm_reviewer.py).
LLMBackendNotConfigured = RealLLMRefused


@dataclass
class RunResult:
    output: dict[str, object]
    candidates: list[Candidate]
    ledger: list[dict[str, object]]
    llm_run_info: dict[str, object] | None = None
    # Gates 1.4.0/1.4.1 only: the held candidates (needs_validation
    # records, as dicts).  None for every other gate — the ledger
    # file then keeps its historical bare-list shape; a list
    # (possibly empty) makes the ledger file an object with a
    # separate "needs_validation" section, never mixed into the
    # findings.
    needs_validation: list[dict[str, object]] | None = None


def _select_gate(config: Mapping[str, str]):
    """Gate selection (RB_CONFIG_GATE): "v1" (default) is the frozen
    gate alma-evidence-gate/1.0.0 of the v1 experiment; "v11" is
    alma-evidence-gate/1.1.0 (Adenda 1 of the v2 pre-registration: the
    1.0.0's 8 classes plus 6 mechanically verifiable ones); "v12" is
    alma-evidence-gate/1.2.0 (Adenda 2: the 1.1.0's 14 classes with
    the red team's hardening — tokenized evidence views, co-occurrence,
    block-level antidotes, added-line requirement); "v13" is
    alma-evidence-gate/1.3.0 (Adenda 3: the 1.2.0's 14 classes with
    the same hardened checks, delegated to the 1.2.0's own function,
    plus the class hunter's 5 best-ranked classes — weak_hash,
    tarfile_unsafe_extract, hardcoded_password_argument,
    jwt_verification_disabled, debug_mode_enabled); "v14" is
    alma-evidence-gate/1.4.0 (PREREGISTRO-PUERTA-140.md: the 1.3.0 by
    delegation plus the third state needs_validation, extended to
    general categories by PREREGISTRO-REVIEWBENCH-V23.md); "v141" is
    alma-evidence-gate/1.4.1 (PREREGISTRO-PUERTA-141.md: the 1.4.0
    with the single routing change of its §2 — check (f), no cited
    line added by this change, is a firm rejection at the frontier
    again, never a needs_validation blocker); "v150" is
    alma-evidence-gate/1.5.0 (PREREGISTRO-PUERTA-150.md: the
    1.4.1 by delegation for the 19 classes, plus the grounding
    rule for the general categories — admitted here by the
    mounting declared in PREREGISTRO-VALIDACION-20261024.md §3).
    The gate exists only in the ALMA arm; the base arm bypasses
    any gate."""

    gate_version = (config.get("gate") or "v1").strip().lower()
    if gate_version == "v1":
        return AlmaGate()
    if gate_version == "v11":
        return AlmaGateV11()
    if gate_version == "v12":
        return AlmaGateV12()
    if gate_version == "v13":
        return AlmaGateV13()
    if gate_version == "v14":
        return AlmaGateV14()
    if gate_version == "v141":
        return AlmaGateV141()
    if gate_version == "v150":
        return AlmaGateV150()
    raise ValueError(
        f"unknown gate version {gate_version!r}; "
        "expected 'v1', 'v11', 'v12', 'v13', 'v14', 'v141' or 'v150' "
        "(RB_CONFIG_GATE)"
    )


def _normalize_repo(pr: Mapping[str, object]) -> str:
    repo = str(pr.get("repo") or "").strip()
    if repo.startswith("http://") or repo.startswith("https://"):
        return repo
    nwo = str(pr.get("nwo") or repo).strip()
    if "/" in nwo and " " not in nwo:
        return f"https://github.com/{nwo}"
    return repo


def validate_output(
    output: Mapping[str, object],
    *,
    expected_head: str | None = None,
    expected_pr_number: int | None = None,
) -> None:
    """Fail closed unless the output follows the ReviewBench contract."""

    if set(output.keys()) != {"pr", "agent", "findings"}:
        raise ValueError("output must contain exactly pr, agent, and findings")
    pr = output.get("pr")
    if not isinstance(pr, dict) or set(pr.keys()) != {"repo", "pr_number", "base", "head"}:
        raise ValueError("output.pr must contain exactly repo, pr_number, base, and head")
    if expected_head is not None and pr["head"] != expected_head:
        raise ValueError("output pr.head does not equal RB_HEAD")
    if expected_pr_number is not None and pr["pr_number"] != expected_pr_number:
        raise ValueError("output pr.pr_number does not equal RB_PR_NUMBER")
    if not isinstance(output.get("agent"), str) or not output["agent"]:
        raise ValueError("output.agent must be a non-empty string")
    findings = output.get("findings")
    if not isinstance(findings, list):
        raise ValueError("output.findings must be a list")
    for finding in findings:
        if not isinstance(finding, dict) or set(finding.keys()) != {
            "file",
            "start_line",
            "end_line",
            "message",
            "producer",
        }:
            raise ValueError("each finding must contain exactly the contract fields")
        path = finding["file"]
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("./")
            or path.startswith("/")
            or "\\" in path
        ):
            raise ValueError(f"invalid repository-relative finding path: {path!r}")
        if not isinstance(finding["start_line"], int) or not isinstance(
            finding["end_line"], int
        ):
            raise ValueError("finding line numbers must be integers")
        if finding["start_line"] < 1 or finding["end_line"] < finding["start_line"]:
            raise ValueError("finding line range is invalid")
        if not isinstance(finding["message"], str) or not finding["message"].strip():
            raise ValueError("finding message must be non-empty")
        if finding["producer"] != output["agent"]:
            raise ValueError("finding producer must equal RB_AGENT/output.agent")


def run_agent(
    *,
    diff_text: str,
    pr_metadata: Mapping[str, object],
    agent_name: str,
    mode: str = "alma",
    backend: str = "mock",
    config: Mapping[str, str] | None = None,
    env: Mapping[str, str] | None = None,
    llm_transport=None,
    run_ledger: RunLedger | None = None,
) -> RunResult:
    config = dict(config or {})
    if mode not in {"alma", "base"}:
        raise ValueError(f"unknown governance mode {mode!r}; expected 'alma' or 'base'")

    diff = parse_unified_diff(diff_text)
    llm_run_info: dict[str, object] | None = None
    if backend == "mock":
        candidates = BaseReviewer().review(diff)
    elif backend == "llm":
        # The adapter refuses (RealLLMRefused) unless ALLOW_REAL_LLM=1, an
        # API key, RB_MODEL_BASE_URL, a configured model and a positive
        # RB_MAX_SPEND_USD are all present.  Its candidates pass through the
        # same frozen gate below as the mock reviewer's.
        #
        # Reviewer selection (RB_CONFIG_REVIEWER): "v1" (default) is the
        # original single-pass diff-only reviewer of the v1 experiment;
        # "v2" is the multi-pass full-context reviewer of
        # PREREGISTRO-REVIEWBENCH-V2.md; "v21" is the single-pass
        # full-context reviewer of PREREGISTRO-REVIEWBENCH-V21.md
        # (design C1 of Adenda 6: the v2's per-class language in ONE
        # call, so the pre-flight guard estimates one pass, not twenty);
        # "v22" is the triage + deep-pass reviewer of
        # PREREGISTRO-REVIEWBENCH-V22.md (design C2: a selection pass
        # over the diff alone marks <=5 classes, the v2's deep passes
        # run only for those, and a pre-registered degradation rule
        # replaces the v2 guard's blanket refusal);
        # "v23" is the generalized-selection reviewer of
        # PREREGISTRO-REVIEWBENCH-V23.md (path A: the selection marks
        # the benchmark's nine public general categories alongside
        # the 19 specialty classes, under the same shared cap of 5
        # deep passes and the same degradation rule).
        # "v24" is the evidence-discipline producer of
        # PREREGISTRO-PRODUCTOR-EVIDENCIA.md (the v2.3 selection
        # unchanged; deep findings are born citable or settle in
        # the production ledger, with the birth shaper as the
        # last production stage); "v25" is the v2.4 plus the
        # lessons context read in production
        # (PREREGISTRO-MEMORIA-LECCIONES.md); "v26" is the v2.5
        # plus the absence context (ADENDA-V26.md).  The three
        # were admitted here by the mounting declared in
        # PREREGISTRO-VALIDACION-20261024.md §3.
        # All of them feed the identical gate.
        effective_env = dict(os.environ) if env is None else env
        reviewer_version = (config.get("reviewer") or "v1").strip().lower()
        if reviewer_version == "v1":
            reviewer = LLMReviewer.from_env(
                effective_env,
                config,
                transport=llm_transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text, diff=diff, config=config
            )
        elif reviewer_version == "v2":
            reviewer = LLMReviewerV2.from_env(
                effective_env,
                config,
                transport=llm_transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=diff,
                config=config,
                mode=mode,
                repo_root=(
                    config.get("repo_root")
                    or effective_env.get("RB_REPO_ROOT")
                    or "/work/repo"
                ),
            )
        elif reviewer_version == "v21":
            reviewer = LLMReviewerV21.from_env(
                effective_env,
                config,
                transport=llm_transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=diff,
                config=config,
                mode=mode,
                repo_root=(
                    config.get("repo_root")
                    or effective_env.get("RB_REPO_ROOT")
                    or "/work/repo"
                ),
            )
        elif reviewer_version == "v22":
            reviewer = LLMReviewerV22.from_env(
                effective_env,
                config,
                transport=llm_transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=diff,
                config=config,
                mode=mode,
                repo_root=(
                    config.get("repo_root")
                    or effective_env.get("RB_REPO_ROOT")
                    or "/work/repo"
                ),
            )
        elif reviewer_version == "v23":
            reviewer = LLMReviewerV23.from_env(
                effective_env,
                config,
                transport=llm_transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=diff,
                config=config,
                mode=mode,
                repo_root=(
                    config.get("repo_root")
                    or effective_env.get("RB_REPO_ROOT")
                    or "/work/repo"
                ),
            )
        elif reviewer_version == "v24":
            reviewer = LLMReviewerV24.from_env(
                effective_env,
                config,
                transport=llm_transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=diff,
                config=config,
                mode=mode,
                repo_root=(
                    config.get("repo_root")
                    or effective_env.get("RB_REPO_ROOT")
                    or "/work/repo"
                ),
            )
        elif reviewer_version == "v25":
            reviewer = LLMReviewerV25.from_env(
                effective_env,
                config,
                transport=llm_transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=diff,
                config=config,
                mode=mode,
                repo_root=(
                    config.get("repo_root")
                    or effective_env.get("RB_REPO_ROOT")
                    or "/work/repo"
                ),
            )
        elif reviewer_version == "v26":
            reviewer = LLMReviewerV26.from_env(
                effective_env,
                config,
                transport=llm_transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=diff,
                config=config,
                mode=mode,
                repo_root=(
                    config.get("repo_root")
                    or effective_env.get("RB_REPO_ROOT")
                    or "/work/repo"
                ),
            )
        else:
            raise ValueError(
                f"unknown reviewer version {reviewer_version!r}; "
                "expected 'v1', 'v2', 'v21', 'v22', 'v23', 'v24', 'v25' "
                "or 'v26' (RB_CONFIG_REVIEWER)"
            )
        if reviewer.last_run_info is not None:
            llm_run_info = reviewer.last_run_info.to_dict()
    else:
        raise ValueError(f"unknown backend {backend!r}; expected 'mock' or 'llm'")

    # Run session ledger (PREREGISTRO-REGISTRO-SESION.md):
    # observability only.  With run_ledger=None — every existing
    # caller — nothing below emits anything and behaviour is
    # unchanged.  Append failures are announced on stderr and
    # never break production (fail-soft, declared in the paper).
    rl_active = run_ledger is not None
    pr_number = int(pr_metadata["pr_number"])

    def _rl_emit(fn) -> None:
        nonlocal rl_active
        if not rl_active:
            return
        try:
            fn()
        except Exception as exc:  # observability must not break the run
            print(
                f"alma-reviewbench run-ledger append failed: {exc}",
                file=sys.stderr,
            )
            rl_active = False

    _rl_emit(
        lambda: record_candidates(
            run_ledger, pr_number=pr_number, candidates=candidates
        )
    )

    gate = _select_gate(config)
    needs_validation: list[dict[str, object]] | None = None
    if mode == "alma":
        gate_result = gate.validate(candidates, diff, agent_name)
        findings = list(gate_result.findings)
        ledger = [entry.to_dict() for entry in gate_result.ledger]
        held = getattr(gate_result, "needs_validation", None)
        if held is not None:
            needs_validation = [record.to_dict() for record in held]
    else:
        findings = [candidate_to_finding(candidate, agent_name) for candidate in candidates]
        ledger = [
            {
                "rule_id": candidate.rule_id,
                "claim_type": candidate.claim_type,
                "file": candidate.file,
                "start_line": candidate.start_line,
                "end_line": candidate.end_line,
                "message": candidate.message,
                "severity_hint": candidate.severity_hint,
                "category_hint": candidate.category_hint,
                "evidence": [
                    {"file": candidate.file, "line": line_number, "text": text}
                    for line_number, text in zip(
                        range(candidate.start_line, candidate.end_line + 1),
                        candidate.evidence_text,
                    )
                ],
                "status": "accepted",
                "reasons": ["ALMA gate bypassed for the pre-registered base A/B arm"],
                "validator_version": "bypassed-base-arm",
                "policy_sha256": gate.policy_sha256,
            }
            for candidate in candidates
        ]

    _rl_emit(
        lambda: record_gate_decisions(
            run_ledger,
            pr_number=pr_number,
            ledger_entries=ledger,
            needs_validation=needs_validation,
        )
    )
    _rl_emit(
        lambda: record_spend(
            run_ledger,
            pr_number=pr_number,
            estimated_cost_usd=(
                float(llm_run_info.get("estimated_cost_usd") or 0.0)
                if llm_run_info is not None
                else 0.0
            ),
            max_spend_usd=(
                float(llm_run_info["max_spend_usd"])
                if llm_run_info is not None
                and llm_run_info.get("max_spend_usd") is not None
                else None
            ),
        )
    )

    output: dict[str, object] = {
        "pr": {
            "repo": _normalize_repo(pr_metadata),
            "pr_number": int(pr_metadata["pr_number"]),
            "base": str(pr_metadata["base"]),
            "head": str(pr_metadata["head"]),
        },
        "agent": agent_name,
        "findings": findings,
    }
    validate_output(output)
    return RunResult(
        output=output,
        candidates=candidates,
        ledger=ledger,
        llm_run_info=llm_run_info,
        needs_validation=needs_validation,
    )


def _rb_config(env: Mapping[str, str]) -> dict[str, str]:
    config: dict[str, str] = {}
    for key, value in sorted(env.items()):
        if key.startswith("RB_CONFIG_"):
            config[key.removeprefix("RB_CONFIG_").lower()] = value
    return config


def _selected_gate_identity(config: Mapping[str, str]) -> tuple[str, str]:
    """The SELECTED gate's (validator, policy_sha256) labels;
    run_agent validates the value and fails closed on an unknown
    one, so an unrecognized value is only labelled here, never
    silently mapped to a real gate."""

    gate_version = (config.get("gate") or "v1").strip().lower()
    if gate_version == "v150":
        return POLICY_VERSION_V150, POLICY_SHA256_V150
    if gate_version == "v141":
        return POLICY_VERSION_V141, POLICY_SHA256_V141
    if gate_version == "v14":
        return POLICY_VERSION_V14, POLICY_SHA256_V14
    if gate_version == "v13":
        return POLICY_VERSION_V13, POLICY_SHA256_V13
    if gate_version == "v12":
        return POLICY_VERSION_V12, POLICY_SHA256_V12
    if gate_version == "v11":
        return POLICY_VERSION_V11, POLICY_SHA256_V11
    if gate_version == "v1":
        return POLICY_VERSION, POLICY_SHA256
    return f"unknown-gate:{gate_version}", "unknown"


def _resolve_run_ledger_path(
    env: Mapping[str, str], config: Mapping[str, str], out_path: Path
) -> Path | None:
    """Run session ledger path (PREREGISTRO-REGISTRO-SESION.md
    §2.3): ALMA_RUN_LEDGER_PATH, then RB_CONFIG_RUN_LEDGER (the
    value "off" is the only off switch), then the default —
    run-ledger.jsonl beside --out, written by the runner itself
    on every run, not opt-in."""

    raw = env.get("ALMA_RUN_LEDGER_PATH") or config.get("run_ledger")
    if raw is not None and raw.strip().lower() == "off":
        return None
    if raw:
        return Path(raw)
    return out_path.with_name("run-ledger.jsonl")


def _print_applied_config(config: Mapping[str, str], mode: str, backend: str) -> None:
    requested_model = config.get("model", "mock-deterministic")
    effort = config.get("effort", "local")
    validator, policy_sha256 = _selected_gate_identity(config)
    print(
        "alma-reviewbench "
        f"requested_model={requested_model} effort={effort} "
        f"effective_backend={backend} governance={mode} "
        f"validator={validator} policy_sha256={policy_sha256}",
        flush=True,
    )
    for key, value in sorted(config.items()):
        print(f"config {key}={value}", flush=True)


def main(argv: list[str] | None = None) -> int:
    env = dict(os.environ)
    config = _rb_config(env)

    parser = argparse.ArgumentParser(description="ALMA ReviewBench reviewer")
    parser.add_argument("--diff", default=env.get("RB_DIFF", "/work/pr/diff.patch"))
    parser.add_argument("--pr-json", default=env.get("RB_PR_JSON", "/work/pr/pr.json"))
    parser.add_argument("--out", default=env.get("RB_OUT", "/work/out/findings.json"))
    parser.add_argument("--ledger", default=env.get("ALMA_LEDGER_PATH"))
    parser.add_argument(
        "--mode",
        choices=["alma", "base"],
        default=config.get("governance", config.get("mode", "alma")),
    )
    parser.add_argument(
        "--backend",
        choices=["mock", "llm"],
        default=config.get("backend", "mock"),
    )
    args = parser.parse_args(argv)

    agent_name = env.get("RB_AGENT", "alma-reviewer")
    _print_applied_config(config, args.mode, args.backend)

    # Run session ledger: opened once the PR is identified,
    # closed after the outputs are written.  Fail-soft by
    # design (PREREGISTRO-REGISTRO-SESION.md §2.4): a ledger
    # that cannot open or append is announced on stderr and the
    # run proceeds — its absence is never silent again.
    run_ledger: RunLedger | None = None
    rl_segment = uuid.uuid4().hex[:12]
    rl_pr_number: int | None = None
    rl_resumed = False

    try:
        diff_text = Path(args.diff).read_text(encoding="utf-8")
        pr_metadata = json.loads(Path(args.pr_json).read_text(encoding="utf-8"))

        expected_head = env.get("RB_HEAD")
        expected_pr_number = (
            int(env["RB_PR_NUMBER"]) if env.get("RB_PR_NUMBER") else None
        )
        if expected_head is not None and str(pr_metadata.get("head")) != expected_head:
            raise ValueError("pr.json head does not equal RB_HEAD")
        if expected_pr_number is not None and int(pr_metadata.get("pr_number")) != expected_pr_number:
            raise ValueError("pr.json pr_number does not equal RB_PR_NUMBER")

        rl_pr_number = int(pr_metadata["pr_number"])
        out_path_hint = Path(args.out)
        rl_path = _resolve_run_ledger_path(env, config, out_path_hint)
        if rl_path is not None:
            run_id = env.get("RB_RUN_ID") or config.get("run_id")
            try:
                run_ledger = RunLedger(rl_path, run_id=run_id)
            except (RunLedgerError, OSError) as exc:
                print(
                    f"alma-reviewbench run-ledger disabled: {exc}",
                    file=sys.stderr,
                )
                run_ledger = None
            if run_ledger is not None:
                rl_resumed = run_ledger.unclosed_session(rl_pr_number)
                gate_version_label, gate_policy_sha = (
                    _selected_gate_identity(config)
                )
                raw_cap = (env.get("RB_MAX_SPEND_USD") or "").strip()
                try:
                    rl_max_spend = float(raw_cap) if raw_cap else None
                except ValueError:
                    rl_max_spend = None
                try:
                    record_session_open(
                        run_ledger,
                        segment=rl_segment,
                        agent=agent_name,
                        mode=args.mode,
                        backend=args.backend,
                        config=config,
                        gate_version=gate_version_label,
                        policy_sha256=gate_policy_sha,
                        image_sha256=(
                            env.get("RB_IMAGE_SHA256")
                            or config.get("image_sha256")
                        ),
                        max_spend_usd=rl_max_spend,
                        pr={
                            "repo": _normalize_repo(pr_metadata),
                            "pr_number": rl_pr_number,
                            "base": str(pr_metadata.get("base") or ""),
                            "head": str(pr_metadata.get("head") or ""),
                        },
                    )
                except Exception as exc:  # observability, fail-soft
                    print(
                        f"alma-reviewbench run-ledger disabled: {exc}",
                        file=sys.stderr,
                    )
                    run_ledger.close()
                    run_ledger = None

        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr_metadata,
            agent_name=agent_name,
            mode=args.mode,
            backend=args.backend,
            config=config,
            env=env,
            run_ledger=run_ledger,
        )
        if result.llm_run_info is not None:
            print(
                "alma-reviewbench llm_run "
                + json.dumps(result.llm_run_info, ensure_ascii=False),
                flush=True,
            )
        validate_output(
            result.output,
            expected_head=expected_head,
            expected_pr_number=expected_pr_number,
        )

        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result.output, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        ledger_path = Path(args.ledger) if args.ledger else None
        if ledger_path is None and env.get("RB_ALMA_LEDGER") == "1":
            ledger_path = out_path.with_name("alma-ledger.json")
        if ledger_path is not None:
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            if result.needs_validation is not None:
                # Gates 1.4.0/1.4.1: the held candidates live in their
                # own section of the ledger file, never among the
                # accepted/rejected entries and never in the findings.
                ledger_payload: object = {
                    "ledger": result.ledger,
                    "needs_validation": result.needs_validation,
                }
            else:
                ledger_payload = result.ledger
            ledger_path.write_text(
                json.dumps(ledger_payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        if run_ledger is not None:
            try:
                status_counts = {"accepted": 0, "rejected": 0}
                for entry in result.ledger:
                    status = str(entry.get("status"))
                    if status in status_counts:
                        status_counts[status] += 1
                record_session_close(
                    run_ledger,
                    pr_number=rl_pr_number,
                    segment=rl_segment,
                    counts={
                        "candidates": len(result.candidates),
                        "accepted": status_counts["accepted"],
                        "rejected": status_counts["rejected"],
                        "needs_validation": len(
                            result.needs_validation or []
                        ),
                    },
                    findings_emitted=len(result.output["findings"]),
                    spend_estimated_usd=(
                        float(
                            result.llm_run_info.get(
                                "estimated_cost_usd"
                            )
                            or 0.0
                        )
                        if result.llm_run_info is not None
                        else 0.0
                    ),
                    resumed=rl_resumed,
                )
                # Second channel, declared in the paper: the
                # portal always captures stdout, so the log
                # carries how many events and which head hash
                # must come back even if the file were lost.
                print(
                    "alma-reviewbench run_ledger "
                    f"events={run_ledger.event_count} "
                    f"head={run_ledger.head_hash}",
                    flush=True,
                )
            except Exception as exc:  # observability, fail-soft
                print(
                    f"alma-reviewbench run-ledger close failed: {exc}",
                    file=sys.stderr,
                )
            finally:
                run_ledger.close()
        return 0
    except Exception as exc:  # The benchmark treats non-zero as a failed PR.
        if run_ledger is not None:
            record_session_error(
                run_ledger,
                pr_number=rl_pr_number,
                segment=rl_segment,
                error=exc,
            )
            run_ledger.close()
        print(f"alma-reviewbench error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
