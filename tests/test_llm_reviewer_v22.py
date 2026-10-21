"""Tests for the v2.2 LLM reviewer (agent/llm_reviewer_v22.py).

Everything runs offline with an in-process scripted transport.  What
this suite proves about the design frozen in
PREREGISTRO-REVIEWBENCH-V22.md (design C2 of Adenda 6):

- the selection pass reads the diff ALONE and marks <=5 classes; only
  the marked classes receive a deep pass, in the triage's priority
  order; overflow and unknown marks are recorded, never silent;
- a deep pass payload is the v2's own payload, byte for byte (same
  template, same guidance — including Adenda 3's citation addenda —
  same context), so the deep look IS the v2's deep look;
- the two-stage guard sums selection + deep passes: sized with the
  v1 anchor PR (cmik_apilix_12: 41,160 prompt tokens, US$0.86 real in
  one v1 pass), the full plan's worst case lands in the order of
  US$2–6 — not the US$36.80 the v2 guard estimated over 20 passes —
  and fits the signed US$6.50 brake;
- the pre-registered DEGRADATION rule fires under a small cap and is
  recorded in the run info: low-priority deep passes are dropped and
  declared; when none fits, the diff-only fallback runs declared, or
  zero findings are emitted WITH the declaration — never a mute zero;
- the findings feed the frozen gate 1.3.0 in the same Candidate
  format (accepted in the ALMA arm, bypass-emitted in the base arm),
  and a mock dry run over the whole frozen semaphore battery
  completes 16/16 codes with no guard refusal at the US$6.50 brake.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.alma_gate_v13 import KNOWN_CLAIM_TYPES_V13  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused, _estimate_tokens  # noqa: E402
from agent.llm_reviewer_v2 import LLMReviewerV2  # noqa: E402
from agent.llm_reviewer_v22 import LLMReviewerV22, MAX_DEEP_PASSES  # noqa: E402
from agent.main import run_agent  # noqa: E402


FIXTURES_SEMAFORO = ROOT / "fixtures_semaforo"
TEST_KEY = "test-key-not-a-real-secret"
USAGE = {"prompt_tokens": 100, "completion_tokens": 10}
# The selection call's reported cost under USAGE at planning prices.
SELECTION_COST = 100 * 15 / 1_000_000 + 10 * 75 / 1_000_000

CONFIG_ALMA_V13 = {
    "model": "gpt-5.6-sol",
    "effort": "medium",
    "governance": "alma",
    "reviewer": "v22",
    "gate": "v13",
}
CONFIG_BASE_V13 = dict(CONFIG_ALMA_V13, governance="base")

SEMAFORO_CASES = [
    "sem_01_sql_injection",
    "sem_02_hardcoded_secret",
    "sem_03_tls_verification_disabled",
    "sem_04_unsafe_deserialization",
    "sem_05_weak_hash",
    "sem_06_jwt_verification_disabled",
    "sem_07_debug_mode_enabled",
    "sem_08_command_execution",
]


def armed_env(**overrides):
    env = {
        "ALLOW_REAL_LLM": "1",
        "RB_MODEL_BASE_URL": "https://models.example.test/v1",
        "OPENAI_API_KEY": TEST_KEY,
        "RB_MAX_SPEND_USD": "6.50",
    }
    env.update(overrides)
    return env


def pass_name_of(payload) -> str:
    user = str(payload["messages"][1]["content"])
    first = user.splitlines()[0]
    assert first.startswith("PASS: "), first
    return first.removeprefix("PASS: ").strip()


class TriageTransport:
    """Scripted transport routed by the payload's PASS line.

    - "selection"       -> {"candidates": [...]} from `triage_marks`
    - "fallback_single" -> {"findings": fallback_findings}
    - "<claim class>"   -> {"findings": deep_findings.get(class, [])}
    """

    def __init__(
        self,
        triage_marks=(),
        deep_findings=None,
        fallback_findings=(),
        usage=USAGE,
    ):
        self.calls: list[dict[str, object]] = []
        self.triage_marks = list(triage_marks)
        self.deep_findings = dict(deep_findings or {})
        self.fallback_findings = list(fallback_findings)
        self.usage = usage

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
        name = pass_name_of(payload)
        if name == "selection":
            content = {
                "candidates": [
                    {"claim_type": mark, "reason": "scripted triage mark"}
                    for mark in self.triage_marks
                ]
            }
        elif name == "fallback_single":
            content = {"findings": self.fallback_findings}
        else:
            content = {"findings": self.deep_findings.get(name, [])}
        body = {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": self.usage,
        }
        return 200, json.dumps(body).encode("utf-8")

    def pass_names(self) -> list[str]:
        return [pass_name_of(call["payload"]) for call in self.calls]


def load_semaforo_case(name: str):
    directory = FIXTURES_SEMAFORO / name
    diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
    pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
    truth = json.loads((directory / "ground_truth.json").read_text(encoding="utf-8"))
    head_lines = (
        (directory / "repo" / truth["file"]).read_text(encoding="utf-8").splitlines()
    )
    planted = {
        "file": truth["file"],
        "start_line": truth["defect_line"],
        "end_line": truth["defect_line"],
        "claim_type": truth["planted_class"],
        "message": "mock echo of the planted defect",
        "evidence": [head_lines[truth["defect_line"] - 1]],
    }
    return directory, diff_text, pr, truth, planted


def run_case(directory, diff_text, pr, config, env, transport, mode="alma"):
    env = dict(env, RB_REPO_ROOT=str(directory / "repo"))
    return run_agent(
        diff_text=diff_text,
        pr_metadata=pr,
        agent_name="alma-reviewer",
        mode=mode,
        backend="llm",
        config=config,
        env=env,
        llm_transport=transport,
    )


class SelectionTests(unittest.TestCase):
    def test_only_marked_classes_get_deep_passes_capped_at_five(self):
        directory, diff_text, pr, truth, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        marks = [
            "tls_verification_disabled",
            "hardcoded_secret",
            "sql_injection",
            "weak_hash",
            "command_execution",
            "debug_mode_enabled",      # 6th valid mark -> overflow
            "mutable_default",         # 7th valid mark -> overflow
            "not_a_gate_class",        # unknown -> counted, never run
            "sql_injection",           # duplicate -> first occurrence wins
        ]
        transport = TriageTransport(
            triage_marks=marks,
            deep_findings={"tls_verification_disabled": [planted]},
        )
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V13, armed_env(), transport
        )
        info = result.llm_run_info
        self.assertEqual(
            info["selection_candidates"],
            [
                "tls_verification_disabled",
                "hardcoded_secret",
                "sql_injection",
                "weak_hash",
                "command_execution",
                "debug_mode_enabled",
                "mutable_default",
            ],
        )
        self.assertEqual(
            info["selection_selected"], info["selection_candidates"][:MAX_DEEP_PASSES]
        )
        self.assertEqual(
            info["selection_overflow"], ["debug_mode_enabled", "mutable_default"]
        )
        self.assertEqual(info["selection_unknown_marks"], 1)
        self.assertIsNone(info["degradation"])
        self.assertEqual(
            transport.pass_names(),
            ["selection"] + info["selection_selected"],
        )
        self.assertEqual(info["calls"], 1 + MAX_DEEP_PASSES)
        self.assertEqual(info["passes"], transport.pass_names())
        self.assertEqual(len(result.output["findings"]), 1)

    def test_triage_marks_nothing_runs_no_deep_pass(self):
        directory, diff_text, pr, _, _ = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        transport = TriageTransport(triage_marks=[])
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V13, armed_env(), transport
        )
        info = result.llm_run_info
        self.assertEqual(transport.pass_names(), ["selection"])
        self.assertEqual(info["selection_selected"], [])
        self.assertEqual(result.candidates, [])
        self.assertIsNone(info["degradation"])

    def test_selection_payload_is_diff_only_and_lists_all_classes(self):
        reviewer = LLMReviewerV22.from_env(
            armed_env(), CONFIG_ALMA_V13, transport=TriageTransport()
        )
        payload = reviewer.build_selection_payload("THE-DIFF-TEXT")
        system = str(payload["messages"][0]["content"])
        user = str(payload["messages"][1]["content"])
        self.assertEqual(len(KNOWN_CLAIM_TYPES_V13), 19)
        for claim_type in KNOWN_CLAIM_TYPES_V13:
            self.assertIn(f"--- CLASS {claim_type} ---", system)
        # Adenda 3 citation addendum rides along in the v13 guidance.
        self.assertIn("CITATION (required by the gate)", system)
        self.assertIn("THE-DIFF-TEXT", user)
        self.assertNotIn("full contents at PR head", user)
        # The triage's own output cap, not the review cap.
        self.assertEqual(payload["max_completion_tokens"], 1024)
        self.assertNotIn("temperature", payload)
        self.assertNotIn("max_tokens", payload)

    def test_deep_payload_is_the_v2_payload_byte_for_byte(self):
        env = armed_env()
        v22 = LLMReviewerV22.from_env(env, CONFIG_ALMA_V13, transport=TriageTransport())
        v2 = LLMReviewerV2.from_env(env, CONFIG_ALMA_V13, transport=TriageTransport())
        for claim_type in ("sql_injection", "weak_hash", "race_condition"):
            with self.subTest(claim_type=claim_type):
                self.assertEqual(
                    v22.build_deep_payload(claim_type, "DIFF", "CONTEXT"),
                    v2.build_payload(claim_type, "DIFF", "CONTEXT"),
                )


class GuardEstimateTests(unittest.TestCase):
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

    def test_guard_sums_selection_plus_five_deeps_in_the_order_of_2_to_6(self):
        reviewer = LLMReviewerV22.from_env(
            armed_env(), CONFIG_ALMA_V13, transport=TriageTransport()
        )
        # Diff padded to ~10k estimated tokens (selection input).
        selection_payload = self._pad_until(
            lambda diff: reviewer.build_selection_payload(diff), 10_000
        )
        # Deep payload whose total estimated input reaches the v1
        # anchor's 41,160 prompt tokens (diff + full head context).
        anchor_diff = "diff --git a/app/x.py b/app/x.py\n"
        deep_payload = self._pad_until(
            lambda context: reviewer.build_deep_payload(
                "sql_injection", anchor_diff, context
            ),
            41_160,
        )
        selection_worst = reviewer.worst_case_estimate(selection_payload)
        deep_worst = reviewer.worst_case_estimate(deep_payload)
        total = selection_worst + MAX_DEEP_PASSES * deep_worst
        # One deep pass on the anchor is the v2.1 paper's ~US$0.95.
        self.assertGreater(deep_worst, 0.70)
        self.assertLess(deep_worst, 1.40)
        # The selection over the diff alone stays a fraction of a pass.
        self.assertLess(selection_worst, 0.60)
        # The whole C2 plan: order US$2–6 — never the v2's US$36.80.
        self.assertGreater(total, 2.0)
        self.assertLess(total, 6.0)
        self.assertLess(total, 36.80 / 5)
        # And it fits the signed brake (Adenda 4).
        self.assertLess(total, 6.50)


def make_repo(tmp: str, n_lines: int = 600):
    """A repo whose head file is big (deep passes carry it whole)
    while the diff stays small — the shape that separates a deep
    pass's worst case from the diff-only fallback's."""

    repo = Path(tmp)
    (repo / "app").mkdir(parents=True)
    lines = [f"value_{i} = compute_something({i})" for i in range(1, n_lines + 1)]
    lines[9] = "digest = hashlib.md5(payload).hexdigest()"
    (repo / "app" / "big.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
    diff_text = (
        "diff --git a/app/big.py b/app/big.py\n"
        "--- a/app/big.py\n+++ b/app/big.py\n"
        "@@ -9,3 +9,3 @@\n"
        " value_9 = compute_something(9)\n"
        "-digest = hashlib.md5(payload).hexdigest()\n"
        "+digest = hashlib.md5(payload).hexdigest()  # touched\n"
        " value_11 = compute_something(11)\n"
    )
    return repo, diff_text, lines


def planned_worsts(reviewer, diff_text, repo, classes):
    """(deep worst per class, fallback worst) from the reviewer's own
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
        for name in classes
    }
    fallback = reviewer.worst_case_estimate(
        reviewer.build_fallback_payload(list(classes), diff_text)
    )
    return deeps, fallback


class DegradationTests(unittest.TestCase):
    def test_degradation_drops_low_priority_passes_and_declares(self):
        import tempfile

        marks = ["weak_hash", "sql_injection", "hardcoded_secret", "mutable_default"]
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, _ = make_repo(tmp)
            probe = LLMReviewerV22.from_env(
                armed_env(), CONFIG_ALMA_V13, transport=TriageTransport()
            )
            deeps, _ = planned_worsts(probe, diff_text, repo, marks)
            worst = deeps[marks[0]]
            # Every deep payload shares the same context, so their
            # worst cases agree to the cent; admit exactly two.
            cap = SELECTION_COST + 2.5 * worst
            transport = TriageTransport(triage_marks=marks)
            reviewer = LLMReviewerV22.from_env(
                armed_env(RB_MAX_SPEND_USD=f"{cap:.4f}"),
                CONFIG_ALMA_V13,
                transport=transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=parse_unified_diff(diff_text),
                config=CONFIG_ALMA_V13,
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

        marks = ["weak_hash", "sql_injection"]
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, lines = make_repo(tmp)
            probe = LLMReviewerV22.from_env(
                armed_env(), CONFIG_ALMA_V13, transport=TriageTransport()
            )
            deeps, fallback_worst = planned_worsts(probe, diff_text, repo, marks)
            # The design assumption of the degenerate branch: over the
            # diff alone, the fallback is cheaper than a deep pass.
            self.assertLess(fallback_worst, deeps[marks[0]])
            cap = SELECTION_COST + (deeps[marks[0]] + fallback_worst) / 2
            finding = {
                "file": "app/big.py",
                "start_line": 10,
                "end_line": 10,
                "claim_type": "weak_hash",
                "message": "md5 digest (scripted fallback echo)",
                "evidence": [lines[9]],
            }
            transport = TriageTransport(
                triage_marks=marks, fallback_findings=[finding]
            )
            reviewer = LLMReviewerV22.from_env(
                armed_env(RB_MAX_SPEND_USD=f"{cap:.4f}"),
                CONFIG_ALMA_V13,
                transport=transport,
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=parse_unified_diff(diff_text),
                config=CONFIG_ALMA_V13,
                mode="alma",
                repo_root=repo,
            )
            info = reviewer.last_run_info
            self.assertEqual(
                transport.pass_names(), ["selection", "fallback_single"]
            )
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0].claim_type, "weak_hash")
            self.assertEqual(candidates[0].producer, "alma-llm-reviewer-v22")
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
        directory, diff_text, _, _, _ = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        probe = LLMReviewerV22.from_env(
            armed_env(), CONFIG_ALMA_V13, transport=TriageTransport()
        )
        selection_worst = probe.worst_case_estimate(
            probe.build_selection_payload(diff_text)
        )
        transport = TriageTransport(triage_marks=["tls_verification_disabled"])
        result = run_case(
            directory,
            diff_text,
            json.loads((directory / "pr.json").read_text(encoding="utf-8")),
            CONFIG_ALMA_V13,
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
        transport = TriageTransport(triage_marks=["tls_verification_disabled"])
        with self.assertRaises(RealLLMRefused) as caught:
            run_case(
                directory,
                diff_text,
                pr,
                CONFIG_ALMA_V13,
                armed_env(RB_MAX_SPEND_USD="0.01"),
                transport,
            )
        self.assertIn("selection pass", str(caught.exception))
        self.assertEqual(transport.calls, [])


class GateFormatTests(unittest.TestCase):
    def test_gate_130_accepts_planted_finding_from_deep_pass(self):
        directory, diff_text, pr, truth, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        transport = TriageTransport(
            triage_marks=[truth["planted_class"]],
            deep_findings={truth["planted_class"]: [planted]},
        )
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V13, armed_env(), transport
        )
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].producer, "alma-llm-reviewer-v22")
        self.assertEqual(
            result.candidates[0].rule_id, "llm_v22_tls_verification_disabled"
        )
        self.assertEqual(len(result.output["findings"]), 1)
        accepted = [
            entry for entry in result.ledger if entry["status"] == "accepted"
        ]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["validator_version"], "alma-evidence-gate/1.3.0")

    def test_base_arm_emits_through_the_bypass(self):
        directory, diff_text, pr, truth, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        transport = TriageTransport(
            triage_marks=[truth["planted_class"]],
            deep_findings={truth["planted_class"]: [planted]},
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
        self.assertEqual(
            result.ledger[0]["validator_version"], "bypassed-base-arm"
        )

    def test_wrong_class_in_deep_pass_malformed_and_misquote_unanchored(self):
        directory, diff_text, pr, truth, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        findings = [
            dict(planted, claim_type="weak_hash"),  # not this pass's class
            dict(planted, message="misquote", evidence=["requests.get(url)"]),
        ]
        transport = TriageTransport(
            triage_marks=[truth["planted_class"]],
            deep_findings={truth["planted_class"]: findings},
        )
        result = run_case(
            directory, diff_text, pr, CONFIG_ALMA_V13, armed_env(), transport
        )
        self.assertEqual(result.candidates, [])
        info = result.llm_run_info
        self.assertEqual(info["malformed_findings"], 1)
        self.assertEqual(info["unanchored_findings"], 1)

    def test_payload_keeps_v1_corrections_and_arming(self):
        reviewer = LLMReviewerV22.from_env(
            armed_env(), CONFIG_ALMA_V13, transport=TriageTransport()
        )
        payload = reviewer.build_deep_payload("sql_injection", "d", "c")
        self.assertNotIn("temperature", payload)
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(payload["max_completion_tokens"], 4096)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["reasoning_effort"], "medium")
        # Disarmed env: the selection never happens.
        directory, diff_text, pr, _, _ = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        env = armed_env(RB_REPO_ROOT=str(directory / "repo"))
        del env["ALLOW_REAL_LLM"]
        transport = TriageTransport(triage_marks=["tls_verification_disabled"])
        with self.assertRaises(RealLLMRefused):
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="llm",
                config=CONFIG_ALMA_V13,
                env=env,
                llm_transport=transport,
            )
        self.assertEqual(transport.calls, [])


class BatteryDryRunTests(unittest.TestCase):
    """Mock dry run over the frozen semaphore battery: the triage
    marks the planted class, the deep pass echoes the planted defect.
    All 16 codes must complete with no guard refusal and no
    degradation at the signed US$6.50 brake (paper §7, step 1)."""

    def test_battery_16_of_16_without_refusals(self):
        for case in SEMAFORO_CASES:
            directory, diff_text, pr, truth, planted = load_semaforo_case(case)
            for config, mode in (
                (CONFIG_ALMA_V13, "alma"),
                (CONFIG_BASE_V13, "base"),
            ):
                with self.subTest(case=case, mode=mode):
                    transport = TriageTransport(
                        triage_marks=[truth["planted_class"]],
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
                    self.assertEqual(info["reviewer_version"], "llm-reviewer/2.2.0")
                    self.assertEqual(info["calls"], 2)
                    self.assertEqual(
                        info["selection_selected"], [truth["planted_class"]]
                    )
                    self.assertIsNone(info["degradation"])
                    # The planted candidate reaches the gate in both
                    # arms; what the gate does with it is the gate's
                    # frozen business (sem_01's citation is rejected
                    # by the 1.3.0 in the ALMA arm, as in v2/v2.1).
                    self.assertEqual(len(result.candidates), 1)
                    if mode == "base":
                        self.assertEqual(len(result.output["findings"]), 1)


if __name__ == "__main__":
    unittest.main()
