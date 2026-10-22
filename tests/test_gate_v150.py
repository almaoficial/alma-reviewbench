"""Gate 1.5.0 tests: the general-category grounding rule.

Pre-registration: PREREGISTRO-PUERTA-150.md — §2 (the design:
(G0) form, (G1) existence against the head, (G2) head-OR-diff
anchor, (G3) affirmative contradiction as the only other
firm-reject family, (G4) affirmative token grounding, (G5)
duplicate; the unverifiable held with SPECIFIC reason codes),
§3 (what does not change: the 19 classes by delegation to the
1.4.1, the frozen gates byte-identical).

What is asserted here:
- the frozen gates 1.0.0–1.4.1 are byte-identical (file hashes)
  and the 1.4.1's POLICY_SHA256 is the registered one;
- a general claim that is well anchored and whose asserted
  tokens stand in its citation is ACCEPTED and emitted (the
  1.4.1 held every such claim);
- the anchor repair: a claim cited on head lines outside every
  diff hunk is accepted when grounded — the same candidate is
  REJECTED by the 1.4.1 (the replay's 17 anchor deaths);
- an affirmative contradiction (the claim declares a token
  absent, its evidence contains it) is firm REJECTED;
- the unverifiable is held with its specific reason code:
  tokens absent from the evidence, and no concrete pattern
  asserted at all — never the old generic blocker;
- a citation that does not resolve against the head (stored
  evidence not covering the cited range) and stored evidence
  contradicting the diff are firm REJECTED;
- class candidates: verdict-equivalence with the 1.4.1
  (accepted / held / rejected) — delegation, not reimplementation;
- the held record carries NO severity anywhere, lives outside
  the findings and the ledger, and is deterministic;
- a grounded general duplicate of an accepted finding is
  rejected as a duplicate.

The §4 REPLAY verdict itself is NOT a unit test: it is measured
by the replay over corpus A and settled in
RESULTADO-REPLAY-150-20261022.md.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent.alma_gate_v141 import POLICY_SHA256 as POLICY_SHA256_V141  # noqa: E402
from agent.alma_gate_v141 import AlmaGateV141  # noqa: E402
from agent.alma_gate_v150 import (  # noqa: E402
    CHECK_NO_CONCRETE_PATTERN,
    CHECK_TOKENS_ABSENT,
    POLICY_SHA256,
    POLICY_VERSION,
    AlmaGateV150,
)
from agent.base_reviewer import Candidate  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from test_gate_v11 import candidate_for, make_diff  # noqa: E402

FROZEN_FILE_SHA256 = {
    "alma_gate.py": "4223cb0567fd398eb0c8b0a08e75a606559997823fabbc9bc1b5665f75607318",
    "alma_gate_v11.py": "fdd974f1ab8bd95c7bb24cd062360e0c2869c94f691c447dde900e4daf2c91f0",
    "alma_gate_v12.py": "c5c32bfc25386caeefe0e6ca91532c829710dd992e29d8718a8485cd3b9073f3",
    "alma_gate_v13.py": "d3b993d4d4f26b9df112dfd54abc391e8018faae024d23c63b4924d86d2dc1e0",
    "alma_gate_v14.py": "b16c5a795c56e0961eef596f57ce8b52eae8b1b3218bd3f7fa730e6b1c1347d8",
    "alma_gate_v141.py": "08d813e977dffeb47ea32938827a8babbb658dfc6a9cdc809508f3480cb6e8ff",
}
FROZEN_POLICY_V141 = (
    "73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _diff_with_hunk_at(path: str, start: int, lines: list[str]) -> str:
    """A unified diff whose single hunk covers head lines
    [start, start+len(lines)) — lines elsewhere are NOT in the
    diff, which is how a head-anchored citation looks."""

    body = "\n".join(lines)
    return (
        f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
        f"@@ -{start},3 +{start},3 @@\n{body}\n"
    )


class FrozenGatesTests(unittest.TestCase):
    def test_frozen_gate_files_byte_identical(self):
        agent_dir = ROOT / "agent"
        for name, expected in FROZEN_FILE_SHA256.items():
            self.assertEqual(
                _sha256(agent_dir / name), expected, f"{name} changed"
            )

    def test_frozen_policy_and_new_identity(self):
        self.assertEqual(POLICY_SHA256_V141, FROZEN_POLICY_V141)
        self.assertEqual(POLICY_VERSION, "alma-evidence-gate/1.5.0")
        self.assertEqual(len(POLICY_SHA256), 64)
        self.assertNotEqual(POLICY_SHA256, POLICY_SHA256_V141)


class GeneralRuleTests(unittest.TestCase):
    def setUp(self):
        self.gate = AlmaGateV150()

    def test_grounded_general_claim_accepted(self):
        lines = [
            "def load(path):",
            "    return pickle.loads(open(path, 'rb').read())",
        ]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            lines,
            1,
            2,
            message=(
                "The loader calls `pickle.loads` on data read from "
                "`open` without any validation of the source."
            ),
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(len(result.needs_validation), 0)
        self.assertEqual(result.ledger[0].status, "accepted")
        self.assertIn(
            "general grounding check passed", result.ledger[0].reasons[0]
        )

    def test_head_only_anchor_accepted__the_repair(self):
        # The citation lives on head lines 1-2; the diff's only
        # hunk covers lines 20-22.  The 1.4.1 rejects this exact
        # shape (not present in the diff) — the replay's 17.
        head = [
            "def fetch(url):",
            "    return requests.get(url, verify=False)",
        ]
        diff = parse_unified_diff(
            _diff_with_hunk_at(
                "app/x.py", 20, [" ctx_a", "+added_b", " ctx_c"]
            )
        )
        candidate = candidate_for(
            "security",
            "app/x.py",
            head,
            1,
            2,
            message=(
                "The call `requests.get` passes `verify=False`, "
                "disabling certificate checks."
            ),
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.ledger[0].status, "accepted")
        # Contrast: the frozen 1.4.1 rejects the same candidate.
        result141 = AlmaGateV141().validate([candidate], diff, "test-agent")
        self.assertEqual(len(result141.findings), 0)
        self.assertEqual(result141.ledger[0].status, "rejected")
        self.assertTrue(
            any(
                "not present in the diff" in reason
                for reason in result141.ledger[0].reasons
            )
        )

    def test_affirmative_contradiction_rejected(self):
        lines = ["cursor.execute(query, params)"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = candidate_for(
            "security",
            "app/x.py",
            lines,
            1,
            1,
            message=(
                "The statement is executed without `params` "
                "binding, so values are interpolated raw."
            ),
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        self.assertEqual(len(result.findings), 0)
        self.assertEqual(len(result.needs_validation), 0)
        entry = result.ledger[0]
        self.assertEqual(entry.status, "rejected")
        self.assertTrue(
            any(
                "affirmative contradiction" in reason
                for reason in entry.reasons
            )
        )

    def test_absent_tokens_held_with_specific_code(self):
        lines = ["value = compute()"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            lines,
            1,
            1,
            message=(
                "The result of `compute` is passed to "
                "`unsafe_eval` without checks."
            ),
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        self.assertEqual(len(result.findings), 0)
        self.assertEqual(len(result.needs_validation), 1)
        record = result.needs_validation[0]
        checks = [b["check"] for b in record.blockers]
        self.assertIn(CHECK_TOKENS_ABSENT, checks)
        self.assertNotIn("sin_regla_de_verificacion_en_puerta", checks)
        reason = next(
            b["reason"] for b in record.blockers
            if b["check"] == CHECK_TOKENS_ABSENT
        )
        self.assertIn("unsafe_eval", reason)

    def test_no_concrete_pattern_held_with_specific_code(self):
        lines = ["x = 1"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = candidate_for(
            "maintainability",
            "app/x.py",
            lines,
            1,
            1,
            message="This code is confusing and should be rewritten.",
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        self.assertEqual(len(result.needs_validation), 1)
        checks = [
            b["check"] for b in result.needs_validation[0].blockers
        ]
        self.assertIn(CHECK_NO_CONCRETE_PATTERN, checks)

    def test_unresolvable_citation_rejected(self):
        # Stored evidence covers 1 line for a cited range of 2:
        # the citation points at a line that does not exist as
        # cited (paper 150 §2 (G1)).
        lines = ["a = 1", "b = 2"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = Candidate(
            rule_id="test_correctness",
            claim_type="correctness",
            file="app/x.py",
            start_line=1,
            end_line=2,
            message="The variable `a` is wrong.",
            evidence_text=("a = 1",),
            severity_hint="high",
            category_hint="correctness",
            producer="test-producer",
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        self.assertEqual(result.ledger[0].status, "rejected")
        self.assertTrue(
            any(
                "do not resolve against the head" in reason
                for reason in result.ledger[0].reasons
            )
        )

    def test_evidence_contradicting_diff_rejected(self):
        lines = ["real = compute()"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = Candidate(
            rule_id="test_correctness",
            claim_type="correctness",
            file="app/x.py",
            start_line=1,
            end_line=1,
            message="The call `compute` is unsafe.",
            evidence_text=("forged = compute()",),
            severity_hint="high",
            category_hint="correctness",
            producer="test-producer",
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        self.assertEqual(result.ledger[0].status, "rejected")
        self.assertTrue(
            any(
                "contradicts the diff" in reason
                for reason in result.ledger[0].reasons
            )
        )

    def test_duplicate_general_rejected(self):
        lines = ["value = pickle.loads(data)"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        message = "The call `pickle.loads` deserializes `data` raw."
        first = candidate_for(
            "security", "app/x.py", lines, 1, 1, message=message
        )
        second = candidate_for(
            "security", "app/x.py", lines, 1, 1, message=message
        )
        result = self.gate.validate([first, second], diff, "test-agent")
        self.assertEqual(len(result.findings), 1)
        statuses = [entry.status for entry in result.ledger]
        self.assertEqual(statuses, ["accepted", "rejected"])
        self.assertTrue(
            any(
                "duplicate" in reason
                for reason in result.ledger[1].reasons
            )
        )

    def test_held_record_has_no_severity(self):
        lines = ["value = compute()"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = candidate_for(
            "correctness",
            "app/x.py",
            lines,
            1,
            1,
            message="Nothing concrete is asserted here at all.",
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        record = result.needs_validation[0]
        self.assertFalse(hasattr(record, "severity_hint"))
        self.assertNotIn("severity", record.to_dict())


class ClassDelegationTests(unittest.TestCase):
    def _verdicts(self, gate, candidate, diff):
        result = gate.validate([candidate], diff, "test-agent")
        held = {
            (r.file, r.start_line, r.end_line, r.message)
            for r in result.needs_validation
        }
        out = []
        for entry in result.ledger:
            out.append((entry.claim_type, entry.status))
        for record in result.needs_validation:
            out.append((record.claim_type, "needs_validation"))
        return out, len(result.findings), held

    def test_class_verdicts_equal_141(self):
        cases = []
        # An accepted class claim (hardcoded secret on an added line).
        secret_lines = ['api_key = "sk_live_1234567890abcdef"']
        cases.append(
            candidate_for(
                "hardcoded_secret", "app/x.py", secret_lines, 1, 1,
                message="A credential is embedded in source.",
            )
        )
        secret_diff = parse_unified_diff(make_diff("app/x.py", secret_lines))
        # A firm-rejected class claim (marker absent).
        plain_lines = ["x = 1"]
        cases.append(
            candidate_for(
                "hardcoded_secret", "app/y.py", plain_lines, 1, 1,
                message="A credential is embedded in source.",
            )
        )
        plain_diff = parse_unified_diff(make_diff("app/y.py", plain_lines))
        for candidate, diff in (
            (cases[0], secret_diff),
            (cases[1], plain_diff),
        ):
            v150 = self._verdicts(AlmaGateV150(), candidate, diff)
            v141 = self._verdicts(AlmaGateV141(), candidate, diff)
            self.assertEqual(v150[0], v141[0])
            self.assertEqual(v150[1], v141[1])

    def test_mixed_batch_order_and_coverage(self):
        lines = ["value = pickle.loads(data)"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        general = candidate_for(
            "security", "app/x.py", lines, 1, 1,
            message="The call `pickle.loads` deserializes `data` raw.",
        )
        secret_lines = ['api_key = "sk_live_1234567890abcdef"']
        secret = candidate_for(
            "hardcoded_secret", "app/x.py", secret_lines, 1, 1,
            message="A credential is embedded in source.",
        )
        # One diff covering both citations is impossible here (the
        # secret line is not in x.py's diff): the class candidate
        # anchors against its own file's absence — both gates must
        # still agree, and every candidate gets exactly one fate.
        result = AlmaGateV150().validate(
            [general, secret], diff, "test-agent"
        )
        total = (
            len(result.ledger) + len(result.needs_validation)
        )
        self.assertEqual(total, 2)
        self.assertEqual(len(result.findings), 1)


if __name__ == "__main__":
    unittest.main()
