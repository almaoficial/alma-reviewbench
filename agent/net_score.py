"""Net score (Breken rule) as the line's secondary metric.

Implements ADENDA-PUNTAJE-NETO.md exactly:

- Unit of account: the emission, with the grounded verdict its
  run's adjudication assigned (per-emission counting, consistent
  with how the line measures precision).
- +1 per TP emission (proven catch), -1 per FPG emission (false
  alarm PROVEN against an FP gold), 0 per GREY (gold neither
  confirms nor refutes) and per NOVEL (no gold counterpart; the
  grounded adjudication does not judge them).
- Reported as raw net (TP - FPG) and net per 100 emissions
  (undefined — None — when the arm emitted 0).
- Reading rule (addenda section 3): secondary metric, never
  adopts or rejects alone; an arm with raw net <= 0 cannot be
  declared an improvement even if it wins on precision.

Arms are re-derived by program from the primary sources
(adjwork298/decisions.json via the line's replay formula), never
from hand lists, and each cross must close exactly against the
published paper of its measurement before its net is seated
(SANITY below).  The ALMA 311 arm is the one exception: no
per-claim decisions file exists for run 311 (its seated
observability defect), so its verdict distribution enters as a
cited constant from its adjudication paper.

US$0: local computation only; no models, no portal.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from agent.alma_gate_v141 import AlmaGateV141
from agent.alma_gate_v150 import AlmaGateV150
from agent.lessons_compiler import (
    DISP_EMITTED,
    ClaimRecord,
    born_candidate,
    compute_dispositions,
    load_corpus,
)

NET_SCORE_VERSION = "alma-net-score/1.0"

VERDICTS = ("TP", "FPG", "GREY", "NOVEL")
PLUS = "TP"          # +1: proven catch
MINUS = "FPG"        # -1: false alarm proven against an FP gold
ZERO = ("GREY", "NOVEL")  # 0: neither proven nor judged false

# Arm identifiers, in table order.
ARM_BASE_298 = "base-298-sin-puerta"
ARM_GATE141_REPLAY = "replay-141-autopsia"
ARM_GATE150_REPLAY = "replay-150-sola"
ARM_CONTRACT_REPLAY = "replay-contrato-150"
ARM_SHAPER_REPLAY = "replay-formador-150"
ARM_ALMA_311 = "alma-311-puerta-141"

# Published crosses each computed arm must reproduce EXACTLY
# before its net is seated (sources: ADJUDICACION-COMPLETA-298
# for the base; RESULTADO-REPLAY-150 section 3; RESULTADO-
# CONTRATO-RECLAMOS section 3; RESULTADO-REVISOR-CONTRATO
# sections 3-4).  The shaper paper publishes emissions, TP and
# FPG but no GREY/NOVEL split of the emitted set, so those two
# cells are this module's derived output (their sum, 31, is
# fixed by the published totals) — declared, not hidden.
SANITY = {
    ARM_BASE_298: {"emissions": 166, "TP": 89, "FPG": 8,
                   "GREY": 17, "NOVEL": 52},
    ARM_GATE141_REPLAY: {"emissions": 0, "TP": 0, "FPG": 0,
                         "GREY": 0, "NOVEL": 0},
    ARM_GATE150_REPLAY: {"emissions": 32, "TP": 19, "FPG": 2,
                         "GREY": 2, "NOVEL": 9},
    ARM_CONTRACT_REPLAY: {"emissions": 49, "TP": 26, "FPG": 2,
                          "GREY": 3, "NOVEL": 18},
    ARM_SHAPER_REPLAY: {"emissions": 79, "TP": 44, "FPG": 4},
}

# Run 311 (real run, gate 1.4.1): the single emission's grounded
# verdict distribution, from ADJUDICACION-COMPLETA-311-20261022
# section 2 (emissions on FP gold / grey zone / novel: 0 / 1 / 0;
# the adjudication explicitly declines FPG under the house
# standard — the gold neither confirms nor refutes it).
ARM_311_SOURCE = ("ADJUDICACION-COMPLETA-311-20261022.md §2 "
                  "(0 TP / 0 FPG / 1 GREY / 0 NOVEL, n=1)")
ARM_311_COUNTS = {"emissions": 1, "TP": 0, "FPG": 0,
                  "GREY": 1, "NOVEL": 0}


@dataclass(frozen=True)
class ArmCounts:
    """One arm's verdict distribution over its own emissions."""

    arm: str
    emissions: int
    tp: int
    fpg: int
    grey: int
    novel: int

    @property
    def zero(self) -> int:
        return self.grey + self.novel

    @property
    def raw(self) -> int:
        """Net raw score: TP - FPG."""
        return self.tp - self.fpg

    @property
    def per_100(self) -> float | None:
        """Net per 100 emissions; None (n/d) when emissions = 0."""
        if self.emissions == 0:
            return None
        return round(self.raw / self.emissions * 100, 1)

    @property
    def blocked_as_improvement(self) -> bool:
        """Addenda section 3.3: raw net <= 0 cannot be declared
        an improvement, whatever precision says."""
        return self.raw <= 0

    def as_dict(self) -> dict:
        return {
            "arm": self.arm,
            "emissions": self.emissions,
            "tp": self.tp,
            "fpg": self.fpg,
            "grey": self.grey,
            "novel": self.novel,
            "zero": self.zero,
            "raw": self.raw,
            "per_100": self.per_100,
            "blocked_as_improvement": self.blocked_as_improvement,
        }


def counts_from_verdicts(arm: str, verdicts) -> ArmCounts:
    """Build an arm's counts from an iterable of grounded verdict
    labels (one per emission).  Unknown labels raise: an
    adjudication class this metric does not know must be defined
    in the addenda before it is silently scored."""
    c = Counter()
    for v in verdicts:
        if v not in VERDICTS:
            raise ValueError(f"unknown grounded verdict {v!r} for {arm}")
        c[v] += 1
    total = sum(c.values())
    return ArmCounts(arm=arm, emissions=total, tp=c["TP"],
                     fpg=c["FPG"], grey=c["GREY"], novel=c["NOVEL"])


def counts_from_cross(arm: str, cross: dict) -> ArmCounts:
    """Build counts from a seated cross dict (emissions + per-
    verdict counts), e.g. the 311 adjudication's distribution."""
    total = cross["TP"] + cross["FPG"] + cross["GREY"] + cross["NOVEL"]
    if total != cross["emissions"]:
        raise ValueError(f"cross for {arm} does not close: {cross}")
    return ArmCounts(arm=arm, emissions=cross["emissions"],
                     tp=cross["TP"], fpg=cross["FPG"],
                     grey=cross["GREY"], novel=cross["NOVEL"])


def net_score(counts: ArmCounts) -> tuple[int, float | None]:
    """The two expressions of the addenda: (raw, per-100)."""
    return counts.raw, counts.per_100


# ------------------------------------------------------------------
# Arms re-derived from the primary sources (corpus A, run 298)
# ------------------------------------------------------------------


def _payload_key(file, start_line, end_line, message) -> tuple:
    """Key matching a gate's emitted payload dicts (both frozen
    gates return findings as payload dicts without rule_id) back
    to the born candidate that produced them."""
    return (file, start_line, end_line, message)


def _gate_accepted(records: list[ClaimRecord], diffs: dict,
                   gate, tag: str) -> list[ClaimRecord]:
    """Records whose born candidate the gate accepts, running the
    gate per PR with the line's replay formula (as in the
    published replays and the executability census).  Matching is
    per PR on the payload key, so identical findings in different
    PRs never cross-match."""
    by_pr: dict[str, list[ClaimRecord]] = {}
    for rec in records:
        by_pr.setdefault(rec.pr, []).append(rec)
    accepted: list[ClaimRecord] = []
    for pr, recs in sorted(by_pr.items()):
        candidates = [born_candidate(r) for r in recs]
        result = gate.validate(candidates, diffs[pr], tag)
        keys = {_payload_key(f["file"], f["start_line"],
                             f["end_line"], f["message"])
                for f in result.findings}
        for rec, cand in zip(recs, candidates):
            if _payload_key(cand.file, cand.start_line,
                            cand.end_line, cand.message) in keys:
                accepted.append(rec)
    return accepted


def compute_arms(root: Path) -> list[ArmCounts]:
    """Every arm of the line with a seated grounded adjudication,
    in table order.  Raises if any computed cross misses its
    published sanity (SANITY) — a net is never seated on a
    reconstruction that does not close."""
    records, diffs, _meta = load_corpus(root)
    arms: list[ArmCounts] = []

    arms.append(counts_from_verdicts(
        ARM_BASE_298, [r.gold for r in records]))

    arms.append(counts_from_verdicts(
        ARM_GATE141_REPLAY,
        [r.gold for r in _gate_accepted(records, diffs,
                                        AlmaGateV141(), "net141")]))

    arms.append(counts_from_verdicts(
        ARM_GATE150_REPLAY,
        [r.gold for r in _gate_accepted(records, diffs,
                                        AlmaGateV150(), "net150")]))

    disps = compute_dispositions(records, diffs)
    # Contract pipeline: the gate emitted 49/49 of the conforming
    # (RESULTADO-CONTRATO-RECLAMOS section 3), so the emitted set
    # is exactly the contract-conforming records.
    arms.append(counts_from_verdicts(
        ARM_CONTRACT_REPLAY,
        [d.record.gold for d in disps if d.contract_conforming]))
    # Shaper pipeline: the dispositions' final emitted set.
    arms.append(counts_from_verdicts(
        ARM_SHAPER_REPLAY,
        [d.record.gold for d in disps if d.final == DISP_EMITTED]))

    arms.append(counts_from_cross(ARM_ALMA_311, ARM_311_COUNTS))

    assert_sanity(arms)
    return arms


def assert_sanity(arms: list[ArmCounts]) -> None:
    """Every published cell of every computed arm must match.
    The 311 arm is a cited constant, not a computation, and is
    checked only for internal closure."""
    by_arm = {a.arm: a for a in arms}
    for arm, expected in SANITY.items():
        got = by_arm[arm]
        cells = {"emissions": got.emissions, "TP": got.tp,
                 "FPG": got.fpg, "GREY": got.grey, "NOVEL": got.novel}
        for cell, want in expected.items():
            if cells[cell] != want:
                raise ValueError(
                    f"net-score sanity failed for {arm}.{cell}: "
                    f"computed {cells[cell]}, published {want}")
        if got.emissions != got.tp + got.fpg + got.grey + got.novel:
            raise ValueError(f"net-score closure failed for {arm}")
    a311 = by_arm[ARM_ALMA_311]
    if a311.emissions != a311.tp + a311.fpg + a311.grey + a311.novel:
        raise ValueError("net-score closure failed for the 311 arm")


def render_table(arms: list[ArmCounts]) -> str:
    lines = [
        "| Brazo | Emisiones | +TP | −FPG | 0 GREY | 0 NOVEL "
        "| Neto crudo | Neto/100 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for a in arms:
        per = "n/d" if a.per_100 is None else f"{a.per_100:+.1f}"
        raw = f"{a.raw:+d}" if a.raw != 0 else "0"
        lines.append(
            f"| {a.arm} | {a.emissions} | {a.tp} | {a.fpg} "
            f"| {a.grey} | {a.novel} | {raw} | {per} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import sys
    root = Path(__file__).resolve().parent.parent
    arms = compute_arms(root)
    if argv and "--json" in argv:
        print(json.dumps(
            {"net_score_version": NET_SCORE_VERSION,
             "arm_311_source": ARM_311_SOURCE,
             "arms": [a.as_dict() for a in arms]},
            indent=1, ensure_ascii=False))
    else:
        print(f"# Puntaje neto — {NET_SCORE_VERSION} "
              f"(sanidad: todos los cruces cierran contra lo publicado)")
        print()
        print(render_table(arms))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
