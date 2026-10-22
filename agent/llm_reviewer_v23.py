"""LLM reviewer v2.3 — generalized selection, deep passes per mark.

Why this module exists (pre-registration: PREREGISTRO-REVIEWBENCH-V23.md,
frozen 2026-10-21, path A chosen by Alejandro after the v2.2 practice
closed with no valid verdict): four practices (v1, v2, v2.1, v2.2)
produced not one valid ALMA-arm score, and the diagnosis measured
why.  The public adjudicated gold holds 352 true positives; 343 of
them (97.4%) fall OUTSIDE the 19 gate classes the reviewers were
allowed to look for — the classes-only structural ceiling is 0.3%
strict (1/352) to 2.6% generous (9/352).  The only grounded base ever
measured (v1, run #251: P 42.9% · R 0.7%) got its 3 TPs from its
unrestricted general pass.  In run #295 all 9 reachable TPs were lost
at the SELECTION event: the 19-class framing blinded the triage, in
two opposite architectures (C1 one pass, C2 triage + deep passes).

Design v2.3 — ONLY this changes against v2.2:

- **Generalized selection over the diff alone**: one call marks, in
  ONE priority list mixing both families, (i) the benchmark's nine
  public general categories — correctness, reliability,
  maintainability, testing, security, documentation,
  api-architecture, performance, accessibility — each with a brief
  guidance derived from its public name alone, and (ii) the active
  gate's defect classes as the specialty family (under gate=v13/v14
  the 19 classes, guidance byte-identical to the v2's, citation
  addenda included).  Anti-fishing declaration (paper §3a, binding):
  the taxonomy comes from the benchmark's PUBLIC documentation — a
  syllabus, not answers; nothing in any prompt or test here derives
  from the per-PR detail of the gold, and no diagnosed case receives
  special treatment.  Unknown marks are discarded and counted,
  duplicates keep their first position, and the hard cap of
  ``MAX_DEEP_PASSES`` (5) is SHARED across both families; marks
  beyond it are recorded as overflow, per family in the run info
  (``selection_general`` / ``selection_specialty`` /
  ``selection_overflow``).  The selection produces NO findings.
- **Deep passes per mark, in the v2's exact format**: a class mark
  runs the v2's class pass (imported template and guidance, full
  head context, same anchor verification); a category mark runs a
  general pass of that category — the SAME imported template and
  context, its guidance the category's public description plus the
  instruction to report only defects of that category, with the same
  exact-citation discipline.  There is no free-form pass.  A finding
  whose claim_type does not equal its pass's mark is malformed.  In
  the base arm every anchor-verified candidate is emitted; in the
  ALMA arm the gate decides (gate=v14: specialty findings are judged
  by the 1.4.0's frontier, general findings are held as
  needs_validation and never emitted — that is the gate's doing, in
  agent/alma_gate_v14.py, not this reviewer's).

What does NOT change (paper §3c, §5): the two-stage guard and the
degradation rule are inherited from the v2.2 unchanged — pre-flight 1
refuses only if the selection's own worst case exceeds the cap;
pre-flight 2 admits deep passes in priority order while they fit and
DECLARES the dropped ones; the degenerate case runs one mixed
diff-only pass restricted to the marked marks (both families,
sectioned by family) or emits zero findings WITH the declaration —
truncation is a datum, never a refusal, never a silence.  The
cumulative reported-cost check after every call fails closed as
always.  The gates 1.0.0–1.3.0 are untouched, byte for byte; the
arming/payload safety contract is the v1's (ALLOW_REAL_LLM=1, API
key, RB_MODEL_BASE_URL, model, positive RB_MAX_SPEND_USD; no
``temperature``, no ``max_tokens``; ``max_completion_tokens``).

Fix v2.3.1 (2026-10-21, diagnosis of practice run #296 —
DIAGNOSTICO-PRACTICA-V23-20261021.md, cause (d)): the generalized
selection, the one stage that changed against v2.2, inherited the
1,024-token completion ceiling unchanged; on real diffs the model's
reasoning over 28 marks exhausts that budget (the ceiling discounts
reasoning AND visible output), the content comes back empty or
truncated mid-JSON, and the reviewer fails closed at the selection
parse — 20 of 35 attempts died there, one whole shard by the
platform's preflight rule.  Two changes, nothing else:

- The DEFAULT selection completion ceiling is 4,096 tokens
  (``DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS``), the same ceiling the deep
  passes already run under.  The measured v2.3.0 behavior stays
  reproducible by configuration: pin
  ``RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS=1024`` (env) or
  ``triage_max_output_tokens=1024`` (RB_CONFIG_TRIAGE_MAX_OUTPUT_
  TOKENS) and the selection budget is exactly the one run #296
  died under; every other byte of behavior is unchanged.
- Parse failures are no longer blind: when any pass's content does
  not parse or comes back empty, the run info settles a
  ``parse_failures`` record (pass, ``finish_reason``, content
  length, a bounded 500-char excerpt) and the refusal message
  carries the same data, so the agent log shows WHY the content
  failed.  The fail-closed rule itself does not move: an
  unparseable response still emits nothing.

Selection: run configuration ``RB_CONFIG_REVIEWER=v23`` (default stays
``v1``); see ``agent/main.py``.  Arms (paper §3d): base gate=v13,
ALMA gate=v14 — the first gate divergence between arm configs,
declared as part of the design: the gate IS the governance
difference.  The v1, v2, v2.1 and v2.2 modules are untouched so all
four experiments stay reproducible.
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
from .alma_gate_v14 import (
    GENERAL_CATEGORIES_V14,
    POLICY_VERSION as GATE_V14_VERSION,
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


REVIEWER_VERSION = "llm-reviewer/2.3.1"
SELECTION_PASS = "selection"
FALLBACK_PASS = "fallback_single"
MAX_DEEP_PASSES = 5
# v2.3.0 shipped 1024 here, inherited unchanged from v2/v2.1/v2.2 —
# the ceiling run #296 died under (module docstring, fix v2.3.1).
# 4096 is the ceiling the deep passes already run under
# (LLMSettings.max_output_tokens default).  Pin the env/config
# (RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS / RB_CONFIG_TRIAGE_MAX_
# OUTPUT_TOKENS) to 1024 to reproduce the measured v2.3.0 budget.
DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS = 4096
PARSE_FAILURE_EXCERPT_CHARS = 500

# The nine general categories (paper §3a): the benchmark's own public
# taxonomy labels, in the paper's order.  The guidance of each is a
# brief description derived from the label's public meaning alone —
# the syllabus, not the answers.
GENERAL_CATEGORIES = GENERAL_CATEGORIES_V14

CATEGORY_GUIDANCE: dict[str, str] = {
    "correctness": (
        "the change computes the wrong thing: logic or condition "
        "errors, the wrong variable or operator, off-by-one, "
        "mishandled edge cases, state updated incorrectly or not "
        "at all"
    ),
    "reliability": (
        "the change can fail, hang, leak or lose data at runtime: "
        "unhandled errors, swallowed failures, resource leaks, "
        "races, missing cleanup, unsafe retries or timeouts"
    ),
    "maintainability": (
        "the change makes the code harder to change safely: "
        "duplicated logic, dead code, misleading names, tangled "
        "responsibilities, needless complexity"
    ),
    "testing": (
        "the change weakens the test suite: missing or broken tests "
        "for changed behaviour, assertions that cannot fail, tests "
        "disabled or skipped without cause"
    ),
    "security": (
        "the change weakens security: injection, broken access "
        "control, secrets in code, unsafe deserialization, disabled "
        "verification, weak cryptography or randomness"
    ),
    "documentation": (
        "the change makes documentation wrong or missing: comments "
        "or docs that contradict the code, undocumented public "
        "behaviour changes"
    ),
    "api-architecture": (
        "the change breaks or degrades the interface: incompatible "
        "signature or contract changes, inconsistent error "
        "behaviour, layering violations, public API misuse"
    ),
    "performance": (
        "the change wastes resources: quadratic or repeated work, "
        "N+1 queries, unbounded loops or buffers, blocking calls "
        "on hot paths"
    ),
    "accessibility": (
        "the change harms accessibility: removed labels or alt "
        "text, keyboard traps, focus loss, contrast or semantics "
        "regressions"
    ),
}

# The deep-pass guidance of a category: its public description plus
# the instruction to report only defects of that category (the v2
# template's own "Report ONLY findings of this class" discipline is
# carried by the template itself).
CATEGORY_GUIDANCE_DEEP: dict[str, str] = {
    name: f"{text} Report only defects of this category."
    for name, text in CATEGORY_GUIDANCE.items()
}

CATEGORY_HINTS: dict[str, tuple[str, str]] = {
    "correctness": ("high", "correctness"),
    "reliability": ("medium", "reliability"),
    "maintainability": ("low", "maintainability"),
    "testing": ("low", "testing"),
    "security": ("high", "security"),
    "documentation": ("low", "documentation"),
    "api-architecture": ("medium", "api-architecture"),
    "performance": ("medium", "performance"),
    "accessibility": ("medium", "accessibility"),
}


def _resolve_gate_v23(
    config: Mapping[str, str],
) -> tuple[tuple[str, ...], dict[str, str], str]:
    """Resolve the active gate's (claim types, guidance, version) from
    RB_CONFIG_GATE — the same key agent/main.py selects the gate with.
    The specialty family of the selection is the active gate's class
    set; gate=v14 carries the 1.3.0's 19 classes (the 1.4.0 inherits
    them by delegation).  Default "v1"."""

    gate_version = (config.get("gate") or "v1").strip().lower()
    if gate_version == "v1":
        return KNOWN_CLAIM_TYPES, _CLASS_GUIDANCE, GATE_V1_VERSION
    if gate_version == "v11":
        return KNOWN_CLAIM_TYPES_V11, _CLASS_GUIDANCE_V11, GATE_V11_VERSION
    if gate_version == "v12":
        return KNOWN_CLAIM_TYPES_V12, _CLASS_GUIDANCE_V11, GATE_V12_VERSION
    if gate_version == "v13":
        return KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V13_VERSION
    if gate_version == "v14":
        return KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V14_VERSION
    raise RealLLMRefused(
        f"backend=llm v2.3 refused: unknown gate version {gate_version!r}; "
        "expected 'v1', 'v11', 'v12', 'v13' or 'v14' (RB_CONFIG_GATE); "
        "no model call was made"
    )


def _resolve_triage_max_output_tokens(
    env: Mapping[str, str], config: Mapping[str, str]
) -> int:
    raw = (config.get("triage_max_output_tokens") or "").strip()
    source = "RB_CONFIG_TRIAGE_MAX_OUTPUT_TOKENS"
    if not raw:
        raw = (env.get("RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS") or "").strip()
        source = "RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS"
    if not raw:
        return DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RealLLMRefused(
            f"backend=llm v2.3 refused: {source}={raw!r} is not an integer"
        ) from exc
    if value <= 0:
        raise RealLLMRefused(
            f"backend=llm v2.3 refused: {source} must be positive"
        )
    return value


def _build_selection_system_prompt(
    claim_types: tuple[str, ...], class_guidance: Mapping[str, str]
) -> str:
    """The generalized triage prompt (paper §3a): the nine public
    categories with their brief guidance, then the active gate's
    classes with the v2's guidance byte-identical.  One priority list
    mixes both families."""

    category_sections = "\n\n".join(
        f"--- CATEGORY {name} ---\n{CATEGORY_GUIDANCE[name]}"
        for name in GENERAL_CATEGORIES
    )
    class_sections = "\n\n".join(
        f"--- CLASS {claim_type} ---\n{class_guidance[claim_type]}"
        for claim_type in claim_types
    )
    return (
        "You are a code reviewer triaging ONE pull request. A deep "
        "review can verify two families of marks: general defect "
        f"categories ({len(GENERAL_CATEGORIES)} sections marked "
        "CATEGORY) and specific defect classes "
        f"({len(claim_types)} sections marked CLASS, each with the "
        "evidence that class requires). Read ONLY the diff and mark "
        "what the diff plausibly introduces — the candidates for a "
        "deep, full-file review. Judge from the changed lines alone: "
        "mark a category or class when the diff contains code of the "
        "shape it describes, even if you cannot yet prove the defect "
        "(proving it is the deep pass's job). Order your marks by "
        "priority, most likely first, mixing both families in ONE "
        f"list. Mark at most {MAX_DEEP_PASSES} marks in total; if "
        f"more seem possible, the {MAX_DEEP_PASSES} most likely. "
        "Respond with a single JSON object and nothing else, of the "
        'form {"candidates": [{"mark": "sql_injection", "reason": '
        '"one short phrase: what in the diff suggests it"}]}. mark '
        "must be exactly one of the category or class names below. "
        'If the diff suggests none of them, return {"candidates": []}.'
        f"\n\n{category_sections}\n\n{class_sections}"
    )


def _build_mixed_system_prompt(
    marks: list[tuple[str, str]], class_guidance: Mapping[str, str]
) -> str:
    """The degenerate-case mixed prompt (paper §3c, inherited): one
    section per marked mark — categories and classes sectioned by
    family — over the diff alone.  The citation contract sentences
    are the v2 template's own, verbatim, as in the v2.1's builder."""

    sections = "\n\n".join(
        (
            f"--- CATEGORY {name} ---\n{CATEGORY_GUIDANCE[name]}"
            if kind == "category"
            else f"--- CLASS {name} ---\n{class_guidance[name]}"
        )
        for kind, name in marks
    )
    return (
        "You are a code reviewer examining ONE pull request. This single "
        f"pass looks for defects of the {len(marks)} marks listed "
        "below, one section per mark. Report ONLY findings that belong "
        "to one of these marks, each finding under its exact mark name "
        "as claim_type.\n\n"
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


def _parse_failure_record(
    pass_name: str, finish_reason: object, content: object
) -> dict[str, object]:
    """Settle WHY a pass's content failed to parse (fix v2.3.1,
    diagnosis §6(ii)): the finish_reason the endpoint reported and a
    bounded excerpt of the raw content, so the next death at this
    stage is read, not inferred.  Observability only — the caller
    still fails closed."""

    if isinstance(content, str):
        length: int | None = len(content)
        excerpt = content[:PARSE_FAILURE_EXCERPT_CHARS]
    else:
        length = None
        excerpt = f"<non-text content: {type(content).__name__}>"
    return {
        "pass": pass_name,
        "finish_reason": finish_reason,
        "content_length": length,
        "content_excerpt": excerpt,
    }


def _refuse_parse_failure(
    info: "LLMRunInfoV23",
    pass_name: str,
    exc: RealLLMRefused,
    finish_reason: object,
    content: object,
) -> None:
    """Record a parse failure in the run info and re-raise the
    refusal with the settled data appended, so it also reaches the
    agent log (main.py prints only the exception on a refusal).
    The original message stays the prefix — log contrasts built on
    it keep working.  Always raises."""

    record = _parse_failure_record(pass_name, finish_reason, content)
    info.parse_failures.append(record)
    excerpt_oneline = " ".join(str(record["content_excerpt"]).split())
    raise RealLLMRefused(
        f"{exc} [parse failure settled: pass={pass_name}, "
        f"finish_reason={finish_reason!r}, "
        f"content_length={record['content_length']}, "
        f"content_excerpt={excerpt_oneline!r}]"
    ) from exc


@dataclass
class LLMRunInfoV23:
    """What the v2.3 run did, for the run log (never the key)."""

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
    # The selection record: what was marked, per family, what ran,
    # what degraded (paper §3a: marks are settled per family).
    selection_candidates: list[str] = field(default_factory=list)
    selection_selected: list[str] = field(default_factory=list)
    selection_overflow: list[str] = field(default_factory=list)
    selection_general: list[str] = field(default_factory=list)
    selection_specialty: list[str] = field(default_factory=list)
    selection_unknown_marks: int = 0
    selection_malformed_entries: int = 0
    degradation: dict[str, object] | None = None
    # Fix v2.3.1 observability: the selection ceiling in force for
    # this run, and one settled record per unparseable response.
    triage_max_output_tokens: int = 0
    parse_failures: list[dict[str, object]] = field(default_factory=list)

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
            "selection_general": list(self.selection_general),
            "selection_specialty": list(self.selection_specialty),
            "selection_unknown_marks": self.selection_unknown_marks,
            "selection_malformed_entries": self.selection_malformed_entries,
            "degradation": self.degradation,
            "triage_max_output_tokens": self.triage_max_output_tokens,
            "parse_failures": [dict(r) for r in self.parse_failures],
        }


class LLMReviewerV23:
    """Generalized-selection + deep-pass reviewer (paper v2.3)."""

    name = "alma-llm-reviewer-v23"

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
        self.last_run_info: LLMRunInfoV23 | None = None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str],
        config: Mapping[str, str],
        transport: Transport | None = None,
    ) -> "LLMReviewerV23":
        claim_types, class_guidance, gate_version = _resolve_gate_v23(config)
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
        # Same payload contract as v1/v2/v2.1/v2.2: no "temperature",
        # no "max_tokens"; the output cap is "max_completion_tokens".
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
            "categories and classes the changed lines plausibly "
            "introduce, in priority order.\n\n"
            f"=== DIFF ===\n{diff_text}"
        )
        return self._payload(
            system_prompt, user_content, self.triage_max_output_tokens
        )

    def build_deep_payload(
        self, pass_name: str, diff_text: str, context_text: str
    ) -> dict[str, object]:
        """A deep pass payload: the v2's own template and context.  A
        class mark uses the class guidance imported from the v2
        (byte-identical payload to the v2/v2.2 for the same inputs);
        a category mark uses the category's deep guidance."""

        if pass_name in GENERAL_CATEGORIES:
            guidance = CATEGORY_GUIDANCE_DEEP[pass_name]
        else:
            guidance = self.class_guidance[pass_name]
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            claim_type=pass_name, guidance=guidance
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
        selected: list[tuple[str, str]],
        diff_text: str,
    ) -> dict[str, object]:
        """The degenerate-case mixed pass: the sectioned prompt
        restricted to the marks the selection made (both families),
        over the diff alone — that is what makes it affordable when
        no full-context deep pass fits."""

        system_prompt = _build_mixed_system_prompt(
            selected, self.class_guidance
        )
        user_content = (
            f"PASS: {FALLBACK_PASS}\n\n"
            "Review this pull request from its diff. The deep review "
            "was not affordable under the spend cap, so this single "
            "pass covers only the marks the triage made.\n\n"
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

    def _call(
        self, payload: dict[str, object]
    ) -> tuple[object, dict | None, object]:
        """Run one chat-completions call; (content, usage-or-None,
        finish_reason-or-None).  The finish_reason travels with the
        content so a later parse failure can settle WHY the content
        looks the way it does (fix v2.3.1)."""

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
            choice = response["choices"][0]
            content = choice["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError) as exc:
            raise RealLLMRefused(
                "model response is not valid chat-completions JSON; "
                "failing closed without emitting findings"
            ) from exc
        finish_reason = (
            choice.get("finish_reason") if isinstance(choice, dict) else None
        )
        usage = response.get("usage") if isinstance(response, dict) else None
        return content, usage if isinstance(usage, dict) else None, finish_reason


    def _account(
        self,
        payload: dict[str, object],
        content: object,
        usage: dict | None,
        info: LLMRunInfoV23,
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
        # `mode` is accepted for interface parity (agent/main.py
        # passes it); it changes NOTHING here — both arms run the
        # same selection and the same deep passes (paper §3d: the
        # arms differ only in the gate config they feed).
        _ = mode
        settings = self.settings
        root = Path(repo_root) if repo_root is not None else self.repo_root
        if not root.is_dir():
            raise RealLLMRefused(
                f"backend=llm v2.3 refused: repo root {root} is not a "
                "directory; the v2.3 reviewer requires the mounted head "
                "checkout (RB_REPO_ROOT); no model call was made"
            )

        order = list(diff.files.keys())
        head_files, missing = _load_head_files(root, order)
        context_text, context_tokens, included, skipped = _render_context(
            head_files, order, self.context_token_budget
        )

        info = LLMRunInfoV23(
            model=settings.model,
            gate_version=self.gate_version,
            passes=[SELECTION_PASS],
            triage_max_output_tokens=self.triage_max_output_tokens,
            context_token_budget=self.context_token_budget,
            context_estimated_tokens=context_tokens,
            context_files_included=included,
            context_files_skipped_budget=skipped,
            context_files_missing=missing,
        )
        self.last_run_info = info
        running = {"prompt": 0, "completion": 0, "cost": 0.0}
        cap = settings.max_spend_usd

        # ---- Stage (a): the generalized selection over the diff alone.
        selection_payload = self.build_selection_payload(diff_text)
        selection_worst = self.worst_case_estimate(selection_payload)
        # Pre-flight 1 (paper §3c.1, inherited): the selection alone
        # must fit — the only blanket refusal left.
        if selection_worst > cap:
            raise RealLLMRefused(
                "backend=llm v2.3 refused before calling: worst-case "
                f"estimate US${selection_worst:.4f} for the selection "
                f"pass exceeds RB_MAX_SPEND_USD=US${cap:.4f}; "
                "no model call was made"
            )
        content, usage, finish_reason = self._call(selection_payload)
        info.calls += 1
        selection_cost = self._account(
            selection_payload, content, usage, info, running
        )
        try:
            raw_selection = _extract_selection(content)
        except RealLLMRefused as exc:
            _refuse_parse_failure(
                info, SELECTION_PASS, exc, finish_reason, content
            )
        selected, overflow = self._filter_selection(raw_selection, info)
        info.selection_selected = [name for _, name in selected]
        info.selection_overflow = list(overflow)

        candidates: list[Candidate] = []
        seen: set[tuple[str, int, int, str, str]] = set()
        if not selected:
            # The selection marked nothing: a declared outcome (the
            # run info shows an empty selection), not an error.
            return candidates
        selected_names = [name for _, name in selected]

        # ---- Pre-flight 2 (paper §3c.2, inherited): plan the deep
        # passes under the SHARED cap, in priority order.
        deep_payloads = {
            name: self.build_deep_payload(name, diff_text, context_text)
            for _, name in selected
        }
        admitted: list[str] = []
        dropped: list[str] = []
        planned_cost = selection_cost
        for name in selected_names:
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
                content, usage, finish_reason = self._call(payload)
                info.calls += 1
                info.passes.append(name)
                self._account(payload, content, usage, info, running)
                self._collect(
                    content,
                    name,
                    selected_names,
                    head_files,
                    info,
                    candidates,
                    seen,
                    finish_reason,
                )
            return candidates

        # ---- Degenerate case (paper §3c.3, inherited): emit only
        # what the selection supports — one mixed pass over the
        # marked marks, both families.
        fallback_payload = self.build_fallback_payload(selected, diff_text)
        if selection_cost + self.worst_case_estimate(fallback_payload) <= cap:
            info.degradation = {
                "reason": "spend_cap",
                "deep_passes_planned": len(selected),
                "deep_passes_run": 0,
                "deep_passes_dropped": list(selected_names),
                "fallback_single_pass": True,
            }
            content, usage, finish_reason = self._call(fallback_payload)
            info.calls += 1
            info.passes.append(FALLBACK_PASS)
            self._account(fallback_payload, content, usage, info, running)
            self._collect(
                content,
                None,
                selected_names,
                head_files,
                info,
                candidates,
                seen,
                finish_reason,
            )
            return candidates

        info.degradation = {
            "reason": "no_deep_pass_affordable",
            "deep_passes_planned": len(selected),
            "deep_passes_run": 0,
            "deep_passes_dropped": list(selected_names),
            "fallback_single_pass": False,
        }
        return candidates

    # -- selection filtering --------------------------------------------------

    def _filter_selection(
        self, raw_entries: list[object], info: LLMRunInfoV23
    ) -> tuple[list[tuple[str, str]], list[str]]:
        """Filter the selection's marks: the nine categories or the
        active gate's classes only, first occurrence wins, hard cap
        MAX_DEEP_PASSES shared across families.  Returns (selected
        [(kind, name)], overflow [names]); everything rejected is
        counted in the run info, and the selected marks are settled
        per family (selection_general / selection_specialty)."""

        valid: list[tuple[str, str]] = []
        for entry in raw_entries:
            if not isinstance(entry, dict):
                info.selection_malformed_entries += 1
                continue
            mark = entry.get("mark")
            if not isinstance(mark, str) or not mark.strip():
                info.selection_malformed_entries += 1
                continue
            mark = mark.strip()
            if mark in GENERAL_CATEGORIES:
                kind = "category"
            elif mark in self.claim_types:
                kind = "class"
            else:
                info.selection_unknown_marks += 1
                continue
            if any(name == mark for _, name in valid):
                continue
            valid.append((kind, mark))
        info.selection_candidates = [name for _, name in valid]
        selected = valid[:MAX_DEEP_PASSES]
        info.selection_general = [
            name for kind, name in selected if kind == "category"
        ]
        info.selection_specialty = [
            name for kind, name in selected if kind == "class"
        ]
        return selected, [name for _, name in valid[MAX_DEEP_PASSES:]]

    # -- findings collection ----------------------------------------------------

    def _collect(
        self,
        content: object,
        pass_name: str | None,
        allowed: list[str],
        head_files: Mapping[str, list[str]],
        info: LLMRunInfoV23,
        candidates: list[Candidate],
        seen: set[tuple[str, int, int, str, str]],
        finish_reason: object = None,
    ) -> None:
        try:
            raw_findings = _extract_findings(content)
        except RealLLMRefused as exc:
            _refuse_parse_failure(
                info,
                pass_name if pass_name is not None else FALLBACK_PASS,
                exc,
                finish_reason,
                content,
            )
        info.raw_findings += len(raw_findings)
        for raw in raw_findings:
            candidate = self._to_candidate_v23(
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

    def _to_candidate_v23(
        self,
        raw: object,
        pass_name: str | None,
        allowed: list[str],
        head_files: Mapping[str, list[str]],
        info: LLMRunInfoV23,
    ) -> Candidate | None:
        """Convert one raw finding, verifying its anchor against the
        head — the v2's discipline, unchanged: malformed shapes are
        counted as malformed; in a deep pass, a finding whose
        claim_type does not match its pass's mark is malformed; in
        the fallback pass, a finding outside the marks the selection
        made is malformed; findings whose cited lines do not exist in
        the head file or whose quoted evidence does not match it
        exactly are counted as unanchored.  Both are dropped here,
        before the gate."""

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
            claim_type, CATEGORY_HINTS.get(claim_type, ("high", "correctness"))
        )
        return Candidate(
            rule_id=f"llm_v23_{claim_type}",
            claim_type=claim_type,
            file=file,
            start_line=start,
            end_line=end,
            message=message.strip(),
            evidence_text=actual,
            severity_hint=severity_hint,
            category_hint=category_hint,
            producer="alma-llm-reviewer-v23",
        )


__all__ = [
    "CATEGORY_GUIDANCE",
    "CATEGORY_GUIDANCE_DEEP",
    "CATEGORY_HINTS",
    "DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS",
    "FALLBACK_PASS",
    "GENERAL_CATEGORIES",
    "LLMReviewerV23",
    "LLMRunInfoV23",
    "MAX_DEEP_PASSES",
    "PARSE_FAILURE_EXCERPT_CHARS",
    "REVIEWER_VERSION",
    "SELECTION_PASS",
]
