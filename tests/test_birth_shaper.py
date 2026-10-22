"""Birth-shaper tests: the producer-side layer of
PREREGISTRO-REVISOR-CONTRATO.md §2.

What is asserted here:
- a claim that declares its pattern with the diff in view is
  BORN CONFORMING: the shaped claim's citation is the minimal
  range containing the pattern, its evidence is the matching
  contiguous slice of the born evidence, and the composed
  pipeline's own contract check (claim_contract, unmodified)
  confirms it as case A — while gate 1.5.0 (unmodified) ACCEPTS
  it end to end;
- an asserted token absent from the cited evidence is TRIMMED
  at origin and settled in the outcome (the claim stops
  asserting it: the backticks come off, the word stays as
  prose); the surviving pattern carries the claim;
- a claim whose asserted tokens are ALL absent from its own
  citation is DECLARED unverifiable at origin with
  `tokens_afirmados_ausentes_en_la_evidencia` — held by its
  producer at birth, not firmly rejected, never silently
  dropped;
- a claim with no declarable or minable pattern is DECLARED
  unverifiable at origin with `sin_patron_concreto_en_el_reclamo`;
- a claim born without backticks whose prose carries a
  code-shaped token standing in its evidence is born with the
  pattern DECLARED from its citation (mined): the shaped
  message differs from the born one ONLY by backticks/quotes
  and the shaped citation is the minimal pattern range;
- class claims pass through untouched (their contract is the
  1.4.1's class dialect);
- the frozen gates 1.0.0–1.4.1, gate 1.5.0 and claim_contract
  stay byte-identical (the pipeline consumes them unmodified).

The §4 MEASUREMENT itself is not a unit test: it is measured by
the composed replay over corpus A and settled in
RESULTADO-REVISOR-CONTRATO-20261022.md.
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
    AlmaGateV150,
)
from agent.birth_shaper import (  # noqa: E402
    ORIGIN_CLASS,
    ORIGIN_DECLARED,
    ORIGIN_MINED,
    ORIGIN_NONE,
    SHAPER_VERSION,
    shape_claim,
    shape_candidates,
)
from agent.claim_contract import normalize_claim  # noqa: E402
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
}

PATH = "app/x.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gate_status(gate, candidate, lines, path=PATH):
    diff = parse_unified_diff(make_diff(path, lines))
    result = gate.validate([candidate], diff, "test-agent")
    assert len(result.ledger) == 1
    return result.ledger[0].status


class IdentityAndFrozenTests(unittest.TestCase):
    def test_shaper_identity(self):
        self.assertEqual(SHAPER_VERSION, "alma-birth-shaper/1.0")

    def test_frozen_gates_gate150_and_contract_byte_identical(self):
        agent_dir = ROOT / "agent"
        for name, expected in FROZEN_FILE_SHA256.items():
            self.assertEqual(
                _sha256(agent_dir / name), expected, f"{name} changed"
            )


class BornConformingWithDiffTests(unittest.TestCase):
    def test_born_with_diff_in_view_shrinks_to_pattern_range(self):
        lines = [
            "import subprocess",
            "def run(cmd):",
            "    return subprocess.run(cmd, shell=True)",
            "    # trailing note",
        ]
        candidate = candidate_for(
            "correctness",
            PATH,
            lines,
            1,
            4,
            message="The call passes `shell=True` to the runner.",
        )
        diff = parse_unified_diff(make_diff(PATH, lines))
        outcome = shape_claim(candidate, diff)

        self.assertTrue(outcome.shaped)
        self.assertEqual(outcome.origin, ORIGIN_DECLARED)
        self.assertEqual(outcome.pattern, ("shell=True",))
        self.assertEqual(outcome.trimmed_tokens, ())
        shaped = outcome.candidate
        self.assertIsNotNone(shaped)
        # (c) the citation is the minimal range containing the
        # pattern; the evidence is the matching born slice.
        self.assertEqual((shaped.start_line, shaped.end_line), (3, 3))
        self.assertEqual(shaped.evidence_text, (lines[2],))
        self.assertEqual(outcome.born_range, (1, 4))
        self.assertEqual(outcome.shaped_range, (3, 3))
        self.assertTrue(outcome.range_has_added_line)
        # The composed pipeline's own contract check confirms it.
        check = normalize_claim(shaped)
        self.assertTrue(check.conforming)
        self.assertEqual(check.origin, "born")
        # And gate 1.5.0 (unmodified) accepts it end to end.
        self.assertEqual(
            _gate_status(AlmaGateV150(), shaped, lines), "accepted"
        )


class TrimAtOriginTests(unittest.TestCase):
    def test_absent_asserted_token_trimmed_and_settled(self):
        lines = [
            "import subprocess",
            "def run(cmd):",
            "    return subprocess.run(cmd, shell=True)",
        ]
        candidate = candidate_for(
            "correctness",
            PATH,
            lines,
            1,
            3,
            message=(
                "The call passes `shell=True` and relies on "
                "`pickle.loads` internally."
            ),
        )
        outcome = shape_claim(candidate)

        self.assertTrue(outcome.shaped)
        self.assertEqual(outcome.origin, ORIGIN_DECLARED)
        # The absent token is settled as trimmed; the surviving
        # pattern is only what the citation contains.
        self.assertEqual(outcome.trimmed_tokens, ("pickle.loads",))
        self.assertEqual(outcome.pattern, ("shell=True",))
        shaped = outcome.candidate
        # The claim stops asserting the trimmed token (backticks
        # off) and keeps asserting the surviving one.
        self.assertNotIn("`pickle.loads`", shaped.message)
        self.assertIn("pickle.loads", shaped.message)
        self.assertIn("`shell=True`", shaped.message)
        # Nothing was added: same text modulo backticks.
        self.assertEqual(
            shaped.message.replace("`", ""), candidate.message.replace("`", "")
        )
        # The contract check confirms the shaped claim, and the
        # gate accepts it.
        self.assertTrue(normalize_claim(shaped).conforming)
        self.assertEqual(
            _gate_status(AlmaGateV150(), shaped, lines), "accepted"
        )

    def test_all_asserted_tokens_absent_declared_unverifiable(self):
        lines = ["value = compute(data)", "return value"]
        candidate = candidate_for(
            "correctness",
            PATH,
            lines,
            1,
            2,
            message="The path uses `eval(` on the input.",
        )
        outcome = shape_claim(candidate)

        self.assertFalse(outcome.shaped)
        self.assertIsNone(outcome.candidate)
        self.assertEqual(outcome.origin, ORIGIN_NONE)
        self.assertEqual(outcome.trimmed_tokens, ("eval(",))
        checks = [b["check"] for b in outcome.blockers]
        self.assertEqual(checks, [CHECK_TOKENS_ABSENT])
        # Declared, not dropped: the batch keeps the outcome and
        # delivers no candidate for it.
        batch = shape_candidates([candidate])
        self.assertEqual(batch.shaped_candidates(), [])
        self.assertEqual(len(batch.held_at_origin()), 1)


class NoPatternAtOriginTests(unittest.TestCase):
    def test_no_declarable_pattern_declared_unverifiable(self):
        lines = ["value = compute(data)", "return value"]
        candidate = candidate_for(
            "correctness",
            PATH,
            lines,
            1,
            2,
            message="This change is risky and should be reviewed carefully.",
        )
        outcome = shape_claim(candidate)

        self.assertFalse(outcome.shaped)
        self.assertIsNone(outcome.candidate)
        self.assertEqual(outcome.origin, ORIGIN_NONE)
        checks = [b["check"] for b in outcome.blockers]
        self.assertEqual(checks, [CHECK_NO_CONCRETE_PATTERN])


class MinedAtBirthTests(unittest.TestCase):
    def test_pattern_declared_at_birth_from_citation(self):
        lines = [
            "import subprocess",
            "def run(cmd):",
            "    return subprocess.run(cmd, shell=True)",
            "    # trailing note",
        ]
        candidate = candidate_for(
            "correctness",
            PATH,
            lines,
            1,
            4,
            message="The handler calls subprocess.run directly here.",
        )
        outcome = shape_claim(candidate)

        self.assertTrue(outcome.shaped)
        self.assertEqual(outcome.origin, ORIGIN_MINED)
        self.assertIn("subprocess.run", outcome.pattern)
        shaped = outcome.candidate
        # The pattern now stands declared, and only that changed.
        self.assertIn("`subprocess.run`", shaped.message)
        self.assertEqual(
            shaped.message.replace("`", ""), candidate.message.replace("`", "")
        )
        # (c) minimal citation: the pattern lives on line 3 only.
        self.assertEqual((shaped.start_line, shaped.end_line), (3, 3))
        self.assertEqual(shaped.evidence_text, (lines[2],))
        # Contract check + gate, unmodified, end to end.  Once
        # the pattern stands declared at birth, the checker sees
        # a born claim (Case A) — that indistinguishability IS
        # the point of shaping at birth.
        check = normalize_claim(shaped)
        self.assertTrue(check.conforming)
        self.assertEqual(check.origin, "born")
        self.assertEqual(
            _gate_status(AlmaGateV150(), shaped, lines), "accepted"
        )


class ClassPassThroughTests(unittest.TestCase):
    def test_class_claim_passes_intact(self):
        lines = ["cursor.execute(query)"]
        candidate = candidate_for("sql_injection", PATH, lines, 1, 1)
        outcome = shape_claim(candidate)
        self.assertTrue(outcome.shaped)
        self.assertEqual(outcome.origin, ORIGIN_CLASS)
        self.assertIs(outcome.candidate, candidate)
        self.assertEqual(outcome.pattern, ())


if __name__ == "__main__":
    unittest.main()
