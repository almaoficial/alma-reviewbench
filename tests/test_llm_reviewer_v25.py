"""Reviewer v2.5 tests — paper PREREGISTRO-MEMORIA-LECCIONES §6.

What is verified dry (US$0, scripted transports only):

- identity and the frozen line: gates 1.0.0–1.5.0,
  claim_contract, birth_shaper, v2.3 and v2.4 byte-identical;
- fail-closed lessons loading: the committed artifact loads and
  its hash verifies; a tampered artifact, a missing file, an
  artifact without markers all raise RealLLMRefused at
  construction, before any call can exist;
- faithful injection: the lessons block appears VERBATIM (after
  the fixed header) in the armed deep and fallback system
  prompts; the user content is untouched; the selection payload
  is byte-identical to the v2.4's;
- the v2.5 provenance: emitted candidates carry
  producer/rule_id v25 tags through the shaping stage, and the
  run info carries lessons_sha256 / lessons_version /
  lessons_block_chars with reviewer_version 2.5.0;
- the inherited discipline does not move: a valid citable claim
  is born conforming and accepted by gate 1.5.0; a no-pattern
  finding settles in the production ledger under
  `sin_patron_concreto_en_el_reclamo`; the guard refuses before
  calling;
- the frozen semaphore battery driven through
  LLMReviewerV25.review(): 8 cases x 2 gate configs = 16/16,
  with the lessons block present in every deep payload.

No test here measures any EFFECT of the lessons on real
production: that is the paper's honest caveat (§4).
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

from agent.alma_gate_v150 import AlmaGateV150  # noqa: E402
from agent.claim_contract import normalize_claim  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.lessons_compiler import extract_block  # noqa: E402
from agent.llm_reviewer import LLMSettings, RealLLMRefused  # noqa: E402
from agent.llm_reviewer_v24 import LLMReviewerV24  # noqa: E402
from agent.llm_reviewer_v25 import (  # noqa: E402
    LESSONS_INJECTION_HEADER,
    REVIEWER_VERSION,
    LLMReviewerV25,
    load_lessons_block,
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

FROZEN_V25 = dict(
    FROZEN_FILE_SHA256,
    **{
        "llm_reviewer_v24.py":
            "f9d3578eed4fce63b85b37cac44ec86023f7a46e5b7da85e7a9ffb3400640a1d",
    },
)

ARTIFACT = ROOT / "CONTEXTO-LECCIONES.md"
MANIFEST = ROOT / "CONTEXTO-LECCIONES.provenance.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reviewer25(transport=None, **kwargs):
    return LLMReviewerV25(
        LLMSettings.from_env(armed_env(), CONFIG_V14),
        transport=transport or EmissionTransport(),
        **kwargs,
    )


class IdentityAndFrozenTests(unittest.TestCase):
    def test_reviewer_identity(self):
        self.assertEqual(REVIEWER_VERSION, "llm-reviewer/2.5.0")
        self.assertEqual(LLMReviewerV25.name, "alma-llm-reviewer-v25")

    def test_frozen_files_byte_identical(self):
        agent_dir = ROOT / "agent"
        for name, expected in FROZEN_V25.items():
            self.assertEqual(
                _sha256(agent_dir / name), expected, f"{name} changed"
            )


class LessonsLoadingTests(unittest.TestCase):
    def test_committed_artifact_loads_and_verifies(self):
        block, sha, version = load_lessons_block(ARTIFACT)
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(block, extract_block(ARTIFACT.read_text()))
        self.assertEqual(sha, hashlib.sha256(
            block.encode("utf-8")).hexdigest())
        self.assertEqual(version, "alma-lessons-context/1.0")
        self.assertEqual(manifest["corpus"]["claims"], 166)

    def test_reviewer_loads_lessons_by_default(self):
        reviewer = _reviewer25()
        block, sha, _version = load_lessons_block(ARTIFACT)
        self.assertEqual(reviewer.lessons_block, block)
        self.assertEqual(reviewer.lessons_sha256, sha)
        self.assertEqual(reviewer.lessons_version,
                         "alma-lessons-context/1.0")
        self.assertEqual(reviewer.lessons_block_chars, len(block))

    def test_tampered_artifact_refused_at_construction(self):
        text = ARTIFACT.read_text()
        marker = text.index("LESSONS-BLOCK-BEGIN")
        tampered = text[:marker] + text[marker:].replace(
            "32 of 166", "33 of 166", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CONTEXTO-LECCIONES.md"
            path.write_text(tampered)
            with self.assertRaises(RealLLMRefused):
                _reviewer25(lessons_path=path)

    def test_missing_and_unmarked_artifacts_refused(self):
        with self.assertRaises(RealLLMRefused):
            _reviewer25(lessons_path=ROOT / "no-such-file.md")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain.md"
            path.write_text("# no markers, no hash\n")
            with self.assertRaises(RealLLMRefused):
                _reviewer25(lessons_path=path)

    def test_direct_block_injection(self):
        reviewer = _reviewer25(lessons_block="SYNTHETIC LESSONS")
        self.assertEqual(reviewer.lessons_block, "SYNTHETIC LESSONS")
        self.assertEqual(
            reviewer.lessons_sha256,
            hashlib.sha256(b"SYNTHETIC LESSONS").hexdigest())


class PromptInjectionTests(unittest.TestCase):
    def setUp(self):
        self.r25 = LLMReviewerV25.from_env(
            armed_env(), CONFIG_V14, transport=EmissionTransport())
        self.r24 = LLMReviewerV24.from_env(
            armed_env(), CONFIG_V14, transport=EmissionTransport())

    def test_deep_payload_carries_block_verbatim(self):
        for pass_name in ("sql_injection", "correctness"):
            p25 = self.r25.build_deep_payload(pass_name, "D", "C")
            p24 = self.r24.build_deep_payload(pass_name, "D", "C")
            s25 = str(p25["messages"][0]["content"])
            s24 = str(p24["messages"][0]["content"])
            self.assertEqual(
                s25,
                s24 + "\n\n" + LESSONS_INJECTION_HEADER + "\n"
                + self.r25.lessons_block)
            self.assertIn(self.r25.lessons_block, s25)
            # User content untouched.
            self.assertEqual(p25["messages"][1], p24["messages"][1])

    def test_fallback_payload_carries_block_verbatim(self):
        selected = [("category", "correctness")]
        p25 = self.r25.build_fallback_payload(selected, "D")
        p24 = self.r24.build_fallback_payload(selected, "D")
        s25 = str(p25["messages"][0]["content"])
        s24 = str(p24["messages"][0]["content"])
        self.assertEqual(
            s25,
            s24 + "\n\n" + LESSONS_INJECTION_HEADER + "\n"
            + self.r25.lessons_block)
        self.assertEqual(p25["messages"][1], p24["messages"][1])

    def test_selection_payload_byte_identical(self):
        p25 = self.r25.build_selection_payload("D")
        p24 = self.r24.build_selection_payload("D")
        self.assertEqual(p25, p24)
        self.assertNotIn(self.r25.lessons_block,
                         str(p25["messages"][0]["content"]))


def _run_review25(lines, transport, config=CONFIG_V14, path=PATH):
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        diff_text = make_diff(path, lines)
        reviewer = LLMReviewerV25.from_env(
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
        emitted, reviewer, diff_text, _t = _run_review25(LINES, transport)
        self.assertEqual(len(emitted), 1)
        candidate = emitted[0]
        self.assertEqual(candidate.producer, "alma-llm-reviewer-v25")
        self.assertEqual(candidate.rule_id, "llm_v25_correctness")
        self.assertTrue(normalize_claim(candidate).conforming)
        result = AlmaGateV150().validate(
            tuple(emitted), parse_unified_diff(diff_text),
            "alma-reviewer")
        self.assertEqual([e.status for e in result.ledger], ["accepted"])
        info = reviewer.last_run_info.to_dict()
        self.assertEqual(info["reviewer_version"], "llm-reviewer/2.5.0")
        self.assertEqual(info["lessons_sha256"], reviewer.lessons_sha256)
        self.assertEqual(info["lessons_version"],
                         "alma-lessons-context/1.0")
        self.assertEqual(info["lessons_block_chars"],
                         len(reviewer.lessons_block))
        # The block really entered the deep call that produced this.
        deep_systems = [
            str(c["messages"][0]["content"]) for c in transport.calls
            if pass_name_of(c) == "correctness"
        ]
        self.assertTrue(deep_systems)
        self.assertTrue(all(reviewer.lessons_block in s
                            for s in deep_systems))

    def test_no_pattern_finding_settles_in_ledger(self):
        finding = _finding()
        del finding["pattern"]
        transport = EmissionTransport(
            marks=["correctness"],
            deep={"correctness": {"findings": [finding],
                                  "unverifiable": []}})
        emitted, reviewer, _d, _t = _run_review25(LINES, transport)
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
            reviewer = LLMReviewerV25.from_env(
                armed_env(RB_MAX_SPEND_USD="0.0001"), CONFIG_V14,
                transport=transport)
            with self.assertRaises(RealLLMRefused):
                reviewer.review(
                    diff_text=diff_text,
                    diff=parse_unified_diff(diff_text),
                    config=CONFIG_V14,
                    repo_root=repo)
        self.assertEqual(transport.calls, [])


class BatteryDryRunV25Tests(unittest.TestCase):
    """The frozen semaphore battery through LLMReviewerV25.review()
    — 8 cases x 2 gate configs = 16 runs, the v2.4 equivalent."""

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
                    reviewer = LLMReviewerV25.from_env(
                        armed_env(), config, transport=transport)
                    emitted = reviewer.review(
                        diff_text=diff_text,
                        diff=parse_unified_diff(diff_text),
                        config=config,
                        repo_root=directory / "repo",
                    )
                    info = reviewer.last_run_info.to_dict()
                    self.assertEqual(
                        info["reviewer_version"], "llm-reviewer/2.5.0")
                    self.assertEqual(info["calls"], 2)
                    self.assertEqual(
                        info["selection_specialty"],
                        [truth["planted_class"]])
                    self.assertEqual(info["selection_general"], [])
                    self.assertIsNone(info["degradation"])
                    self.assertEqual(info["production_ledger"], [])
                    self.assertEqual(len(emitted), 1)
                    self.assertEqual(emitted[0].producer,
                                     "alma-llm-reviewer-v25")
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
                        for s in deep_systems))
                    runs += 1
        self.assertEqual(runs, 16)


if __name__ == "__main__":
    unittest.main()
