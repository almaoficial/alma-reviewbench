"""Reviewer v2.3 tests: generalized selection + deep passes per mark.

Pre-registration: PREREGISTRO-REVIEWBENCH-V23.md — §3a generalized
selection (nine public categories + the gate's classes as specialty,
one priority list, shared cap of 5), §3b deep passes (class mark ->
the v2's class pass; category mark -> a general pass of that category
on the same template), §3c the inherited two-stage guard and
degradation rule, §3d arm parity (base gate=v13 emits everything;
ALMA gate=v14 judges specialty findings and holds general findings
as needs_validation, never emitted), §7 economy at planning prices.

Everything runs on scripted transports: no real model call, US$0.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused, _estimate_tokens  # noqa: E402
from agent.llm_reviewer_v2 import LLMReviewerV2  # noqa: E402
from agent.llm_reviewer_v23 import (  # noqa: E402
    CATEGORY_GUIDANCE,
    GENERAL_CATEGORIES,
    MAX_DEEP_PASSES,
    LLMReviewerV23,
)
from agent.main import run_agent  # noqa: E402
from test_gate_v11 import armed_env as _armed_env  # noqa: E402
from test_llm_reviewer_v22 import (  # noqa: E402
    load_semaforo_case,
    make_repo,
    run_case,
)

FIXTURES_SEMAFORO = ROOT / "fixtures_semaforo"
SEMAFORO_CASES = sorted(p.name for p in FIXTURES_SEMAFORO.iterdir() if p.is_dir())
# Reported cost of one scripted call under the harness usage
# {100 prompt, 10 completion} at planning prices (15/75 per Mtok).
SELECTION_COST = 100 * 15 / 1_000_000 + 10 * 75 / 1_000_000

CONFIG_ALMA_V14 = {
    "model": "gpt-5.6-sol",
    "effort": "medium",
    "governance": "alma",
    "reviewer": "v23",
    "gate": "v14",
}
CONFIG_BASE_V13 = dict(CONFIG_ALMA_V14, governance="base", gate="v13")
CONFIG_ALMA_V13 = dict(CONFIG_ALMA_V14, gate="v13")


def armed_env(**overrides):
    overrides.setdefault("RB_MAX_SPEND_USD", "6.50")
    return _armed_env(**overrides)


def pass_name_of(payload) -> str:
    user = str(payload["messages"][1]["content"])
    first = user.splitlines()[0] if user.splitlines() else ""
    return first.removeprefix("PASS: ").strip()


class GeneralizedTransport:
    """Scripted transport for the v2.3 reviewer: the selection pass
    answers with `mark` entries; each deep pass (named by its PASS
    line: a class or a category) answers with its scripted findings;
    the fallback pass likewise."""

    USAGE = {"prompt_tokens": 100, "completion_tokens": 10}

    def __init__(self, marks=(), deep_findings=None, fallback_findings=()):
        self.marks = list(marks)
        self.deep_findings = dict(deep_findings or {})
        self.fallback_findings = list(fallback_findings)
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
        name = pass_name_of(payload)
        if name == "selection":
            content = {
                "candidates": [
                    {"mark": mark, "reason": "scripted mark"} for mark in self.marks
                ]
            }
        elif name == "fallback_single":
            content = {"findings": self.fallback_findings}
        else:
            content = {"findings": self.deep_findings.get(name, [])}
        body = {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": self.USAGE,
        }
        return 200, json.dumps(body).encode("utf-8")

    def pass_names(self) -> list[str]:
        return [pass_name_of(call["payload"]) for call in self.calls]


class HeavySelectionTransport(GeneralizedTransport):
    """The selection reports having used most of its output budget
    (completion 4000 of the v2.3.1 ceiling) — the post-fix world
    the no-deep-affordable scenario lives in."""

    USAGE = {"prompt_tokens": 100, "completion_tokens": 4000}


class SelectionTests(unittest.TestCase):
    def test_mixed_marks_share_one_cap_and_settle_per_family(self):
        directory, diff_text, pr, truth, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        marks = [
            "correctness",               # category
            "sql_injection",             # class
            "security",                  # category
            "weak_hash",                 # class
            "testing",                   # category — 5th, last admitted
            "performance",               # category — overflow
            "not_a_mark",                # unknown -> counted, never run
            "sql_injection",             # duplicate -> first wins
        ]
        transport = GeneralizedTransport(marks=marks)
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V14, armed_env(), transport
        )
        info = result.llm_run_info
        self.assertEqual(info["reviewer_version"], "llm-reviewer/2.3.2")
        self.assertEqual(info["gate_version"], "alma-evidence-gate/1.4.0")
        self.assertEqual(
            info["selection_candidates"],
            ["correctness", "sql_injection", "security", "weak_hash", "testing", "performance"],
        )
        self.assertEqual(
            info["selection_selected"], info["selection_candidates"][:MAX_DEEP_PASSES]
        )
        self.assertEqual(info["selection_overflow"], ["performance"])
        self.assertEqual(
            info["selection_general"], ["correctness", "security", "testing"]
        )
        self.assertEqual(
            info["selection_specialty"], ["sql_injection", "weak_hash"]
        )
        self.assertEqual(info["selection_unknown_marks"], 1)
        self.assertIsNone(info["degradation"])
        self.assertEqual(
            transport.pass_names(), ["selection"] + info["selection_selected"]
        )
        self.assertEqual(info["calls"], 1 + MAX_DEEP_PASSES)

    def test_selection_marks_nothing_runs_no_deep_pass(self):
        directory, diff_text, pr, _, _ = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        transport = GeneralizedTransport(marks=[])
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V14, armed_env(), transport
        )
        info = result.llm_run_info
        self.assertEqual(transport.pass_names(), ["selection"])
        self.assertEqual(info["selection_selected"], [])
        self.assertEqual(info["selection_general"], [])
        self.assertEqual(info["selection_specialty"], [])
        self.assertEqual(result.candidates, [])
        self.assertIsNone(info["degradation"])

    def test_selection_payload_is_diff_only_and_lists_both_families(self):
        reviewer = LLMReviewerV23.from_env(
            armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
        )
        payload = reviewer.build_selection_payload("THE-DIFF-TEXT")
        system = str(payload["messages"][0]["content"])
        user = str(payload["messages"][1]["content"])
        self.assertEqual(len(GENERAL_CATEGORIES), 9)
        for name in GENERAL_CATEGORIES:
            self.assertIn(f"--- CATEGORY {name} ---", system)
        from agent.alma_gate_v13 import KNOWN_CLAIM_TYPES_V13

        self.assertEqual(len(KNOWN_CLAIM_TYPES_V13), 19)
        for claim_type in KNOWN_CLAIM_TYPES_V13:
            self.assertIn(f"--- CLASS {claim_type} ---", system)
        self.assertIn("CITATION (required by the gate)", system)
        self.assertIn("THE-DIFF-TEXT", user)
        self.assertNotIn("full contents at PR head", user)
        # Fix v2.3.1: the selection ceiling defaults to 4096 (was
        # 1024 in v2.3.0 — the budget run #296 died under; the 1024
        # pin stays reproducible, see test_llm_reviewer_v231.py).
        self.assertEqual(payload["max_completion_tokens"], 4096)
        self.assertNotIn("temperature", payload)
        self.assertNotIn("max_tokens", payload)

    def test_class_deep_payload_is_the_v2_payload_byte_for_byte(self):
        env = armed_env()
        v23 = LLMReviewerV23.from_env(env, CONFIG_ALMA_V13, transport=GeneralizedTransport())
        v2 = LLMReviewerV2.from_env(env, CONFIG_ALMA_V13, transport=GeneralizedTransport())
        for claim_type in ("sql_injection", "weak_hash", "race_condition"):
            with self.subTest(claim_type=claim_type):
                self.assertEqual(
                    v23.build_deep_payload(claim_type, "DIFF", "CONTEXT"),
                    v2.build_payload(claim_type, "DIFF", "CONTEXT"),
                )

    def test_category_deep_payload_uses_the_same_template(self):
        reviewer = LLMReviewerV23.from_env(
            armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
        )
        payload = reviewer.build_deep_payload("correctness", "DIFF", "CONTEXT")
        system = str(payload["messages"][0]["content"])
        self.assertIn("exactly one class of defect: correctness", system)
        self.assertIn(CATEGORY_GUIDANCE["correctness"], system)
        self.assertIn("Report only defects of this category.", system)
        self.assertIn("CONTEXT", str(payload["messages"][1]["content"]))
        self.assertEqual(payload["max_completion_tokens"], 4096)

    def test_gate_v14_resolves_and_unknown_gate_refuses(self):
        reviewer = LLMReviewerV23.from_env(
            armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
        )
        self.assertEqual(len(reviewer.claim_types), 19)
        self.assertEqual(reviewer.gate_version, "alma-evidence-gate/1.4.0")
        with self.assertRaises(RealLLMRefused):
            LLMReviewerV23.from_env(
                armed_env(),
                dict(CONFIG_ALMA_V14, gate="v9"),
                transport=GeneralizedTransport(),
            )


class GuardEstimateTests(unittest.TestCase):
    """§7 economy at planning prices (US$15/M in, US$75/M out):
    the anchor PR is the v1 measurement — a deep pass whose total
    estimated input is 41,160 tokens."""

    def _pad_until(self, build, target_tokens: int) -> dict:
        filler = "filler = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'\n"
        text = ""
        payload = build(text)
        while True:
            estimated = sum(
                _estimate_tokens(str(m["content"])) for m in payload["messages"]
            )
            if estimated >= target_tokens:
                return payload
            text += filler * 200
            payload = build(text)

    def _reviewer(self):
        return LLMReviewerV23.from_env(
            armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
        )

    def test_anchor_plan_fits_the_brake(self):
        reviewer = self._reviewer()
        anchor_diff = "diff --git a/app/x.py b/app/x.py\n"
        deep = reviewer.worst_case_estimate(
            self._pad_until(
                lambda context: reviewer.build_deep_payload(
                    "sql_injection", anchor_diff, context
                ),
                41_160,
            )
        )
        deep_general = reviewer.worst_case_estimate(
            self._pad_until(
                lambda context: reviewer.build_deep_payload(
                    "correctness", anchor_diff, context
                ),
                41_160,
            )
        )
        # One deep pass on the anchor: the paper's ~US$0.95, for a
        # class pass and a category pass alike.
        self.assertGreater(deep, 0.70)
        self.assertLess(deep, 1.40)
        self.assertGreater(deep_general, 0.70)
        self.assertLess(deep_general, 1.40)
        # The generalized selection over the anchor-sized diff alone:
        # re-derived under the fix v2.3.1 ceiling (4096): worst case
        # US$0.9653 (was US$0.7349 at the v2.3.0 ceiling of 1024 —
        # the delta is exactly 3072 output tokens x US$75/Mtok =
        # US$0.2304).  The full anchor plan still fits the brake.
        selection = reviewer.worst_case_estimate(
            self._pad_until(
                lambda diff: reviewer.build_selection_payload(diff), 41_160
            )
        )
        self.assertGreater(selection, 0.90)
        self.assertLess(selection, 1.00)
        total = selection + MAX_DEEP_PASSES * deep
        self.assertLess(total, 6.50)

    def test_saturated_context_enters_degradation_territory(self):
        reviewer = self._reviewer()
        anchor_diff = "diff --git a/app/x.py b/app/x.py\n"
        deep_sat = reviewer.worst_case_estimate(
            self._pad_until(
                lambda context: reviewer.build_deep_payload(
                    "sql_injection", anchor_diff, context
                ),
                60_000,
            )
        )
        selection_sat = reviewer.worst_case_estimate(
            self._pad_until(
                lambda diff: reviewer.build_selection_payload(diff), 60_000
            )
        )
        # The paper's saturated plan (~US$6.90 with its selection
        # estimate) exceeds the US$6.50 brake: exactly 4 deep passes
        # fit after the selection — the 5th is declared degradation.
        self.assertGreater(selection_sat + MAX_DEEP_PASSES * deep_sat, 6.50)
        planned = selection_sat
        admitted = 0
        while planned + deep_sat <= 6.50:
            planned += deep_sat
            admitted += 1
        self.assertEqual(admitted, 4)


def planned_worsts(reviewer, diff_text, repo, marks):
    """(deep worst per mark, fallback worst) from the reviewer's own
    arithmetic, rendering the context exactly as review() does."""

    from agent.llm_reviewer_v2 import _load_head_files, _render_context

    head_files, _ = _load_head_files(repo, ["app/big.py"])
    context_text, _, _, _ = _render_context(
        head_files, ["app/big.py"], reviewer.context_token_budget
    )
    deeps = {
        name: reviewer.worst_case_estimate(
            reviewer.build_deep_payload(name, diff_text, context_text)
        )
        for name in marks
    }
    kinds = [
        ("category" if name in GENERAL_CATEGORIES else "class", name)
        for name in marks
    ]
    fallback = reviewer.worst_case_estimate(
        reviewer.build_fallback_payload(kinds, diff_text)
    )
    return deeps, fallback


class DegradationTests(unittest.TestCase):
    def test_degradation_drops_low_priority_marks_and_declares(self):
        import tempfile

        marks = ["correctness", "weak_hash", "sql_injection", "reliability"]
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, _ = make_repo(tmp)
            probe = LLMReviewerV23.from_env(
                armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
            )
            deeps, _ = planned_worsts(probe, diff_text, repo, marks)
            worst = deeps[marks[0]]
            cap = SELECTION_COST + 2.5 * worst
            transport = GeneralizedTransport(marks=marks)
            reviewer = LLMReviewerV23.from_env(
                armed_env(RB_MAX_SPEND_USD=f"{cap:.4f}"),
                CONFIG_ALMA_V14,
                transport=transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=parse_unified_diff(diff_text),
                config=CONFIG_ALMA_V14,
                mode="alma",
                repo_root=repo,
            )
            self.assertEqual(candidates, [])
            info = reviewer.last_run_info
            self.assertEqual(
                transport.pass_names(), ["selection", marks[0], marks[1]]
            )
            self.assertEqual(
                info.degradation,
                {
                    "reason": "spend_cap",
                    "deep_passes_planned": 4,
                    "deep_passes_run": 2,
                    "deep_passes_dropped": marks[2:],
                    "fallback_single_pass": False,
                },
            )

    def test_fallback_single_pass_when_no_deep_fits(self):
        import tempfile

        marks = ["correctness", "weak_hash"]
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, lines = make_repo(tmp)
            probe = LLMReviewerV23.from_env(
                armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
            )
            deeps, fallback_worst = planned_worsts(probe, diff_text, repo, marks)
            self.assertLess(fallback_worst, deeps[marks[0]])
            cap = SELECTION_COST + (deeps[marks[0]] + fallback_worst) / 2
            finding = {
                "file": "app/big.py",
                "start_line": 10,
                "end_line": 10,
                "claim_type": "correctness",
                "message": "wrong digest update (scripted fallback echo)",
                "evidence": [lines[9]],
            }
            transport = GeneralizedTransport(
                marks=marks, fallback_findings=[finding]
            )
            reviewer = LLMReviewerV23.from_env(
                armed_env(RB_MAX_SPEND_USD=f"{cap:.4f}"),
                CONFIG_ALMA_V14,
                transport=transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=parse_unified_diff(diff_text),
                config=CONFIG_ALMA_V14,
                mode="alma",
                repo_root=repo,
            )
            info = reviewer.last_run_info
            self.assertEqual(
                transport.pass_names(), ["selection", "fallback_single"]
            )
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0].claim_type, "correctness")
            self.assertEqual(candidates[0].producer, "alma-llm-reviewer-v23")
            self.assertEqual(candidates[0].rule_id, "llm_v23_correctness")
            self.assertEqual(
                info.degradation,
                {
                    "reason": "spend_cap",
                    "deep_passes_planned": 2,
                    "deep_passes_run": 0,
                    "deep_passes_dropped": marks,
                    "fallback_single_pass": True,
                },
            )

    def test_no_deep_pass_affordable_declares_and_emits_zero(self):
        directory, diff_text, pr, _, _ = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        probe = LLMReviewerV23.from_env(
            armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
        )
        selection_worst = probe.worst_case_estimate(
            probe.build_selection_payload(diff_text)
        )
        # Fix v2.3.1 scenario note: with the selection and deep
        # ceilings now equal (4096), a cap priced at the selection's
        # worst case would admit a small deep pass whenever the
        # selection's REPORTED cost is tiny — admission runs on the
        # reported cost.  The scenario therefore reports a
        # selection that used its budget (the post-fix world); the
        # declaration under test is unchanged.
        transport = HeavySelectionTransport(marks=["tls_verification_disabled"])
        result = run_case(
            directory,
            diff_text,
            pr,
            CONFIG_ALMA_V14,
            armed_env(RB_MAX_SPEND_USD=f"{selection_worst + 0.005:.4f}"),
            transport,
        )
        info = result.llm_run_info
        self.assertEqual(result.candidates, [])
        self.assertEqual(transport.pass_names(), ["selection"])
        self.assertEqual(
            info["degradation"],
            {
                "reason": "no_deep_pass_affordable",
                "deep_passes_planned": 1,
                "deep_passes_run": 0,
                "deep_passes_dropped": ["tls_verification_disabled"],
                "fallback_single_pass": False,
            },
        )

    def test_preflight_refuses_when_selection_alone_exceeds_cap(self):
        directory, diff_text, pr, _, _ = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        transport = GeneralizedTransport(marks=["tls_verification_disabled"])
        with self.assertRaises(RealLLMRefused) as caught:
            run_case(
                directory,
                diff_text,
                pr,
                CONFIG_ALMA_V14,
                armed_env(RB_MAX_SPEND_USD="0.01"),
                transport,
            )
        self.assertIn("selection pass", str(caught.exception))
        self.assertEqual(transport.calls, [])


class ArmBehaviorTests(unittest.TestCase):
    """§3d/§4: same reviewer, two gates.  Base (gate=v13) emits every
    anchor-verified candidate; ALMA (gate=v14) emits specialty
    findings the 1.4.0 accepts and HOLDS general findings as
    needs_validation — not emitted, not in the findings file, in the
    run's needs_validation section with their blockers."""

    def _general_finding(self, case="sem_03_tls_verification_disabled"):
        directory, diff_text, pr, truth, _ = load_semaforo_case(case)
        head_lines = (
            (directory / "repo" / truth["file"]).read_text(encoding="utf-8").splitlines()
        )
        finding = {
            "file": truth["file"],
            "start_line": truth["defect_line"],
            "end_line": truth["defect_line"],
            "claim_type": "correctness",
            "message": "the change computes the wrong thing (scripted)",
            "evidence": [head_lines[truth["defect_line"] - 1]],
        }
        return directory, diff_text, pr, truth, finding

    def test_alma_holds_general_finding_as_needs_validation(self):
        directory, diff_text, pr, truth, finding = self._general_finding()
        transport = GeneralizedTransport(
            marks=["correctness"], deep_findings={"correctness": [finding]}
        )
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V14, armed_env(), transport
        )
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].claim_type, "correctness")
        # Not emitted; not in the gate ledger; held with blockers.
        self.assertEqual(result.output["findings"], [])
        self.assertEqual(result.ledger, [])
        self.assertIsNotNone(result.needs_validation)
        self.assertEqual(len(result.needs_validation), 1)
        record = result.needs_validation[0]
        self.assertEqual(record["claim_type"], "correctness")
        self.assertEqual(
            [b["check"] for b in record["blockers"]],
            ["sin_regla_de_verificacion_en_puerta"],
        )
        self.assertNotIn("severity", json.dumps(record))
        self.assertEqual(record["validator_version"], "alma-evidence-gate/1.4.0")

    def test_base_arm_emits_the_same_general_finding(self):
        directory, diff_text, pr, truth, finding = self._general_finding()
        transport = GeneralizedTransport(
            marks=["correctness"], deep_findings={"correctness": [finding]}
        )
        result = run_case(
            directory,
            diff_text,
            pr,
            CONFIG_BASE_V13,
            armed_env(),
            transport,
            mode="base",
        )
        self.assertEqual(len(result.output["findings"]), 1)
        self.assertEqual(result.candidates[0].claim_type, "correctness")
        self.assertEqual(
            result.output["findings"][0]["file"], truth["file"]
        )
        self.assertIsNone(result.needs_validation)
        self.assertEqual(
            result.ledger[0]["validator_version"], "bypassed-base-arm"
        )

    def test_alma_specialty_finding_judged_by_gate_140(self):
        directory, diff_text, pr, truth, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        transport = GeneralizedTransport(
            marks=[truth["planted_class"]],
            deep_findings={truth["planted_class"]: [planted]},
        )
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V14, armed_env(), transport
        )
        self.assertEqual(len(result.output["findings"]), 1)
        accepted = [
            entry for entry in result.ledger if entry["status"] == "accepted"
        ]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(
            accepted[0]["validator_version"], "alma-evidence-gate/1.4.0"
        )
        self.assertEqual(result.needs_validation, [])

    def test_alma_specialty_incomplete_citation_is_held(self):
        # The sem_01 shape, produced live by the v2.3 reviewer: the
        # deep pass cites the whole statement (lines 11-14) whose
        # skeleton and construction sit on different lines.
        directory, diff_text, pr, truth, _ = load_semaforo_case(
            "sem_01_sql_injection"
        )
        head_lines = (
            (directory / "repo" / truth["file"]).read_text(encoding="utf-8").splitlines()
        )
        finding = {
            "file": truth["file"],
            "start_line": 11,
            "end_line": 14,
            "claim_type": "sql_injection",
            "message": "query built by string interpolation (scripted)",
            "evidence": head_lines[10:14],
        }
        transport = GeneralizedTransport(
            marks=["sql_injection"], deep_findings={"sql_injection": [finding]}
        )
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V14, armed_env(), transport
        )
        self.assertEqual(result.output["findings"], [])
        self.assertEqual(result.ledger, [])
        self.assertEqual(len(result.needs_validation), 1)
        self.assertEqual(
            [b["check"] for b in result.needs_validation[0]["blockers"]],
            ["co_occurrence"],
        )

    def test_wrong_mark_in_deep_pass_is_malformed(self):
        directory, diff_text, pr, truth, finding = self._general_finding()
        wrong = dict(finding, claim_type="reliability")
        transport = GeneralizedTransport(
            marks=["correctness"], deep_findings={"correctness": [wrong]}
        )
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V14, armed_env(), transport
        )
        self.assertEqual(result.candidates, [])
        self.assertEqual(result.llm_run_info["malformed_findings"], 1)


class BatteryDryRunTests(unittest.TestCase):
    """Mock dry run over the frozen semaphore battery (paper §11
    step 2): the selection marks the planted class, the deep pass
    echoes the planted defect.  All 16 codes must complete with no
    guard refusal and no degradation at the US$6.50 brake."""

    def test_battery_16_of_16_without_refusals(self):
        for case in SEMAFORO_CASES:
            directory, diff_text, pr, truth, planted = load_semaforo_case(case)
            for config, mode in (
                (CONFIG_ALMA_V14, "alma"),
                (CONFIG_BASE_V13, "base"),
            ):
                with self.subTest(case=case, mode=mode):
                    transport = GeneralizedTransport(
                        marks=[truth["planted_class"]],
                        deep_findings={truth["planted_class"]: [planted]},
                    )
                    result = run_case(
                        directory,
                        diff_text,
                        pr,
                        config,
                        armed_env(),
                        transport,
                        mode=mode,
                    )
                    info = result.llm_run_info
                    self.assertEqual(info["reviewer_version"], "llm-reviewer/2.3.2")
                    self.assertEqual(info["calls"], 2)
                    self.assertEqual(
                        info["selection_specialty"], [truth["planted_class"]]
                    )
                    self.assertEqual(info["selection_general"], [])
                    self.assertIsNone(info["degradation"])
                    self.assertEqual(len(result.candidates), 1)
                    if mode == "base":
                        self.assertEqual(len(result.output["findings"]), 1)
                        self.assertIsNone(result.needs_validation)
                    else:
                        # The echo cites only the defect line: every
                        # planted class passes the 1.4.0 except
                        # sem_01's sql_injection, whose one-line echo
                        # lacks the skeleton in the citation and is
                        # rejected outright (the settled multi-line
                        # citation is the one the frontier holds).
                        self.assertEqual(result.needs_validation, [])
                        expected = 0 if case.startswith("sem_01") else 1
                        self.assertEqual(len(result.output["findings"]), expected)


if __name__ == "__main__":
    unittest.main()
