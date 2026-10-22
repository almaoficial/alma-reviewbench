"""Gate 1.4.1 tests: the third state with check (f) restored as a
firm rejection.

Pre-registration: PREREGISTRO-PUERTA-141.md — §2 (the single change:
check (f) "no line added by this change" leaves the completeness
checks that enable needs_validation; a candidate whose cited
evidence contains no added line is FIRM REJECTED at the frontier,
dominating any completeness failure), §4 (the adoption measurement
and its test categories), §5 (falsifiers), §6 (label gate=v141,
module agent/alma_gate_v141.py, POLICY_VERSION
alma-evidence-gate/1.4.1).

What is asserted here:
- the frozen gates 1.0.0–1.3.0 AND the 1.4.0 are byte-identical
  (file hashes) and their POLICY_SHA256 values are the registered
  ones — the 1.4.0 stays intact as a built and measured artifact;
- the §4 routing categories: (i) S3-type case — cited evidence with
  no added line, support present — -> firm rejection, no
  needs_validation record, no state move against the 1.3.0;
  (ii) VP-type case — added line present in the citation and
  co-occurrence split across cited lines — -> still
  needs_validation with its completeness blocker; (iii) mixed case
  — failing (f) AND (a) — -> firm rejection (dominance of (f));
- acceptance equivalence with the 1.3.0 on the inherited pairs, on
  the mock reviewer's candidates over every fixture, and on the red
  battery (69 attacks) — where, stronger than the 1.4.0, the 1.4.1
  must produce ZERO state moves of any kind;
- firm rejection inherited from the 1.4.0's frontier: unknown class,
  malformed, false anchor, antidote present, primary marker absent,
  duplicate of an accepted finding;
- the held record carries NO severity anywhere, lives outside the
  findings and the ledger, and is deterministic;
- general categories (v2.3 extension, UNTOUCHED by paper 141 §2):
  held with sin_regla_de_verificacion_en_puerta when well-formed
  and anchored (context-only citations still add the no_added_line
  blocker there), rejected when malformed or unanchored.

The §4 ADOPTION verdict itself is NOT a unit test: it is measured
by medir_adopcion_v141.py over the three universes and settled in
RESULTADO-MEDICION-PUERTA-141.md.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent import alma_gate, alma_gate_v11, alma_gate_v12, alma_gate_v13, alma_gate_v14  # noqa: E402
from agent.alma_gate_v13 import AlmaGateV13  # noqa: E402
from agent.alma_gate_v14 import AlmaGateV14  # noqa: E402
from agent.alma_gate_v141 import (  # noqa: E402
    GENERAL_CATEGORIES_V141,
    KNOWN_CLAIM_TYPES_V141,
    POLICY_SHA256 as POLICY_SHA256_V141,
    POLICY_VERSION as POLICY_VERSION_V141,
    AlmaGateV141,
)
from agent.base_reviewer import BaseReviewer, Candidate  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from test_gate_v11 import INHERITED_PAIRS, candidate_for, make_diff  # noqa: E402
from test_gate_v12 import ATTACKS, attack_candidate, attack_diff  # noqa: E402
from test_gate_v13 import NEW_ATTACKS  # noqa: E402

FROZEN_POLICY_SHA256 = {
    "1.0.0": "3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35",
    "1.1.0": "6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9",
    "1.2.0": "a768afa46136ba1bf542da65006a946d11cb39e8db73fbd484c3f021b7994211",
    "1.3.0": "0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78",
    "1.4.0": "b0c0aa661f644b5229ea3ee1984b3fd2dbb17649d1eeae91e5945fd357fd6d19",
}
FROZEN_FILE_SHA256 = {
    "alma_gate.py": "4223cb0567fd398eb0c8b0a08e75a606559997823fabbc9bc1b5665f75607318",
    "alma_gate_v11.py": "fdd974f1ab8bd95c7bb24cd062360e0c2869c94f691c447dde900e4daf2c91f0",
    "alma_gate_v12.py": "c5c32bfc25386caeefe0e6ca91532c829710dd992e29d8718a8485cd3b9073f3",
    "alma_gate_v13.py": "d3b993d4d4f26b9df112dfd54abc391e8018faae024d23c63b4924d86d2dc1e0",
    "alma_gate_v14.py": "b16c5a795c56e0961eef596f57ce8b52eae8b1b3218bd3f7fa730e6b1c1347d8",
}

CO_OCCURRENCE_LINES = [
    "    query = (",
    '        "SELECT * FROM orders "',
    "        f\"WHERE customer = '{customer_name}'\"",
    "    )",
]
S3_LINES = [
    'q = "SELECT * FROM users"',
    'query = f"SELECT * FROM users WHERE id = {user_id}"',
    "cursor.execute(query)",
]


def outcome141(candidate, diff):
    result = AlmaGateV141().validate([candidate], diff, "test-agent")
    if result.needs_validation:
        return "needs_validation", result.needs_validation[0]
    return result.ledger[0].status, result.ledger[0]


def outcome14(candidate, diff):
    result = AlmaGateV14().validate([candidate], diff, "test-agent")
    if result.needs_validation:
        return "needs_validation", result.needs_validation[0]
    return result.ledger[0].status, result.ledger[0]


def outcome13(candidate, diff):
    result = AlmaGateV13().validate([candidate], diff, "test-agent")
    return result.ledger[0].status


def added_candidate(claim_type, lines, start=1, end=None, path="app/x.py"):
    end = len(lines) if end is None else end
    diff = parse_unified_diff(make_diff(path, lines))
    return candidate_for(claim_type, path, lines, start, end), diff


class PolicyTests(unittest.TestCase):
    def test_frozen_gates_byte_identical_including_140(self):
        agent_dir = ROOT / "agent"
        for module, expected in (
            (alma_gate, FROZEN_POLICY_SHA256["1.0.0"]),
            (alma_gate_v11, FROZEN_POLICY_SHA256["1.1.0"]),
            (alma_gate_v12, FROZEN_POLICY_SHA256["1.2.0"]),
            (alma_gate_v13, FROZEN_POLICY_SHA256["1.3.0"]),
            (alma_gate_v14, FROZEN_POLICY_SHA256["1.4.0"]),
        ):
            self.assertEqual(module.POLICY_SHA256, expected)
        for name, expected in FROZEN_FILE_SHA256.items():
            digest = hashlib.sha256((agent_dir / name).read_bytes()).hexdigest()
            self.assertEqual(digest, expected, f"{name} changed")

    def test_v141_policy_identity(self):
        self.assertEqual(POLICY_VERSION_V141, "alma-evidence-gate/1.4.1")
        self.assertNotIn(POLICY_SHA256_V141, FROZEN_POLICY_SHA256.values())
        self.assertEqual(KNOWN_CLAIM_TYPES_V141, alma_gate_v13.KNOWN_CLAIM_TYPES_V13)
        self.assertEqual(len(KNOWN_CLAIM_TYPES_V141), 19)
        self.assertEqual(GENERAL_CATEGORIES_V141, alma_gate_v14.GENERAL_CATEGORIES_V14)


class RoutingFTests(unittest.TestCase):
    """Paper 141 §4, category by category."""

    def test_s3_attack_is_firmly_rejected_without_moving(self):
        """(i) The battery's own S3: rejected by the 1.3.0, held by
        the 1.4.0 with blocker no_added_line — and firmly rejected
        by the 1.4.1, with NO needs_validation record at all."""

        attack = next(a for a in ATTACKS if a[0] == "S3")
        _id, claim_type, _trick, lines, start, end, message, ctx = attack
        diff = parse_unified_diff(attack_diff(lines, ctx))
        candidate = attack_candidate(claim_type, start, end, lines, message)
        self.assertEqual(outcome13(candidate, diff), "rejected")
        s14, record14 = outcome14(candidate, diff)
        self.assertEqual(s14, "needs_validation")
        self.assertEqual([b["check"] for b in record14.blockers], ["no_added_line"])
        result = AlmaGateV141().validate([candidate], diff, "test-agent")
        self.assertEqual(result.needs_validation, ())
        self.assertEqual(result.findings, ())
        self.assertEqual(len(result.ledger), 1)
        self.assertEqual(result.ledger[0].status, "rejected")
        self.assertIn(
            "no line added by this change", " ".join(result.ledger[0].reasons)
        )

    def test_only_f_failure_with_support_present_stays_rejected(self):
        """(i) A context-only citation whose support PASSES (the
        1.4.0 held it via (c) alone): the 1.4.1 rejects it — (f) is
        a rejection cause, not a completeness gap."""

        lines = ["    requests.get(url, verify=False)"]
        diff = parse_unified_diff(attack_diff(lines, "context"))
        candidate = attack_candidate(
            "tls_verification_disabled", 1, 1, lines, "tls off"
        )
        self.assertEqual(outcome13(candidate, diff), "rejected")
        s14, record14 = outcome14(candidate, diff)
        self.assertEqual(s14, "needs_validation")
        self.assertEqual([b["check"] for b in record14.blockers], ["no_added_line"])
        status, _ = outcome141(candidate, diff)
        self.assertEqual(status, "rejected")

    def test_vp_case_with_added_line_still_held(self):
        """(ii) Added line present in the citation, co-occurrence
        split across cited lines: the candidate still lands in
        needs_validation, with the completeness blocker only —
        no_added_line never appears on the class frontier."""

        candidate, diff = added_candidate("sql_injection", CO_OCCURRENCE_LINES)
        self.assertEqual(outcome13(candidate, diff), "rejected")
        status, record = outcome141(candidate, diff)
        self.assertEqual(status, "needs_validation")
        self.assertEqual([b["check"] for b in record.blockers], ["co_occurrence"])

    def test_mixed_f_and_a_is_firmly_rejected_by_dominance(self):
        """(iii) The same co-occurrence shape cited on CONTEXT lines
        only: it fails (f) and would fail (a).  The 1.4.0 held it
        with both blockers; the 1.4.1 rejects it — (f) dominates."""

        diff = parse_unified_diff(attack_diff(CO_OCCURRENCE_LINES, False))
        candidate = attack_candidate(
            "sql_injection", 1, len(CO_OCCURRENCE_LINES), CO_OCCURRENCE_LINES, "mixed"
        )
        self.assertEqual(outcome13(candidate, diff), "rejected")
        s14, record14 = outcome14(candidate, diff)
        self.assertEqual(s14, "needs_validation")
        self.assertEqual(
            [b["check"] for b in record14.blockers],
            ["co_occurrence", "no_added_line"],
        )
        result = AlmaGateV141().validate([candidate], diff, "test-agent")
        self.assertEqual(result.needs_validation, ())
        self.assertEqual(result.ledger[0].status, "rejected")

    def test_settled_semaphore_sem01_candidate_is_still_held(self):
        """The adoption measurement's known VP (runs of the v2.1
        semaphore, ALMA arm, sem_01): rejected by the 1.3.0 for the
        citation, held by the 1.4.0 — and still held by the 1.4.1,
        because its citation DOES contain added lines."""

        ledger = json.loads(
            (ROOT / "runs" / "semaforo-v21-20261021" / "alma-sem_01_sql_injection-ledger.json").read_text(encoding="utf-8")
        )
        entry = ledger[0]
        diff = parse_unified_diff(
            (ROOT / "fixtures_semaforo" / "sem_01_sql_injection" / "diff.patch").read_text(encoding="utf-8")
        )
        candidate = Candidate(
            rule_id=entry["rule_id"],
            claim_type=entry["claim_type"],
            file=entry["file"],
            start_line=entry["start_line"],
            end_line=entry["end_line"],
            message=entry["message"],
            evidence_text=tuple(e["text"] for e in entry["evidence"]),
            severity_hint=entry["severity_hint"],
            category_hint=entry["category_hint"],
            producer="alma-llm-reviewer-v21",
        )
        self.assertEqual(outcome13(candidate, diff), "rejected")
        status, record = outcome141(candidate, diff)
        self.assertEqual(status, "needs_validation")
        self.assertEqual([b["check"] for b in record.blockers], ["co_occurrence"])

    def test_construction_outside_span_still_held(self):
        """(b) survives the change untouched: a JWT candidate whose
        disabling option stands in the call span but outside the
        cited lines (all cited lines added) is still held."""

        lines = [
            "    payload = jwt.decode(",
            "        token,",
            '        options={"verify_signature": False},',
            "    )",
        ]
        candidate, diff = added_candidate(
            "jwt_verification_disabled", lines, start=1, end=2
        )
        self.assertEqual(outcome13(candidate, diff), "rejected")
        status, record = outcome141(candidate, diff)
        self.assertEqual(status, "needs_validation")
        self.assertEqual(
            [b["check"] for b in record.blockers],
            ["construction_outside_cited_span"],
        )


class FrontierFirmRejectionTests(unittest.TestCase):
    """Inherited from the 1.4.0 frontier, unchanged by paper 141."""

    def test_antidote_present_stays_rejected(self):
        lines = [
            "    import yaml",
            "    data = yaml.load(payload, Loader=yaml.SafeLoader)",
        ]
        candidate, diff = added_candidate("unsafe_deserialization", lines)
        status, _ = outcome141(candidate, diff)
        self.assertEqual(status, "rejected")

    def test_placeholder_secret_stays_rejected(self):
        lines = ['    API_KEY = "test-placeholder-value-123"']
        candidate, diff = added_candidate("hardcoded_secret", lines)
        status, _ = outcome141(candidate, diff)
        self.assertEqual(status, "rejected")

    def test_absent_marker_stays_rejected(self):
        lines = ['    query = "SELECT * FROM orders WHERE customer = \'x\'"']
        candidate, diff = added_candidate("sql_injection", lines)
        status, _ = outcome141(candidate, diff)
        self.assertEqual(status, "rejected")

    def test_sql_split_across_statements_stays_rejected(self):
        lines = [
            '    query = "SELECT * FROM orders WHERE customer = \'x\'"',
            '    log = f"done {n}"',
        ]
        candidate, diff = added_candidate("sql_injection", lines)
        status, _ = outcome141(candidate, diff)
        self.assertEqual(status, "rejected")

    def test_unknown_claim_stays_rejected(self):
        lines = ["    x = compute()"]
        candidate, diff = added_candidate("not_a_gate_class", lines)
        status, _ = outcome141(candidate, diff)
        self.assertEqual(status, "rejected")

    def test_malformed_stays_rejected(self):
        lines = ["    x = compute()"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = Candidate(
            rule_id="test",
            claim_type="sql_injection",
            file="app/x.py",
            start_line=3,
            end_line=2,
            message="bad range",
            evidence_text=(),
            severity_hint="high",
            category_hint="sql_injection",
        )
        status, _ = outcome141(candidate, diff)
        self.assertEqual(status, "rejected")

    def test_false_anchor_stays_rejected(self):
        lines = ["    requests.get(url, verify=False)"]
        candidate, diff = added_candidate("tls_verification_disabled", lines)
        tampered = Candidate(
            rule_id=candidate.rule_id,
            claim_type=candidate.claim_type,
            file=candidate.file,
            start_line=candidate.start_line,
            end_line=candidate.end_line,
            message=candidate.message,
            evidence_text=("    requests.get(url, verify=True)",),
            severity_hint=candidate.severity_hint,
            category_hint=candidate.category_hint,
        )
        status, _ = outcome141(tampered, diff)
        self.assertEqual(status, "rejected")

    def test_duplicate_of_accepted_stays_rejected(self):
        lines = ["    requests.get(url, verify=False)"]
        candidate, diff = added_candidate("tls_verification_disabled", lines)
        twin, _ = added_candidate("tls_verification_disabled", lines)
        result = AlmaGateV141().validate([candidate, twin], diff, "test-agent")
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.needs_validation, ())
        self.assertEqual(
            [entry.status for entry in result.ledger], ["accepted", "rejected"]
        )


class HeldRecordTests(unittest.TestCase):
    def _held(self):
        candidate, diff = added_candidate("sql_injection", CO_OCCURRENCE_LINES)
        result = AlmaGateV141().validate([candidate], diff, "test-agent")
        return candidate, diff, result

    def test_record_has_no_severity_anywhere(self):
        _, _, result = self._held()
        record = result.needs_validation[0]
        payload = json.dumps(record.to_dict())
        self.assertNotIn("severity", payload)
        self.assertFalse(hasattr(record, "severity_hint"))
        for blocker in record.blockers:
            self.assertEqual(
                set(blocker.keys()), {"check", "reason", "requirement"}
            )
            self.assertTrue(blocker["reason"])
            self.assertTrue(blocker["requirement"])

    def test_held_is_neither_emitted_nor_in_ledger(self):
        _, _, result = self._held()
        self.assertEqual(result.findings, ())
        self.assertEqual(result.ledger, ())
        self.assertEqual(len(result.needs_validation), 1)
        record = result.needs_validation[0]
        self.assertEqual(record.validator_version, "alma-evidence-gate/1.4.1")
        self.assertEqual(record.policy_sha256, POLICY_SHA256_V141)
        self.assertEqual(record.producer, "test-producer")

    def test_deterministic_bit_for_bit(self):
        candidate, diff, result = self._held()
        again = AlmaGateV141().validate([candidate], diff, "test-agent")
        self.assertEqual(
            json.dumps(result.needs_validation[0].to_dict(), sort_keys=True),
            json.dumps(again.needs_validation[0].to_dict(), sort_keys=True),
        )


class GeneralCategoryTests(unittest.TestCase):
    """The v2.3 general extension: paper 141 §2 does NOT touch it."""

    def test_general_candidate_held_with_no_rule_blocker(self):
        lines = ["    return total + tax"]
        candidate, diff = added_candidate("correctness", lines)
        status, record = outcome141(candidate, diff)
        self.assertEqual(status, "needs_validation")
        self.assertEqual(
            [b["check"] for b in record.blockers],
            ["sin_regla_de_verificacion_en_puerta"],
        )

    def test_general_candidate_context_only_keeps_no_added_line_blocker(self):
        lines = ["    return total + tax"]
        diff = parse_unified_diff(attack_diff(lines, "context"))
        candidate = attack_candidate("reliability", 1, 1, lines, "general claim")
        status, record = outcome141(candidate, diff)
        self.assertEqual(status, "needs_validation")
        self.assertEqual(
            [b["check"] for b in record.blockers],
            ["sin_regla_de_verificacion_en_puerta", "no_added_line"],
        )
        # Bit-for-bit the same held record the 1.4.0 produces, apart
        # from the gate identity stamps.
        s14, record14 = outcome14(candidate, diff)
        self.assertEqual(s14, "needs_validation")
        self.assertEqual(record.blockers, record14.blockers)

    def test_general_candidate_false_anchor_rejected(self):
        lines = ["    return total + tax"]
        candidate, diff = added_candidate("correctness", lines)
        tampered = Candidate(
            rule_id=candidate.rule_id,
            claim_type="correctness",
            file=candidate.file,
            start_line=1,
            end_line=1,
            message=candidate.message,
            evidence_text=("    return total - tax",),
            severity_hint="high",
            category_hint="correctness",
        )
        status, _ = outcome141(tampered, diff)
        self.assertEqual(status, "rejected")

    def test_general_candidate_malformed_rejected(self):
        lines = ["    return total + tax"]
        diff = parse_unified_diff(make_diff("app/x.py", lines))
        candidate = Candidate(
            rule_id="test",
            claim_type="correctness",
            file="app/x.py",
            start_line=0,
            end_line=1,
            message="bad range",
            evidence_text=(),
            severity_hint="high",
            category_hint="correctness",
        )
        status, _ = outcome141(candidate, diff)
        self.assertEqual(status, "rejected")


class EquivalenceTests(unittest.TestCase):
    def test_inherited_pairs_acceptance_equivalent(self):
        for claim_type, (accept_lines, reject_lines) in INHERITED_PAIRS.items():
            for lines in (accept_lines, reject_lines):
                with self.subTest(claim_type=claim_type):
                    candidate, diff = added_candidate(claim_type, lines)
                    s13 = outcome13(candidate, diff)
                    s141, _ = outcome141(candidate, diff)
                    if lines is accept_lines and claim_type != "race_condition":
                        self.assertEqual(s13, "accepted")
                    else:
                        self.assertEqual(s13, "rejected")
                    self.assertEqual(s141 == "accepted", s13 == "accepted")
                    if s13 == "rejected":
                        self.assertIn(s141, ("rejected", "needs_validation"))

    def test_mock_candidates_over_fixtures_acceptance_equivalent(self):
        roots = ("fixtures", "fixtures_v2", "fixtures_v11", "fixtures_v13", "fixtures_semaforo")
        checked = 0
        for root_name in roots:
            for fixture_dir in sorted((ROOT / root_name).iterdir()):
                diff_path = fixture_dir / "diff.patch"
                if not diff_path.exists():
                    continue
                diff = parse_unified_diff(diff_path.read_text(encoding="utf-8"))
                candidates = BaseReviewer().review(diff)
                with self.subTest(fixture=f"{root_name}/{fixture_dir.name}"):
                    r13 = AlmaGateV13().validate(candidates, diff, "t")
                    r141 = AlmaGateV141().validate(candidates, diff, "t")
                    self.assertEqual(
                        [f["file"] for f in r13.findings],
                        [f["file"] for f in r141.findings],
                    )
                    self.assertEqual(len(r13.findings), len(r141.findings))
                checked += len(candidates)
        self.assertGreater(checked, 0)

    def test_red_battery_acceptance_equivalent(self):
        for attacks in (ATTACKS, NEW_ATTACKS):
            for attack in attacks:
                attack_id, claim_type, _trick, lines, start, end, message, ctx = attack
                with self.subTest(attack=attack_id):
                    diff = parse_unified_diff(attack_diff(lines, ctx))
                    candidate = attack_candidate(claim_type, start, end, lines, message)
                    s13 = outcome13(candidate, diff)
                    s141, _ = outcome141(candidate, diff)
                    self.assertEqual(s141 == "accepted", s13 == "accepted")

    def test_red_battery_has_zero_state_moves(self):
        """Paper 141 §4 precision: in universe 2 the state map of the
        1.4.1 must be IDENTICAL to the 1.3.0's, candidate by
        candidate — S3 included (under the 1.4.0 this same battery
        had exactly one move: S3)."""

        moves = []
        for attacks in (ATTACKS, NEW_ATTACKS):
            for attack in attacks:
                attack_id, claim_type, _trick, lines, start, end, message, ctx = attack
                diff = parse_unified_diff(attack_diff(lines, ctx))
                candidate = attack_candidate(claim_type, start, end, lines, message)
                s13 = outcome13(candidate, diff)
                s141, _ = outcome141(candidate, diff)
                if s13 != s141:
                    moves.append((attack_id, s13, s141))
        self.assertEqual(moves, [])

    def test_declared_residuals_stay_accepted(self):
        for attacks in (ATTACKS, NEW_ATTACKS):
            for attack in attacks:
                attack_id, claim_type, _trick, lines, start, end, message, ctx = attack
                if attack_id not in ("C3", "X2"):
                    continue
                diff = parse_unified_diff(attack_diff(lines, ctx))
                candidate = attack_candidate(claim_type, start, end, lines, message)
                s141, _ = outcome141(candidate, diff)
                self.assertEqual(s141, "accepted", attack_id)


if __name__ == "__main__":
    unittest.main()
