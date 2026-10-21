"""LLM reviewer v2.1 — the v2's language in ONE pass per PR.

Why this module exists (pre-registration: PREREGISTRO-REVIEWBENCH-V21.md,
frozen 2026-10-21; diagnosis: Adenda 6 of PREREGISTRO-REVIEWBENCH-V2.md):
the v2 reviewer (``agent/llm_reviewer_v2.py``) speaks the frozen gate's
language and proved it in the semaphore (21/10: base 8/8 planted defects,
ALMA 6/8, semaphore GREEN) — but its design makes one full-context call
per claim class, and on real PRs its own pre-flight spend guard estimated
US$8.37–US$97.21 per PR over 20 passes and refused to run (portal runs
#282/#287: "refused before calling", no model call was made).  The v1
reviewer measured the same PR (cmik_apilix_12) at US$0.86 REAL in one
pass; the v2 guard estimated that PR at US$36.80.  The brake was the
messenger: 20 full-context passes do not fit this experiment's economy.

Design C1 (Adenda 6) — what changes, and ONLY this:

- **One call per PR.**  A single prompt walks the ACTIVE gate's claim
  classes (the 1.3.0's 19 under ``RB_CONFIG_GATE=v13``) in sections —
  one section per class carrying the v2's per-class guidance, including
  the citation-discipline addenda of Adenda 3's lever 1, byte-identical —
  and asks for one JSON object whose ``findings`` array mixes classes,
  each finding declaring its ``claim_type``.
- **No general pass in the base arm.**  The v2 paper allowed the base
  arm one extra free-form pass; with a single call there is no "extra
  pass" that keeps A/B parity, so both arms make THE SAME single call
  and the only differing field between arms is ``governance`` again.
  Both arms hunt only verifiable classes; the base arm emits without
  the gate, the ALMA arm is judged by the gate.

What does NOT change (the v2.1 pre-registration, §3):

- The gates 1.0.0–1.3.0 are untouched, byte for byte; candidates reach
  the gate in the identical ``Candidate`` format.
- Full-file context: the diff plus the complete head contents of every
  touched file, same per-PR context budget (default 60000 estimated
  tokens), same included/skipped/missing declaration.
- The exact-citation discipline, VERBATIM from the v2: the model must
  quote the exact text of every cited line, and the reviewer's anchor
  verification keeps a candidate only if the cited range exists in the
  head file and the quote matches it byte-for-byte at line level;
  ``evidence_text`` is filled from the head file, never the model's
  words.  Unanchored findings are dropped here, counted.
- The safety contract: same ``LLMSettings`` arming rules (ALLOW_REAL_LLM=1,
  API key, RB_MODEL_BASE_URL, model, positive RB_MAX_SPEND_USD), same
  payload corrections (no ``temperature``, no ``max_tokens``;
  ``max_completion_tokens``; HTTP error body excerpt in refusals), same
  fail-closed behaviour, cumulative cost checked after the call.  The
  pre-flight guard now covers the SINGLE pass: with the anchor PR's
  size its worst case is ~US$0.95 (paper §4), ~US$1.31 with the context
  budget saturated — under the signed US$6.50 brake with ~5x margin.

Selection: run configuration ``RB_CONFIG_REVIEWER=v21`` (default stays
``v1``); see ``agent/main.py``.  The v1 and v2 modules are untouched so
both experiments stay reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Mapping

from .alma_gate import KNOWN_CLAIM_TYPES, POLICY_VERSION as GATE_V1_VERSION
from .alma_gate_v11 import (
    KNOWN_CLAIM_TYPES_V11,
    POLICY_VERSION as GATE_V11_VERSION,
)
from .alma_gate_v12 import (
    KNOWN_CLAIM_TYPES_V12,
    POLICY_VERSION as GATE_V12_VERSION,
)
from .alma_gate_v13 import (
    KNOWN_CLAIM_TYPES_V13,
    POLICY_VERSION as GATE_V13_VERSION,
)
from .base_reviewer import Candidate
from .diff_parser import DiffIndex
from .llm_reviewer import (
    LLMSettings,
    RealLLMRefused,
    Transport,
    _estimate_tokens,
    _extract_findings,
    _urllib_transport,
)
from .llm_reviewer_v2 import (
    _ALL_CLAIM_HINTS,
    _CLASS_GUIDANCE,
    _CLASS_GUIDANCE_V11,
    _CLASS_GUIDANCE_V13,
    _load_head_files,
    _render_context,
    _resolve_context_budget,
)


REVIEWER_VERSION = "llm-reviewer/2.1.0"
SINGLE_PASS = "single"


def _resolve_gate_v21(
    config: Mapping[str, str],
) -> tuple[tuple[str, ...], dict[str, str], str]:
    """Resolve the active gate's (claim types, guidance, version) from
    RB_CONFIG_GATE — the same key agent/main.py selects the gate with,
    the same resolution as the v2 reviewer's (its refusal text differs
    only in naming this reviewer).  Default "v1": the frozen gate's 8
    classes."""

    gate_version = (config.get("gate") or "v1").strip().lower()
    if gate_version == "v1":
        return KNOWN_CLAIM_TYPES, _CLASS_GUIDANCE, GATE_V1_VERSION
    if gate_version == "v11":
        return KNOWN_CLAIM_TYPES_V11, _CLASS_GUIDANCE_V11, GATE_V11_VERSION
    if gate_version == "v12":
        return KNOWN_CLAIM_TYPES_V12, _CLASS_GUIDANCE_V11, GATE_V12_VERSION
    if gate_version == "v13":
        return KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V13_VERSION
    raise RealLLMRefused(
        f"backend=llm v2.1 refused: unknown gate version {gate_version!r}; "
        "expected 'v1', 'v11', 'v12' or 'v13' (RB_CONFIG_GATE); "
        "no model call was made"
    )


def _build_system_prompt(
    claim_types: tuple[str, ...], class_guidance: Mapping[str, str]
) -> str:
    """Compose the single-pass system prompt: one section per class.

    The per-class guidance text is the v2's, byte-identical (under
    gate=v13 that includes Adenda 3's citation-discipline addenda),
    and the citation contract sentences are the v2 template's own,
    verbatim — the exact-citation discipline is not paraphrased.
    """

    sections = "\n\n".join(
        f"--- CLASS {claim_type} ---\n{class_guidance[claim_type]}"
        for claim_type in claim_types
    )
    return (
        "You are a code reviewer examining ONE pull request. This single "
        f"pass looks for defects of the {len(claim_types)} classes listed "
        "below, one section per class. Report ONLY findings that belong "
        "to one of these classes, each finding under its exact "
        "claim_type.\n\n"
        f"{sections}\n\n"
        "Respond with a single JSON object and nothing else, of the "
        'form {"findings": [{"file": "path/in/repo.py", "start_line": '
        '12, "end_line": 12, "claim_type": "sql_injection", "message": '
        '"what is wrong and why", "evidence": ["the exact text of line '
        '12"]}]}. Lines refer to the file at the PR head, numbered '
        "exactly as shown. The evidence array must reproduce the cited "
        "lines EXACTLY as they appear in the file, one entry per line "
        "from start_line to end_line, without the line-number prefix. "
        "Cite the smallest line range that contains the evidence, and "
        "prefer lines that appear in the diff (added or context lines): "
        "the full files are context so you can judge the changed lines. "
        "If you find nothing that you can prove, return "
        '{"findings": []}.'
    )


@dataclass
class LLMRunInfoV21:
    """What the v2.1 run did, for the run log (never the key)."""

    model: str
    reviewer_version: str = REVIEWER_VERSION
    gate_version: str = GATE_V1_VERSION
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    estimated_cost_usd: float | None = None
    raw_findings: int = 0
    malformed_findings: int = 0
    unanchored_findings: int = 0
    calls: int = 0
    passes: list[str] = field(default_factory=list)
    context_token_budget: int = 0
    context_estimated_tokens: int = 0
    context_files_included: list[str] = field(default_factory=list)
    context_files_skipped_budget: list[str] = field(default_factory=list)
    context_files_missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "reviewer_version": self.reviewer_version,
            "gate_version": self.gate_version,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "raw_findings": self.raw_findings,
            "malformed_findings": self.malformed_findings,
            "unanchored_findings": self.unanchored_findings,
            "calls": self.calls,
            "passes": list(self.passes),
            "context_token_budget": self.context_token_budget,
            "context_estimated_tokens": self.context_estimated_tokens,
            "context_files_included": list(self.context_files_included),
            "context_files_skipped_budget": list(
                self.context_files_skipped_budget
            ),
            "context_files_missing": list(self.context_files_missing),
        }


class LLMReviewerV21:
    """Single-pass, full-context reviewer aligned with the frozen gate."""

    name = "alma-llm-reviewer-v21"

    def __init__(
        self,
        settings: LLMSettings,
        context_token_budget: int = 60000,
        repo_root: str | Path | None = None,
        transport: Transport | None = None,
        claim_types: tuple[str, ...] | None = None,
        class_guidance: Mapping[str, str] | None = None,
        gate_version: str = GATE_V1_VERSION,
    ) -> None:
        self.settings = settings
        self.context_token_budget = context_token_budget
        self.repo_root = (
            Path(repo_root) if repo_root is not None else Path("/work/repo")
        )
        self.transport = transport or _urllib_transport
        self.claim_types = (
            tuple(claim_types) if claim_types is not None else KNOWN_CLAIM_TYPES
        )
        self.class_guidance = (
            dict(class_guidance)
            if class_guidance is not None
            else dict(_CLASS_GUIDANCE)
        )
        self.gate_version = gate_version
        self.last_run_info: LLMRunInfoV21 | None = None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str],
        config: Mapping[str, str],
        transport: Transport | None = None,
    ) -> "LLMReviewerV21":
        claim_types, class_guidance, gate_version = _resolve_gate_v21(config)
        return cls(
            LLMSettings.from_env(env, config),
            context_token_budget=_resolve_context_budget(env, config),
            repo_root=(
                config.get("repo_root") or env.get("RB_REPO_ROOT") or "/work/repo"
            ),
            transport=transport,
            claim_types=claim_types,
            class_guidance=class_guidance,
            gate_version=gate_version,
        )

    # -- prompt / payload ------------------------------------------------

    def build_payload(
        self, diff_text: str, context_text: str
    ) -> dict[str, object]:
        # Same payload contract as v1/v2 (see llm_reviewer.build_payload):
        # no "temperature", no "max_tokens" — OpenAI reasoning models
        # reject both with HTTP 400; the output cap is
        # "max_completion_tokens".
        system_prompt = _build_system_prompt(
            self.claim_types, self.class_guidance
        )
        user_content = (
            f"PASS: {SINGLE_PASS}\n\n"
            "Review this pull request. First the diff, then the full "
            "contents of the touched files at the PR head.\n\n"
            f"=== DIFF ===\n{diff_text}\n\n{context_text}"
        )
        payload: dict[str, object] = {
            "model": self.settings.model,
            "max_completion_tokens": self.settings.max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        if self.settings.effort:
            payload["reasoning_effort"] = self.settings.effort
        return payload

    def worst_case_estimate(self, payload: dict[str, object]) -> float:
        """The pre-flight guard's number for the single pass, exposed so
        tests (and the run log) can quote the guard's own arithmetic."""

        estimated_input = sum(
            _estimate_tokens(str(message["content"]))
            for message in payload["messages"]
        )
        return self.settings.cost_usd(
            estimated_input, self.settings.max_output_tokens
        )

    # -- the review --------------------------------------------------------

    def review(
        self,
        *,
        diff_text: str,
        diff: DiffIndex,
        config: Mapping[str, str],
        mode: str = "alma",
        repo_root: str | Path | None = None,
    ) -> list[Candidate]:
        # `mode` is accepted for interface parity with the v2 reviewer
        # (agent/main.py passes it); it changes NOTHING here — both arms
        # make the same single call (pre-registration v2.1, §3).
        _ = mode
        settings = self.settings
        root = Path(repo_root) if repo_root is not None else self.repo_root
        if not root.is_dir():
            raise RealLLMRefused(
                f"backend=llm v2.1 refused: repo root {root} is not a "
                "directory; the v2.1 reviewer requires the mounted head "
                "checkout (RB_REPO_ROOT); no model call was made"
            )

        order = list(diff.files.keys())
        head_files, missing = _load_head_files(root, order)
        context_text, context_tokens, included, skipped = _render_context(
            head_files, order, self.context_token_budget
        )

        info = LLMRunInfoV21(
            model=settings.model,
            gate_version=self.gate_version,
            passes=[SINGLE_PASS],
            context_token_budget=self.context_token_budget,
            context_estimated_tokens=context_tokens,
            context_files_included=included,
            context_files_skipped_budget=skipped,
            context_files_missing=missing,
        )
        self.last_run_info = info

        payload = self.build_payload(diff_text, context_text)

        # Pre-flight spend guard over the SINGLE pass: refuse BEFORE
        # spending.  (The v2 summed this over 19-20 passes; that sum is
        # the number that killed the practice — Adenda 6.)
        worst_case = self.worst_case_estimate(payload)
        if worst_case > settings.max_spend_usd:
            raise RealLLMRefused(
                "backend=llm v2.1 refused before calling: worst-case "
                f"estimate US${worst_case:.4f} over 1 pass "
                f"exceeds RB_MAX_SPEND_USD=US${settings.max_spend_usd:.4f}; "
                "no model call was made"
            )

        content, usage = self._call(payload)
        info.calls = 1

        if usage is not None and usage.get("prompt_tokens") is not None:
            prompt_tokens = int(usage["prompt_tokens"])
            completion_tokens = int(usage.get("completion_tokens") or 0)
        else:
            prompt_tokens = sum(
                _estimate_tokens(str(m["content"]))
                for m in payload["messages"]
            )
            completion_tokens = _estimate_tokens(str(content))
        total_cost = settings.cost_usd(prompt_tokens, completion_tokens)
        info.prompt_tokens = prompt_tokens
        info.completion_tokens = completion_tokens
        info.estimated_cost_usd = total_cost
        if total_cost > settings.max_spend_usd:
            raise RealLLMRefused(
                "cumulative reported cost US$"
                f"{total_cost:.4f} exceeds RB_MAX_SPEND_USD="
                f"US${settings.max_spend_usd:.4f}; failing closed "
                "without emitting findings"
            )

        raw_findings = _extract_findings(content)
        info.raw_findings = len(raw_findings)
        candidates: list[Candidate] = []
        seen: set[tuple[str, int, int, str, str]] = set()
        for raw in raw_findings:
            candidate = self._to_candidate_v21(raw, head_files, info)
            if candidate is None:
                continue
            key = (
                candidate.file,
                candidate.start_line,
                candidate.end_line,
                candidate.claim_type,
                candidate.message.strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
        return candidates

    # -- one model call ---------------------------------------------------

    def _call(self, payload: dict[str, object]) -> tuple[object, dict | None]:
        """Run the single chat-completions call; (content, usage-or-None)."""

        settings = self.settings
        status, body = self.transport(
            settings.chat_url(),
            settings.headers(),
            payload,
            settings.timeout_seconds,
        )
        if status != 200:
            # Same rule as v1/v2: include a bounded excerpt of the error
            # body — the bare status cost an afternoon on 2026-10-19.
            excerpt = " ".join(body.decode("utf-8", errors="replace").split())[:400]
            detail = f" — body: {excerpt}" if excerpt else ""
            raise RealLLMRefused(
                f"model endpoint returned HTTP {status}; "
                f"failing closed without emitting findings{detail}"
            )
        try:
            response = json.loads(body.decode("utf-8"))
            content = response["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError) as exc:
            raise RealLLMRefused(
                "model response is not valid chat-completions JSON; "
                "failing closed without emitting findings"
            ) from exc
        usage = response.get("usage") if isinstance(response, dict) else None
        return content, usage if isinstance(usage, dict) else None

    # -- candidate conversion + anchoring ----------------------------------

    def _to_candidate_v21(
        self,
        raw: object,
        head_files: Mapping[str, list[str]],
        info: LLMRunInfoV21,
    ) -> Candidate | None:
        """Convert one raw finding, verifying its anchor against the head.

        Same discipline as the v2: malformed shapes are counted as
        malformed; a finding whose claim_type is not one of the ACTIVE
        gate's classes is malformed too (in a single mixed pass, the
        class discipline is enforced here instead of by the pass);
        findings whose cited lines do not exist in the head file or
        whose quoted evidence does not match it exactly are counted as
        unanchored.  Both are dropped in the reviewer, before the gate.
        """

        if not isinstance(raw, dict):
            info.malformed_findings += 1
            return None
        file = raw.get("file")
        start = raw.get("start_line")
        end = raw.get("end_line", start)
        claim_type = raw.get("claim_type")
        message = raw.get("message")
        evidence = raw.get("evidence")
        if not isinstance(file, str) or not file.strip():
            info.malformed_findings += 1
            return None
        if not isinstance(start, int) or isinstance(start, bool):
            info.malformed_findings += 1
            return None
        if not isinstance(end, int) or isinstance(end, bool):
            info.malformed_findings += 1
            return None
        if not isinstance(claim_type, str) or not claim_type.strip():
            info.malformed_findings += 1
            return None
        if not isinstance(message, str) or not message.strip():
            info.malformed_findings += 1
            return None
        if start < 1 or end < start or end - start > 500:
            info.malformed_findings += 1
            return None
        claim_type = claim_type.strip()
        if claim_type not in self.claim_types:
            info.malformed_findings += 1
            return None

        file = file.strip().removeprefix("./")
        lines = head_files.get(file)
        if lines is None or end > len(lines):
            info.unanchored_findings += 1
            return None
        actual = tuple(lines[start - 1 : end])
        if (
            not isinstance(evidence, list)
            or len(evidence) != end - start + 1
            or any(not isinstance(item, str) for item in evidence)
            or tuple(evidence) != actual
        ):
            info.unanchored_findings += 1
            return None

        severity_hint, category_hint = _ALL_CLAIM_HINTS.get(
            claim_type, ("high", "correctness")
        )
        return Candidate(
            rule_id=f"llm_v21_{claim_type}",
            claim_type=claim_type,
            file=file,
            start_line=start,
            end_line=end,
            message=message.strip(),
            evidence_text=actual,
            severity_hint=severity_hint,
            category_hint=category_hint,
            producer="alma-llm-reviewer-v21",
        )


__all__ = [
    "LLMReviewerV21",
    "LLMRunInfoV21",
    "REVIEWER_VERSION",
    "SINGLE_PASS",
]
