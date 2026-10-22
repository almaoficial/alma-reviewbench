"""Lessons compiler tests — paper PREREGISTRO-MEMORIA-LECCIONES §6.

What is verified dry (US$0, no model anywhere):

- on a synthetic corpus with hand-computable fates, the computed
  dispositions and the compiled taxonomy equal the hand counts;
- the provenance audit of the compiled artifact is clean, and a
  tampered artifact (a changed count, a corrupted manifest hash)
  makes the audit FAIL, naming the violation — zero invented
  examples, zero hand counts;
- the block cap and the paper's declared mechanical trim are
  exercised (lived examples trimmed first, taxonomy / rules / the
  rejected example never cut; a cap below the untrimmable core
  makes the compiler fail, as declared);
- on the REAL corpus (when its clones are present in the
  checkout), the committed artifact audits clean against a fresh
  re-derivation and its taxonomy equals the line's published
  counts (79 / 54 / 32 / 1).

No test here measures any EFFECT of the lessons on production:
that is the paper's honest caveat, not an omission.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import agent.lessons_compiler as lc  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from test_gate_v11 import make_diff  # noqa: E402


A_LINES = [
    'code = request.args.get("code")',
    "def load_config(path):",
    "    return yaml.load(open(path))",
    'token = vault.read("api_token")',
]
B_LINES = [
    "session = Session()",
    "session.commit()",
]
C_LINES = [
    "value = compute_total(items)",
]


def _rec(pr, idx, file, start, end, message, evidence, gold,
         gold_idx=None, note=None):
    return lc.ClaimRecord(
        pr=pr, idx=idx, file=file, start_line=start, end_line=end,
        message=message, evidence=tuple(evidence), gold=gold,
        gold_idx=gold_idx, gold_note=note,
    )


def _synthetic_corpus():
    records = [
        # synth_a e0 — TP, born declaring, emitted.
        _rec("synth_a", 0, "a.py", 2, 3,
             "The loader calls `yaml.load` on an open file handle "
             "without a safe loader.",
             A_LINES[1:3], "TP", 10),
        # synth_a e1 — TP, dead at origin: asserted token absent.
        _rec("synth_a", 1, "a.py", 4, 4,
             "The handler leaks `secret_key` into the log output.",
             A_LINES[3:4], "TP", 11),
        # synth_a e2 — NOVEL, dead at origin: no pattern at all.
        _rec("synth_a", 2, "a.py", 1, 2,
             "This part feels fragile and might break under load "
             "someday.",
             A_LINES[0:2], "NOVEL"),
        # synth_a e3 — TP, rejected firmly: declares `code` absent,
        # its citation contains it (the Mcp-Docker shape).
        _rec("synth_a", 3, "a.py", 1, 1,
             "The callback arrives without a `code` and is dropped "
             "silently.",
             A_LINES[0:1], "TP", 12),
        # synth_a e4 — GREY, dead at origin, with adjudication note.
        _rec("synth_a", 4, "a.py", 3, 4,
             "The error handling here seems inconsistent with the "
             "rest of the module.",
             A_LINES[2:4], "GREY", None,
             "Preocupación real sin entrada gold (nota sintética)."),
        # synth_a e5 — TP, born minable, emitted.
        _rec("synth_a", 5, "a.py", 2, 3,
             "The startup path calls load_config before the vault "
             "is ready.",
             A_LINES[1:3], "TP", 13),
        # synth_b e0 — FPG, dead at origin: asserted token absent.
        _rec("synth_b", 0, "b.py", 1, 2,
             "The session exposes `admin_bypass` for debugging.",
             B_LINES[0:2], "FPG"),
        # synth_b e1 — NOVEL, born declaring, emitted.
        _rec("synth_b", 1, "b.py", 1, 2,
             "The session reaches `session.commit` without any "
             "prior flush.",
             B_LINES[0:2], "NOVEL"),
    ]
    diffs = {
        "synth_a": parse_unified_diff(make_diff("a.py", A_LINES)),
        "synth_b": parse_unified_diff(make_diff("b.py", B_LINES)),
    }
    return records, diffs


HAND_TAXONOMY = {
    lc.DISP_EMITTED: 3,
    lc.DISP_DEAD_TOKENS: 2,
    lc.DISP_DEAD_NO_PATTERN: 2,
    lc.DISP_REJECTED: 1,
}


class SyntheticCorpusTests(unittest.TestCase):
    def setUp(self):
        records, diffs = _synthetic_corpus()
        self.disps = lc.compute_dispositions(records, diffs)
        self.compiled = lc.compile_lessons(self.disps, "ab" * 32)

    def test_dispositions_match_hand_counts(self):
        from collections import Counter
        self.assertEqual(
            dict(Counter(d.final for d in self.disps)), HAND_TAXONOMY)
        by_key = {(d.record.pr, d.record.idx): d for d in self.disps}
        self.assertEqual(by_key[("synth_a", 5)].shaper_origin, "mined")
        self.assertEqual(by_key[("synth_a", 0)].shaper_origin, "declared")
        self.assertEqual(by_key[("synth_a", 1)].absent_tokens,
                         ("secret_key",))
        self.assertEqual(by_key[("synth_b", 0)].absent_tokens,
                         ("admin_bypass",))

    def test_compiled_taxonomy_and_selection(self):
        m = self.compiled.manifest
        self.assertEqual(m["taxonomy"], HAND_TAXONOMY)
        self.assertEqual(m["corpus"]["claims"], 8)
        order = [(e["pr"], e["idx"]) for e in m["examples"]]
        self.assertEqual(order, [
            ("synth_a", 1),   # D1 TP dead tokens
            ("synth_b", 0),   # D2 FPG dead tokens
            ("synth_a", 4),   # D3 GREY dead no-pattern (note carried)
            ("synth_a", 2),   # D4 NOVEL dead no-pattern
            ("synth_a", 3),   # D5 the rejected claim
            ("synth_a", 0),   # L1 TP emitted, declared
            ("synth_a", 5),   # L2 TP emitted, mined
        ])
        self.assertIn("3 of 8", self.compiled.block)
        self.assertIn("Preocupación real sin entrada gold",
                      self.compiled.block)

    def test_audit_clean_and_tampering_fails(self):
        artifact = lc.render_artifact(self.compiled)
        self.assertEqual(
            lc.audit_artifact(artifact, self.compiled.manifest,
                              self.disps), [])
        # A changed count inside the block.
        tampered = artifact.replace("3 of 8", "4 of 8", 1)
        violations = lc.audit_artifact(
            tampered, self.compiled.manifest, self.disps)
        self.assertTrue(violations)
        # A corrupted provenance hash in the manifest.
        bad_manifest = json.loads(json.dumps(self.compiled.manifest))
        bad_manifest["examples"][0]["message_sha256"] = "0" * 64
        violations = lc.audit_artifact(
            artifact, bad_manifest, self.disps)
        self.assertTrue(any("D1" in v for v in violations))
        # Markers gone.
        violations = lc.audit_artifact(
            "# nothing here", self.compiled.manifest, self.disps)
        self.assertTrue(violations)


class TrimTests(unittest.TestCase):
    def _corpus_c(self):
        records, diffs = _synthetic_corpus()
        for i in range(4):
            records.append(_rec(
                "synth_c", i, "c.py", 1, 1,
                f"The audit trail drops `missing_token_{i}` whenever "
                "the batch is reconciled against the ledger and the "
                "totals are recomputed for the monthly close report.",
                C_LINES, "TP", 20 + i))
        for i in (4, 5):
            records.append(_rec(
                "synth_c", i, "c.py", 1, 1,
                "The pipeline calls `compute_total` before the items "
                "are validated, so the figure it publishes mixes "
                "unvalidated rows into the monthly totals that the "
                "close report distributes to every stakeholder.",
                C_LINES, "TP", 20 + i))
        diffs["synth_c"] = parse_unified_diff(make_diff("c.py", C_LINES))
        return records, diffs

    def test_declared_trim_and_untrimmable_core(self):
        records, diffs = self._corpus_c()
        disps = lc.compute_dispositions(records, diffs)
        original_cap = lc.BLOCK_MAX_CHARS
        try:
            lc.BLOCK_MAX_CHARS = 10 ** 9
            full = lc.compile_lessons(disps, "cd" * 32)
            cap = len(full.block) - 500
            lc.BLOCK_MAX_CHARS = cap
            trimmed = lc.compile_lessons(disps, "cd" * 32)
            self.assertLessEqual(len(trimmed.block), cap)
            self.assertLess(len(trimmed.manifest["examples"]),
                            len(full.manifest["examples"]))
            # Taxonomy, rules and the rejected example never cut.
            self.assertIn("## How the claims died", trimmed.block)
            self.assertIn("## Rules distilled", trimmed.block)
            self.assertIn("disp=rechazado_puerta", trimmed.block)
            # A cap below the untrimmable core: the compiler fails.
            lc.BLOCK_MAX_CHARS = 300
            with self.assertRaises(ValueError):
                lc.compile_lessons(disps, "cd" * 32)
        finally:
            lc.BLOCK_MAX_CHARS = original_cap


class RealCorpusAuditTests(unittest.TestCase):
    """The committed artifact against a fresh re-derivation from
    the real corpus.  Skipped only when the corpus clones are not
    present in the checkout (they are build cache, not source)."""

    def test_committed_artifact_audits_clean(self):
        repos = ROOT / "adjwork298" / "repos"
        if not repos.is_dir() or not any(repos.iterdir()):
            self.skipTest("corpus clones not present in this checkout")
        records, diffs, _meta = lc.load_corpus(ROOT)
        disps = lc.compute_dispositions(records, diffs)
        self.assertEqual(len(disps), 166)
        artifact = (ROOT / "CONTEXTO-LECCIONES.md").read_text()
        manifest = json.loads(
            (ROOT / "CONTEXTO-LECCIONES.provenance.json").read_text())
        self.assertEqual(manifest["taxonomy"], {
            "emitido": 79,
            "muerto_en_origen_sin_patron": 54,
            "muerto_en_origen_tokens": 32,
            "rechazado_puerta": 1,
        })
        self.assertEqual(
            lc.audit_artifact(artifact, manifest, disps), [])


if __name__ == "__main__":
    unittest.main()
