"""Tests for the executability census (PREREGISTRO-CENSO-EJECUTABILIDAD).

The script-stage rules are exercised on synthetic claims (one per
rule family, plus the conflict and no-signal cases that must fall
to DUDA), and the integration tests re-derive the waiting room
from the frozen gate 1.4.1 and assert the published replay sanity
closes exactly before anything is classified.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent.alma_gate_v141 import POLICY_SHA256 as POLICY_SHA_V141
from agent.executability_census import (
    E1, E2, E3, E4, SANITY_HELD, run_census, script_classify,
)
from agent.lessons_compiler import ClaimRecord

ROOT = Path(__file__).resolve().parent.parent


def rec(message, file="src/mod.py", gold="TP"):
    return ClaimRecord(
        pr="synthetic", idx=0, file=file, start_line=1, end_line=2,
        message=message, evidence=("line one", "line two"),
        gold=gold, gold_idx=None, gold_note=None)


class ScriptRuleTests(unittest.TestCase):

    def test_gate_141_policy_is_the_frozen_one(self):
        self.assertTrue(POLICY_SHA_V141.startswith("73a403d8"))

    def test_e1_test_asis(self):
        cls, rules, _ = script_classify(rec(
            "The test passes without touching the network: the client "
            "is never constructed.", file="pkg/test_client.py"))
        self.assertEqual(cls, E1)
        self.assertEqual(rules, ["e1_test_asis"])

    def test_e1_command_decides(self):
        cls, rules, _ = script_classify(rec(
            "This does not compile: the module fails to parse under "
            "the project interpreter."))
        self.assertEqual(cls, E1)
        self.assertIn("e1_command_decides", rules)

    def test_e2_input_outcome(self):
        cls, rules, _ = script_classify(rec(
            "When called with an empty list, `merge` returns None "
            "instead of an empty dict."))
        self.assertEqual(cls, E2)
        self.assertIn("e2_input_outcome", rules)

    def test_e2_counterfactual_test(self):
        cls, rules, _ = script_classify(rec(
            "The assertions still pass even if the implementation is "
            "completely broken.", file="pkg/test_merge.py"))
        self.assertEqual(cls, E2)
        self.assertIn("e2_counterfactual", rules)

    def test_e3_design_vocab(self):
        cls, rules, _ = script_classify(rec(
            "This class is confusing and hard to maintain; it "
            "duplicates the validation logic and should be split "
            "for readability."))
        self.assertEqual(cls, E3)
        self.assertIn("e3_design_vocab", rules)

    def test_e3_absence_static(self):
        cls, rules, _ = script_classify(rec(
            "The helper `old_parse` is never called anywhere in the "
            "codebase."))
        self.assertEqual(cls, E3)
        self.assertIn("e3_absence_static", rules)

    def test_e3_doc_file(self):
        cls, rules, _ = script_classify(rec(
            "The guide shows the old flag name in its example.",
            file="docs/guide.md"))
        self.assertEqual(cls, E3)
        self.assertIn("e3_doc_file", rules)

    def test_duda_on_class_conflict(self):
        # E2 (input + outcome) and E3 (static absence) both draw
        # votes: the script must abstain and leave it to review.
        cls, _, votes = script_classify(rec(
            "When called with a fresh config, `load` returns the "
            "parsed value, but the legacy helper is never called "
            "anywhere."))
        self.assertIsNone(cls)
        self.assertTrue(votes[E2] and votes[E3])

    def test_duda_on_no_signal(self):
        cls, _, _ = script_classify(rec("The behavior here is questionable."))
        self.assertIsNone(cls)


class CensusIntegrationTests(unittest.TestCase):

    def test_waiting_room_sanity_and_script_stage(self):
        entries, summary = run_census(ROOT, {})
        self.assertEqual(summary["sanity"], {
            "accepted": 0, "held": 149, "rejected": 17,
            "held_gold": {"TP": 80, "FPG": 8, "GREY": 16, "NOVEL": 45},
        })
        self.assertEqual(summary["total"], SANITY_HELD)
        self.assertEqual(summary["via"], {"script": 28, "duda": 121})
        self.assertEqual(summary["by_class"][E1], 4)
        self.assertEqual(summary["by_class"][E2], 5)
        self.assertEqual(summary["by_class"][E3], 19)
        self.assertEqual(summary["by_class"][E4], 0)
        self.assertEqual(summary["unclassified"], 121)
        self.assertEqual(len(entries), 149)

    def test_review_assignment_closes_a_duda(self):
        entries, _ = run_census(ROOT, {})
        duda_key = next(e["key"] for e in entries if e["class"] is None)
        entries2, summary2 = run_census(
            ROOT, {duda_key: {"class": E2, "reason": "synthetic review"}})
        self.assertEqual(summary2["unclassified"], 120)
        assigned = next(e for e in entries2 if e["key"] == duda_key)
        self.assertEqual(assigned["class"], E2)
        self.assertEqual(assigned["via"], "revision")
        self.assertEqual(assigned["reason"], "synthetic review")

    def test_review_rejects_bad_class(self):
        entries, _ = run_census(ROOT, {})
        duda_key = next(e["key"] for e in entries if e["class"] is None)
        with self.assertRaises(ValueError):
            run_census(ROOT, {duda_key: {"class": "E9", "reason": "x"}})


if __name__ == "__main__":
    unittest.main()
