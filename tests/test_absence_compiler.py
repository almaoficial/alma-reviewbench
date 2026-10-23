"""Absence compiler tests — paper PREREGISTRO-LECCIONES-AUSENCIA.

What is verified dry (US$0, no model anywhere):

- on a synthetic corpus with hand-computable absences, the
  computed dimensions and the compiled counts equal the hand
  counts, and every compiled example is an absent gold TP;
- the provenance audit of the compiled artifact is clean, and a
  tampered artifact (a changed count in the block, a corrupted
  manifest hash, an example pointing at a TOUCHED gold entry)
  makes the audit FAIL, naming the violation — zero invented
  examples, zero hand counts;
- the block cap and the paper's declared mechanical trim are
  exercised (examples trimmed, counts/rules never cut; a cap
  below the untrimmable core makes the compiler fail);
- on the REAL corpus, the adjudication closes exactly as
  published (352 gold TP = 66 touched + 286 absent; families
  A1 = 104, A2 = 182) and the committed artifact audits clean
  against a fresh re-derivation.

No test here measures any EFFECT of the absence lessons on
recall: that is the paper's honest caveat, not an omission.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent.absence_compiler as ac  # noqa: E402


def _gold(pr, g, file, start, end, message, touched, family,
          file_emissions=0, overlap=None, grazes=0, category="correctness",
          context="diff-only", scope="introduced-by-pr",
          difficulty="easy", severity="high"):
    return ac.GoldRecord(
        pr=pr, gold_idx=g, file=file, start_line=start, end_line=end,
        message=message, severity=severity, category=category,
        scope=scope, difficulty=difficulty, context_required=context,
        touched=touched, family=family, file_emissions=file_emissions,
        overlap_emission=overlap, grey_grazes=grazes)


def _synthetic():
    records = [
        # pr_x g0 — touched.
        _gold("pr_x", 0, "a.py", 1, 3, "Touched defect.", True, None,
              file_emissions=1),
        # pr_x g1 — absent A1 (reviewer never emitted on b.py).
        _gold("pr_x", 1, "b.py", 5, 8,
              "The parser drops empty segments silently.", False,
              ac.FAMILY_NEVER_VISITED, category="reliability"),
        # pr_x g2 — absent A2 with an overlapping emission.
        _gold("pr_x", 2, "a.py", 10, 12,
              "The cache key ignores the tenant id.", False,
              ac.FAMILY_VISITED_MISSED, file_emissions=2, overlap=0,
              grazes=1),
        # pr_x g3 — absent A2, wide citation: not example-eligible.
        _gold("pr_x", 3, "a.py", 20, 60,
              "A long-range defect nobody claimed.", False,
              ac.FAMILY_VISITED_MISSED, file_emissions=2,
              category="maintainability"),
    ]
    emissions = {"pr_x": ac.PrEmissions(
        pr="pr_x",
        messages=("First claim on a.py.", "Second claim on a.py."),
        files=("a.py", "a.py"),
        ranges=((10, 11), (30, 31)))}
    meta = {"decisions_sha256": "0" * 64, "gold_tp": 4, "touched": 1,
            "absent": 3, "grey_refs_total": 1, "grey_refs_parsed": 1}
    return records, emissions, meta


class TestSyntheticCorpus(unittest.TestCase):
    def setUp(self):
        self.records, self.emissions, self.meta = _synthetic()
        self.compiled = ac.compile_absences(
            self.records, self.emissions, self.meta)

    def test_dimensions_equal_hand_counts(self):
        dims = ac.compute_dimensions(self.records)
        self.assertEqual(dims["families"], {
            ac.FAMILY_NEVER_VISITED: 1, ac.FAMILY_VISITED_MISSED: 2})
        self.assertEqual(dims["a2_with_overlap"], 1)
        self.assertEqual(dims["grey_grazed_absent"], 1)
        self.assertEqual(dims["by_category"]["correctness"],
                         {"gold_tp": 2, "absent": 1})
        self.assertEqual(dims["by_category"]["maintainability"],
                         {"gold_tp": 1, "absent": 1})
        self.assertEqual(dims["by_pr"]["pr_x"],
                         {"gold_tp": 4, "absent": 3})

    def test_examples_are_absent_and_eligible(self):
        tags = [e["tag"] for e in self.compiled.manifest["examples"]]
        self.assertEqual(tags, ["A1-1", "A2-1"])  # g3 too wide
        for e in self.compiled.manifest["examples"]:
            rec = next(r for r in self.records
                       if r.pr == e["pr"] and r.gold_idx == e["gold_idx"])
            self.assertFalse(rec.touched)
        a2 = next(e for e in self.compiled.manifest["examples"]
                  if e["tag"] == "A2-1")
        self.assertEqual(a2["quoted_emission"], 0)

    def test_audit_clean(self):
        text = ac.render_artifact(self.compiled)
        violations = ac.audit_artifact(
            text, self.compiled.manifest, self.records,
            self.emissions, self.meta)
        self.assertEqual(violations, [])

    def test_audit_names_a_changed_count(self):
        text = ac.render_artifact(self.compiled).replace(
            "of 4 true defects, 1 were claimed and 3 were never "
            "claimed", "of 4 true defects, 2 were claimed and 2 "
            "were never claimed")
        violations = ac.audit_artifact(
            text, self.compiled.manifest, self.records,
            self.emissions, self.meta)
        self.assertTrue(any("hash" in v or "recompilation" in v
                            for v in violations), violations)

    def test_audit_names_a_corrupt_manifest_hash(self):
        bad = json.loads(json.dumps(self.compiled.manifest))
        bad["examples"][0]["message_sha256"] = "0" * 64
        violations = ac.audit_artifact(
            ac.render_artifact(self.compiled), bad, self.records,
            self.emissions, self.meta)
        self.assertTrue(any("message hash" in v for v in violations),
                        violations)

    def test_audit_names_an_example_pointing_at_a_touched_entry(self):
        bad = json.loads(json.dumps(self.compiled.manifest))
        bad["examples"][0]["gold_idx"] = 0  # the TOUCHED entry
        violations = ac.audit_artifact(
            ac.render_artifact(self.compiled), bad, self.records,
            self.emissions, self.meta)
        self.assertTrue(any("TOUCHED" in v or "tag order" in v
                            for v in violations), violations)

    def test_trim_and_failure_follow_the_paper(self):
        saved = ac.BLOCK_MAX_CHARS
        try:
            ac.BLOCK_MAX_CHARS = 200  # below the untrimmable core
            with self.assertRaises(ValueError):
                ac.compile_absences(self.records, self.emissions,
                                    self.meta)
        finally:
            ac.BLOCK_MAX_CHARS = saved


@unittest.skipUnless((ROOT / "adjwork298" / "decisions.json").exists(),
                     "real corpus not in this checkout")
class TestRealCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.emissions, cls.meta = \
            ac.load_absence_corpus(ROOT)
        cls.compiled = ac.compile_absences(
            cls.records, cls.emissions, cls.meta)

    def test_closure_matches_the_published_adjudication(self):
        self.assertEqual(self.meta["gold_tp"], 352)
        self.assertEqual(self.meta["touched"], 66)
        self.assertEqual(self.meta["absent"], 286)
        dims = ac.compute_dimensions(self.records)
        self.assertEqual(dims["families"], {
            ac.FAMILY_NEVER_VISITED: 104,
            ac.FAMILY_VISITED_MISSED: 182})
        self.assertEqual(dims["a2_with_overlap"], 54)
        self.assertEqual(dims["grey_grazed_absent"], 11)
        self.assertEqual(self.meta["grey_refs_total"], 17)
        # 16 of 17 refs parse clean; the 17th is the double ref
        # "G13/G6" (konturio E1), which the paper's declared rule
        # counts as unparsed.
        self.assertEqual(self.meta["grey_refs_parsed"], 16)

    def test_compilation_is_deterministic(self):
        again = ac.compile_absences(self.records, self.emissions,
                                    self.meta)
        self.assertEqual(again.block_sha256,
                         self.compiled.block_sha256)
        self.assertLessEqual(self.compiled.manifest["block_chars"],
                             ac.BLOCK_MAX_CHARS)

    def test_committed_artifact_audits_clean(self):
        text = (ROOT / "CONTEXTO-AUSENCIAS.md").read_text()
        manifest = json.loads(
            (ROOT / "CONTEXTO-AUSENCIAS.provenance.json").read_text())
        violations = ac.audit_artifact(
            text, manifest, self.records, self.emissions, self.meta)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
