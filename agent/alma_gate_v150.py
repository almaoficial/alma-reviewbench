"""ALMA evidence gate 1.5.0: a verification rule for the general
categories — the rule the 1.4.1 never defined.

Pre-registered in PREREGISTRO-PUERTA-150.md.  The antecedent is
measured, not hypothetical: the full adjudication of practice run
nº 311 (ADJUDICACION-COMPLETA-311-20261022.md) showed gate 1.4.1
passing 1 of ≤165 candidates in ALMA mode, and the offline replay
(REPLAY-PUERTA-141-20261022.md) decomposed the death on the 166
real findings of base run nº 298 — 149/166 (89.8 %) held as
``needs_validation`` under the single blocker
``sin_regla_de_verificacion_en_puerta`` because the 1.4.1 defines
NO verification rule for the reviewer's nine general categories,
and 17/166 (10.2 %) firm-rejected on the anchor: the reviewer
builds its evidence against the full HEAD file (and verifies that
match before the gate, ``_to_candidate_v23``), while the 1.4.1
anchors only against the diff hunks.  TP-kill was 89/89 and the 8
gold-confirmed FPs shared fate and reason with the true ones:
zero discrimination on the general path.  The class-evidence
dialect killed zero measurable claims — this gate does not
touch it.

WHAT 1.5.0 IS:

* The 19 classes: UNCHANGED behaviour, by delegation.  Class
  candidates are validated through an ``AlmaGateV141`` instance,
  untouched; their verdicts, reasons and acceptance equivalence
  are the 1.4.1's by construction.  This module reimplements no
  class rule.
* The general categories (the v2.3 paper §3(a) nine labels): a
  NEW deterministic grounding rule (paper 150 §2).  The
  candidate's stored evidence IS the head excerpt for the cited
  range — the pipeline's construction guarantee (the reviewer
  verifies it against the head before the gate and drops what
  does not match; in the base arm those same candidates are the
  findings).  The gate checks:

  (G0) form — a valid line range, as in the whole line;
  (G1) existence against the head — the stored evidence covers
       exactly the cited range, else the citation points at
       lines that do not exist as cited: firm rejection;
  (G2) the anchor — head OR diff: every cited line the diff
       DOES contain must match the stored evidence exactly (a
       contradiction between artifacts is a firm rejection:
       the citation is neither the head nor the diff), and
       lines the diff does not contain resolve against the
       head excerpt.  This repairs the 17 anchor deaths of the
       replay, whose evidence matched the file exactly;
  (G3) affirmative contradiction — the ONLY other firm-reject
       family: the claim declares absent a guard its own
       evidence shows present (a backtick code token governed
       by a closed list of absence markers in its sentence, and
       the normalized token present in the cited evidence);
  (G4) affirmative grounding — the concrete pattern the claim
       asserts is the set of code tokens it backtick-quotes
       (normalization declared in the paper: no leading dot, no
       trailing empty ``()``; a code token has no internal
       whitespace and length ≥ 2).  When EVERY asserted token
       appears in the cited evidence lines, the claim is
       grounded in its own citation: ACCEPTED and emitted;
  (G5) duplicate of an already accepted finding (class or
       general), with the whole line's discipline.

  What can neither be verified nor contradicted is held as
  ``needs_validation`` with a SPECIFIC reason code — never the
  old single generic blocker:

  * ``sin_patron_concreto_en_el_reclamo`` — the message asserts
    no code token the gate can check against its citation;
  * ``tokens_afirmados_ausentes_en_la_evidencia`` — some
    asserted tokens are absent from the cited lines (the
    reason lists them).

  Held general candidates also carry the informative
  ``no_added_line`` blocker when no cited line is ``added`` in
  the diff (continuity with the 1.4.1's general path).  The
  fate of ``needs_validation`` in production — marked emission,
  a later validation stage, or declared discard — is an OPEN
  question the paper leaves to Alejandro (paper 150 §5); this
  gate's measurement reading is strict emission: only accepted
  candidates emit.

Declared limitations (paper 150 §2): token verification is by
substring over the cited lines — no AST, no comment/string/code
distinction; the contradiction family is a closed list of
English absence markers (the reviewer's messages are English);
the gate trusts ``evidence_text`` as the head excerpt per the
pipeline's construction contract and cross-checks it against
the diff on every line the diff contains.

Deterministic duplicate semantics across paths (declared here):
class verdicts are computed by one delegated batch over the
class subset — identical to the 1.4.1 by construction — and
their accepted keys seed the general path's duplicate set;
general candidates are then judged in list order.

The gates 1.0.0–1.4.1 are never touched: this module only
imports them.  Frozen POLICY_SHA256 values: 1.0.0
3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35,
1.1.0 6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9,
1.2.0 a768afa46136ba1bf542da65006a946d11cb39e8db73fbd484c3f021b7994211,
1.3.0 0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78,
1.4.0 b0c0aa661f644b5229ea3ee1984b3fd2dbb17649d1eeae91e5945fd357fd6d19,
1.4.1 73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from dataclasses import asdict, dataclass

from .alma_gate import candidate_to_finding
from .alma_gate_v141 import (
    _POLICY as _POLICY_V141,
    GENERAL_CATEGORIES_V141,
    KNOWN_CLAIM_TYPES_V141,
    AlmaGateV141,
    EvidenceLineV141,
    LedgerEntryV141,
)
from .alma_gate_v141 import (
    NeedsValidationRecord as NeedsValidationRecordV141,
)
from .base_reviewer import Candidate
from .diff_parser import DiffIndex

POLICY_VERSION = "alma-evidence-gate/1.5.0"

GENERAL_CATEGORIES_V150 = GENERAL_CATEGORIES_V141

_POLICY = {
    "version": POLICY_VERSION,
    "required_checks": list(_POLICY_V141["required_checks"])
    + [
        "a general-category candidate (the v2.3 taxonomy) is verified against its own citation: the anchor resolves against the head file or the diff hunks — every cited line the diff contains must match the stored evidence exactly, and lines the diff does not contain resolve against the head excerpt the reviewer verified — and every concrete code token the claim asserts (backtick-quoted, normalized) is present in the cited evidence; a candidate so verified is accepted and emitted",
        "a general-category candidate is firm rejected only on an invalid line range, on a citation that does not resolve against the head file (the stored evidence does not cover exactly the cited range), on stored evidence that contradicts the diff, on an affirmative contradiction (the cited evidence contains a token the claim declares absent), or as a duplicate of an already accepted finding",
        "a general-category candidate that can neither be verified nor contradicted is held as needs_validation with a specific reason code — sin_patron_concreto_en_el_reclamo when the message asserts no checkable code token, tokens_afirmados_ausentes_en_la_evidencia when asserted tokens are absent from the cited lines — never a single generic no-rule blocker",
    ],
    "claims": dict(_POLICY_V141["claims"]),
}
POLICY_SHA256 = hashlib.sha256(
    json.dumps(_POLICY, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

KNOWN_CLAIM_TYPES_V150 = tuple(sorted(_POLICY["claims"].keys()))

# Blocker check ids for the general path (paper 150 §2).  The
# no_added_line id is shared with the 1.4.1's general path on
# purpose: it is the same informative condition.
CHECK_NO_CONCRETE_PATTERN = "sin_patron_concreto_en_el_reclamo"
CHECK_TOKENS_ABSENT = "tokens_afirmados_ausentes_en_la_evidencia"
CHECK_NO_ADDED_LINE = "no_added_line"

_REQUIREMENTS = {
    CHECK_NO_CONCRETE_PATTERN: (
        "un reclamo que afirme un patrón de código concreto "
        "(tokens entre backticks) contrastable con su cita"
    ),
    CHECK_TOKENS_ABSENT: (
        "una cita que contenga los tokens que el reclamo afirma, "
        "o una reformulación del reclamo cuyos tokens estén en "
        "la evidencia citada"
    ),
    CHECK_NO_ADDED_LINE: (
        "una cita que incluya al menos una línea agregada por el cambio"
    ),
}

_NO_ADDED_REASON = (
    "cited evidence contains no line added by this change "
    "(every cited line is pre-existing context)"
)


def _blocker(check: str, reason: str) -> dict:
    return {
        "check": check,
        "reason": reason,
        "requirement": _REQUIREMENTS[check],
    }


@dataclass(frozen=True)
class EvidenceLineV150:
    """One cited line.  ``kind`` is the diff kind when the line
    is in the diff; for a line resolved against the head file
    alone it is ``context`` (the line is pre-existing by
    definition — it is not part of this change's hunks)."""

    file: str
    line: int
    kind: str
    text: str


@dataclass(frozen=True)
class NeedsValidationRecordV150:
    """A held candidate.  NOTE: there is deliberately NO severity
    field of any kind on this type — a held finding with a severity
    is a schema error under the third state's contract, inherited
    unchanged from the 1.4.x."""

    rule_id: str
    claim_type: str
    file: str
    start_line: int
    end_line: int
    message: str
    evidence: tuple[EvidenceLineV150, ...]
    producer: str
    blockers: tuple[dict, ...]
    validator_version: str
    policy_sha256: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LedgerEntryV150:
    """The line's ledger entry shape, stamped with the 1.5.0
    identity.  Statuses here are only accepted / rejected: held
    candidates live in ``needs_validation``, never in this ledger."""

    rule_id: str
    claim_type: str
    file: str
    start_line: int
    end_line: int
    message: str
    severity_hint: str
    category_hint: str
    evidence: tuple[EvidenceLineV150, ...]
    status: str
    reasons: tuple[str, ...]
    validator_version: str
    policy_sha256: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GateResultV150:
    findings: tuple[dict, ...]
    ledger: tuple[LedgerEntryV150, ...]
    needs_validation: tuple[NeedsValidationRecordV150, ...]


# ------------------------------------------------------------------
# Token machinery (paper 150 §2 (G3)/(G4)) — deterministic, closed.
# ------------------------------------------------------------------

_BACKTICK_RE = re.compile(r"`([^`\n]+)`")

# A closed list of absence markers that, immediately governing a
# backticked token (optional article in between), make the claim
# declare that token absent.  English only: the reviewer's
# messages are English.
_ABSENCE_GOVERN_RE = re.compile(
    r"\b(without|no|missing|lacks|does\s+not\s+use|doesn't\s+use"
    r"|never\s+uses|not\s+using)\s+(?:a\s+|an\s+|the\s+)?`([^`\n]+)`",
    re.IGNORECASE,
)


def _normalize_token(raw: str) -> str:
    token = raw.strip()
    if token.startswith("."):
        token = token[1:]
    if token.endswith("()"):
        token = token[:-2]
    return token.strip()


def _is_code_token(token: str) -> bool:
    return len(token) >= 2 and not any(char.isspace() for char in token)


def _asserted_tokens(message: str) -> list[str]:
    """The concrete pattern the claim asserts: its backtick-quoted
    code tokens, normalized, in order of first appearance."""

    tokens: list[str] = []
    for span in _BACKTICK_RE.findall(message):
        token = _normalize_token(span)
        if _is_code_token(token) and token not in tokens:
            tokens.append(token)
    return tokens


def _absence_contradiction(
    message: str, evidence_blob: str
) -> str | None:
    """Paper 150 §2 (G3): returns the normalized token the claim
    declares absent while its cited evidence contains it, or
    None.  Only absence-governed tokens are considered — a token
    merely mentioned is not declared absent."""

    for match in _ABSENCE_GOVERN_RE.finditer(message):
        token = _normalize_token(match.group(2))
        if _is_code_token(token) and token in evidence_blob:
            return token
    return None


def _evidence_lines_v150(
    evidence: tuple[EvidenceLineV141, ...],
) -> tuple[EvidenceLineV150, ...]:
    return tuple(
        EvidenceLineV150(
            file=item.file, line=item.line, kind=item.kind, text=item.text
        )
        for item in evidence
    )


def _restamp_entry(entry: LedgerEntryV141) -> LedgerEntryV150:
    return LedgerEntryV150(
        rule_id=entry.rule_id,
        claim_type=entry.claim_type,
        file=entry.file,
        start_line=entry.start_line,
        end_line=entry.end_line,
        message=entry.message,
        severity_hint=entry.severity_hint,
        category_hint=entry.category_hint,
        evidence=_evidence_lines_v150(entry.evidence),
        status=entry.status,
        reasons=tuple(entry.reasons),
        validator_version=POLICY_VERSION,
        policy_sha256=POLICY_SHA256,
    )


def _restamp_held(
    record: NeedsValidationRecordV141,
) -> NeedsValidationRecordV150:
    return NeedsValidationRecordV150(
        rule_id=record.rule_id,
        claim_type=record.claim_type,
        file=record.file,
        start_line=record.start_line,
        end_line=record.end_line,
        message=record.message,
        evidence=_evidence_lines_v150(record.evidence),
        producer=record.producer,
        blockers=tuple(record.blockers),
        validator_version=POLICY_VERSION,
        policy_sha256=POLICY_SHA256,
    )


def _key(candidate: Candidate) -> tuple[str, int, int, str]:
    """The line's duplicate key (the 1.3.0's, unchanged)."""

    return (
        candidate.file,
        candidate.start_line,
        candidate.end_line,
        candidate.message.strip().lower(),
    )


class AlmaGateV150:
    """Evidence validator 1.5.0: the 1.4.1 by delegation for the
    19 classes, plus the general-category grounding rule of paper
    150 §2 — the rule whose absence the replay of the 1.4.1
    measured at 149/166 holds and 17/166 anchor rejections."""

    version = POLICY_VERSION
    policy_sha256 = POLICY_SHA256

    def validate(
        self,
        candidates: list[Candidate],
        diff: DiffIndex,
        agent_name: str,
    ) -> GateResultV150:
        class_candidates = [
            candidate
            for candidate in candidates
            if candidate.claim_type not in GENERAL_CATEGORIES_V150
        ]
        v141_result = AlmaGateV141().validate(
            class_candidates, diff, agent_name
        )
        # Map the delegated outcomes back to their candidates, in
        # order.  The 1.4.1's ledger holds one entry per delegated
        # candidate that was accepted or rejected; held candidates
        # live in its needs_validation.  Findings parallel the
        # accepted ledger entries in order.
        ledger_by_key: dict[tuple, deque] = {}
        for entry in v141_result.ledger:
            ledger_by_key.setdefault(
                (
                    entry.rule_id,
                    entry.file,
                    entry.start_line,
                    entry.end_line,
                    entry.message,
                ),
                deque(),
            ).append(entry)
        held_by_key: dict[tuple, deque] = {}
        for record in v141_result.needs_validation:
            held_by_key.setdefault(
                (
                    record.rule_id,
                    record.file,
                    record.start_line,
                    record.end_line,
                    record.message,
                ),
                deque(),
            ).append(record)
        class_findings = deque(v141_result.findings)
        # Declared semantics (module docstring): the delegated
        # class acceptances seed the duplicate set BEFORE any
        # general candidate is judged; general acceptances join
        # it as they happen.
        accepted_keys: set[tuple[str, int, int, str]] = {
            (
                entry.file,
                entry.start_line,
                entry.end_line,
                entry.message.strip().lower(),
            )
            for entry in v141_result.ledger
            if entry.status == "accepted"
        }

        findings: list[dict] = []
        ledger: list[LedgerEntryV150] = []
        held: list[NeedsValidationRecordV150] = []

        for candidate in candidates:
            if candidate.claim_type in GENERAL_CATEGORIES_V150:
                outcome = self._validate_general(
                    candidate, diff, agent_name, accepted_keys
                )
                if isinstance(outcome, NeedsValidationRecordV150):
                    held.append(outcome)
                elif isinstance(outcome, tuple):
                    finding, entry = outcome
                    findings.append(finding)
                    ledger.append(entry)
                else:
                    ledger.append(outcome)
                continue
            map_key = (
                candidate.rule_id,
                candidate.file,
                candidate.start_line,
                candidate.end_line,
                candidate.message,
            )
            if ledger_by_key.get(map_key):
                entry = ledger_by_key[map_key].popleft()
                if entry.status == "accepted":
                    findings.append(class_findings.popleft())
                ledger.append(_restamp_entry(entry))
            else:
                record = held_by_key[map_key].popleft()
                held.append(_restamp_held(record))

        return GateResultV150(
            findings=tuple(findings),
            ledger=tuple(ledger),
            needs_validation=tuple(held),
        )

    def _validate_general(
        self,
        candidate: Candidate,
        diff: DiffIndex,
        agent_name: str,
        accepted_keys: set[tuple[str, int, int, str]],
    ) -> (
        LedgerEntryV150
        | NeedsValidationRecordV150
        | tuple[dict, LedgerEntryV150]
    ):
        """The general-category grounding rule (paper 150 §2):
        (G0) form, (G1) existence against the head, (G2) the
        head-OR-diff anchor, (G3) affirmative contradiction,
        (G4) affirmative token grounding, (G5) duplicate.  Firm
        rejection only from G0–G3/G5; the unverifiable-but-not-
        contradicted is held with a specific reason code."""

        def rejected(
            reasons: list[str],
            evidence: tuple[EvidenceLineV150, ...],
        ) -> LedgerEntryV150:
            return LedgerEntryV150(
                rule_id=candidate.rule_id,
                claim_type=candidate.claim_type,
                file=candidate.file,
                start_line=candidate.start_line,
                end_line=candidate.end_line,
                message=candidate.message,
                severity_hint=candidate.severity_hint,
                category_hint=candidate.category_hint,
                evidence=evidence,
                status="rejected",
                reasons=tuple(reasons),
                validator_version=POLICY_VERSION,
                policy_sha256=POLICY_SHA256,
            )

        # (G0) form.
        if (
            candidate.start_line < 1
            or candidate.end_line < candidate.start_line
        ):
            return rejected(["invalid line range"], ())

        # (G1) existence against the head: the stored evidence —
        # the head excerpt by the pipeline's construction
        # contract — must cover exactly the cited range.
        span = candidate.end_line - candidate.start_line + 1
        if len(candidate.evidence_text) != span:
            return rejected(
                [
                    "cited lines do not resolve against the head "
                    f"file: stored evidence covers "
                    f"{len(candidate.evidence_text)} line(s) for a "
                    f"cited range of {span}"
                ],
                (),
            )

        # (G2) the anchor, head OR diff: lines the diff contains
        # must match the stored evidence exactly; lines it does
        # not contain resolve against the head excerpt.
        evidence: list[EvidenceLineV150] = []
        contradictions: list[str] = []
        for offset, line_number in enumerate(
            range(candidate.start_line, candidate.end_line + 1)
        ):
            diff_line = diff.get_line(candidate.file, line_number)
            if diff_line is None:
                kind = "context"
            else:
                kind = diff_line.kind
                if diff_line.text != candidate.evidence_text[offset]:
                    contradictions.append(
                        "stored evidence contradicts the diff at "
                        f"{candidate.file}:{line_number}"
                    )
            evidence.append(
                EvidenceLineV150(
                    file=candidate.file,
                    line=line_number,
                    kind=kind,
                    text=candidate.evidence_text[offset],
                )
            )
        evidence_tuple = tuple(evidence)
        if contradictions:
            return rejected(contradictions, evidence_tuple)

        evidence_blob = "\n".join(candidate.evidence_text)

        # (G3) affirmative contradiction: the claim declares a
        # token absent and its own citation contains it.
        contradicted = _absence_contradiction(
            candidate.message, evidence_blob
        )
        if contradicted is not None:
            return rejected(
                [
                    "affirmative contradiction: the claim declares "
                    f"{contradicted!r} absent but the cited "
                    "evidence contains it"
                ],
                evidence_tuple,
            )

        # (G4) affirmative grounding: every asserted code token
        # must stand in the cited evidence.
        tokens = _asserted_tokens(candidate.message)
        blockers: list[dict] = []
        if not tokens:
            blockers.append(
                _blocker(
                    CHECK_NO_CONCRETE_PATTERN,
                    "the claim asserts no concrete code pattern "
                    "(no code tokens between backticks) that the "
                    "gate can check against its citation",
                )
            )
        else:
            missing = [t for t in tokens if t not in evidence_blob]
            if missing:
                blockers.append(
                    _blocker(
                        CHECK_TOKENS_ABSENT,
                        "asserted token(s) absent from the cited "
                        "evidence: " + ", ".join(missing),
                    )
                )
        if blockers:
            if not any(item.kind == "added" for item in evidence):
                blockers.append(
                    _blocker(CHECK_NO_ADDED_LINE, _NO_ADDED_REASON)
                )
            return NeedsValidationRecordV150(
                rule_id=candidate.rule_id,
                claim_type=candidate.claim_type,
                file=candidate.file,
                start_line=candidate.start_line,
                end_line=candidate.end_line,
                message=candidate.message,
                evidence=evidence_tuple,
                producer=candidate.producer,
                blockers=tuple(blockers),
                validator_version=POLICY_VERSION,
                policy_sha256=POLICY_SHA256,
            )

        # (G5) duplicate of an already accepted finding.
        key = _key(candidate)
        if key in accepted_keys:
            return rejected(
                ["duplicate of an already accepted finding"],
                evidence_tuple,
            )
        accepted_keys.add(key)
        entry = LedgerEntryV150(
            rule_id=candidate.rule_id,
            claim_type=candidate.claim_type,
            file=candidate.file,
            start_line=candidate.start_line,
            end_line=candidate.end_line,
            message=candidate.message,
            severity_hint=candidate.severity_hint,
            category_hint=candidate.category_hint,
            evidence=evidence_tuple,
            status="accepted",
            reasons=(
                "general grounding check passed: anchor resolved "
                "against the head file/diff; "
                f"{len(tokens)} asserted token(s) present in the "
                "cited evidence",
            ),
            validator_version=POLICY_VERSION,
            policy_sha256=POLICY_SHA256,
        )
        return candidate_to_finding(candidate, agent_name), entry


__all__ = [
    "CHECK_NO_ADDED_LINE",
    "CHECK_NO_CONCRETE_PATTERN",
    "CHECK_TOKENS_ABSENT",
    "GENERAL_CATEGORIES_V150",
    "KNOWN_CLAIM_TYPES_V150",
    "POLICY_SHA256",
    "POLICY_VERSION",
    "AlmaGateV150",
    "GateResultV150",
    "LedgerEntryV150",
    "NeedsValidationRecordV150",
]
