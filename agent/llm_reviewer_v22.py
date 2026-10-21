"""LLM reviewer v2.2 — triage over the diff, deep passes for what it marks.

Why this module exists (pre-registration: PREREGISTRO-REVIEWBENCH-V22.md,
frozen 2026-10-21; design C2 of Adenda 6 of PREREGISTRO-REVIEWBENCH-V2.md):
the two previous designs failed at opposite ends, both measured.  The v2
reviewer (``agent/llm_reviewer_v2.py``) hunted well — semaphore 8/8 base,
6/8 ALMA — but its pre-flight guard summed the worst case over 20
full-context passes (US$8.37–US$97.21 per real PR) and refused to run at
all (portal runs #282/#287).  The v2.1 reviewer (one pass, all 19 classes
in sections) fixed the economy and completed the practice, but the single
pass DILUTED on real, large PRs: base run #290 scored recall 0.4% — the
pre-registered flashlight test (base recall must beat the v1's 0.7%)
FAILED, the ALMA arm was never launched, and the v2.1 practice closed
with no valid verdict.

Design C2 — the middle point, and ONLY this changes:

- **A selection pass over the diff alone** (no head files): one call
  that reads only the changed lines and marks the ACTIVE gate's claim
  classes the diff plausibly introduces, in priority order.  The
  reviewer filters unknown classes, dedupes and applies a hard cap of
  ``MAX_DEEP_PASSES`` (5); marks beyond the cap are recorded as
  overflow in the run info, never silently dropped.  The selection
  produces NO findings — it only decides where the deep look goes.
- **Deep passes in the v2's exact format**, one per selected class:
  the v2's prompt template and per-class guidance are IMPORTED (under
  gate=v13 that includes Adenda 3's citation-discipline addenda,
  byte-identical), the context is the diff plus the complete head
  contents under the same per-PR budget, and the anchor verification
  and Candidate conversion follow the v2's discipline (a finding
  whose class does not match its pass is malformed).  Candidates
  reach the frozen gate in the identical format.
- **No general pass in either arm** (A/B parity, inherited from the
  v2.1 paper §3): both arms run the same selection and the same deep
  passes; the only differing field between arms is ``governance``.

The spend guard is two-stage and the DEGRADATION RULE is pre-registered
(paper §3c) — it replaces the v2's blanket refusal:

1. Pre-flight 1: if the selection pass's own worst case exceeds
   ``RB_MAX_SPEND_USD``, refuse before any call (fail closed, as
   always).  Nothing else is demanded up front: the full plan depends
   on the triage.
2. Pre-flight 2 (after the selection, before the deep passes): admit
   deep passes in priority order while (actual selection cost + sum
   of admitted deep worst cases) <= cap.  Marked classes that do not
   fit DO NOT RUN and are declared in the run info as a degradation
   record — the truncation is a datum of the run, never a silence.
3. Degenerate case — not one deep pass fits: the reviewer emits ONLY
   what the selection supports — one mixed single pass restricted to
   the marked classes (the v2.1's sectioned prompt, only those
   classes) over the diff alone, like the selection itself, if its
   worst case fits the remaining cap, declared via
   ``degradation.fallback_single_pass`` (paper Adenda 1).  If even
   that does not fit, it emits zero findings WITH the declaration
   recorded (``degradation.reason == "no_deep_pass_affordable"``) —
   never a mute refusal, never a zero disguised as "found nothing".
4. The cumulative reported-cost check after every call is inherited
   unchanged: if actual spend exceeds the cap, fail closed without
   emitting findings.

What does NOT change: the gates 1.0.0–1.3.0 are untouched, byte for
byte; the arming/payload safety contract is the v1's (ALLOW_REAL_LLM=1,
API key, RB_MODEL_BASE_URL, model, positive RB_MAX_SPEND_USD; no
``temperature``, no ``max_tokens``; ``max_completion_tokens``; HTTP
error body excerpt in refusals).

Selection: run configuration ``RB_CONFIG_REVIEWER=v22`` (default stays
``v1``); see ``agent/main.py``.  The v1, v2 and v2.1 modules are
untouched so all three experiments stay reproducible.
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
    _SYSTEM_PROMPT_TEMPLATE,
    _load_head_files,
    _render_context,
    _resolve_context_budget,
)
from .llm_reviewer_v21 import _build_system_prompt as _build_mixed_system_prompt


REVIEWER_VERSION = "llm-reviewer/2.2.0"
SELECTION_PASS = "selection"
FALLBACK_PASS = "fallback_single"
MAX_DEEP_PASSES = 5
DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS = 1024


def _resolve_gate_v22(
    config: Mapping[str, str],
) -> tuple[tuple[str, ...], dict[str, str], str]:
    """Resolve the active gate's (claim types, guidance, version) from
    RB_CONFIG_GATE — the same key agent/main.py selects the gate with,
    the same resolution as the v2/v2.1 reviewers'.  Default "v1"."""

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
        f"backend=llm v2.2 refused: unknown gate version {gate_version!r}; "
        "expected 'v1', 'v11', 'v12' or 'v13' (RB_CONFIG_GATE); "
        "no model call was made"
    )


def _resolve_triage_max_output_tokens(
    env: Mapping[str, str], config: Mapping[str, str]
) -> int:
    raw = (config.get("triage_max_output_tokens") or "").strip()
    source = "RB_CONFIG_TRIAGE_MAX_OUTPUT_TOKENS"
    if not raw:
        raw = (env.get("RB_LLM_V22_TRIAGE_MAX_OUTPUT_TOKENS") or "").strip()
        source = "RB_LLM_V22_TRIAGE_MAX_OUTPUT_TOKENS"
    if not raw:
        return DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RealLLMRefused(
            f"backend=llm v2.2 refused: {source}={raw!r} is not an integer"
        ) from exc
    if value <= 0:
        raise RealLLMRefused(
            f"backend=llm v2.2 refused: {source} must be positive"
        )
    return value


def _build_selection_system_prompt(
    claim_types: tuple[str, ...], class_guidance: Mapping[str, str]
) -> str:
    """The triage prompt: the v2's per-class guidance, byte-identical,
    reframed as marking instructions over the diff alone."""

    sections = "\n\n".join(
        f"--- CLASS {claim_type} ---\n{class_guidance[claim_type]}"
        for claim_type in claim_types
    )
    return (
        "You are a code reviewer triaging ONE pull request. Below are "
        f"the {len(claim_types)} defect classes a deep review can "
        "verify, one section per class with the evidence each class "
        "requires. Read ONLY the diff and mark the classes the diff "
        "plausibly introduces — the candidates for a deep, full-file "
        "review. Judge from the changed lines alone: mark a class when "
        "the diff contains code of the shape the class describes, even "
        "if you cannot yet prove the defect (proving it is the deep "
        "pass's job). Order your marks by priority, most likely first. "
        f"Mark at most {MAX_DEEP_PASSES} classes; if more seem "
        f"possible, the {MAX_DEEP_PASSES} most likely. Respond with a "
        "single JSON object and nothing else, of the form "
        '{"candidates": [{"claim_type": "sql_injection", "reason": '
        '"one short phrase: what in the diff suggests it"}]}. '
        "claim_type must be exactly one of the class names below. If "
        'the diff suggests none of them, return {"candidates": []}.\n\n'
        f"{sections}"
    )


def _extract_selection(content: object) -> list[object]:
    """Pull the candidates array out of the selection content, strictly
    (same fail-closed philosophy as _extract_findings)."""

    if not isinstance(content, str):
        raise RealLLMRefused("model content is not text; failing closed")
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
    except ValueError as exc:
        raise RealLLMRefused(
            "selection pass did not return parseable JSON; failing closed"
        ) from exc
    if isinstance(parsed, dict):
        candidates = parsed.get("candidates")
    elif isinstance(parsed, list):
        candidates = parsed
    else:
        candidates = None
    if not isinstance(candidates, list):
        raise RealLLMRefused(
            "selection pass JSON has no candidates array; failing closed"
        )
    return candidates


@dataclass
class LLMRunInfoV22:
    """What the v2.2 run did, for the run log (never the key)."""

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
    # The C2 record: what the triage marked, what ran, what degraded.
    selection_candidates: list[str] = field(default_factory=list)
    selection_selected: list[str] = field(default_factory=list)
    selection_overflow: list[str] = field(default_factory=list)
    selection_unknown_marks: int = 0
    selection_malformed_entries: int = 0
    degradation: dict[str, object] | None = None

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
            "selection_candidates": list(self.selection_candidates),
            "selection_selected": list(self.selection_selected),
            "selection_overflow": list(self.selection_overflow),
            "selection_unknown_marks": self.selection_unknown_marks,
            "selection_malformed_entries": self.selection_malformed_entries,
            "degradation": self.degradation,
        }


class LLMReviewerV22:
    """Triage + deep-pass reviewer aligned with the frozen gate."""

    name = "alma-llm-reviewer-v22"

    def __init__(
        self,
        settings: LLMSettings,
        context_token_budget: int = 60000,
        repo_root: str | Path | None = None,
        transport: Transport | None = None,
        claim_types: tuple[str, ...] | None = None,
        class_guidance: Mapping[str, str] | None = None,
        gate_version: str = GATE_V1_VERSION,
        triage_max_output_tokens: int = DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS,
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
        self.triage_max_output_tokens = triage_max_output_tokens
        self.last_run_info: LLMRunInfoV22 | None = None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str],
        config: Mapping[str, str],
        transport: Transport | None = None,
    ) -> "LLMReviewerV22":
        claim_types, class_guidance, gate_version = _resolve_gate_v22(config)
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
            triage_max_output_tokens=_resolve_triage_max_output_tokens(
                env, config
            ),
        )

    # -- payloads ---------------------------------------------------------

    def _payload(
        self, system_prompt: str, user_content: str, max_output_tokens: int
    ) -> dict[str, object]:
        # Same payload contract as v1/v2/v2.1: no "temperature", no
        # "max_tokens"; the output cap is "max_completion_tokens".
        payload: dict[str, object] = {
            "model": self.settings.model,
            "max_completion_tokens": max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        if self.settings.effort:
            payload["reasoning_effort"] = self.settings.effort
        return payload

    def build_selection_payload(self, diff_text: str) -> dict[str, object]:
        system_prompt = _build_selection_system_prompt(
            self.claim_types, self.class_guidance
        )
        user_content = (
            f"PASS: {SELECTION_PASS}\n\n"
            "Triage this pull request from its diff alone. Mark the "
            "defect classes the changed lines plausibly introduce, in "
            "priority order.\n\n"
            f"=== DIFF ===\n{diff_text}"
        )
        return self._payload(
            system_prompt, user_content, self.triage_max_output_tokens
        )

    def build_deep_payload(
        self, pass_name: str, diff_text: str, context_text: str
    ) -> dict[str, object]:
        """A deep pass payload: the v2's, built from its own template
        and guidance (imported, not paraphrased)."""

        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            claim_type=pass_name, guidance=self.class_guidance[pass_name]
        )
        user_content = (
            f"PASS: {pass_name}\n\n"
            "Review this pull request. First the diff, then the full "
            "contents of the touched files at the PR head.\n\n"
            f"=== DIFF ===\n{diff_text}\n\n{context_text}"
        )
        return self._payload(
            system_prompt, user_content, self.settings.max_output_tokens
        )

    def build_fallback_payload(
        self,
        selected: list[str],
        diff_text: str,
    ) -> dict[str, object]:
        """The degenerate-case mixed pass: the v2.1's sectioned prompt
        restricted to the classes the selection marked, over the diff
        alone (paper Adenda 1) — that is what makes it affordable when
        no full-context deep pass fits."""

        system_prompt = _build_mixed_system_prompt(
            tuple(selected), self.class_guidance
        )
        user_content = (
            f"PASS: {FALLBACK_PASS}\n\n"
            "Review this pull request from its diff. The deep review "
            "was not affordable under the spend cap, so this single "
            "pass covers only the classes the triage marked.\n\n"
            f"=== DIFF ===\n{diff_text}"
        )
        return self._payload(
            system_prompt, user_content, self.settings.max_output_tokens
        )

    # -- guard arithmetic ---------------------------------------------------

    def worst_case_estimate(self, payload: dict[str, object]) -> float:
        """Worst case of ONE payload under its own output cap, exposed
        so tests (and the run log) can quote the guard's arithmetic."""

        estimated_input = sum(
            _estimate_tokens(str(message["content"]))
            for message in payload["messages"]
        )
        return self.settings.cost_usd(
            estimated_input, int(payload["max_completion_tokens"])
        )

    # -- one model call -----------------------------------------------------

    def _call(self, payload: dict[str, object]) -> tuple[object, dict | None]:
        """Run one chat-completions call; (content, usage-or-None)."""

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

    def _account(
        self,
        payload: dict[str, object],
        content: object,
        usage: dict | None,
        info: LLMRunInfoV22,
        running: dict[str, float],
    ) -> float:
        """Fold one call's usage into the run totals; enforce the
        cumulative cap (fail closed) exactly like the other reviewers.
        Returns this call's reported cost."""

        settings = self.settings
        if usage is not None and usage.get("prompt_tokens") is not None:
            prompt_tokens = int(usage["prompt_tokens"])
            completion_tokens = int(usage.get("completion_tokens") or 0)
        else:
            prompt_tokens = sum(
                _estimate_tokens(str(m["content"]))
                for m in payload["messages"]
            )
            completion_tokens = _estimate_tokens(str(content))
        cost = settings.cost_usd(prompt_tokens, completion_tokens)
        running["prompt"] += prompt_tokens
        running["completion"] += completion_tokens
        running["cost"] += cost
        info.prompt_tokens = int(running["prompt"])
        info.completion_tokens = int(running["completion"])
        info.estimated_cost_usd = running["cost"]
        if running["cost"] > settings.max_spend_usd:
            raise RealLLMRefused(
                "cumulative reported cost US$"
                f"{running['cost']:.4f} exceeds RB_MAX_SPEND_USD="
                f"US${settings.max_spend_usd:.4f}; failing closed "
                "without emitting findings"
            )
        return cost

    # -- the review ----------------------------------------------------------

    def review(
        self,
        *,
        diff_text: str,
        diff: DiffIndex,
        config: Mapping[str, str],
        mode: str = "alma",
        repo_root: str | Path | None = None,
    ) -> list[Candidate]:
        # `mode` is accepted for interface parity with the v2/v2.1
        # reviewers (agent/main.py passes it); it changes NOTHING here —
        # both arms run the same selection and the same deep passes
        # (pre-registration v2.2, §3b: no general pass in either arm).
        _ = mode
        settings = self.settings
        root = Path(repo_root) if repo_root is not None else self.repo_root
        if not root.is_dir():
            raise RealLLMRefused(
                f"backend=llm v2.2 refused: repo root {root} is not a "
                "directory; the v2.2 reviewer requires the mounted head "
                "checkout (RB_REPO_ROOT); no model call was made"
            )

        order = list(diff.files.keys())
        head_files, missing = _load_head_files(root, order)
        context_text, context_tokens, included, skipped = _render_context(
            head_files, order, self.context_token_budget
        )

        info = LLMRunInfoV22(
            model=settings.model,
            gate_version=self.gate_version,
            passes=[SELECTION_PASS],
            context_token_budget=self.context_token_budget,
            context_estimated_tokens=context_tokens,
            context_files_included=included,
            context_files_skipped_budget=skipped,
            context_files_missing=missing,
        )
        self.last_run_info = info
        running = {"prompt": 0, "completion": 0, "cost": 0.0}
        cap = settings.max_spend_usd

        # ---- Stage (a): the selection pass over the diff alone. ----
        selection_payload = self.build_selection_payload(diff_text)
        selection_worst = self.worst_case_estimate(selection_payload)
        # Pre-flight 1 (paper §3c.1): the selection alone must fit.
        if selection_worst > cap:
            raise RealLLMRefused(
                "backend=llm v2.2 refused before calling: worst-case "
                f"estimate US${selection_worst:.4f} for the selection "
                f"pass exceeds RB_MAX_SPEND_USD=US${cap:.4f}; "
                "no model call was made"
            )
        content, usage = self._call(selection_payload)
        info.calls += 1
        selection_cost = self._account(
            selection_payload, content, usage, info, running
        )
        selected, overflow = self._filter_selection(
            _extract_selection(content), info
        )
        info.selection_selected = list(selected)
        info.selection_overflow = list(overflow)

        candidates: list[Candidate] = []
        seen: set[tuple[str, int, int, str, str]] = set()
        if not selected:
            # The triage marked nothing: a declared outcome (the run
            # info shows an empty selection), not an error.
            return candidates

        # ---- Pre-flight 2 (paper §3c.2): plan the deep passes. ----
        deep_payloads = {
            name: self.build_deep_payload(name, diff_text, context_text)
            for name in selected
        }
        admitted: list[str] = []
        dropped: list[str] = []
        planned_cost = selection_cost
        for name in selected:
            worst = self.worst_case_estimate(deep_payloads[name])
            if planned_cost + worst <= cap:
                admitted.append(name)
                planned_cost += worst
            else:
                dropped.append(name)

        if admitted:
            if dropped:
                info.degradation = {
                    "reason": "spend_cap",
                    "deep_passes_planned": len(selected),
                    "deep_passes_run": len(admitted),
                    "deep_passes_dropped": list(dropped),
                    "fallback_single_pass": False,
                }
            for name in admitted:
                payload = deep_payloads[name]
                content, usage = self._call(payload)
                info.calls += 1
                info.passes.append(name)
                self._account(payload, content, usage, info, running)
                self._collect(
                    content, name, selected, head_files, info, candidates, seen
                )
            return candidates

        # ---- Degenerate case (paper §3c.3): emit only what the
        # selection supports — one mixed pass over the marked classes.
        fallback_payload = self.build_fallback_payload(selected, diff_text)
        if selection_cost + self.worst_case_estimate(fallback_payload) <= cap:
            info.degradation = {
                "reason": "spend_cap",
                "deep_passes_planned": len(selected),
                "deep_passes_run": 0,
                "deep_passes_dropped": list(selected),
                "fallback_single_pass": True,
            }
            content, usage = self._call(fallback_payload)
            info.calls += 1
            info.passes.append(FALLBACK_PASS)
            self._account(fallback_payload, content, usage, info, running)
            self._collect(
                content, None, selected, head_files, info, candidates, seen
            )
            return candidates

        info.degradation = {
            "reason": "no_deep_pass_affordable",
            "deep_passes_planned": len(selected),
            "deep_passes_run": 0,
            "deep_passes_dropped": list(selected),
            "fallback_single_pass": False,
        }
        return candidates

    # -- selection filtering --------------------------------------------------

    def _filter_selection(
        self, raw_entries: list[object], info: LLMRunInfoV22
    ) -> tuple[list[str], list[str]]:
        """Filter the triage's marks: known active classes only, first
        occurrence wins, hard cap MAX_DEEP_PASSES.  Returns (selected,
        overflow); everything rejected is counted in the run info."""

        valid: list[str] = []
        for entry in raw_entries:
            if not isinstance(entry, dict):
                info.selection_malformed_entries += 1
                continue
            claim_type = entry.get("claim_type")
            if not isinstance(claim_type, str) or not claim_type.strip():
                info.selection_malformed_entries += 1
                continue
            claim_type = claim_type.strip()
            if claim_type not in self.claim_types:
                info.selection_unknown_marks += 1
                continue
            if claim_type in valid:
                continue
            valid.append(claim_type)
        info.selection_candidates = list(valid)
        return valid[:MAX_DEEP_PASSES], valid[MAX_DEEP_PASSES:]

    # -- findings collection ----------------------------------------------------

    def _collect(
        self,
        content: object,
        pass_name: str | None,
        allowed: list[str],
        head_files: Mapping[str, list[str]],
        info: LLMRunInfoV22,
        candidates: list[Candidate],
        seen: set[tuple[str, int, int, str, str]],
    ) -> None:
        raw_findings = _extract_findings(content)
        info.raw_findings += len(raw_findings)
        for raw in raw_findings:
            candidate = self._to_candidate_v22(
                raw, pass_name, allowed, head_files, info
            )
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

    def _to_candidate_v22(
        self,
        raw: object,
        pass_name: str | None,
        allowed: list[str],
        head_files: Mapping[str, list[str]],
        info: LLMRunInfoV22,
    ) -> Candidate | None:
        """Convert one raw finding, verifying its anchor against the head.

        The v2's discipline, unchanged: malformed shapes are counted
        as malformed; in a deep pass, a finding whose claim_type does
        not match its pass is malformed; in the fallback pass, a
        finding outside the classes the selection marked is malformed;
        findings whose cited lines do not exist in the head file or
        whose quoted evidence does not match it exactly are counted as
        unanchored.  Both are dropped here, before the frozen gate.
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
        if pass_name is not None and claim_type != pass_name:
            info.malformed_findings += 1
            return None
        if pass_name is None and claim_type not in allowed:
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
            rule_id=f"llm_v22_{claim_type}",
            claim_type=claim_type,
            file=file,
            start_line=start,
            end_line=end,
            message=message.strip(),
            evidence_text=actual,
            severity_hint=severity_hint,
            category_hint=category_hint,
            producer="alma-llm-reviewer-v22",
        )


__all__ = [
    "DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS",
    "FALLBACK_PASS",
    "LLMReviewerV22",
    "LLMRunInfoV22",
    "MAX_DEEP_PASSES",
    "REVIEWER_VERSION",
    "SELECTION_PASS",
]
