"""Tests for the net score (ADENDA-PUNTAJE-NETO.md).

Synthetic arms are checked against hand counts; the integration
tests re-derive every arm of the line from the primary sources
and assert each cross closes EXACTLY against the published paper
of its measurement, plus the net values those crosses imply.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent.net_score import (
    ARM_311_COUNTS,
    ARM_ALMA_311,
    ARM_BASE_298,
    ARM_CONTRACT_REPLAY,
    ARM_GATE141_REPLAY,
    ARM_GATE150_REPLAY,
    ARM_SHAPER_REPLAY,
    ArmCounts,
    compute_arms,
    counts_from_cross,
    counts_from_verdicts,
    net_score,
)

ROOT = Path(__file__).resolve().parent.parent


class TestSyntheticCounts(unittest.TestCase):
    def test_hand_counted_mix(self):
        c = counts_from_verdicts(
            "synthetic",
            ["TP"] * 3 + ["FPG"] + ["GREY"] * 2 + ["NOVEL"] * 4)
        self.assertEqual(c.emissions, 10)
        self.assertEqual((c.tp, c.fpg, c.grey, c.novel), (3, 1, 2, 4))
        self.assertEqual(c.zero, 6)
        self.assertEqual(net_score(c), (2, 20.0))
        self.assertFalse(c.blocked_as_improvement)

    def test_grey_and_novel_score_zero_not_minus(self):
        # The addenda's core definition: unproven is not false.
        c = counts_from_verdicts("grey", ["GREY", "NOVEL"])
        self.assertEqual(net_score(c), (0, 0.0))
        self.assertTrue(c.blocked_as_improvement)  # raw <= 0

    def test_zero_emissions_normalized_undefined(self):
        c = counts_from_verdicts("silent", [])
        self.assertEqual(c.emissions, 0)
        self.assertEqual(c.raw, 0)
        self.assertIsNone(c.per_100)

    def test_negative_net(self):
        c = counts_from_verdicts("noisy", ["FPG", "FPG", "TP"])
        self.assertEqual(net_score(c), (-1, -33.3))
        self.assertTrue(c.blocked_as_improvement)

    def test_unknown_verdict_refuses(self):
        with self.assertRaises(ValueError):
            counts_from_verdicts("bad", ["TP", "MAYBE"])

    def test_cross_must_close(self):
        with self.assertRaises(ValueError):
            counts_from_cross("bad", {"emissions": 5, "TP": 1,
                                      "FPG": 1, "GREY": 1, "NOVEL": 1})

    def test_arm_311_constant_is_grey_not_fpg(self):
        # ADJUDICACION-COMPLETA-311 section 2: the single emission
        # is grey zone (0 FP-gold / 1 grey / 0 novel), explicitly
        # NOT FPG under the house standard — so its net is 0,
        # and rule 3.3 still blocks it as an improvement.
        c = counts_from_cross(ARM_ALMA_311, ARM_311_COUNTS)
        self.assertEqual((c.tp, c.fpg, c.grey, c.novel), (0, 0, 1, 0))
        self.assertEqual(net_score(c), (0, 0.0))
        self.assertTrue(c.blocked_as_improvement)


class TestRealArms(unittest.TestCase):
    """Closure against the published papers, from decisions.json."""

    @classmethod
    def setUpClass(cls):
        cls.arms = {a.arm: a for a in compute_arms(ROOT)}

    def test_base_298_cross_and_net(self):
        a = self.arms[ARM_BASE_298]
        self.assertEqual((a.emissions, a.tp, a.fpg, a.grey, a.novel),
                         (166, 89, 8, 17, 52))
        self.assertEqual(net_score(a), (81, 48.8))

    def test_gate141_replay_emitted_nothing(self):
        a = self.arms[ARM_GATE141_REPLAY]
        self.assertEqual(a.emissions, 0)
        self.assertEqual(a.raw, 0)
        self.assertIsNone(a.per_100)  # silence normalizes to n/d

    def test_gate150_cross_and_net(self):
        a = self.arms[ARM_GATE150_REPLAY]
        self.assertEqual((a.emissions, a.tp, a.fpg, a.grey, a.novel),
                         (32, 19, 2, 2, 9))
        self.assertEqual(net_score(a), (17, 53.1))

    def test_contract_cross_and_net(self):
        a = self.arms[ARM_CONTRACT_REPLAY]
        self.assertEqual((a.emissions, a.tp, a.fpg, a.grey, a.novel),
                         (49, 26, 2, 3, 18))
        self.assertEqual(net_score(a), (24, 49.0))

    def test_shaper_cross_and_net(self):
        a = self.arms[ARM_SHAPER_REPLAY]
        self.assertEqual(a.emissions, 79)
        self.assertEqual((a.tp, a.fpg), (44, 4))
        # GREY/NOVEL split is this module's derived output; the
        # published totals fix only their sum.
        self.assertEqual(a.grey + a.novel, 31)
        self.assertEqual(net_score(a), (40, 50.6))

    def test_alma_311_arm(self):
        a = self.arms[ARM_ALMA_311]
        self.assertEqual((a.emissions, a.tp, a.fpg, a.grey, a.novel),
                         (1, 0, 0, 1, 0))
        self.assertEqual(net_score(a), (0, 0.0))
        self.assertTrue(a.blocked_as_improvement)

    def test_every_arm_closes(self):
        for a in self.arms.values():
            self.assertEqual(
                a.emissions, a.tp + a.fpg + a.grey + a.novel,
                f"{a.arm} does not close")


if __name__ == "__main__":
    unittest.main()
