"""Birth-time claim shaper: claims born in the contract's form.

Provenance: PREREGISTRO-REVISOR-CONTRATO.md (2026-10-22).  The
claim-contract paper (PREREGISTRO-CONTRATO-RECLAMOS.md) specified the
form a finding must be BORN in to be verifiable (C1-C5) and measured
how much of an already-born corpus fits that form after the fact,
without inventing evidence: 49/166.  The 63 non-conforming claims
whose asserted tokens were absent from their own citation were
non-normalizable BY DESIGN there — the normalizer refused to trim
the asserted pattern to rescue them, because trimming after the
fact would paper over the signal.  This module is the producer-side
layer that paper left at design level: it acts INSIDE the reviewer,
on each candidate BEFORE the gate and with the full diff in view,
at the point where the claim is still the producer's own emission
and can reformulate its own assertion — assert only what its
citation contains — instead of being judged later for an assertion
that was born broken.  Every trim is settled in the outcome, so the
signal is not papered over: it moves from the gate's verdict to the
birth declaration.

Deterministic, no model calls.  The tokenization has a single
source of truth — the 1.5.0 gate's, imported unmodified (the same
helpers claim_contract.py consumes) — and the prose mining reuses
the normalizer's, imported unmodified: this module does not
redefine what a token is or which prose shapes are minable.

The shaping rules (PREREGISTRO-REVISOR-CONTRATO.md §2):

- Case C — the 19 classes pass INTACT: their contract is the
  1.4.1 class dialect (a pipeline decision, not the shaper's;
  the same rule as the normalizer's Case C).
- Case A — the claim already declares a pattern (>= 1 backticked
  token): the surviving pattern is the asserted tokens PRESENT in
  the cited lines; asserted tokens absent from the citation are
  DE-DECLARED at origin (their backticks are removed, so the token
  stays as a prose word and the claim stops asserting it) and each
  trim is settled in the outcome.  Nothing is ever added.  A token
  that IS in the citation is never de-declared, even under an
  absence marker: affirmative contradiction (G3) is the gate's
  firm-reject family, not material for the shaper to launder.
  If NO asserted token stands in the citation, the claim cannot
  be born in contract: it is DECLARED unverifiable at origin.
- Case B — the claim declares no token: the pattern is declared
  at birth, copied from the claim's own citation, by the
  normalizer's closed mining (code-shaped prose tokens, veto on
  absence-governed tokens, verbatim presence in the cited
  evidence).  With >= 1 mined token the shaped message is the
  born one with those tokens backticked — no word added, removed
  or reordered.  With 0, the claim is DECLARED unverifiable at
  origin.
- (c) The shaped citation is the MINIMAL range containing the
  pattern, chosen INSIDE the born citation: the first and last
  cited lines that contain some pattern token.  The shaped
  evidence is the corresponding contiguous slice of the born
  evidence — the same lines, never re-read or altered.  File,
  claim type, rule id, severity, category and producer are born
  values.
- (d) What cannot be born in contract is DECLARED unverifiable
  at origin, with its reason code settled (the line's own codes:
  tokens_afirmados_ausentes / sin_patron), never silently dropped
  and never firmly rejected: the declaration is a hold the
  producer itself states at birth; firm rejection stays reserved
  to the gate (contract C5).

Integrity: the shaper asserts only tokens the born claim asserted
(Case A) or that its prose and its citation both contain (Case B);
the shaped evidence is a contiguous slice of the born evidence,
line-for-line identical; the shaped citation is contained in the
born citation; no token is asserted unless it occurs in the born
text AND in the shaped evidence.  The measurement's programmatic
audit (PREREGISTRO-REVISOR-CONTRATO.md §4(5)) verifies exactly
this over the corpus.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import re

from .alma_gate_v141 import KNOWN_CLAIM_TYPES_V141
from .alma_gate_v150 import (
    CHECK_NO_CONCRETE_PATTERN,
    CHECK_TOKENS_ABSENT,
    _BACKTICK_RE,
    _asserted_tokens,
    _normalize_token,
)
from .base_reviewer import Candidate
from .claim_contract import _REQUIREMENTS, _mine_pattern
from .diff_parser import DiffIndex


SHAPER_VERSION = "alma-birth-shaper/1.0"

# Origins of a shaping outcome.
ORIGIN_DECLARED = "declared"  # Case A: pattern declared at birth, shaped
ORIGIN_MINED = "mined"        # Case B: pattern declared at birth from prose
ORIGIN_CLASS = "class"        # Case C: class claim, passed intact
ORIGIN_NONE = "none"          # declared unverifiable at origin


def _blocker(check: str) -> dict:
    return {
        "check": check,
        "reason": check,
        "requirement": _REQUIREMENTS[check],
    }


def _claim_summary(candidate: Candidate) -> dict:
    return {
        "rule_id": candidate.rule_id,
        "claim_type": candidate.claim_type,
        "file": candidate.file,
        "start_line": candidate.start_line,
        "end_line": candidate.end_line,
    }


def _undeclare(message: str, trimmed: list[str]) -> str:
    """Remove the backticks of every span whose token was trimmed.

    The token's words stay as plain prose; the claim stops
    asserting them.  Spans whose normalized token survives (or is
    not a code token at all) keep their backticks untouched.
    """
    trimmed_set = set(trimmed)

    def _sub(match: "re.Match[str]") -> str:
        raw = match.group(1)
        token = _normalize_token(raw)
        if token is not None and token in trimmed_set:
            return raw.strip()
        return match.group(0)

    return _BACKTICK_RE.sub(_sub, message)


def _minimal_range(candidate: Candidate, pattern: tuple[str, ...]) -> tuple[int, int]:
    """First/last cited lines containing some pattern token.

    By construction every pattern token stands in the cited
    evidence, so the hit list is never empty; the born range is
    returned unchanged as a defensive fallback.
    """
    hits = [
        i
        for i, line in enumerate(candidate.evidence_text)
        if any(token in line for token in pattern)
    ]
    if not hits:
        return candidate.start_line, candidate.end_line
    return (
        candidate.start_line + hits[0],
        candidate.start_line + hits[-1],
    )


def _range_has_added_line(
    diff: DiffIndex | None, path: str, start: int, end: int
) -> bool | None:
    """Whether the diff shows an `added` line inside [start, end].

    Informative datum settled in the outcome (the same fact the
    gates record as no_added_line); None when the diff has no
    line of the range at all.
    """
    if diff is None:
        return None
    saw_line = False
    for number in range(start, end + 1):
        line = diff.get_line(path, number)
        if line is None:
            continue
        saw_line = True
        if line.kind == "added":
            return True
    return False if saw_line else None


@dataclass(frozen=True)
class ShapingOutcome:
    """The birth declaration of one claim."""

    candidate: Candidate | None  # the shaped claim; None = unverifiable at origin
    claim: dict = field(default_factory=dict)
    shaped: bool = False  # a candidate is delivered in contract form (or intact)
    origin: str = ORIGIN_NONE  # declared | mined | class | none
    pattern: tuple[str, ...] = ()  # final asserted tokens (empty for class/none)
    trimmed_tokens: tuple[str, ...] = ()  # born asserted tokens cut at origin
    born_range: tuple[int, int] = (0, 0)
    shaped_range: tuple[int, int] | None = None
    range_has_added_line: bool | None = None
    blockers: tuple[dict, ...] = ()
    notes: tuple[str, ...] = ()


def shape_claim(candidate: Candidate, diff: DiffIndex | None = None) -> ShapingOutcome:
    """Shape one born claim into the contract's form, or declare it.

    Deterministic; never invents evidence and never firmly
    rejects.  See the module docstring for the rules.
    """
    claim = _claim_summary(candidate)
    born_range = (candidate.start_line, candidate.end_line)

    # Case C — the 19 classes pass intact (their contract is the
    # 1.4.1 class dialect; pipeline decision, not the shaper's).
    if candidate.claim_type in KNOWN_CLAIM_TYPES_V141:
        return ShapingOutcome(
            candidate=candidate,
            claim=claim,
            shaped=True,
            origin=ORIGIN_CLASS,
            born_range=born_range,
            shaped_range=born_range,
            range_has_added_line=_range_has_added_line(
                diff, candidate.file, *born_range
            ),
            notes=("class_claim_passed_intact",),
        )

    evidence_blob = "\n".join(candidate.evidence_text)
    born_pattern = _asserted_tokens(candidate.message)
    trimmed: list[str] = []
    notes: list[str] = []

    if born_pattern:
        # Case A — keep only what the citation contains; settle
        # every trim.  Never add, never launder a contradiction.
        surviving = [t for t in born_pattern if t in evidence_blob]
        trimmed = [t for t in born_pattern if t not in evidence_blob]
        if not surviving:
            return ShapingOutcome(
                candidate=None,
                claim=claim,
                shaped=False,
                origin=ORIGIN_NONE,
                trimmed_tokens=tuple(trimmed),
                born_range=born_range,
                blockers=(_blocker(CHECK_TOKENS_ABSENT),),
                notes=("declared_unverifiable_at_origin",),
            )
        message = (
            _undeclare(candidate.message, trimmed) if trimmed else candidate.message
        )
        if trimmed:
            notes.append("tokens_trimmed_at_origin")
        pattern = tuple(surviving)
        origin = ORIGIN_DECLARED
    else:
        # Case B — declare the pattern at birth, copied from the
        # claim's own citation via the normalizer's closed mining.
        mined, normalized = _mine_pattern(candidate.message, evidence_blob)
        if not mined:
            return ShapingOutcome(
                candidate=None,
                claim=claim,
                shaped=False,
                origin=ORIGIN_NONE,
                born_range=born_range,
                blockers=(_blocker(CHECK_NO_CONCRETE_PATTERN),),
                notes=("declared_unverifiable_at_origin",),
            )
        message = normalized
        pattern = tuple(mined)
        origin = ORIGIN_MINED
        notes.append("pattern_declared_at_origin_from_citation")

    # (c) The citation is the minimal range containing the pattern,
    # chosen inside the born citation; the evidence is the matching
    # contiguous slice of the born evidence.
    start, end = _minimal_range(candidate, pattern)
    if (start, end) != born_range:
        evidence = candidate.evidence_text[
            start - candidate.start_line : end - candidate.start_line + 1
        ]
        shaped = replace(
            candidate,
            message=message,
            start_line=start,
            end_line=end,
            evidence_text=evidence,
        )
        notes.append("citation_shrunk_to_pattern_range")
    elif message != candidate.message:
        shaped = replace(candidate, message=message)
    else:
        shaped = candidate

    return ShapingOutcome(
        candidate=shaped,
        claim=claim,
        shaped=True,
        origin=origin,
        pattern=pattern,
        trimmed_tokens=tuple(trimmed),
        born_range=born_range,
        shaped_range=(shaped.start_line, shaped.end_line),
        range_has_added_line=_range_has_added_line(
            diff, shaped.file, shaped.start_line, shaped.end_line
        ),
        notes=tuple(notes),
    )


@dataclass(frozen=True)
class ShapingBatch:
    outcomes: tuple[ShapingOutcome, ...] = ()

    def shaped_candidates(self) -> list[Candidate]:
        """The claims delivered in contract form, in born order."""
        return [o.candidate for o in self.outcomes if o.candidate is not None]

    def held_at_origin(self) -> list[ShapingOutcome]:
        """The claims declared unverifiable at origin, with reasons."""
        return [o for o in self.outcomes if o.candidate is None]


def shape_candidates(
    candidates: list[Candidate], diff: DiffIndex | None = None
) -> ShapingBatch:
    """Shape a batch of born claims, preserving order."""
    return ShapingBatch(
        outcomes=tuple(shape_claim(c, diff) for c in candidates)
    )
