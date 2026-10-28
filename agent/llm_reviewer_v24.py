"""LLM reviewer v2.4 — evidence-discipline production.

Why this module exists (pre-registration:
PREREGISTRO-PRODUCTOR-EVIDENCIA.md, 2026-10-22, written before this
code): the free chain closed with a measured diagnosis in three
steps.  Gate 1.5.0 emits on the general path but its bar FAILED —
133/166 held, its two dominant blockers properties of how claims
are BORN (71 with no concrete pattern asserted, 62 asserting
tokens absent from their own citation).  The claim contract
measured the after-the-fact ceiling: 49/166 conformable without
inventing evidence, and those 49 passed the gate 49/49 — the
bottleneck sat entirely at birth.  The birth shaper
(agent/birth_shaper.py) then formed claims at birth inside the
pipeline: conformance 80/166, emitted precision 55.7% — but the
composite bar still FAILED (51.8% held against <50%), and its
paper's §6 settled the final reading: the bottleneck is no longer
the claims' FORM but their MATTER — 86 of the 166 are born with
nothing citable to assert (54 with no pattern in their prose, 32
asserting only tokens their citation does not contain), 44 of the
89 true positives among them.  The reviewer asserts true things
without citing verifiable evidence, and no deterministic
downstream layer can create that evidence without inventing it.

Design v2.4 — ONLY this changes against v2.3.2 (which stays
byte-identical and reproducible):

- **Evidence-first emission schema**: every deep pass (class or
  category) and the mixed fallback pass answer ONE JSON object
  with two arrays.  ``findings`` is the v2/v2.3 finding shape PLUS
  a ``pattern`` field: the code tokens the claim asserts, copied
  VERBATIM from the cited evidence lines; the message wraps each
  pattern token in backticks and asserts no other backticked
  token — the pattern the contract reads (C1) is exactly the
  declared one.  ``unverifiable`` is the model's own declaration
  path: a defect it believes real but cannot support with citable
  lines is listed there, with a ``reason`` — a declaration,
  never a finding in disguise.
- **Evidence discipline in the prompts**: a new deep-pass
  template (``_SYSTEM_PROMPT_TEMPLATE_V24``) and a v2.4 mixed
  prompt carry the same binding text — choose the exact proving
  lines FIRST, write the claim from those lines alone; assert
  only what is visible in the cited lines; what cannot be cited
  is declared under ``unverifiable``, never disguised.  The
  class/category guidance itself is inherited unchanged, and the
  SELECTION prompt is byte-identical to the v2.3's (marking does
  not assert; the discipline does not apply to the stage that
  only marks).
- **The production ledger**: conversion keeps the v2.3's
  shape/anchor discipline (malformed / unanchored counters,
  unchanged), and settles every non-citable birth in the run
  info's ``production_ledger`` instead of emitting or dropping
  it: a finding with no declared pattern
  (``sin_patron_concreto_en_el_reclamo``), a finding whose
  declared pattern differs from the pattern its message asserts
  (``patron_declarado_distinto_del_mensaje``), and each
  model-declared ``unverifiable`` entry
  (``declarado_no_verificable_en_origen``, with the model's
  reason).  Nothing non-citable is emitted disguised and nothing
  is silently lost.
- **The birth shaper is the last production stage**: after
  collection, ``birth_shaper.shape_candidates`` (unmodified)
  runs over every candidate with the diff in view, before the
  reviewer returns anything and before any gate.  What it
  delivers in contract form IS this reviewer's production; what
  it declares unverifiable at origin is settled in the
  production ledger under the shaper's own codes, and every
  trim at origin is counted in the run info.  There is no
  post-shaping deduplication in this paper (declared).

What does NOT change (paper §2, §6): the generalized selection,
the shared ``MAX_DEEP_PASSES`` cap, the two-stage guard and the
degradation rule, the cumulative reported-cost check that fails
closed, the per-PR spend brake and every existing configuration,
the gate resolution (``_resolve_gate_v23``, imported: v1…v141),
the payload safety contract (no ``temperature``, no
``max_tokens``; ``max_completion_tokens``), and the gates
1.0.0–1.5.0, ``claim_contract.py`` and ``birth_shaper.py``, which
this module consumes unmodified.  ``agent/main.py`` is NOT
touched: v2.4 is not mounted in any image or config by this
paper — mounting is the run paper's decision.

THE HONEST CAVEAT (paper §3, binding): the effect of the
evidence discipline on the rate of citable claims CANNOT be
measured dry — that rate is a property of what a real model does
with the new prompt, and a scripted transport would be scripting
the answer.  This module's dry verification covers only the
schema's mechanical correctness, the armed prompts' contents,
the semaphore battery and the readiness of the measurement
harness.  No effect number is claimed here; the paid validation
is designed in the paper (§4) and stays PARKED until Alejandro's
run paper, with its line cap, says otherwise.

THE RUN-344 AMENDMENT (ADENDA-ARREGLO-TOPE-20261024.md,
2026-10-24, declared there before this code): run nº 344 died
because the deep passes inherited the v1 base's 4096 output
ceiling — on two PRs the model's reasoning alone exhausted it
and the response came back empty with finish_reason 'length',
and the portal's retries reused the same budget to the same
result.  Two repairs, in this shared layer (the v2.5 and the
v2.6 inherit both whole): the deep-pass output budget is now
this family's own resolvable setting
(``DEFAULT_DEEP_MAX_OUTPUT_TOKENS``), and a deep or fallback
response that returns empty with finish_reason 'length' earns
ONE in-agent retry at double budget — guarded by the remaining
spend brake, its cost folded into the same cumulative check,
the event settled in the run info — before failing closed
exactly as before.  No prompt, no gate, no other error path
moves; ``REVIEWER_VERSION`` stays "llm-reviewer/2.4.0" (the
reviewer's identity, not its bytes — the amendment and the new
image digest carry the code identity, as in the whole line).

THE RUN-373 AMENDMENT
(ADENDA-RECALIBRACION-PRESUPUESTO-20261027.md, 2026-10-27,
declared there before this code): run nº 373 finished but
its recall collapsed — the autopsy's floor 1.  Pre-flight 2
priced every deep payload at its full output ceiling
(16,384), so at planning prices each pass projected
US$1.2288 of output alone and the unchanged per-PR brake
(US$6.50) bought far fewer passes than the design plans:
degradation in 19 of 25 PRs, 54 deep passes dropped,
candidates 168 -> 108 — while the real spend came in BELOW
the base run's, because observed deep completions average
~2,336 tokens (PR-average maximum ~5,164), nowhere near the
ceiling the projection assumed.  The repair, in this same
shared layer: admission planning prices a production
payload's output at this family's own planning line
(``DEFAULT_DEEP_PLANNING_OUTPUT_TOKENS``, resolved like its
sibling budgets and declared per run in the run info),
never above the payload's own cap.  What guards real money
keeps pricing the true worst case, unmodified: pre-flight 1,
the length-retry guard, and the cumulative reported-cost
check that fails closed against RB_MAX_SPEND_USD.  The
gate 1.5.0 and its origin discards (the autopsy's floor 2)
are expressly NOT touched by this amendment.

THE GATE-FORM AMENDMENT (ADENDA-PUERTA-FORMA-20261027.md,
2026-10-27, declared there before this code): the autopsies
of runs nº 373 and nº 374 closed the attribution — with the
budget absolved, grounded recall stayed at 9.4–9.8 % because
claims died at origin for FORM: 29 (nº 373) and 36 (nº 374)
findings whose cited evidence matched the head file exactly
were settled in this conversion under
``sin_patron_concreto_en_el_reclamo`` solely because the
emission's ``pattern`` field came back missing, not a list,
or empty — before the birth shaper's Case B mining, the
pipeline's own rescue for pattern-less claims, could ever see
them (zero ``production_shaping`` settlements in either run).
The amendment, in this same shared layer: a finding with NO
declared pattern is no longer settled in the conversion; it
is built as a candidate exactly as born and flows to the
shaping stage, whose closed mining extracts a pattern from
its own prose against its citation or declares it
unverifiable at origin under the same code — a claim now dies
for lack of anything extractable (matter), not for an
undeclared field (form).  Nothing else moves: a declared
pattern that contradicts the message's asserted tokens still
settles here as before, the model's own ``unverifiable``
declarations still settle here as before, and the shaping
stage, the claim contract and every gate stay unmodified.
Gate resolution additionally admits "v151"
(alma-evidence-gate/1.5.1, the same amendment's gate half:
the 1.5.0 plus the extraction pre-pass), with the 1.5.0's
claim family.  ``REVIEWER_VERSION`` stays "llm-reviewer/2.4.0",
as with the two amendments above.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Mapping

from .alma_gate import KNOWN_CLAIM_TYPES, POLICY_VERSION as GATE_V1_VERSION
from .alma_gate_v13 import KNOWN_CLAIM_TYPES_V13
from .alma_gate_v150 import (
    CHECK_NO_CONCRETE_PATTERN,
    POLICY_VERSION as GATE_V150_VERSION,
    _asserted_tokens,
    _is_code_token,
    _normalize_token,
)
from .alma_gate_v151 import POLICY_VERSION as GATE_V151_VERSION
from .base_reviewer import Candidate
from .birth_shaper import shape_candidates
from .diff_parser import DiffIndex
from .llm_reviewer import (
    LLMSettings,
    RealLLMRefused,
    Transport,
    _estimate_tokens,
    _urllib_transport,
)
from .llm_reviewer_v2 import (
    _ALL_CLAIM_HINTS,
    _CLASS_GUIDANCE,
    _load_head_files,
    _render_context,
    _resolve_context_budget,
)
from .llm_reviewer_v23 import (
    CATEGORY_GUIDANCE,
    CATEGORY_GUIDANCE_DEEP,
    CATEGORY_HINTS,
    DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS,
    FALLBACK_PASS,
    GENERAL_CATEGORIES,
    MAX_DEEP_PASSES,
    SELECTION_PASS,
    _CLASS_GUIDANCE_V13,
    _build_selection_system_prompt,
    _extract_selection,
    _refuse_parse_failure,
    _resolve_gate_v23,
    _resolve_triage_max_output_tokens,
)


REVIEWER_VERSION = "llm-reviewer/2.4.0"

# The run-344 fix (ADENDA-ARREGLO-TOPE-20261024.md §2, declared
# there before this code).  The deep passes used to read the v1
# base's shared default (LLMSettings.max_output_tokens, 4096) —
# a ceiling no paper of this family ever chose for them, and the
# one run nº 344 died under: reasoning alone exhausted it and
# the response came back empty.  16384 is 4x that ceiling and
# more than the largest whole-PR completion total observed in
# run nº 344 (14,132 tokens over <=6 calls), now available to a
# SINGLE pass; it sits far inside the GPT-5 family's admitted
# completion ceiling (128k), so the binding constraint stays the
# spend brake: pre-flight 2 prices the armed payload as built,
# and on the largest contexts the price is declared degradation
# (settled, survivable), never a silent length death (total).
DEFAULT_DEEP_MAX_OUTPUT_TOKENS = 16384
# A length-empty response retries ONCE, in-agent, at this
# multiple of the pass budget (32768 at the default above).
LENGTH_RETRY_MULTIPLIER = 2


def _resolve_deep_max_output_tokens(
    env: Mapping[str, str], config: Mapping[str, str]
) -> int:
    """Resolve the deep-pass output budget — the triage
    resolver's exact pattern and fail-closed discipline, one
    budget line over: RB_CONFIG_DEEP_MAX_OUTPUT_TOKENS, then
    RB_LLM_V24_DEEP_MAX_OUTPUT_TOKENS, then the default."""

    raw = (config.get("deep_max_output_tokens") or "").strip()
    source = "RB_CONFIG_DEEP_MAX_OUTPUT_TOKENS"
    if not raw:
        raw = (env.get("RB_LLM_V24_DEEP_MAX_OUTPUT_TOKENS") or "").strip()
        source = "RB_LLM_V24_DEEP_MAX_OUTPUT_TOKENS"
    if not raw:
        return DEFAULT_DEEP_MAX_OUTPUT_TOKENS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RealLLMRefused(
            f"backend=llm v2.4 refused: {source}={raw!r} is not an integer"
        ) from exc
    if value <= 0:
        raise RealLLMRefused(
            f"backend=llm v2.4 refused: {source} must be positive"
        )
    return value


# The run-373 recalibration
# (ADENDA-RECALIBRACION-PRESUPUESTO-20261027.md §2, declared
# there before this code).  Pre-flight 2 used to price every
# deep payload at its full output ceiling: with the ceiling
# at 16384, the projected output component per pass became
# US$1.2288 and the per-PR brake bought far fewer passes
# than the design plans — the system braked on ASSUMED price,
# not real spend (run nº 373 cost less than the base while
# dropping 54 deep passes).  The planning line prices a
# production pass's output at observed usage instead: in run
# nº 373 deep completions averaged ~2,336 tokens per call
# (PR-average maximum ~5,164), so 6144 sits above every
# observed PR-average with headroom, at ~2.6x the observed
# mean — and deliberately NOT at the old 4096, which today's
# passes demonstrably exceed (the evidence schema writes
# more, and reasoning counts as completion): planning below
# observed usage would shift the protection onto the
# cumulative real-cost brake mid-plan and turn declared
# degradation into whole-PR deaths.  This line feeds ONLY
# the planning estimates (pre-flight 2 admission and the
# fallback affordability check); the payload's own cap and
# every worst-case guard on real money are untouched.
DEFAULT_DEEP_PLANNING_OUTPUT_TOKENS = 6144


def _resolve_deep_planning_output_tokens(
    env: Mapping[str, str], config: Mapping[str, str]
) -> int:
    """Resolve the deep-pass planning line — the deep
    budget resolver's exact pattern and fail-closed
    discipline, one line over:
    RB_CONFIG_DEEP_PLANNING_OUTPUT_TOKENS, then
    RB_LLM_V24_DEEP_PLANNING_OUTPUT_TOKENS, then the
    default."""

    raw = (config.get("deep_planning_output_tokens") or "").strip()
    source = "RB_CONFIG_DEEP_PLANNING_OUTPUT_TOKENS"
    if not raw:
        raw = (env.get("RB_LLM_V24_DEEP_PLANNING_OUTPUT_TOKENS") or "").strip()
        source = "RB_LLM_V24_DEEP_PLANNING_OUTPUT_TOKENS"
    if not raw:
        return DEFAULT_DEEP_PLANNING_OUTPUT_TOKENS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RealLLMRefused(
            f"backend=llm v2.4 refused: {source}={raw!r} is not an integer"
        ) from exc
    if value <= 0:
        raise RealLLMRefused(
            f"backend=llm v2.4 refused: {source} must be positive"
        )
    return value


def _is_length_empty(content: object, finish_reason: object) -> bool:
    """The run-344 death, recognized exactly: the endpoint
    closed the response for length ('length') and NO content
    came back — an empty or blank string, or no content at
    all — because the reasoning consumed the whole output
    budget before the first content token.  Any other shape
    (content present, another finish reason) is not this mode
    and keeps its historical path, without retry."""

    if finish_reason != "length":
        return False
    if content is None:
        return True
    return isinstance(content, str) and content.strip() == ""

# Production-ledger codes (paper §2c).  The first is the line's
# own gate check code, reused because the settlement IS that
# condition, declared at birth; the other two are production
# codes of this reviewer (they never reach a gate).
CODE_NO_PATTERN = CHECK_NO_CONCRETE_PATTERN
CODE_PATTERN_MISMATCH = "patron_declarado_distinto_del_mensaje"
CODE_DECLARED_UNVERIFIABLE = "declarado_no_verificable_en_origen"


# ------------------------------------------------------------------
# The evidence-discipline prompts (paper §2b).
# ------------------------------------------------------------------

_EVIDENCE_DISCIPLINE = (
    "EVIDENCE DISCIPLINE (binding): every finding must be born "
    "citable. Choose FIRST the exact lines that prove the defect, "
    "then write the claim from those lines alone. (1) \"pattern\" "
    "lists the code tokens the claim asserts, copied VERBATIM from "
    "the cited lines: every pattern token must appear in the "
    "evidence lines exactly as written there. (2) The \"message\" "
    "asserts ONLY what is visible in the cited lines and wraps "
    "each pattern token in backticks; no other backticked code "
    "token may appear in the message, and no token, behaviour or "
    "fact absent from the cited lines may be asserted. "
    "(3) \"evidence\" reproduces the cited lines EXACTLY as they "
    "appear in the file, one entry per line from start_line to "
    "end_line, without the line-number prefix. Cite the smallest "
    "line range that contains the evidence, and prefer lines that "
    "appear in the diff (added or context lines): the full files "
    "are context so you can judge the changed lines. If you "
    "believe a defect exists but you CANNOT cite lines whose text "
    "supports it — the pattern does not appear in any line you "
    "can cite — do NOT put it in \"findings\": list it under "
    "\"unverifiable\" with the fields you can give and a "
    "\"reason\" saying why no citable lines support it; an "
    "unverifiable entry is a declaration, not a finding."
)

_SYSTEM_PROMPT_TEMPLATE_V24 = (
    "You are a code reviewer examining ONE pull request. This pass looks "
    "for exactly one class of defect: {claim_type} — {guidance}. Report "
    "ONLY findings of this class. "
    + _EVIDENCE_DISCIPLINE
    + " Respond with a single JSON object and nothing else, of the "
    'form {{"findings": [{{"file": "path/in/repo.py", "start_line": '
    '12, "end_line": 12, "claim_type": "{claim_type}", "message": '
    '"what is wrong and why", "pattern": ["token"], "evidence": '
    '["the exact text of line 12"]}}], "unverifiable": []}}. Lines '
    "refer to the file at the PR head, numbered exactly as shown. "
    "If you find nothing of this class that you can prove, return "
    '{{"findings": [], "unverifiable": []}}.'
)


def _build_mixed_system_prompt_v24(
    marks: list[tuple[str, str]], class_guidance: Mapping[str, str]
) -> str:
    """The degenerate-case mixed prompt, v2.4: the v2.3's sectioned
    structure (one section per marked mark, families sectioned)
    with the evidence discipline and the two-array schema."""

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
        + _EVIDENCE_DISCIPLINE
        + " Respond with a single JSON object and nothing else, of the "
        'form {"findings": [{"file": "path/in/repo.py", "start_line": '
        '12, "end_line": 12, "claim_type": "sql_injection", "message": '
        '"what is wrong and why", "pattern": ["token"], "evidence": '
        '["the exact text of line 12"]}], "unverifiable": []}. Lines '
        "refer to the file at the PR head, numbered exactly as shown. "
        "If you find nothing that you can prove, return "
        '{"findings": [], "unverifiable": []}.'
    )


def _extract_emissions(
    content: object,
) -> tuple[list[object], list[object]]:
    """Pull the (findings, unverifiable) arrays out of the model's
    content, strictly — the v1 extractor's fail-closed philosophy,
    extended to the v2.4 two-array schema: a missing findings list
    or a non-list unverifiable fails closed; a bare list response
    is findings only (the v1 tolerance)."""

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
            "model did not return parseable JSON findings; failing closed"
        ) from exc
    if isinstance(parsed, dict):
        findings = parsed.get("findings")
        unverifiable = parsed.get("unverifiable", [])
    elif isinstance(parsed, list):
        findings = parsed
        unverifiable = []
    else:
        findings = None
        unverifiable = []
    if not isinstance(findings, list):
        raise RealLLMRefused("model JSON has no findings list; failing closed")
    if not isinstance(unverifiable, list):
        raise RealLLMRefused(
            "model JSON unverifiable is not a list; failing closed"
        )
    return findings, unverifiable


def _declared_pattern(raw: dict) -> list[str]:
    """The finding's declared pattern, normalized with the line's
    single tokenization (gate 1.5.0's, imported): strings only,
    code tokens only, duplicates removed in order.  Anything else
    (missing, not a list, no surviving token) is an empty pattern
    — the no-pattern settlement path of paper §2c."""

    declared = raw.get("pattern")
    if not isinstance(declared, list):
        return []
    pattern: list[str] = []
    for item in declared:
        if not isinstance(item, str):
            return []
        token = _normalize_token(item)
        if _is_code_token(token) and token not in pattern:
            pattern.append(token)
    return pattern


@dataclass
class LLMRunInfoV24:
    """What the v2.4 run did, for the run log (never the key): the
    v2.3's record, plus the production ledger and the shaping
    stage's settlement (paper §2c)."""

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
    selection_candidates: list[str] = field(default_factory=list)
    selection_selected: list[str] = field(default_factory=list)
    selection_overflow: list[str] = field(default_factory=list)
    selection_general: list[str] = field(default_factory=list)
    selection_specialty: list[str] = field(default_factory=list)
    selection_unknown_marks: int = 0
    selection_malformed_entries: int = 0
    degradation: dict[str, object] | None = None
    triage_max_output_tokens: int = 0
    parse_failures: list[dict[str, object]] = field(default_factory=list)
    # The run-344 fix (ADENDA-ARREGLO-TOPE-20261024.md): the
    # deep-pass output budget in force for this run (the mirror
    # of triage_max_output_tokens, one budget line over), and one
    # settled record per length-empty retry event — the pass,
    # both budgets, and the outcome ("recovered", "still_empty"
    # or "refused_spend_cap").
    deep_max_output_tokens: int = 0
    length_retries: list[dict[str, object]] = field(default_factory=list)
    # The run-373 recalibration
    # (ADENDA-RECALIBRACION-PRESUPUESTO-20261027.md): the
    # planning line this run's pre-flight 2 priced production
    # output at — settled per run so any degradation or death
    # is attributable to the exact line that governed its
    # planning.
    deep_planning_output_tokens: int = 0
    # The production ledger (paper §2c): every birth this reviewer
    # declared non-citable, with its code and reason — settled by
    # the conversion (no pattern / pattern mismatch / declared by
    # the model) or by the shaping stage (the shaper's own codes).
    production_ledger: list[dict[str, object]] = field(default_factory=list)
    # The shaping stage's settlement: what production delivered.
    shaping: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        by_code: dict[str, int] = {}
        for record in self.production_ledger:
            code = str(record.get("code"))
            by_code[code] = by_code.get(code, 0) + 1
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
            "deep_max_output_tokens": self.deep_max_output_tokens,
            "length_retries": [dict(r) for r in self.length_retries],
            "deep_planning_output_tokens": self.deep_planning_output_tokens,
            "production_ledger": [dict(r) for r in self.production_ledger],
            "production_ledger_by_code": by_code,
            "shaping": dict(self.shaping) if self.shaping is not None else None,
        }


def _resolve_gate_v24(
    config: Mapping[str, str],
) -> tuple[tuple[str, ...], dict[str, str], str]:
    """Resolve the active gate's (claim types, guidance, version)
    for the v2.4-family reviewers (v2.4, and v2.5/v2.6 by
    inheritance — neither defines its own ``from_env``).

    Mounting declared in PREREGISTRO-VALIDACION-20261024.md §3,
    written before this code: the parked design's arms are
    "v2.4 con puerta 1.5.0" (and its heirs), but the admission
    list of ``_resolve_gate_v23`` ends at "v141" — the same
    drift the Adenda 4 repaired for "v141", one gate later.
    This wrapper adds ONLY the "v150" branch — the 1.5.0's
    specialty family is the 1.3.0's 19 classes (its class
    behaviour is the 1.4.1's by delegation; verified by
    program: ``KNOWN_CLAIM_TYPES_V150`` equals the v13 set) —
    and delegates every other value to ``_resolve_gate_v23``,
    which stays byte-identical.  The gate-form amendment
    (ADENDA-PUERTA-FORMA-20261027) adds the "v151" branch
    beside it, with the same family and guidance."""

    gate_version = (config.get("gate") or "v1").strip().lower()
    if gate_version == "v150":
        return KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V150_VERSION
    if gate_version == "v151":
        # Gate-form amendment (ADENDA-PUERTA-FORMA-20261027):
        # the 1.5.1's specialty family is the 1.5.0's — its
        # class behaviour is the 1.4.1's by delegation through
        # the 1.5.0 — so only the version string moves.
        return KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V151_VERSION
    return _resolve_gate_v23(config)


class LLMReviewerV24:
    """Generalized selection + deep passes, with evidence-discipline
    production (paper: PREREGISTRO-PRODUCTOR-EVIDENCIA.md)."""

    name = "alma-llm-reviewer-v24"

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
        deep_max_output_tokens: int = DEFAULT_DEEP_MAX_OUTPUT_TOKENS,
        deep_planning_output_tokens: int = (
            DEFAULT_DEEP_PLANNING_OUTPUT_TOKENS
        ),
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
        # The run-344 fix: this family's own deep-pass budget,
        # and the escalated budget of its single length retry.
        self.deep_max_output_tokens = deep_max_output_tokens
        self.length_retry_max_output_tokens = (
            deep_max_output_tokens * LENGTH_RETRY_MULTIPLIER
        )
        # The run-373 recalibration: the planning line
        # pre-flight 2 prices production output at (admission
        # only — never the payload, never the brake).
        self.deep_planning_output_tokens = deep_planning_output_tokens
        self.last_run_info: LLMRunInfoV24 | None = None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str],
        config: Mapping[str, str],
        transport: Transport | None = None,
    ) -> "LLMReviewerV24":
        claim_types, class_guidance, gate_version = _resolve_gate_v24(config)
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
            deep_max_output_tokens=_resolve_deep_max_output_tokens(
                env, config
            ),
            deep_planning_output_tokens=(
                _resolve_deep_planning_output_tokens(env, config)
            ),
        )

    # -- payloads ---------------------------------------------------------

    def _payload(
        self, system_prompt: str, user_content: str, max_output_tokens: int
    ) -> dict[str, object]:
        # Same payload contract as v1/v2/v2.3: no "temperature",
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
        # The selection prompt is the v2.3's, imported unmodified
        # (paper §2: marking does not assert).
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
        """A deep pass payload under the evidence-first schema: the
        v2.4 template with the inherited guidance (class mark -> the
        gate's class guidance; category mark -> the category's deep
        guidance) — only the template's discipline changed."""

        if pass_name in GENERAL_CATEGORIES:
            guidance = CATEGORY_GUIDANCE_DEEP[pass_name]
        else:
            guidance = self.class_guidance[pass_name]
        system_prompt = _SYSTEM_PROMPT_TEMPLATE_V24.format(
            claim_type=pass_name, guidance=guidance
        )
        user_content = (
            f"PASS: {pass_name}\n\n"
            "Review this pull request. First the diff, then the full "
            "contents of the touched files at the PR head.\n\n"
            f"=== DIFF ===\n{diff_text}\n\n{context_text}"
        )
        # The output cap is this family's own deep budget
        # (ADENDA-ARREGLO-TOPE-20261024.md), not the v1 base's
        # shared settings default the run nº 344 died under.
        return self._payload(
            system_prompt, user_content, self.deep_max_output_tokens
        )

    def build_fallback_payload(
        self,
        selected: list[tuple[str, str]],
        diff_text: str,
    ) -> dict[str, object]:
        """The degenerate-case mixed pass, v2.4: the sectioned prompt
        restricted to the marked marks, under the same evidence
        discipline and two-array schema."""

        system_prompt = _build_mixed_system_prompt_v24(
            selected, self.class_guidance
        )
        user_content = (
            f"PASS: {FALLBACK_PASS}\n\n"
            "Review this pull request from its diff. The deep review "
            "was not affordable under the spend cap, so this single "
            "pass covers only the marks the triage made.\n\n"
            f"=== DIFF ===\n{diff_text}"
        )
        # Same deep budget line as the deep passes (the fallback
        # IS a production pass; adenda cited in build_deep_payload).
        return self._payload(
            system_prompt, user_content, self.deep_max_output_tokens
        )

    # -- guard arithmetic ---------------------------------------------------

    def worst_case_estimate(self, payload: dict[str, object]) -> float:
        """Worst case of ONE payload under its own output cap (the
        v2.3's arithmetic, unchanged)."""

        estimated_input = sum(
            _estimate_tokens(str(message["content"]))
            for message in payload["messages"]
        )
        return self.settings.cost_usd(
            estimated_input, int(payload["max_completion_tokens"])
        )

    def planning_estimate(self, payload: dict[str, object]) -> float:
        """Planning price of ONE production payload (the run-373
        recalibration, ADENDA-RECALIBRACION-PRESUPUESTO-20261027.md
        §2): the input priced as estimated, the output priced at
        this family's planning line
        (``deep_planning_output_tokens``) — observed usage, never
        above the payload's own cap.  This estimate decides ONLY
        which production passes pre-flight 2 plans under the
        brake; it never prices a real call.  The guards on real
        money keep the worst case: pre-flight 1, the
        length-retry guard and the cumulative reported-cost
        check in ``_account`` are unmodified."""

        estimated_input = sum(
            _estimate_tokens(str(message["content"]))
            for message in payload["messages"]
        )
        planned_output = min(
            int(payload["max_completion_tokens"]),
            self.deep_planning_output_tokens,
        )
        return self.settings.cost_usd(estimated_input, planned_output)

    # -- one model call -----------------------------------------------------

    def _call(
        self, payload: dict[str, object]
    ) -> tuple[object, dict | None, object]:
        """Run one chat-completions call; (content, usage-or-None,
        finish_reason-or-None) — the v2.3's behavior, unchanged."""

        settings = self.settings
        status, body = self.transport(
            settings.chat_url(),
            settings.headers(),
            payload,
            settings.timeout_seconds,
        )
        if status != 200:
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
        info: LLMRunInfoV24,
        running: dict[str, float],
    ) -> float:
        """Fold one call's usage into the run totals; enforce the
        cumulative cap (fail closed) exactly like the other
        reviewers (unchanged)."""

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

    def _call_deep(
        self,
        payload: dict[str, object],
        pass_label: str,
        info: LLMRunInfoV24,
        running: dict[str, float],
    ) -> tuple[object, object]:
        """Run one production call (a deep pass or the mixed
        fallback) and account it — with the run-344 fix
        (ADENDA-ARREGLO-TOPE-20261024.md §2b): a response that
        comes back EMPTY with finish_reason 'length' — the model
        spent the whole output budget reasoning and emitted no
        content — earns ONE in-agent retry at
        LENGTH_RETRY_MULTIPLIER x the pass budget, before the
        caller settles the content and, if it still fails, fails
        closed exactly as before.  The retry is guarded by the
        brake: it fires only if the accumulated actual cost plus
        the retry's worst case still fits RB_MAX_SPEND_USD;
        otherwise there is no second call and the original
        content takes the historical fail-closed path.  The
        retry's actual cost folds into the same cumulative
        check (_account, unmodified).  Every event is settled in
        info.length_retries.  No other response — HTTP errors,
        malformed JSON with content, any other finish reason —
        changes behaviour."""

        content, usage, finish_reason = self._call(payload)
        info.calls += 1
        self._account(payload, content, usage, info, running)
        if not _is_length_empty(content, finish_reason):
            return content, finish_reason
        record: dict[str, object] = {
            "pass": pass_label,
            "first_max_output_tokens": int(payload["max_completion_tokens"]),
            "retry_max_output_tokens": self.length_retry_max_output_tokens,
            "outcome": "refused_spend_cap",
        }
        info.length_retries.append(record)
        retry_payload = dict(payload)
        retry_payload["max_completion_tokens"] = (
            self.length_retry_max_output_tokens
        )
        if (
            running["cost"] + self.worst_case_estimate(retry_payload)
            > self.settings.max_spend_usd
        ):
            return content, finish_reason
        content, usage, finish_reason = self._call(retry_payload)
        info.calls += 1
        self._account(retry_payload, content, usage, info, running)
        record["outcome"] = (
            "still_empty"
            if _is_length_empty(content, finish_reason)
            else "recovered"
        )
        return content, finish_reason


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
        """Produce this reviewer's findings: the v2.3 production
        flow (selection, guarded deep passes or the mixed fallback)
        with the evidence-first conversion, and — as the LAST
        production stage, before anything is returned and before
        any gate — the birth shaper (paper §2c).  What review()
        returns is only what was born in contract form; every
        non-citable birth is settled in the run info's production
        ledger."""

        info = LLMRunInfoV24(
            model=self.settings.model,
            gate_version=self.gate_version,
        )
        self.last_run_info = info
        candidates = self._produce(
            diff_text=diff_text,
            diff=diff,
            config=config,
            mode=mode,
            repo_root=repo_root,
            info=info,
        )

        # The shaping stage (paper §2c): deterministic, unmodified.
        batch = shape_candidates(candidates, diff)
        emitted: list[Candidate] = []
        origins = {"declared": 0, "mined": 0, "class": 0}
        trimmed_total = 0
        held = 0
        for outcome in batch.outcomes:
            trimmed_total += len(outcome.trimmed_tokens)
            if outcome.candidate is not None:
                emitted.append(outcome.candidate)
                if outcome.origin in origins:
                    origins[outcome.origin] += 1
                continue
            held += 1
            blocker = outcome.blockers[0] if outcome.blockers else {}
            info.production_ledger.append(
                {
                    "pass": "production_shaping",
                    "claim_type": outcome.claim.get("claim_type"),
                    "file": outcome.claim.get("file"),
                    "start_line": outcome.claim.get("start_line"),
                    "end_line": outcome.claim.get("end_line"),
                    "code": blocker.get("check", ""),
                    "reason": blocker.get("reason", ""),
                }
            )
        info.shaping = {
            "emitted": len(emitted),
            "held_at_origin": held,
            "trimmed_tokens": trimmed_total,
            "origins": origins,
        }
        return emitted

    def _produce(
        self,
        *,
        diff_text: str,
        diff: DiffIndex,
        config: Mapping[str, str],
        mode: str,
        repo_root: str | Path | None,
        info: LLMRunInfoV24,
    ) -> list[Candidate]:
        """The v2.3's production flow, stage for stage (selection,
        pre-flight 1, pre-flight 2, degradation, the mixed
        fallback), with the v2.4 conversion at collection time.
        `mode` is interface parity only, as in the v2.3: the arms
        differ in the gate config they feed, not here."""

        _ = mode
        _ = config
        settings = self.settings
        root = Path(repo_root) if repo_root is not None else self.repo_root
        if not root.is_dir():
            raise RealLLMRefused(
                f"backend=llm v2.4 refused: repo root {root} is not a "
                "directory; the v2.4 reviewer requires the mounted head "
                "checkout (RB_REPO_ROOT); no model call was made"
            )

        order = list(diff.files.keys())
        head_files, missing = _load_head_files(root, order)
        context_text, context_tokens, included, skipped = _render_context(
            head_files, order, self.context_token_budget
        )

        info.passes = [SELECTION_PASS]
        info.triage_max_output_tokens = self.triage_max_output_tokens
        info.deep_max_output_tokens = self.deep_max_output_tokens
        info.deep_planning_output_tokens = self.deep_planning_output_tokens
        info.context_token_budget = self.context_token_budget
        info.context_estimated_tokens = context_tokens
        info.context_files_included = included
        info.context_files_skipped_budget = skipped
        info.context_files_missing = missing
        running = {"prompt": 0, "completion": 0, "cost": 0.0}
        cap = settings.max_spend_usd

        # ---- Stage (a): the generalized selection over the diff alone.
        selection_payload = self.build_selection_payload(diff_text)
        selection_worst = self.worst_case_estimate(selection_payload)
        # Pre-flight 1 (inherited): the selection alone must fit.
        if selection_worst > cap:
            raise RealLLMRefused(
                "backend=llm v2.4 refused before calling: worst-case "
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
            # The selection marked nothing: a declared outcome.
            return candidates
        selected_names = [name for _, name in selected]

        # ---- Pre-flight 2 (inherited): plan the deep passes under
        # the SHARED cap, in priority order.  Admission prices
        # each payload at the planning line (run-373
        # recalibration): observed output usage, not the
        # payload's full ceiling — the brake itself still
        # guards real spend through the cumulative check.
        deep_payloads = {
            name: self.build_deep_payload(name, diff_text, context_text)
            for _, name in selected
        }
        admitted: list[str] = []
        dropped: list[str] = []
        planned_cost = selection_cost
        for name in selected_names:
            planned = self.planning_estimate(deep_payloads[name])
            if planned_cost + planned <= cap:
                admitted.append(name)
                planned_cost += planned
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
                info.passes.append(name)
                content, finish_reason = self._call_deep(
                    payload, name, info, running
                )
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

        # ---- Degenerate case (inherited): one mixed pass over the
        # marked marks, both families.
        fallback_payload = self.build_fallback_payload(selected, diff_text)
        if selection_cost + self.planning_estimate(fallback_payload) <= cap:
            info.degradation = {
                "reason": "spend_cap",
                "deep_passes_planned": len(selected),
                "deep_passes_run": 0,
                "deep_passes_dropped": list(selected_names),
                "fallback_single_pass": True,
            }
            info.passes.append(FALLBACK_PASS)
            content, finish_reason = self._call_deep(
                fallback_payload, FALLBACK_PASS, info, running
            )
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
        self, raw_entries: list[object], info: LLMRunInfoV24
    ) -> tuple[list[tuple[str, str]], list[str]]:
        """The v2.3's filter, unchanged: the nine categories or the
        active gate's classes only, first occurrence wins, hard cap
        MAX_DEEP_PASSES shared across families; rejections counted
        in the run info, selections settled per family."""

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

    # -- production ledger ------------------------------------------------------

    def _settle_ledger(
        self,
        info: LLMRunInfoV24,
        *,
        pass_name: str,
        claim_type: object,
        file: object,
        start_line: object,
        end_line: object,
        code: str,
        reason: str,
    ) -> None:
        """Settle one non-citable birth in the production ledger
        (paper §2c): never emitted, never silently dropped."""

        info.production_ledger.append(
            {
                "pass": pass_name,
                "claim_type": claim_type if isinstance(claim_type, str) else None,
                "file": file if isinstance(file, str) else None,
                "start_line": (
                    start_line
                    if isinstance(start_line, int)
                    and not isinstance(start_line, bool)
                    else None
                ),
                "end_line": (
                    end_line
                    if isinstance(end_line, int)
                    and not isinstance(end_line, bool)
                    else None
                ),
                "code": code,
                "reason": reason,
            }
        )

    def _settle_declared_unverifiable(
        self, entry: object, pass_name: str, info: LLMRunInfoV24
    ) -> None:
        """Settle one model-declared `unverifiable` entry: an entry
        with an identifiable shape (claim_type and message strings)
        is a production declaration with the model's own reason;
        anything shapeless fails the emission schema's form and
        counts as malformed, like the inherited discipline."""

        if not isinstance(entry, dict):
            info.malformed_findings += 1
            return
        claim_type = entry.get("claim_type")
        message = entry.get("message")
        if (
            not isinstance(claim_type, str)
            or not claim_type.strip()
            or not isinstance(message, str)
            or not message.strip()
        ):
            info.malformed_findings += 1
            return
        reason = entry.get("reason")
        self._settle_ledger(
            info,
            pass_name=pass_name,
            claim_type=claim_type.strip(),
            file=entry.get("file"),
            start_line=entry.get("start_line"),
            end_line=entry.get("end_line", entry.get("start_line")),
            code=CODE_DECLARED_UNVERIFIABLE,
            reason=reason if isinstance(reason, str) else "",
        )

    # -- findings collection ----------------------------------------------------

    def _collect(
        self,
        content: object,
        pass_name: str | None,
        allowed: list[str],
        head_files: Mapping[str, list[str]],
        info: LLMRunInfoV24,
        candidates: list[Candidate],
        seen: set[tuple[str, int, int, str, str]],
        finish_reason: object = None,
    ) -> None:
        label = pass_name if pass_name is not None else FALLBACK_PASS
        try:
            raw_findings, raw_unverifiable = _extract_emissions(content)
        except RealLLMRefused as exc:
            _refuse_parse_failure(info, label, exc, finish_reason, content)
        for entry in raw_unverifiable:
            self._settle_declared_unverifiable(entry, label, info)
        info.raw_findings += len(raw_findings)
        for raw in raw_findings:
            candidate = self._to_candidate_v24(
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

    def _to_candidate_v24(
        self,
        raw: object,
        pass_name: str | None,
        allowed: list[str],
        head_files: Mapping[str, list[str]],
        info: LLMRunInfoV24,
    ) -> Candidate | None:
        """Convert one raw finding under the evidence-first schema.

        The inherited discipline first (paper §2c step 1): malformed
        shapes count as malformed; in a deep pass, a finding whose
        claim_type does not match its pass's mark is malformed; in
        the fallback pass, a finding outside the marked marks is
        malformed; findings whose cited lines do not exist in the
        head file or whose quoted evidence does not match it exactly
        count as unanchored.  Then the schema's own paths (steps
        2–3): a finding whose declared pattern differs from the
        pattern its message asserts is born marked unverifiable
        at origin — settled in the production ledger, never
        emitted, never counted malformed.  A finding with NO
        declared pattern is NOT settled here (gate-form
        amendment, ADENDA-PUERTA-FORMA-20261027): it is built as
        a candidate exactly as born and the shaping stage —
        whose Case B exists precisely for pattern-less claims —
        extracts its pattern from its own prose against its
        citation or declares it unverifiable at origin under the
        same code.  Whether the declared tokens stand in the
        citation is NOT judged here: that is the shaping stage's
        settled trim."""

        label = pass_name if pass_name is not None else FALLBACK_PASS
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

        # The evidence-first paths (paper §2c, steps 2–3, with
        # the gate-form amendment of ADENDA-PUERTA-FORMA-20261027:
        # no declared pattern no longer settles here — the
        # candidate is built as born and the shaping stage's
        # Case B mining decides its fate; only a CONTRADICTORY
        # declaration — a pattern is declared and the message
        # asserts a different one — still settles here).
        declared = _declared_pattern(raw)
        asserted = _asserted_tokens(message)
        if declared and set(declared) != set(asserted):
            self._settle_ledger(
                info,
                pass_name=label,
                claim_type=claim_type,
                file=file,
                start_line=start,
                end_line=end,
                code=CODE_PATTERN_MISMATCH,
                reason=(
                    "declared pattern "
                    f"{sorted(set(declared))} differs from the pattern "
                    f"the message asserts {sorted(set(asserted))}"
                ),
            )
            return None

        severity_hint, category_hint = _ALL_CLAIM_HINTS.get(
            claim_type, CATEGORY_HINTS.get(claim_type, ("high", "correctness"))
        )
        return Candidate(
            rule_id=f"llm_v24_{claim_type}",
            claim_type=claim_type,
            file=file,
            start_line=start,
            end_line=end,
            message=message.strip(),
            evidence_text=actual,
            severity_hint=severity_hint,
            category_hint=category_hint,
            producer="alma-llm-reviewer-v24",
        )


__all__ = [
    "CODE_DECLARED_UNVERIFIABLE",
    "CODE_NO_PATTERN",
    "CODE_PATTERN_MISMATCH",
    "DEFAULT_DEEP_MAX_OUTPUT_TOKENS",
    "LENGTH_RETRY_MULTIPLIER",
    "LLMReviewerV24",
    "LLMRunInfoV24",
    "REVIEWER_VERSION",
]
