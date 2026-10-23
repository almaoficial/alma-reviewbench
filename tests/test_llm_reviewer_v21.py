"""Tests for the v2.1 LLM reviewer (agent/llm_reviewer_v21.py).

Everything runs offline with an in-process fake transport.  What this
suite proves about the design frozen in PREREGISTRO-REVIEWBENCH-V21.md
(design C1 of Adenda 6 of the v2 pre-registration):

- ONE call per PR, in both arms: the single payload carries the active
  gate's classes as sections (19 under gate=v13) with the v2's guidance
  — including Adenda 3's citation-discipline addenda, byte-identical —
  and the v2's exact-citation contract sentences, verbatim;
- the pre-flight guard estimates ONE pass: sized with the real anchor
  PR of the v1 measurement (cmik_apilix_12: 41,160 prompt tokens
  reported by the API, US$0.86 real in one v1 pass), its worst case
  lands in the order of US$1 — not the US$36.80 the v2 guard estimated
  for the same PR over 20 passes — and it passes under the signed
  US$6.50 brake that the v2 could not pass;
- the single JSON output feeds the frozen gate 1.3.0 in the same
  Candidate format as today (a gate-shaped finding is accepted; the
  base arm emits through the bypass), classes outside the active
  gate's list are dropped as malformed, and the reviewer's anchor
  verification still drops misquoted evidence before the gate;
- the v1 payload corrections and arming refusals survive; v1 stays the
  default reviewer and RB_CONFIG_REVIEWER=v21 selects this one.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.alma_gate_v13 import KNOWN_CLAIM_TYPES_V13  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused, _estimate_tokens  # noqa: E402
from agent.llm_reviewer_v21 import LLMReviewerV21  # noqa: E402
from agent.main import run_agent  # noqa: E402


FIXTURES_V2 = ROOT / "fixtures_v2"
FIXTURES_SEMAFORO = ROOT / "fixtures_semaforo"
TEST_KEY = "test-key-not-a-real-secret"
USAGE = {"prompt_tokens": 100, "completion_tokens": 10}

CONFIG_ALMA_V13 = {
    "model": "gpt-5.6-sol",
    "effort": "medium",
    "governance": "alma",
    "reviewer": "v21",
    "gate": "v13",
}
CONFIG_BASE_V13 = dict(CONFIG_ALMA_V13, governance="base")


def armed_env(**overrides):
    env = {
        "ALLOW_REAL_LLM": "1",
        "RB_MODEL_BASE_URL": "https://models.example.test/v1",
        "OPENAI_API_KEY": TEST_KEY,
        "RB_MAX_SPEND_USD": "6.50",
    }
    env.update(overrides)
    return env


class SingleTransport:
    """Fake transport for the single-pass reviewer: one scripted reply."""

    def __init__(self, findings=None, usage=USAGE, status=200, raw_body=None):
        self.calls: list[dict[str, object]] = []
        self.findings = findings or []
        self.usage = usage
        self.status = status
        self.raw_body = raw_body

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
        if self.raw_body is not None:
            return self.status, self.raw_body
        body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"findings": self.findings})
                    }
                }
            ],
            "usage": self.usage,
        }
        return self.status, json.dumps(body).encode("utf-8")


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


class SingleCallTests(unittest.TestCase):
    def test_one_call_per_pr_in_both_arms(self):
        directory, diff_text, pr, _, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        env = armed_env(RB_REPO_ROOT=str(directory / "repo"))
        for config, mode in (
            (CONFIG_ALMA_V13, "alma"),
            (CONFIG_BASE_V13, "base"),
        ):
            with self.subTest(mode=mode):
                transport = SingleTransport([planted])
                result = run_agent(
                    diff_text=diff_text,
                    pr_metadata=pr,
                    agent_name="alma-reviewer",
                    mode=mode,
                    backend="llm",
                    config=config,
                    env=env,
                    llm_transport=transport,
                )
                self.assertEqual(len(transport.calls), 1)
                info = result.llm_run_info
                self.assertEqual(info["calls"], 1)
                self.assertEqual(info["passes"], ["single"])
                self.assertEqual(info["reviewer_version"], "llm-reviewer/2.1.0")
                self.assertEqual(info["gate_version"], "alma-evidence-gate/1.3.0")
                self.assertEqual(len(result.output["findings"]), 1)

    def test_system_prompt_has_all_19_sections_and_v2_citation_text(self):
        transport = SingleTransport([])
        reviewer = LLMReviewerV21.from_env(
            armed_env(), CONFIG_ALMA_V13, transport=transport
        )
        payload = reviewer.build_payload("diff", "context")
        system = payload["messages"][0]["content"]
        self.assertEqual(len(KNOWN_CLAIM_TYPES_V13), 19)
        for claim_type in KNOWN_CLAIM_TYPES_V13:
            self.assertIn(f"--- CLASS {claim_type} ---", system)
        # The exact-citation contract, verbatim from the v2 template.
        self.assertIn(
            "The evidence array must reproduce the cited lines EXACTLY "
            "as they appear in the file",
            system,
        )
        self.assertIn(
            "Cite the smallest line range that contains the evidence",
            system,
        )
        # Adenda 3 lever 1: the citation-discipline addendum is present
        # under gate=v13 (sql section), byte-identical to the v2's.
        self.assertIn(
            "CITATION (required by the gate): cite the line where the "
            "SQL skeleton",
            system,
        )

    def test_citation_addendum_absent_under_older_gates(self):
        config = dict(CONFIG_ALMA_V13, gate="v12")
        reviewer = LLMReviewerV21.from_env(
            armed_env(), config, transport=SingleTransport([])
        )
        system = reviewer.build_payload("d", "c")["messages"][0]["content"]
        self.assertNotIn("CITATION (required by the gate)", system)
        self.assertIn("--- CLASS sql_injection ---", system)
        self.assertNotIn("--- CLASS weak_hash ---", system)


class GuardEstimateTests(unittest.TestCase):
    def _anchor_sized_payload(self, reviewer):
        """A payload whose guard-estimated input is ~the v1 anchor PR.

        The v1 measurement (Adenda 6): PR cmik_apilix_12 reported
        41,160 prompt tokens from the API and cost US$0.86 real in one
        pass.  Pad the context with filler lines until the guard's own
        estimator sees that order of input for THIS payload.
        """

        filler_line = "filler = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'\n"
        context = ""
        payload = reviewer.build_payload("diff", context)
        while True:
            estimated = sum(
                _estimate_tokens(str(m["content"])) for m in payload["messages"]
            )
            if estimated >= 41160:
                return payload, estimated
            context += filler_line * 200
            payload = reviewer.build_payload("diff", context)

    def test_guard_estimates_one_pass_in_the_order_of_one_dollar(self):
        reviewer = LLMReviewerV21.from_env(
            armed_env(), CONFIG_ALMA_V13, transport=SingleTransport([])
        )
        payload, estimated_input = self._anchor_sized_payload(reviewer)
        self.assertLess(estimated_input, 45000)
        worst_case = reviewer.worst_case_estimate(payload)
        # Order of US$1 (paper §4 computes US$0.9484 for the anchor) —
        # and nowhere near the v2 guard's US$36.80 for the same PR.
        self.assertGreater(worst_case, 0.70)
        self.assertLess(worst_case, 1.40)
        self.assertLess(worst_case, 36.80 / 10)
        # Under the signed brake (Adenda 4) that the v2 could not pass.
        self.assertLess(worst_case, 6.50)

    def test_preflight_refuses_over_a_small_cap_before_any_call(self):
        directory, diff_text, pr, _, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        transport = SingleTransport([planted])
        with self.assertRaises(RealLLMRefused) as caught:
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="llm",
                config=CONFIG_ALMA_V13,
                env=armed_env(
                    RB_MAX_SPEND_USD="0.01",
                    RB_REPO_ROOT=str(directory / "repo"),
                ),
                llm_transport=transport,
            )
        self.assertIn("over 1 pass", str(caught.exception))
        self.assertEqual(transport.calls, [])


class GateFormatTests(unittest.TestCase):
    def test_gate_130_accepts_a_gate_shaped_finding_from_one_json(self):
        directory, diff_text, pr, _, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        transport = SingleTransport([planted])
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="alma-reviewer",
            mode="alma",
            backend="llm",
            config=CONFIG_ALMA_V13,
            env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
            llm_transport=transport,
        )
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].producer, "alma-llm-reviewer-v21")
        self.assertEqual(result.candidates[0].rule_id, "llm_v21_tls_verification_disabled")
        findings = result.output["findings"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["producer"], "alma-reviewer")
        accepted = [
            entry for entry in result.ledger if entry["status"] == "accepted"
        ]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["validator_version"], "alma-evidence-gate/1.3.0")

    def test_mixed_classes_in_one_response_both_reach_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app").mkdir()
            lines = [
                "import hashlib",
                "import requests",
                "",
                "def fetch(url):",
                "    return requests.get(url, verify=False)",
                "",
                "def digest(pw):",
                "    return hashlib.md5(pw.encode()).hexdigest()",
            ]
            (repo / "app" / "mix.py").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
            added = "".join(f"+{line}\n" for line in lines)
            diff_text = (
                "diff --git a/app/mix.py b/app/mix.py\nnew file mode 100644\n"
                "--- /dev/null\n+++ b/app/mix.py\n"
                f"@@ -0,0 +1,{len(lines)} @@\n" + added
            )
            pr = {
                "repo": "https://github.com/example/mix",
                "pr_number": 1,
                "base": "a" * 40,
                "head": "b" * 40,
            }
            findings = [
                {
                    "file": "app/mix.py", "start_line": 5, "end_line": 5,
                    "claim_type": "tls_verification_disabled",
                    "message": "verify=False",
                    "evidence": [lines[4]],
                },
                {
                    "file": "app/mix.py", "start_line": 8, "end_line": 8,
                    "claim_type": "weak_hash",
                    "message": "md5 for a password digest",
                    "evidence": [lines[7]],
                },
            ]
            transport = SingleTransport(findings)
            result = run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="llm",
                config=CONFIG_ALMA_V13,
                env=armed_env(RB_REPO_ROOT=str(repo)),
                llm_transport=transport,
            )
            self.assertEqual(len(transport.calls), 1)
            self.assertEqual(len(result.output["findings"]), 2)
            accepted_types = {
                entry["claim_type"]
                for entry in result.ledger
                if entry["status"] == "accepted"
            }
            self.assertEqual(
                accepted_types, {"tls_verification_disabled", "weak_hash"}
            )

    def test_unknown_claim_type_is_malformed_and_misquote_unanchored(self):
        directory, diff_text, pr, truth, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        findings = [
            dict(planted, claim_type="logic_error"),  # not a gate class
            dict(planted, message="misquote", evidence=["requests.get(url)"]),
        ]
        transport = SingleTransport(findings)
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="alma-reviewer",
            mode="alma",
            backend="llm",
            config=CONFIG_ALMA_V13,
            env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
            llm_transport=transport,
        )
        self.assertEqual(result.candidates, [])
        info = result.llm_run_info
        self.assertEqual(info["malformed_findings"], 1)
        self.assertEqual(info["unanchored_findings"], 1)


class SafetyAndSelectionTests(unittest.TestCase):
    def test_payload_keeps_v1_corrections(self):
        reviewer = LLMReviewerV21.from_env(
            armed_env(), CONFIG_ALMA_V13, transport=SingleTransport([])
        )
        payload = reviewer.build_payload("d", "c")
        self.assertNotIn("temperature", payload)
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(payload["max_completion_tokens"], 4096)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["reasoning_effort"], "medium")

    def test_refuses_without_allow_flag_before_any_call(self):
        directory, diff_text, pr, _, planted = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        env = armed_env(RB_REPO_ROOT=str(directory / "repo"))
        del env["ALLOW_REAL_LLM"]
        transport = SingleTransport([planted])
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

    def test_unknown_reviewer_version_fails_closed(self):
        _, diff_text, pr, _ = (
            FIXTURES_V2 / "v2_01_sql_injection",
            (FIXTURES_V2 / "v2_01_sql_injection" / "diff.patch").read_text(
                encoding="utf-8"
            ),
            json.loads(
                (FIXTURES_V2 / "v2_01_sql_injection" / "pr.json").read_text(
                    encoding="utf-8"
                )
            ),
            None,
        )
        config = dict(CONFIG_ALMA_V13, reviewer="v99")
        with self.assertRaises(ValueError) as caught:
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="llm",
                config=config,
                env=armed_env(),
                llm_transport=SingleTransport([]),
            )
        self.assertIn("'v22'", str(caught.exception))

    def test_diff_index_type_is_used(self):
        # Guard against signature drift with agent/main.py: review()
        # receives the parsed DiffIndex, exactly like the v2.
        directory, diff_text, _, _, _ = load_semaforo_case(
            "sem_03_tls_verification_disabled"
        )
        reviewer = LLMReviewerV21.from_env(
            armed_env(), CONFIG_ALMA_V13, transport=SingleTransport([])
        )
        candidates = reviewer.review(
            diff_text=diff_text,
            diff=parse_unified_diff(diff_text),
            config=CONFIG_ALMA_V13,
            mode="alma",
            repo_root=directory / "repo",
        )
        self.assertEqual(candidates, [])
        self.assertEqual(reviewer.last_run_info.calls, 1)


if __name__ == "__main__":
    unittest.main()
