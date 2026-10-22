"""ALMA claim contract 1.0: the form a finding must be born in
to be deterministically verifiable — and the deterministic
normalizer that brings a born claim to that form when it can
be done without inventing evidence.

Pre-registered in PREREGISTRO-CONTRATO-RECLAMOS.md.  The
antecedent is measured: gate 1.5.0 (PREREGISTRO-PUERTA-150.md)
defined the general-path verification rule the 1.4.1 lacked,
and its replay (RESULTADO-REPLAY-150-20261022.md) still held
133/166 of base run nº 298's findings — 71 under
``sin_patron_concreto_en_el_reclamo`` (the message asserts no
code token a deterministic gate can check against its citation)
and 62 under ``tokens_afirmados_ausentes_en_la_evidencia``
(the claim asserts tokens its own cited lines do not contain).
Both blockers are properties of how claims are BORN, not of
the gate.  This module is the producer-side end of the tube:

THE CONTRACT (paper §2): a finding is in contract form when
(C1) its message declares a concrete pattern — a non-empty
set of backtick-quoted code tokens, in the exact form gate
1.5.0's rule (G4) reads; (C2) every affirmed token stands in
the cited evidence lines; (C3) the citation resolves against
the head file and/or the diff hunks (checked by the gate in
(G1)/(G2)); (C4) the claim type is one of the 19 classes or a
general category WITH a concrete pattern; (C5) non-conformity
is never a firm rejection at the contract stage — the claim
is held as ``needs_validation`` with its specific reason
code.

THE NORMALIZER (paper §3): deterministic, extraction-only.
It takes a candidate as born and returns either the candidate
in contract form or a non-conformity declaration with its
specific reason code:

* Case A — the claim already declares a pattern (>= 1 backtick
  code token): conforming UNCHANGED when every affirmed token
  stands in its cited evidence; NON-conforming when any is
  absent.  The normalizer never trims the declared pattern to
  rescue the claim, and never substitutes a mined pattern for
  the declared one: a claim that asserts what its citation
  does not contain is the signal the measurement protects.
* Case B — the claim declares no code token: the normalizer
  mines the message prose (outside backtick spans) for tokens
  with a code shape from a closed list (snake_case, dotted
  paths, camelCase/PascalCase, call shape, ALL-CAPS >= 3,
  whitespace-free quoted literals).  A mined token is affirmed
  only if it has code shape in the claim's own prose, is NOT
  absence-governed anywhere in the message (the closed
  absence list of gate rule (G3); the normalizer never affirms
  as present what the claim declares absent), and stands
  verbatim in the cited evidence.  The normalized message is
  the original with each ungoverned occurrence of each mined
  token wrapped in backticks — not one word added, removed or
  reordered; file, range, type and evidence stay byte-identical
  to the born ones.  Zero minable tokens: NON-conforming.
* Case C — the 19 classes: passed through untouched; their
  contract is the 1.4.1's class dialect.

INTEGRITY (paper §3, the clause that governs everything): the
normalizer affirms only tokens that occur in the claim's own
text AND in its cited evidence; it adds, removes or alters no
evidence line and moves no citation.  A claim whose affirmed
tokens do not exist in its evidence is NON-conforming and
counted as such — that non-conformity is signal about the
reviewer, not a defect to paper over.

The token definition has a single source of truth: gate
1.5.0's own extractor and normalization, imported unmodified.
The gates 1.0.0–1.5.0 are never touched by this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .alma_gate_v141 import GENERAL_CATEGORIES_V141
from .alma_gate_v150 import (
    CHECK_NO_CONCRETE_PATTERN,
    CHECK_TOKENS_ABSENT,
    _asserted_tokens,
    _is_code_token,
    _normalize_token,
)
from .base_reviewer import Candidate

CONTRACT_VERSION = "alma-claim-contract/1.0"

GENERAL_CATEGORIES = GENERAL_CATEGORIES_V141

_REQUIREMENTS = {
    CHECK_TOKENS_ABSENT: (
        "un patrón declarado cuyos tokens estén todos en la "
        "evidencia citada (contrato C2)"
    ),
    CHECK_NO_CONCRETE_PATTERN: (
        "un patrón concreto declarado entre backticks, o "
        "minable de la prosa: tokens con forma de código "
        "presentes en el mensaje y en la evidencia citada "
        "(contrato C1/C4)"
    ),
}


def _blocker(check: str, reason: str) -> dict:
    return {
        "check": check,
        "reason": reason,
        "requirement": _REQUIREMENTS[check],
    }


@dataclass(frozen=True)
class ContractOutcome:
    """The normalizer's verdict on one born candidate.

    ``candidate`` is the contract-form candidate when
    ``conforming`` is true — the born candidate itself for
    origins ``born``/``class``, a message-reformatted copy for
    origin ``mined`` — and None when the claim is declared
    non-conforming (then ``blockers`` carries the specific
    reason, in the gate's blocker shape).  ``pattern`` is the
    affirmed pattern after normalization (the born declared
    pattern, or the mined one); empty when no pattern exists.
    """

    candidate: Candidate | None
    conforming: bool
    origin: str  # "born" | "mined" | "class" | "none"
    pattern: tuple[str, ...]
    blockers: tuple[dict, ...]

    @property
    def check(self) -> str | None:
        """The primary non-conformity code, or None."""
        return self.blockers[0]["check"] if self.blockers else None


# ------------------------------------------------------------------
# Prose mining (paper §3, Case B) — deterministic, closed shapes.
# ------------------------------------------------------------------

_BACKTICK_SPAN_RE = re.compile(r"`[^`\n]+`")
_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
_QUOTED_RE = re.compile(r"'([^'\n]+)'|\"([^\"\n]+)\"")

# The closed absence-governance list of gate rule (G3), applied
# to prose: a marker immediately governing a word (optional
# article in between) declares that word absent.
_ABSENCE_PROSE_RE = re.compile(
    r"\b(?:without|no|missing|lacks|does\s+not\s+use|doesn't\s+use"
    r"|never\s+uses|not\s+using)\s+(?:a\s+|an\s+|the\s+)?"
    r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)",
    re.IGNORECASE,
)


def _has_code_shape(word: str, call_shape: bool) -> bool:
    """The closed code-shape list of paper §3 Case B, applied
    to a dotted word as written in the prose."""

    if "_" in word or "." in word:
        return True
    if call_shape:
        return True
    if (
        len(word) >= 3
        and word.isupper()
        and sum(char.isalpha() for char in word) >= 2
    ):
        return True
    return re.search(r"[a-z][A-Z]", word) is not None


def _prose_segments(message: str) -> list[tuple[int, int]]:
    """The (start, end) spans of `message` OUTSIDE backtick
    spans — the only text the miner may read or reformat."""

    segments: list[tuple[int, int]] = []
    cursor = 0
    for match in _BACKTICK_SPAN_RE.finditer(message):
        if match.start() > cursor:
            segments.append((cursor, match.start()))
        cursor = match.end()
    if cursor < len(message):
        segments.append((cursor, len(message)))
    return segments


def _mine_pattern(
    message: str, evidence_blob: str
) -> tuple[tuple[str, ...], str]:
    """Case B mining: returns (pattern, normalized_message).

    A token is mined when it has code shape in the claim's own
    prose, is not absence-governed anywhere in the message,
    and stands verbatim in the cited evidence.  The
    normalized message wraps every ungoverned occurrence of
    each mined token in backticks (quoted literals trade
    their prose quotes for the backticks); no word is added,
    removed or reordered."""

    governed_types: set[str] = set()
    for start, end in _prose_segments(message):
        segment = message[start:end]
        for match in _ABSENCE_PROSE_RE.finditer(segment):
            governed_types.add(_normalize_token(match.group(1)))

    # Candidate replacements per segment:
    # (seg_start, span_start, span_end, replacement, token).
    replacements: list[tuple[int, int, str, str]] = []
    pattern: list[str] = []
    for start, end in _prose_segments(message):
        segment = message[start:end]
        found: list[tuple[int, int, str, str]] = []
        for match in _WORD_RE.finditer(segment):
            word = match.group(0)
            call_shape = segment[match.end() : match.end() + 1] == "("
            if not _has_code_shape(word, call_shape):
                continue
            token = _normalize_token(word)
            if token in governed_types or not _is_code_token(token):
                continue
            if token not in evidence_blob:
                continue
            span_end = match.end()
            if segment[span_end : span_end + 2] == "()":
                span_end += 2
            found.append(
                (match.start(), span_end, f"`{segment[match.start():span_end]}`", token)
            )
        for match in _QUOTED_RE.finditer(segment):
            content = match.group(1) or match.group(2) or ""
            if (
                not content
                or any(char.isspace() for char in content)
                or len(content) < 2
            ):
                continue
            token = _normalize_token(content)
            if token in governed_types or not _is_code_token(token):
                continue
            if token not in evidence_blob:
                continue
            found.append(
                (match.start(), match.end(), f"`{content}`", token)
            )
        found.sort(key=lambda item: item[0])
        last_end = -1
        for span_start, span_end, replacement, token in found:
            if span_start < last_end:
                continue  # overlap: the earlier span wins
            last_end = span_end
            replacements.append(
                (start + span_start, start + span_end, replacement, token)
            )
            if token not in pattern:
                pattern.append(token)

    if not pattern:
        return (), message
    replacements.sort(key=lambda item: item[0])
    pieces: list[str] = []
    cursor = 0
    for span_start, span_end, replacement, _token in replacements:
        pieces.append(message[cursor:span_start])
        pieces.append(replacement)
        cursor = span_end
    pieces.append(message[cursor:])
    return tuple(pattern), "".join(pieces)


# ------------------------------------------------------------------
# The normalizer (paper §3).
# ------------------------------------------------------------------


def normalize_claim(candidate: Candidate) -> ContractOutcome:
    """Bring one born candidate to contract form, or declare
    its non-conformity with a specific reason code.  The
    candidate is never mutated; a mined normalization returns
    a copy whose ONLY changed field is the message."""

    # Case C — the 19 classes: their contract is the 1.4.1's
    # class dialect; the normalizer does not rewrite them.
    if candidate.claim_type not in GENERAL_CATEGORIES:
        return ContractOutcome(
            candidate=candidate,
            conforming=True,
            origin="class",
            pattern=tuple(_asserted_tokens(candidate.message)),
            blockers=(),
        )

    evidence_blob = "\n".join(candidate.evidence_text)
    born = _asserted_tokens(candidate.message)

    # Case A — the claim already declares its pattern.
    if born:
        absent = [token for token in born if token not in evidence_blob]
        if not absent:
            return ContractOutcome(
                candidate=candidate,
                conforming=True,
                origin="born",
                pattern=tuple(born),
                blockers=(),
            )
        return ContractOutcome(
            candidate=None,
            conforming=False,
            origin="none",
            pattern=tuple(born),
            blockers=(
                _blocker(
                    CHECK_TOKENS_ABSENT,
                    "asserted token(s) absent from the cited "
                    "evidence: " + ", ".join(absent),
                ),
            ),
        )

    # Case B — no declared pattern: mine the prose.
    pattern, normalized_message = _mine_pattern(
        candidate.message, evidence_blob
    )
    if not pattern:
        return ContractOutcome(
            candidate=None,
            conforming=False,
            origin="none",
            pattern=(),
            blockers=(
                _blocker(
                    CHECK_NO_CONCRETE_PATTERN,
                    "the claim asserts no concrete code pattern: "
                    "no backtick token is declared and no "
                    "code-shaped prose token stands in the "
                    "cited evidence",
                ),
            ),
        )
    return ContractOutcome(
        candidate=replace(candidate, message=normalized_message),
        conforming=True,
        origin="mined",
        pattern=pattern,
        blockers=(),
    )


def normalize_candidates(
    candidates: list[Candidate],
) -> list[ContractOutcome]:
    """Order-preserving batch form of `normalize_claim`."""
    return [normalize_claim(candidate) for candidate in candidates]


__all__ = [
    "CONTRACT_VERSION",
    "GENERAL_CATEGORIES",
    "ContractOutcome",
    "normalize_candidates",
    "normalize_claim",
]
