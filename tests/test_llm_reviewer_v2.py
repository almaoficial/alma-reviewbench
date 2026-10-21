"""Tests for the v2 LLM reviewer (agent/llm_reviewer_v2.py).

Everything runs offline with an in-process fake transport, exactly like
the v1 adapter tests.  What this suite proves about the design frozen in
PREREGISTRO-REVIEWBENCH-V2.md:

- the reviewer makes one pass per verifiable claim class (8 calls in the
  ALMA arm, never a general pass) and the candidates it produces from the
  per-class fixtures are ACCEPTED by the frozen gate — reviewer and gate
  speak the same language;
- the base arm adds exactly one general pass;
- the model sees the full head contents of touched files (context beyond
  the diff), bounded by the declared per-PR context token budget;
- anchoring is enforced in the reviewer: misquoted evidence, out-of-file
  lines and wrong-class returns in a class pass are dropped before the
  gate, and counted;
- the v1 payload corrections survive (no temperature, no max_tokens,
  max_completion_tokens, HTTP error body excerpt in the refusal) and the
  arming/spend refusals still fire before any transport call;
- v1 stays the default reviewer; RB_CONFIG_REVIEWER selects v2.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.alma_gate import KNOWN_CLAIM_TYPES  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused  # noqa: E402
from agent.llm_reviewer_v2 import LLMReviewerV2  # noqa: E402
from agent.main import run_agent  # noqa: E402


FIXTURES_V2 = ROOT / "fixtures_v2"
TEST_KEY = "test-key-not-a-real-secret"
USAGE = {"prompt_tokens": 100, "completion_tokens": 10}

CONFIG_ALMA = {
    "model": "gpt-5.6-sol",
    "effort": "medium",
    "governance": "alma",
    "reviewer": "v2",
}
CONFIG_BASE = dict(CONFIG_ALMA, governance="base")


def armed_env(**overrides):
    env = {
        "ALLOW_REAL_LLM": "1",
        "RB_MODEL_BASE_URL": "https://models.example.test/v1",
        "OPENAI_API_KEY": TEST_KEY,
        "RB_MAX_SPEND_USD": "5.00",
    }
    env.update(overrides)
    return env


def load_v2_fixture(name: str):
    directory = FIXTURES_V2 / name
    diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
    pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
    responses_doc = json.loads(
        (directory / "model_responses.json").read_text(encoding="utf-8")
    )
    responses = dict(responses_doc.get("passes", {}))
    responses["general"] = responses_doc.get("general", [])
    return directory, diff_text, pr, responses


class PassTransport:
    """Fake transport that answers per pass, keyed by the PASS marker."""

    def __init__(self, responses=None, usage=USAGE, status=200, raw_body=None):
        self.calls: list[dict[str, object]] = []
        self.responses = responses or {}
        self.usage = usage
        self.status = status
        self.raw_body = raw_body

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
        if self.raw_body is not None:
            return self.status, self.raw_body
        user_content = payload["messages"][1]["content"]
        marker = user_content.splitlines()[0]
        assert marker.startswith("PASS: "), marker
        pass_name = marker[len("PASS: ") :].strip()
        findings = self.responses.get(pass_name, [])
        body = {
            "choices": [
                {"message": {"content": json.dumps({"findings": findings})}}
            ],
            "usage": self.usage,
        }
        return self.status, json.dumps(body).encode("utf-8")

    def pass_names(self) -> list[str]:
        names = []
        for call in self.calls:
            marker = call["payload"]["messages"][1]["content"].splitlines()[0]
            names.append(marker[len("PASS: ") :].strip())
        return names


class PerClassFixtureTests(unittest.TestCase):
    def test_each_class_fixture_yields_one_gate_accepted_finding(self):
        fixture_dirs = sorted(
            path for path in FIXTURES_V2.iterdir() if path.is_dir()
        )
        # One fixture per verifiable class, no more, no fewer.
        self.assertEqual(len(fixture_dirs), len(KNOWN_CLAIM_TYPES))
        for directory in fixture_dirs:
            with self.subTest(fixture=directory.name):
                _, diff_text, pr, responses = load_v2_fixture(directory.name)
                expected = [
                    finding
                    for findings in responses.values()
                    for finding in findings
                ]
                self.assertEqual(len(expected), 1)
                expected = expected[0]

                transport = PassTransport(responses)
                result = run_agent(
                    diff_text=diff_text,
                    pr_metadata=pr,
                    agent_name="alma-reviewer",
                    mode="alma",
                    backend="llm",
                    config=CONFIG_ALMA,
                    env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
                    llm_transport=transport,
                )

                # Eight class passes, in the gate's class order, no general.
                self.assertEqual(transport.pass_names(), list(KNOWN_CLAIM_TYPES))
                self.assertEqual(len(transport.calls), 8)

                findings = result.output["findings"]
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0]["file"], expected["file"])
                self.assertEqual(findings[0]["start_line"], expected["start_line"])
                self.assertEqual(findings[0]["end_line"], expected["end_line"])
                self.assertEqual(findings[0]["producer"], "alma-reviewer")

                accepted = [
                    entry for entry in result.ledger if entry["status"] == "accepted"
                ]
                self.assertEqual(len(accepted), 1)
                self.assertEqual(accepted[0]["claim_type"], expected["claim_type"])
                self.assertEqual(
                    result.llm_run_info["reviewer_version"], "llm-reviewer/2.0.0"
                )
                self.assertEqual(result.llm_run_info["calls"], 8)
                self.assertEqual(result.llm_run_info["unanchored_findings"], 0)


class ContextTests(unittest.TestCase):
    def test_model_sees_full_head_file_beyond_the_diff(self):
        directory, diff_text, _, responses = load_v2_fixture("v2_01_sql_injection")
        transport = PassTransport(responses)
        reviewer = LLMReviewerV2.from_env(
            armed_env(), CONFIG_ALMA, transport=transport
        )
        reviewer.review(
            diff_text=diff_text,
            diff=parse_unified_diff(diff_text),
            config=CONFIG_ALMA,
            mode="alma",
            repo_root=directory / "repo",
        )
        # Line 3 of the head file is NOT in the diff, but the prompt has it.
        self.assertNotIn("DB_PATH", diff_text)
        user_content = transport.calls[0]["payload"]["messages"][1]["content"]
        self.assertIn('3: DB_PATH = "app.db"', user_content)
        self.assertIn("=== FILE app/db.py (full contents at PR head) ===", user_content)
        self.assertEqual(
            reviewer.last_run_info.context_files_included, ["app/db.py"]
        )

    def test_context_budget_skips_files_and_declares_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "a.py").write_text("x = 1\ny = 2\nz = 3\n", encoding="utf-8")
            big = "\n".join(f"value_{i} = {i}" for i in range(500)) + "\n"
            (repo / "b.py").write_text(big, encoding="utf-8")
            diff_text = (
                "diff --git a/a.py b/a.py\nnew file mode 100644\n"
                "--- /dev/null\n+++ b/a.py\n@@ -0,0 +1,3 @@\n"
                "+x = 1\n+y = 2\n+z = 3\n"
                "diff --git a/b.py b/b.py\nnew file mode 100644\n"
                "--- /dev/null\n+++ b/b.py\n@@ -0,0 +1,1 @@\n+value_0 = 0\n"
            )
            config = dict(CONFIG_ALMA, context_token_budget="200")
            transport = PassTransport({})
            reviewer = LLMReviewerV2.from_env(
                armed_env(), config, transport=transport
            )
            candidates = reviewer.review(
                diff_text=diff_text,
                diff=parse_unified_diff(diff_text),
                config=config,
                mode="alma",
                repo_root=repo,
            )
            self.assertEqual(candidates, [])
            info = reviewer.last_run_info
            self.assertEqual(info.context_files_included, ["a.py"])
            self.assertEqual(info.context_files_skipped_budget, ["b.py"])
            self.assertEqual(info.context_token_budget, 200)


class AnchoringTests(unittest.TestCase):
    def _reviewer_with(self, responses):
        directory = FIXTURES_V2 / "v2_01_sql_injection"
        diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
        transport = PassTransport(responses)
        reviewer = LLMReviewerV2.from_env(
            armed_env(), CONFIG_ALMA, transport=transport
        )
        candidates = reviewer.review(
            diff_text=diff_text,
            diff=parse_unified_diff(diff_text),
            config=CONFIG_ALMA,
            mode="alma",
            repo_root=directory / "repo",
        )
        return reviewer, candidates

    def test_misquoted_and_out_of_range_and_unquoted_are_dropped(self):
        good_line = '    query = f"SELECT * FROM users WHERE id = {user_id}"'
        responses = {
            "sql_injection": [
                {  # right lines, wrong quote -> unanchored
                    "file": "app/db.py", "start_line": 11, "end_line": 11,
                    "claim_type": "sql_injection", "message": "mismatch",
                    "evidence": ["    query = f'SELECT * FROM users'"],
                },
                {  # line outside the head file -> unanchored
                    "file": "app/db.py", "start_line": 999, "end_line": 999,
                    "claim_type": "sql_injection", "message": "ghost",
                    "evidence": [good_line],
                },
                {  # no evidence at all -> unanchored
                    "file": "app/db.py", "start_line": 11, "end_line": 11,
                    "claim_type": "sql_injection", "message": "no quote",
                },
            ]
        }
        reviewer, candidates = self._reviewer_with(responses)
        self.assertEqual(candidates, [])
        self.assertEqual(reviewer.last_run_info.unanchored_findings, 3)
        self.assertEqual(reviewer.last_run_info.malformed_findings, 0)

    def test_wrong_claim_type_in_class_pass_is_dropped(self):
        responses = {
            "sql_injection": [
                {
                    "file": "app/db.py", "start_line": 11, "end_line": 11,
                    "claim_type": "hardcoded_secret",
                    "message": "Anchored fine, but not this pass's class.",
                    "evidence": [
                        '    query = f"SELECT * FROM users WHERE id = {user_id}"'
                    ],
                }
            ]
        }
        reviewer, candidates = self._reviewer_with(responses)
        self.assertEqual(candidates, [])
        self.assertEqual(reviewer.last_run_info.malformed_findings, 1)


class GeneralPassTests(unittest.TestCase):
    def test_base_arm_adds_general_pass_alma_arm_never_calls_it(self):
        _, diff_text, pr, responses = load_v2_fixture("v2_01_sql_injection")
        responses = dict(responses)
        responses["general"] = [
            {
                "file": "app/db.py", "start_line": 12, "end_line": 12,
                "claim_type": "sql_injection",
                "message": "The interpolated query is executed here.",
                "evidence": ["    cursor.execute(query)"],
            }
        ]
        directory = FIXTURES_V2 / "v2_01_sql_injection"
        env = armed_env(RB_REPO_ROOT=str(directory / "repo"))

        alma_transport = PassTransport(responses)
        alma = run_agent(
            diff_text=diff_text, pr_metadata=pr, agent_name="alma-reviewer",
            mode="alma", backend="llm", config=CONFIG_ALMA, env=env,
            llm_transport=alma_transport,
        )
        self.assertNotIn("general", alma_transport.pass_names())
        self.assertEqual(len(alma.output["findings"]), 1)

        base_transport = PassTransport(responses)
        base = run_agent(
            diff_text=diff_text, pr_metadata=pr, agent_name="base-reviewer",
            mode="base", backend="llm",
            config=dict(CONFIG_BASE), env=env, llm_transport=base_transport,
        )
        self.assertEqual(base_transport.pass_names()[-1], "general")
        self.assertEqual(len(base_transport.calls), 9)
        # Class finding (line 11) + general finding (line 12), unfiltered.
        self.assertEqual(len(base.output["findings"]), 2)


class SafetyAndPayloadTests(unittest.TestCase):
    def test_payload_keeps_v1_corrections(self):
        _, diff_text, pr, responses = load_v2_fixture("v2_01_sql_injection")
        directory = FIXTURES_V2 / "v2_01_sql_injection"
        transport = PassTransport(responses)
        run_agent(
            diff_text=diff_text, pr_metadata=pr, agent_name="alma-reviewer",
            mode="alma", backend="llm", config=CONFIG_ALMA,
            env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
            llm_transport=transport,
        )
        payload = transport.calls[0]["payload"]
        self.assertNotIn("temperature", payload)
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(payload["max_completion_tokens"], 4096)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(payload["reasoning_effort"], "medium")
        self.assertEqual(payload["model"], "gpt-5.6-sol")

    def test_http_error_refusal_includes_body_excerpt(self):
        _, diff_text, pr, _ = load_v2_fixture("v2_01_sql_injection")
        directory = FIXTURES_V2 / "v2_01_sql_injection"
        transport = PassTransport(
            status=400,
            raw_body=b'{"error": {"message": "max_tokens is not supported"}}',
        )
        with self.assertRaises(RealLLMRefused) as caught:
            run_agent(
                diff_text=diff_text, pr_metadata=pr, agent_name="alma-reviewer",
                mode="alma", backend="llm", config=CONFIG_ALMA,
                env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
                llm_transport=transport,
            )
        self.assertIn("HTTP 400", str(caught.exception))
        self.assertIn("max_tokens is not supported", str(caught.exception))

    def test_refuses_without_allow_flag_before_any_call(self):
        _, diff_text, pr, responses = load_v2_fixture("v2_01_sql_injection")
        directory = FIXTURES_V2 / "v2_01_sql_injection"
        env = armed_env(RB_REPO_ROOT=str(directory / "repo"))
        del env["ALLOW_REAL_LLM"]
        transport = PassTransport(responses)
        with self.assertRaises(RealLLMRefused):
            run_agent(
                diff_text=diff_text, pr_metadata=pr, agent_name="alma-reviewer",
                mode="alma", backend="llm", config=CONFIG_ALMA, env=env,
                llm_transport=transport,
            )
        self.assertEqual(transport.calls, [])

    def test_refuses_preflight_when_worst_case_exceeds_cap(self):
        _, diff_text, pr, responses = load_v2_fixture("v2_01_sql_injection")
        directory = FIXTURES_V2 / "v2_01_sql_injection"
        transport = PassTransport(responses)
        with self.assertRaises(RealLLMRefused):
            run_agent(
                diff_text=diff_text, pr_metadata=pr, agent_name="alma-reviewer",
                mode="alma", backend="llm", config=CONFIG_ALMA,
                env=armed_env(
                    RB_MAX_SPEND_USD="0.01", RB_REPO_ROOT=str(directory / "repo")
                ),
                llm_transport=transport,
            )
        self.assertEqual(transport.calls, [])

    def test_missing_repo_root_refuses_before_any_call(self):
        _, diff_text, pr, responses = load_v2_fixture("v2_01_sql_injection")
        transport = PassTransport(responses)
        with self.assertRaises(RealLLMRefused):
            run_agent(
                diff_text=diff_text, pr_metadata=pr, agent_name="alma-reviewer",
                mode="alma", backend="llm", config=CONFIG_ALMA,
                env=armed_env(RB_REPO_ROOT="/nonexistent-repo-root"),
                llm_transport=transport,
            )
        self.assertEqual(transport.calls, [])


class SelectionTests(unittest.TestCase):
    def test_unknown_reviewer_version_fails_closed(self):
        _, diff_text, pr, _ = load_v2_fixture("v2_01_sql_injection")
        config = dict(CONFIG_ALMA, reviewer="v3")
        with self.assertRaises(ValueError):
            run_agent(
                diff_text=diff_text, pr_metadata=pr, agent_name="alma-reviewer",
                mode="alma", backend="llm", config=config, env=armed_env(),
                llm_transport=PassTransport({}),
            )


if __name__ == "__main__":
    unittest.main()
