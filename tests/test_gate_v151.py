"""Gate 1.5.1 tests: the extraction pre-pass of the gate-form
amendment (ADENDA-PUERTA-FORMA-20261027.md, declared before
the code).

What is asserted here:
- the frozen gates 1.0.0–1.5.0, the claim contract and the
  birth shaper are byte-identical (file hashes), and the
  1.5.0's POLICY_SHA256 is the registered one;
- a general claim asserting NO code token but carrying a
  pattern extractable from its own prose against its citation
  is ACCEPTED by the 1.5.1, with the acceptance reason
  declaring the extraction — the same candidate is HELD by
  the 1.5.0 under sin_patron_concreto_en_el_reclamo (the
  measured death of runs nº 373/374);
- a general claim with nothing extractable is held by the
  1.5.1 under the same historical code as the 1.5.0 (death by
  matter, not form);
- the non-form deaths are intact: an affirmative
  contradiction (G3) is firm REJECTED, asserted tokens absent
  from the citation stay held under
  tokens_afirmados_ausentes_en_la_evidencia (extraction never
  substitutes an asserted pattern);
- class candidates: verdict-equivalence with the 1.5.0
  (delegation, not reimplementation);
- the held record carries NO severity anywhere and the whole
  validation is deterministic.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent.alma_gate_v150 import (  # noqa: E402
    CHECK_NO_CONCRETE_PATTERN,
    CHECK_TOKENS_ABSENT,
    POLICY_SHA256 as POLICY_SHA256_V150,
    AlmaGateV150,
)
from agent.alma_gate_v151 import (  # noqa: E402
    EXTRACTION_REASON,
    POLICY_SHA256,
    POLICY_VERSION,
    AlmaGateV151,
)
from agent.diff_parser import parse_unified_diff  # noqa: E402
from test_gate_v11 import candidate_for, make_diff  # noqa: E402

FROZEN_FILE_SHA256 = {
    "alma_gate.py": "4223cb0567fd398eb0c8b0a08e75a606559997823fabbc9bc1b5665f75607318",
    "alma_gate_v11.py": "fdd974f1ab8bd95c7bb24cd062360e0c2869c94f691c447dde900e4daf2c91f0",
    "alma_gate_v12.py": "c5c32bfc25386caeefe0e6ca91532c829710dd992e29d8718a8485cd3b9073f3",
    "alma_gate_v13.py": "d3b993d4d4f26b9df112dfd54abc391e8018faae024d23c63b4924d86d2dc1e0",
    "alma_gate_v14.py": "b16c5a795c56e0961eef596f57ce8b52eae8b1b3218bd3f7fa730e6b1c1347d8",
    "alma_gate_v141.py": "08d813e977dffeb47ea32938827a8babbb658dfc6a9cdc809508f3480cb6e8ff",
    "alma_gate_v150.py": "71b1996b604858b1b071646feb734dfaef361e6c120428b0e68cb88f8206c404",
    "claim_contract.py": "7df8abc77ec1cec46222bd276b739b0d23be4671882e2d96323d11818268f0f8",
    "birth_shaper.py": "2b127b23b58e5b8ad70c05860faf4cc128e715a756d8e44d7d749cb5a7664cd1",
}
FROZEN_POLICY_V150 = (
    "16befdd1c71d84ad83b54b857fc3ed2260c6c881a32f7498b70437b3f861654c"
)

LINES = [
    "def fetch(query):",
    "    return db.execute(query)",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate(gate, candidate, lines=LINES, path="app/x.py"):
    diff = parse_unified_diff(make_diff(path, lines))
    return gate.validate([candidate], diff, "test-agent")


class FrozenAndIdentityTests(unittest.TestCase):
    def test_frozen_files_byte_identical(self):
        agent_dir = ROOT / "agent"
        for name, expected in FROZEN_FILE_SHA256.items():
            self.assertEqual(
                _sha256(agent_dir / name), expected, f"{name} changed"
            )

    def test_identity(self):
        self.assertEqual(POLICY_SHA256_V150, FROZEN_POLICY_V150)
        self.assertEqual(POLICY_VERSION, "alma-evidence-gate/1.5.1")
        self.assertEqual(len(POLICY_SHA256), 64)
        self.assertNotEqual(POLICY_SHA256, POLICY_SHA256_V150)
        self.assertEqual(AlmaGateV151().version, POLICY_VERSION)


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.gate = AlmaGateV151()
        self.gate150 = AlmaGateV150()

    def test_extractable_pattern_accepted_and_declared(self):
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            LINES,
            1,
            2,
            message=(
                "The handler passes the raw query straight to "
                "db.execute, so injected SQL reaches the database."
            ),
        )
        # The 1.5.0 holds this exact candidate for form.
        held150 = _validate(self.gate150, candidate)
        self.assertEqual(len(held150.needs_validation), 1)
        self.assertEqual(
            held150.needs_validation[0].blockers[0]["check"],
            CHECK_NO_CONCRETE_PATTERN,
        )
        # The 1.5.1 extracts db.execute from the claim's own
        # prose against its citation and judges it: accepted,
        # emitted, and the acceptance declares the extraction.
        result = _validate(self.gate, candidate)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(len(result.needs_validation), 0)
        self.assertEqual(len(result.ledger), 1)
        entry = result.ledger[0]
        self.assertEqual(entry.status, "accepted")
        self.assertEqual(entry.validator_version, POLICY_VERSION)
        self.assertTrue(
            any(
                reason.startswith(EXTRACTION_REASON)
                and "db.execute" in reason
                for reason in entry.reasons
            ),
            entry.reasons,
        )

    def test_nothing_extractable_held_with_historical_code(self):
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            LINES,
            1,
            2,
            message="The code here is confusing and may hide problems later.",
        )
        result = _validate(self.gate, candidate)
        self.assertEqual(result.findings, ())
        self.assertEqual(len(result.needs_validation), 1)
        record = result.needs_validation[0]
        self.assertEqual(
            record.blockers[0]["check"], CHECK_NO_CONCRETE_PATTERN
        )
        self.assertNotIn("severity", record.to_dict())

    def test_affirmative_contradiction_still_firm_rejected(self):
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            LINES,
            1,
            2,
            message="The query path runs without `db.execute` anywhere.",
        )
        result = _validate(self.gate, candidate)
        self.assertEqual(result.findings, ())
        self.assertEqual(len(result.ledger), 1)
        self.assertEqual(result.ledger[0].status, "rejected")
        self.assertTrue(
            any(
                "affirmative contradiction" in reason
                for reason in result.ledger[0].reasons
            )
        )

    def test_asserted_tokens_absent_not_rescued_by_extraction(self):
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            LINES,
            1,
            2,
            message="The handler calls `missing_helper` on the query.",
        )
        result = _validate(self.gate, candidate)
        self.assertEqual(result.findings, ())
        self.assertEqual(len(result.needs_validation), 1)
        self.assertEqual(
            result.needs_validation[0].blockers[0]["check"],
            CHECK_TOKENS_ABSENT,
        )

    def test_declared_pattern_acceptance_carries_no_extraction_note(self):
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            LINES,
            1,
            2,
            message="The handler calls `db.execute` on the raw query.",
        )
        result = _validate(self.gate, candidate)
        self.assertEqual(len(result.findings), 1)
        self.assertFalse(
            any(
                reason.startswith(EXTRACTION_REASON)
                for reason in result.ledger[0].reasons
            )
        )

    def test_class_path_equivalent_to_v150(self):
        candidate = candidate_for(
            "command_execution",
            "app/x.py",
            LINES,
            1,
            2,
            message="test claim",
        )
        result151 = _validate(self.gate, candidate)
        result150 = _validate(self.gate150, candidate)
        self.assertEqual(
            [entry.status for entry in result151.ledger],
            [entry.status for entry in result150.ledger],
        )
        self.assertEqual(len(result151.findings), len(result150.findings))
        self.assertEqual(
            len(result151.needs_validation),
            len(result150.needs_validation),
        )

    def test_deterministic(self):
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            LINES,
            1,
            2,
            message=(
                "The handler passes the raw query straight to "
                "db.execute, so injected SQL reaches the database."
            ),
        )
        first = _validate(self.gate, candidate)
        second = _validate(self.gate, candidate)
        self.assertEqual(
            [entry.to_dict() for entry in first.ledger],
            [entry.to_dict() for entry in second.ledger],
        )
        self.assertEqual(first.findings, second.findings)


if __name__ == "__main__":
    unittest.main()
