"""ALMA evidence gate 1.5.1: the 1.5.0, plus one repair on the
general path — a claim no longer dies for form alone.

Declared in ADENDA-PUERTA-FORMA-20261027.md BEFORE this code.
The antecedent is measured, twice: practice runs nº 373 and
nº 374 (autopsies of 27/10/2026) settled 29 and 36 claims at
origin under ``sin_patron_concreto_en_el_reclamo`` — the claim
asserted no backticked code token — with the discards
concentrated on gold-TP territory (autopsy 374, settled by
code: 22 of the 36 form discards overlap a gold TP; the form
discards alone overlap 34 distinct gold TPs).  Precision held
at ~72 % while grounded recall stayed at 9.4–9.8 % against the
base's 18.75 %.  The claims died for the FORM of their
assertion (no declared pattern), unjudged on their matter.

WHAT 1.5.1 IS — the 1.5.0 by delegation, with ONE change:

* The 19 classes and every general-path check of the 1.5.0 —
  (G0) form, (G1) existence against the head, (G2) the
  head-OR-diff anchor, (G3) affirmative contradiction, (G4)
  affirmative token grounding, (G5) duplicate, the specific
  ``needs_validation`` reason codes — are the 1.5.0's BY
  CONSTRUCTION: this module validates through an
  ``AlmaGateV150`` instance and reimplements no rule of it.
* The change is a pre-pass on general-category candidates
  that assert NO code token: before the 1.5.0 judges them,
  the gate attempts a deterministic pattern extraction from
  the claim's OWN prose against its cited evidence — the
  claim contract's closed mining (``_mine_pattern``, imported
  unmodified: code-shaped prose tokens only, veto on
  absence-governed tokens, verbatim presence in the cited
  evidence required).  When the extraction yields a pattern,
  the candidate the 1.5.0 judges is a copy whose message is
  the born one with the extracted tokens backticked — not one
  word added, removed or reordered; file, range, type and
  evidence stay byte-identical — and the acceptance ledger
  entry records that the pattern was EXTRACTED at the gate,
  not declared at birth.  When the extraction yields nothing,
  the candidate passes through untouched and the 1.5.0 holds
  it under the historical code: it dies for lack of anything
  checkable (matter), not for an undeclared form.

What does NOT change: a claim that DOES assert tokens keeps
the 1.5.0's exact fate — asserted tokens absent from the
citation stay held under
``tokens_afirmados_ausentes_en_la_evidencia`` (the gate never
trims or substitutes an asserted pattern); every firm
rejection (G0–G3, G5) is the 1.5.0's; the class path is the
1.5.0's delegation to the 1.4.1, untouched.  The gate invents
no evidence and moves no citation: extraction reads only the
claim's own text and its own cited lines, with the contract's
integrity clause.

The gates 1.0.0–1.5.0 are never touched: this module only
imports them.  The 1.5.0's frozen POLICY_SHA256 is imported
below as POLICY_SHA256_V150 and asserted by the tests.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace

from .alma_gate_v150 import (
    _POLICY as _POLICY_V150,
    GENERAL_CATEGORIES_V150,
    KNOWN_CLAIM_TYPES_V150,
    POLICY_SHA256 as POLICY_SHA256_V150,
    AlmaGateV150,
    EvidenceLineV150,
    LedgerEntryV150,
    NeedsValidationRecordV150,
    _asserted_tokens,
)
from .base_reviewer import Candidate
from .claim_contract import _mine_pattern
from .diff_parser import DiffIndex

POLICY_VERSION = "alma-evidence-gate/1.5.1"

GENERAL_CATEGORIES_V151 = GENERAL_CATEGORIES_V150

_POLICY = {
    "version": POLICY_VERSION,
    "required_checks": list(_POLICY_V150["required_checks"])
    + [
        "a general-category candidate that asserts no code token is not held for form alone: the gate first attempts a deterministic extraction of a concrete pattern from the claim's own prose against its cited evidence (the claim contract's closed mining — code-shaped prose tokens, absence-governed tokens vetoed, verbatim presence in the cited evidence required); when a pattern is extracted the candidate is judged on it and the acceptance records the extraction; when none can be extracted the candidate is held as needs_validation under sin_patron_concreto_en_el_reclamo exactly as in the 1.5.0",
    ],
    "claims": dict(_POLICY_V150["claims"]),
}
POLICY_SHA256 = hashlib.sha256(
    json.dumps(_POLICY, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

KNOWN_CLAIM_TYPES_V151 = KNOWN_CLAIM_TYPES_V150

EXTRACTION_REASON = (
    "pattern extracted by gate 1.5.1 from the claim's own prose "
    "against its cited evidence (not declared at birth): "
)


@dataclass(frozen=True)
class EvidenceLineV151:
    file: str
    line: int
    kind: str
    text: str


@dataclass(frozen=True)
class NeedsValidationRecordV151:
    """A held candidate, restamped with the 1.5.1 identity.
    Deliberately NO severity field, as in the whole line."""

    rule_id: str
    claim_type: str
    file: str
    start_line: int
    end_line: int
    message: str
    evidence: tuple[EvidenceLineV151, ...]
    producer: str
    blockers: tuple[dict, ...]
    validator_version: str
    policy_sha256: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LedgerEntryV151:
    rule_id: str
    claim_type: str
    file: str
    start_line: int
    end_line: int
    message: str
    severity_hint: str
    category_hint: str
    evidence: tuple[EvidenceLineV151, ...]
    status: str
    reasons: tuple[str, ...]
    validator_version: str
    policy_sha256: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GateResultV151:
    findings: tuple[dict, ...]
    ledger: tuple[LedgerEntryV151, ...]
    needs_validation: tuple[NeedsValidationRecordV151, ...]


def _evidence_lines_v151(
    evidence: tuple[EvidenceLineV150, ...],
) -> tuple[EvidenceLineV151, ...]:
    return tuple(
        EvidenceLineV151(
            file=item.file, line=item.line, kind=item.kind, text=item.text
        )
        for item in evidence
    )


def _restamp_entry(
    entry: LedgerEntryV150, extra_reason: str | None
) -> LedgerEntryV151:
    reasons = tuple(entry.reasons)
    if extra_reason is not None:
        reasons = reasons + (extra_reason,)
    return LedgerEntryV151(
        rule_id=entry.rule_id,
        claim_type=entry.claim_type,
        file=entry.file,
        start_line=entry.start_line,
        end_line=entry.end_line,
        message=entry.message,
        severity_hint=entry.severity_hint,
        category_hint=entry.category_hint,
        evidence=_evidence_lines_v151(entry.evidence),
        status=entry.status,
        reasons=reasons,
        validator_version=POLICY_VERSION,
        policy_sha256=POLICY_SHA256,
    )


def _restamp_held(
    record: NeedsValidationRecordV150,
) -> NeedsValidationRecordV151:
    return NeedsValidationRecordV151(
        rule_id=record.rule_id,
        claim_type=record.claim_type,
        file=record.file,
        start_line=record.start_line,
        end_line=record.end_line,
        message=record.message,
        evidence=_evidence_lines_v151(record.evidence),
        producer=record.producer,
        blockers=tuple(record.blockers),
        validator_version=POLICY_VERSION,
        policy_sha256=POLICY_SHA256,
    )


def _key(candidate: Candidate) -> tuple[str, int, int, str]:
    """The line's duplicate key (the 1.3.0's, unchanged), used
    here only to match delegated ledger entries back to the
    candidates whose pattern this gate extracted."""

    return (
        candidate.file,
        candidate.start_line,
        candidate.end_line,
        candidate.message.strip().lower(),
    )


class AlmaGateV151:
    """Evidence validator 1.5.1: the 1.5.0 by delegation, plus
    the extraction pre-pass of ADENDA-PUERTA-FORMA-20261027 —
    no general claim is held for form without a deterministic
    extraction attempt over its own prose and citation."""

    version = POLICY_VERSION
    policy_sha256 = POLICY_SHA256

    def validate(
        self,
        candidates: list[Candidate],
        diff: DiffIndex,
        agent_name: str,
    ) -> GateResultV151:
        prepared: list[Candidate] = []
        extracted: dict[tuple[str, int, int, str], tuple[str, ...]] = {}
        for candidate in candidates:
            if (
                candidate.claim_type in GENERAL_CATEGORIES_V151
                and not _asserted_tokens(candidate.message)
            ):
                pattern, normalized = _mine_pattern(
                    candidate.message,
                    "\n".join(candidate.evidence_text),
                )
                if pattern:
                    rescued = replace(candidate, message=normalized)
                    prepared.append(rescued)
                    extracted[_key(rescued)] = tuple(pattern)
                    continue
            prepared.append(candidate)

        result = AlmaGateV150().validate(prepared, diff, agent_name)

        ledger: list[LedgerEntryV151] = []
        for entry in result.ledger:
            extra = None
            if entry.status == "accepted":
                pattern = extracted.get(
                    (
                        entry.file,
                        entry.start_line,
                        entry.end_line,
                        entry.message.strip().lower(),
                    )
                )
                if pattern:
                    extra = EXTRACTION_REASON + ", ".join(pattern)
            ledger.append(_restamp_entry(entry, extra))

        return GateResultV151(
            findings=result.findings,
            ledger=tuple(ledger),
            needs_validation=tuple(
                _restamp_held(record) for record in result.needs_validation
            ),
        )


__all__ = [
    "EXTRACTION_REASON",
    "GENERAL_CATEGORIES_V151",
    "KNOWN_CLAIM_TYPES_V151",
    "POLICY_SHA256",
    "POLICY_SHA256_V150",
    "POLICY_VERSION",
    "AlmaGateV151",
    "GateResultV151",
    "LedgerEntryV151",
    "NeedsValidationRecordV151",
]
