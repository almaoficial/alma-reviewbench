"""Claim-contract tests: the normalizer of
PREREGISTRO-CONTRATO-RECLAMOS.md §3.

What is asserted here:
- a claim born WITH a declared pattern whose tokens all stand
  in its cited evidence is conforming UNCHANGED (the normalizer
  is the identity — it adds and removes nothing);
- a claim affirming a token absent from its own evidence is
  NON-conforming with `tokens_afirmados_ausentes_en_la_evidencia`
  and is NOT rescued by trimming the pattern to the surviving
  tokens (the integrity clause: the non-conformity is signal
  about the reviewer, not a defect to paper over);
- a claim with no declarable or minable pattern is
  NON-conforming with `sin_patron_concreto_en_el_reclamo`;
- a claim born without backticks whose prose carries a
  code-shaped token standing in its evidence is conforming by
  mining: the normalized message differs from the born one
  ONLY by backticks, and gate 1.5.0 (unmodified) ACCEPTS it;
- an absence-governed prose token is never mined (the
  normalizer does not affirm as present what the claim
  declares absent), even when the token stands in the
  evidence;
- a whitespace-free quoted literal standing in the evidence
  is minable;
- class claims pass through untouched (their contract is the
  1.4.1's class dialect);
- the frozen gates 1.0.0–1.4.1 and gate 1.5.0 stay
  byte-identical (the pipeline consumes 1.5.0 unmodified).

The §5 MEASUREMENT itself is not a unit test: it is measured
by the composed replay over corpus A and settled in
RESULTADO-CONTRATO-RECLAMOS-20261022.md.
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
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FrozenFilesTests(unittest.TestCase):
    def test_frozen_gates_and_gate_150_byte_identical(self):
        agent_dir = ROOT / "agent"
        for name, expected in FROZEN_FILE_SHA256.items():
            self.assertEqual(
                _sha256(agent_dir / name), expected, f"{name} changed"
            )


class BornPatternTests(unittest.TestCase):
    def test_born_conforming_is_identity(self):
        lines = [
            "def load(path):",
            "    return pickle.loads(open(path, 'rb').read())",
        ]
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            lines,
            1,
            2,
            message="The loader calls `pickle.loads` on untrusted data.",
        )
        outcome = normalize_claim(candidate)
        self.assertTrue(outcome.conforming)
        self.assertEqual(outcome.origin, "born")
        self.assertIs(outcome.candidate, candidate)
        self.assertEqual(outcome.pattern, ("pickle.loads",))
        self.assertEqual(outcome.blockers, ())

    def test_absent_tokens_nonconforming_and_not_trimmed(self):
        lines = [
            "def load(path):",
            "    return present_fn(open(path).read())",
        ]
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            lines,
            1,
            2,
            message=(
                "The loader calls `present_fn` and `missing_fn` "
                "on untrusted data."
            ),
        )
        outcome = normalize_claim(candidate)
        self.assertFalse(outcome.conforming)
        self.assertIsNone(outcome.candidate)
        self.assertEqual(outcome.check, CHECK_TOKENS_ABSENT)
        self.assertIn("missing_fn", outcome.blockers[0]["reason"])
        # The integrity clause: no rescued candidate affirming
        # only the surviving token was produced.
        self.assertEqual(outcome.pattern, ("present_fn", "missing_fn"))


class NoPatternTests(unittest.TestCase):
    def test_no_pattern_nonconforming(self):
        lines = [
            "total = compute_total(items)",
            "return total",
        ]
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            lines,
            1,
            2,
            message=(
                "The logic is incorrect and may produce wrong "
                "results at runtime."
            ),
        )
        outcome = normalize_claim(candidate)
        self.assertFalse(outcome.conforming)
        self.assertIsNone(outcome.candidate)
        self.assertEqual(outcome.check, CHECK_NO_CONCRETE_PATTERN)
        self.assertEqual(outcome.pattern, ())


class MiningTests(unittest.TestCase):
    LINES = [
        "def unpack(blob, dest):",
        "    tar.extractall(dest)",
    ]
    MESSAGE = (
        "The archive is unpacked with extractall( and member "
        "names are never validated."
    )

    def _candidate(self):
        return candidate_for(
            "correctness",
            "app/x.py",
            self.LINES,
            1,
            2,
            message=self.MESSAGE,
        )

    def test_mined_claim_conforms(self):
        candidate = self._candidate()
        outcome = normalize_claim(candidate)
        self.assertTrue(outcome.conforming)
        self.assertEqual(outcome.origin, "mined")
        self.assertEqual(outcome.pattern, ("extractall",))
        normalized = outcome.candidate
        self.assertIsNotNone(normalized)
        # Only the message changed, and only by backticks.
        self.assertEqual(
            normalized.message.replace("`", ""), candidate.message
        )
        self.assertIn("`extractall`", normalized.message)
        self.assertEqual(normalized.evidence_text, candidate.evidence_text)
        self.assertEqual(normalized.file, candidate.file)
        self.assertEqual(normalized.start_line, candidate.start_line)
        self.assertEqual(normalized.end_line, candidate.end_line)
        self.assertEqual(normalized.claim_type, candidate.claim_type)

    def test_mined_claim_accepted_by_gate_150_unmodified(self):
        outcome = normalize_claim(self._candidate())
        diff = parse_unified_diff(make_diff("app/x.py", self.LINES))
        result = AlmaGateV150().validate(
            [outcome.candidate], diff, "test-agent"
        )
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.ledger[0].status, "accepted")
        self.assertEqual(result.needs_validation, ())

    def test_mined_tokens_occur_in_message_and_evidence(self):
        candidate = self._candidate()
        outcome = normalize_claim(candidate)
        blob = "\n".join(candidate.evidence_text)
        for token in outcome.pattern:
            self.assertIn(token, candidate.message)
            self.assertIn(token, blob)

    def test_absence_governed_token_is_never_mined(self):
        lines = [
            "def store(f):",
            "    validate_upload(f)",
            "    return save(f)",
        ]
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            lines,
            1,
            3,
            message=(
                "The upload flow never uses validate_upload "
                "before storing files."
            ),
        )
        outcome = normalize_claim(candidate)
        self.assertFalse(outcome.conforming)
        self.assertEqual(outcome.check, CHECK_NO_CONCRETE_PATTERN)
        self.assertEqual(outcome.pattern, ())

    def test_quoted_literal_is_minable(self):
        lines = ["resp.set_cookie('session', 'admin')"]
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            lines,
            1,
            1,
            message=(
                "The session cookie is set with the 'admin' "
                "role hardcoded."
            ),
        )
        outcome = normalize_claim(candidate)
        self.assertTrue(outcome.conforming)
        self.assertEqual(outcome.origin, "mined")
        self.assertEqual(outcome.pattern, ("admin",))
        self.assertIn("`admin`", outcome.candidate.message)


class ClassPassthroughTests(unittest.TestCase):
    def test_class_claim_passes_through_untouched(self):
        lines = ["cursor.execute(q)"]
        candidate = candidate_for(
            "sql_injection",
            "app/x.py",
            lines,
            1,
            1,
            message="Query built by string formatting.",
        )
        outcome = normalize_claim(candidate)
        self.assertTrue(outcome.conforming)
        self.assertEqual(outcome.origin, "class")
        self.assertIs(outcome.candidate, candidate)


if __name__ == "__main__":
    unittest.main()
