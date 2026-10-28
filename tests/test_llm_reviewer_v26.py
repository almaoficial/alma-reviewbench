"""Reviewer v2.6 tests — paper ADENDA-V26.md §7.

What is verified dry (US$0, scripted transports only):

- identity and the frozen line: gates 1.0.0–1.5.0,
  claim_contract, birth_shaper, v2.3, v2.4 AND v2.5, both
  compilers and both context artifacts byte-identical;
- fail-closed loading, PER BLOCK: the committed absence
  artifact loads and its hash verifies; a tampered absence
  artifact, a missing file, an artifact without markers all
  raise RealLLMRefused at construction, before any call can
  exist; a tampered LESSONS artifact also refuses (the v2.5's
  own fail-closed keeps binding through inheritance);
- faithful DOUBLE injection: the absence block appears
  VERBATIM (after its fixed header) AFTER the lessons header
  and block in the armed deep and fallback system prompts —
  each block exactly once, lessons before absences; the user
  content is untouched; the selection payload is
  byte-identical to the v2.4's and to the v2.5's;
- the combined context budget, computed by program with the
  line's own estimator, matches the paper's §4 table and fits
  both declared criteria;
- the v2.6 provenance: emitted candidates carry
  producer/rule_id v26 tags through the shaping stage, and the
  run info carries lessons_* AND absence_* fields with
  reviewer_version 2.6.0;
- the inherited discipline does not move: a valid citable
  claim is born conforming and accepted by gate 1.5.0; a
  no-pattern finding settles in the production ledger; the
  guard refuses before calling;
- the frozen semaphore battery driven through
  LLMReviewerV26.review(): 8 cases x 2 gate configs = 16/16,
  with BOTH blocks present in every deep payload.

No test here measures any EFFECT of the absence context on
real production: that is the paper's honest caveat (§5).
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent.absence_compiler import extract_block as extract_absence_block  # noqa: E402
from agent.alma_gate_v150 import AlmaGateV150  # noqa: E402
from agent.claim_contract import normalize_claim  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import LLMSettings, RealLLMRefused, _estimate_tokens  # noqa: E402
from agent.llm_reviewer_v24 import LLMReviewerV24  # noqa: E402
from agent.llm_reviewer_v25 import (  # noqa: E402
    LESSONS_INJECTION_HEADER,
    LLMReviewerV25,
)
from agent.llm_reviewer_v26 import (  # noqa: E402
    ABSENCE_INJECTION_HEADER,
    REVIEWER_VERSION,
    LLMReviewerV26,
    load_absence_block,
)
from test_gate_v11 import make_diff  # noqa: E402
from test_llm_reviewer_v22 import load_semaforo_case  # noqa: E402
from test_llm_reviewer_v23 import armed_env, pass_name_of  # noqa: E402
from test_llm_reviewer_v24 import (  # noqa: E402
    CONFIG_V13,
    CONFIG_V14,
    FROZEN_FILE_SHA256,
    LINES,
    PATH,
    BatteryTransport,
    EmissionTransport,
    _citable_token,
    _finding,
)

FROZEN_V26 = dict(
    FROZEN_FILE_SHA256,
    **{
        "llm_reviewer_v24.py":
            "a771ae728ebe99bba7c867af6ee6b3bf6f20ff6dc48640d2a166dbce21bbf1dc",
        "llm_reviewer_v25.py":
            "47ae82e69589f88be68557eb12747b16acd5d7c7a5a38f776c3d13b4b5a17606",
        "lessons_compiler.py":
            "482fce85f4fba2e4f479fd7e991aaaf1391e9ee38021f3f1b3ed79f9a7e96ce4",
        "absence_compiler.py":
            "567c67d97a423a195fbfa03886f0219ce0d82a7f40b217b8a55075c06557a5cc",
    },
)

FROZEN_ARTIFACTS = {
    "CONTEXTO-LECCIONES.md":
        "92895d857307059cabf024eea5562bcb062ff88ecbafacedc171f388c9956aab",
    "CONTEXTO-AUSENCIAS.md":
        "530ad9524a8d94865678eab304ea0e590b1503d80d8a62774576e66c18876056",
}

LESSONS_ARTIFACT = ROOT / "CONTEXTO-LECCIONES.md"
ABSENCE_ARTIFACT = ROOT / "CONTEXTO-AUSENCIAS.md"
ABSENCE_MANIFEST = ROOT / "CONTEXTO-AUSENCIAS.provenance.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reviewer26(transport=None, **kwargs):
    return LLMReviewerV26(
        LLMSettings.from_env(armed_env(), CONFIG_V14),
        transport=transport or EmissionTransport(),
        **kwargs,
    )


class IdentityAndFrozenTests(unittest.TestCase):
    def test_reviewer_identity(self):
        self.assertEqual(REVIEWER_VERSION, "llm-reviewer/2.6.0")
        self.assertEqual(LLMReviewerV26.name, "alma-llm-reviewer-v26")

    def test_frozen_files_byte_identical(self):
        agent_dir = ROOT / "agent"
        for name, expected in FROZEN_V26.items():
            self.assertEqual(
                _sha256(agent_dir / name), expected, f"{name} changed"
            )
        for name, expected in FROZEN_ARTIFACTS.items():
            self.assertEqual(
                _sha256(ROOT / name), expected, f"{name} changed"
            )


class AbsenceLoadingTests(unittest.TestCase):
    def test_committed_artifact_loads_and_verifies(self):
        block, sha, version = load_absence_block(ABSENCE_ARTIFACT)
        manifest = json.loads(ABSENCE_MANIFEST.read_text())
        self.assertEqual(block, extract_absence_block(
            ABSENCE_ARTIFACT.read_text()))
        self.assertEqual(
            sha, "be712a35ba052806c51622bd861e5bd8fa57b44a68b038221651c"
                 "8c8b913fb2f")
        self.assertEqual(sha, hashlib.sha256(
            block.encode("utf-8")).hexdigest())
        self.assertEqual(len(block), 8427)
        self.assertEqual(version, "alma-absence-context/1.0")
        self.assertEqual(manifest["corpus"]["absent"], 286)

    def test_reviewer_loads_both_memories_by_default(self):
        reviewer = _reviewer26()
        self.assertEqual(reviewer.lessons_block_chars, 9052)
        self.assertEqual(
            reviewer.lessons_sha256,
            "2cdb32ced88785164491bda5f9cda72121b2be048ec18c7b3f236fa17a5bae6b")
        self.assertEqual(reviewer.absence_block, extract_absence_block(
            ABSENCE_ARTIFACT.read_text()))
        self.assertEqual(
            reviewer.absence_sha256,
            "be712a35ba052806c51622bd861e5bd8fa57b44a68b038221651c"
            "8c8b913fb2f")
        self.assertEqual(reviewer.absence_version,
                         "alma-absence-context/1.0")
        self.assertEqual(reviewer.absence_block_chars, 8427)

    def test_tampered_absence_artifact_refused_at_construction(self):
        text = ABSENCE_ARTIFACT.read_text()
        marker = text.index("ABSENCE-BLOCK-BEGIN")
        tampered = text[:marker] + text[marker:].replace(
            "286 were never claimed", "287 were never claimed", 1)
        self.assertNotEqual(tampered, text)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CONTEXTO-AUSENCIAS.md"
            path.write_text(tampered)
            with self.assertRaises(RealLLMRefused):
                _reviewer26(absence_path=path)

    def test_missing_and_unmarked_absence_artifacts_refused(self):
        with self.assertRaises(RealLLMRefused):
            _reviewer26(absence_path=ROOT / "no-such-file.md")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain.md"
            path.write_text("# no markers, no hash\n")
            with self.assertRaises(RealLLMRefused):
                _reviewer26(absence_path=path)

    def test_tampered_lessons_artifact_still_refused(self):
        # The v2.5's fail-closed keeps binding in the v2.6: each
        # block refuses on its own side.
        text = LESSONS_ARTIFACT.read_text()
        marker = text.index("LESSONS-BLOCK-BEGIN")
        tampered = text[:marker] + text[marker:].replace(
            "32 of 166", "33 of 166", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CONTEXTO-LECCIONES.md"
            path.write_text(tampered)
            with self.assertRaises(RealLLMRefused):
                _reviewer26(lessons_path=path)

    def test_direct_block_injection(self):
        reviewer = _reviewer26(absence_block="SYNTHETIC ABSENCES")
        self.assertEqual(reviewer.absence_block, "SYNTHETIC ABSENCES")
        self.assertEqual(
            reviewer.absence_sha256,
            hashlib.sha256(b"SYNTHETIC ABSENCES").hexdigest())


class PromptInjectionTests(unittest.TestCase):
    def setUp(self):
        self.r26 = LLMReviewerV26.from_env(
            armed_env(), CONFIG_V14, transport=EmissionTransport())
        self.r25 = LLMReviewerV25.from_env(
            armed_env(), CONFIG_V14, transport=EmissionTransport())
        self.r24 = LLMReviewerV24.from_env(
            armed_env(), CONFIG_V14, transport=EmissionTransport())

    def _expected_system(self, base_system: str) -> str:
        return (
            base_system
            + "\n\n" + LESSONS_INJECTION_HEADER + "\n"
            + self.r26.lessons_block
            + "\n\n" + ABSENCE_INJECTION_HEADER + "\n"
            + self.r26.absence_block
        )

    def test_deep_payload_carries_both_blocks_verbatim_in_order(self):
        for pass_name in ("sql_injection", "correctness"):
            p26 = self.r26.build_deep_payload(pass_name, "D", "C")
            p24 = self.r24.build_deep_payload(pass_name, "D", "C")
            s26 = str(p26["messages"][0]["content"])
            s24 = str(p24["messages"][0]["content"])
            self.assertEqual(s26, self._expected_system(s24))
            # Each block exactly once; lessons before absences.
            self.assertEqual(s26.count(self.r26.lessons_block), 1)
            self.assertEqual(s26.count(self.r26.absence_block), 1)
            self.assertLess(s26.index(self.r26.lessons_block),
                            s26.index(self.r26.absence_block))
            # User content untouched.
            self.assertEqual(p26["messages"][1], p24["messages"][1])

    def test_fallback_payload_carries_both_blocks_verbatim(self):
        selected = [("category", "correctness")]
        p26 = self.r26.build_fallback_payload(selected, "D")
        p24 = self.r24.build_fallback_payload(selected, "D")
        s26 = str(p26["messages"][0]["content"])
        s24 = str(p24["messages"][0]["content"])
        self.assertEqual(s26, self._expected_system(s24))
        self.assertEqual(p26["messages"][1], p24["messages"][1])

    def test_selection_payload_byte_identical(self):
        p26 = self.r26.build_selection_payload("D")
        self.assertEqual(p26, self.r24.build_selection_payload("D"))
        self.assertEqual(p26, self.r25.build_selection_payload("D"))
        system = str(p26["messages"][0]["content"])
        self.assertNotIn(self.r26.lessons_block, system)
        self.assertNotIn(self.r26.absence_block, system)


class CombinedBudgetTests(unittest.TestCase):
    """ADENDA-V26.md §4: the combined injection, computed by
    program with the line's own estimator, fits both declared
    criteria — and no shrink was applied to either artifact."""

    def test_combined_budget_matches_paper_and_fits(self):
        reviewer = _reviewer26()
        combined_chars = (reviewer.lessons_block_chars
                          + reviewer.absence_block_chars)
        self.assertEqual(combined_chars, 17479)
        # Criterion 1: sum of the two standing per-block caps.
        self.assertLessEqual(combined_chars, 9600 + 9600)
        combined_tokens = _estimate_tokens(
            reviewer.lessons_block + reviewer.absence_block)
        self.assertEqual(combined_tokens, 4994)
        injected = (
            "\n\n" + LESSONS_INJECTION_HEADER + "\n"
            + reviewer.lessons_block
            + "\n\n" + ABSENCE_INJECTION_HEADER + "\n"
            + reviewer.absence_block
        )
        self.assertEqual(len(injected), 17803)
        self.assertEqual(_estimate_tokens(injected), 5087)
        # Criterion 2: 10% of the line's 60,000-token budget.
        self.assertLessEqual(_estimate_tokens(injected), 6000)


def _run_review26(lines, transport, config=CONFIG_V14, path=PATH):
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        diff_text = make_diff(path, lines)
        reviewer = LLMReviewerV26.from_env(
            armed_env(), config, transport=transport)
        emitted = reviewer.review(
            diff_text=diff_text,
            diff=parse_unified_diff(diff_text),
            config=config,
            repo_root=repo,
        )
        return emitted, reviewer, diff_text, transport


class EndToEndDryTests(unittest.TestCase):
    def test_citable_claim_born_tagged_conforming_accepted(self):
        transport = EmissionTransport(
            marks=["correctness"],
            deep={"correctness": {"findings": [_finding()],
                                  "unverifiable": []}})
        emitted, reviewer, diff_text, _t = _run_review26(LINES, transport)
        self.assertEqual(len(emitted), 1)
        candidate = emitted[0]
        self.assertEqual(candidate.producer, "alma-llm-reviewer-v26")
        self.assertEqual(candidate.rule_id, "llm_v26_correctness")
        self.assertTrue(normalize_claim(candidate).conforming)
        result = AlmaGateV150().validate(
            tuple(emitted), parse_unified_diff(diff_text),
            "alma-reviewer")
        self.assertEqual([e.status for e in result.ledger], ["accepted"])
        info = reviewer.last_run_info.to_dict()
        self.assertEqual(info["reviewer_version"], "llm-reviewer/2.6.0")
        self.assertEqual(info["lessons_sha256"], reviewer.lessons_sha256)
        self.assertEqual(info["lessons_version"],
                         "alma-lessons-context/1.0")
        self.assertEqual(info["lessons_block_chars"], 9052)
        self.assertEqual(info["absence_sha256"], reviewer.absence_sha256)
        self.assertEqual(info["absence_version"],
                         "alma-absence-context/1.0")
        self.assertEqual(info["absence_block_chars"], 8427)
        # BOTH blocks really entered the deep call that produced this.
        deep_systems = [
            str(c["messages"][0]["content"]) for c in transport.calls
            if pass_name_of(c) == "correctness"
        ]
        self.assertTrue(deep_systems)
        self.assertTrue(all(
            reviewer.lessons_block in s and reviewer.absence_block in s
            for s in deep_systems))

    def test_no_pattern_finding_settles_in_ledger(self):
        # Gate-form amendment (ADENDA-PUERTA-FORMA-20261027):
        # same declared fixture change as the v2.5 test — a
        # claim with nothing asserted and nothing extractable;
        # the default _finding() now survives origin by
        # extraction and no longer settles.
        finding = _finding(
            start_line=2,
            end_line=2,
            message="The function ignores its argument.",
            evidence=[LINES[1]],
        )
        del finding["pattern"]
        transport = EmissionTransport(
            marks=["correctness"],
            deep={"correctness": {"findings": [finding],
                                  "unverifiable": []}})
        emitted, reviewer, _d, _t = _run_review26(LINES, transport)
        self.assertEqual(emitted, [])
        info = reviewer.last_run_info.to_dict()
        self.assertEqual(
            info["production_ledger_by_code"],
            {"sin_patron_concreto_en_el_reclamo": 1})

    def test_guard_refuses_before_calling(self):
        transport = EmissionTransport(marks=["correctness"])
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / PATH).parent.mkdir(parents=True)
            (repo / PATH).write_text("\n".join(LINES) + "\n")
            diff_text = make_diff(PATH, LINES)
            reviewer = LLMReviewerV26.from_env(
                armed_env(RB_MAX_SPEND_USD="0.0001"), CONFIG_V14,
                transport=transport)
            with self.assertRaises(RealLLMRefused):
                reviewer.review(
                    diff_text=diff_text,
                    diff=parse_unified_diff(diff_text),
                    config=CONFIG_V14,
                    repo_root=repo)
        self.assertEqual(transport.calls, [])


class BatteryDryRunV26Tests(unittest.TestCase):
    """The frozen semaphore battery through LLMReviewerV26.review()
    — 8 cases x 2 gate configs = 16 runs, the v2.5 equivalent,
    with both memory blocks in every deep payload."""

    def test_battery_16_of_16_without_refusals(self):
        fixtures = ROOT / "fixtures_semaforo"
        cases = sorted(p.name for p in fixtures.iterdir() if p.is_dir())
        self.assertEqual(len(cases), 8)
        runs = 0
        for case in cases:
            directory, diff_text, _pr, truth, planted = \
                load_semaforo_case(case)
            token = _citable_token(planted["evidence"][0])
            for config in (CONFIG_V13, CONFIG_V14):
                with self.subTest(case=case, gate=config["gate"]):
                    transport = BatteryTransport(planted, token)
                    reviewer = LLMReviewerV26.from_env(
                        armed_env(), config, transport=transport)
                    emitted = reviewer.review(
                        diff_text=diff_text,
                        diff=parse_unified_diff(diff_text),
                        config=config,
                        repo_root=directory / "repo",
                    )
                    info = reviewer.last_run_info.to_dict()
                    self.assertEqual(
                        info["reviewer_version"], "llm-reviewer/2.6.0")
                    self.assertEqual(info["calls"], 2)
                    self.assertEqual(
                        info["selection_specialty"],
                        [truth["planted_class"]])
                    self.assertEqual(info["selection_general"], [])
                    self.assertIsNone(info["degradation"])
                    self.assertEqual(info["production_ledger"], [])
                    self.assertEqual(len(emitted), 1)
                    self.assertEqual(emitted[0].producer,
                                     "alma-llm-reviewer-v26")
                    self.assertTrue(
                        normalize_claim(emitted[0]).conforming)
                    deep_systems = [
                        str(c["messages"][0]["content"])
                        for c in transport.calls
                        if pass_name_of(c) != "selection"
                    ]
                    self.assertTrue(deep_systems)
                    self.assertTrue(all(
                        reviewer.lessons_block in s
                        and reviewer.absence_block in s
                        for s in deep_systems))
                    runs += 1
        self.assertEqual(runs, 16)


if __name__ == "__main__":
    unittest.main()
