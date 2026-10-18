"""Tests for the flag-guarded real LLM backend (agent/llm_reviewer.py).

Everything here runs offline: the HTTP transport is an in-process fake, the
API key is a literal test string, and no network is touched.  The suite
proves the safety contract:

- without ALLOW_REAL_LLM=1 / key / base URL / model / spend cap, the
  backend refuses BEFORE any transport call;
- the spend cap also refuses pre-flight when the worst-case estimate
  exceeds it, and post-call when reported usage exceeds it;
- with full flags, the request is built correctly (URL, auth header,
  model, effort, JSON-only findings prompt);
- model findings become candidates whose evidence comes from the real
  diff, and the frozen ALMA gate filters them exactly as it filters the
  deterministic reviewer's candidates.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.llm_reviewer import LLMReviewer, LLMSettings, RealLLMRefused  # noqa: E402
from agent.main import run_agent  # noqa: E402


FIXTURES = ROOT / "fixtures"
TEST_KEY = "test-key-not-a-real-secret"


def load_fixture(name: str):
    directory = FIXTURES / name
    diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
    pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
    return diff_text, pr


def armed_env(**overrides):
    env = {
        "ALLOW_REAL_LLM": "1",
        "RB_MODEL_BASE_URL": "https://models.example.test/v1",
        "OPENAI_API_KEY": TEST_KEY,
        "RB_MAX_SPEND_USD": "5.00",
    }
    env.update(overrides)
    return env


CONFIG = {"model": "gpt-5.6-sol", "effort": "medium", "governance": "alma"}


class FakeTransport:
    """Records calls and replies with a canned chat-completions body."""

    def __init__(self, findings, usage=None, status=200, raw_content=None):
        self.calls: list[dict[str, object]] = []
        self.status = status
        if raw_content is not None:
            content = raw_content
        else:
            content = json.dumps({"findings": findings})
        self.body = {
            "choices": [{"message": {"content": content}}],
        }
        if usage is not None:
            self.body["usage"] = usage

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
        return self.status, json.dumps(self.body).encode("utf-8")


# Fixture 01_sql, app/db.py at head:
#   line 4: query = f"SELECT * FROM users WHERE id = {user_id}"  (real SQLi)
#   line 9: cursor.execute(query, (user_id,))                    (parameterized)
MODEL_FINDINGS = [
    {
        "file": "app/db.py",
        "start_line": 4,
        "end_line": 4,
        "claim_type": "sql_injection",
        "message": "SQL injection: the query interpolates user_id directly.",
    },
    {
        "file": "app/db.py",
        "start_line": 9,
        "end_line": 9,
        "claim_type": "sql_injection",
        "message": "Possible SQL injection at this execute call.",
    },
    {
        "file": "app/nope.py",
        "start_line": 3,
        "end_line": 3,
        "claim_type": "sql_injection",
        "message": "Hallucinated finding in a file that is not in the diff.",
    },
    {
        "file": "app/db.py",
        "start_line": 4,
        "end_line": 4,
        "claim_type": "bad_vibes",
        "message": "A claim type the gate does not know.",
    },
    {
        "file": "app/db.py",
        "start_line": 5,
        "end_line": 5,
        "claim_type": "sql_injection",
        # no "message": malformed, must be skipped and counted
    },
]


class RefusalTests(unittest.TestCase):
    def _reviewer(self, env, config=CONFIG, transport=None):
        return LLMReviewer.from_env(env, config, transport=transport or FakeTransport([]))

    def test_refuses_without_allow_flag(self):
        transport = FakeTransport([])
        env = armed_env()
        del env["ALLOW_REAL_LLM"]
        with self.assertRaises(RealLLMRefused):
            self._reviewer(env, transport=transport)
        self.assertEqual(transport.calls, [])

    def test_refuses_with_allow_flag_not_one(self):
        env = armed_env(ALLOW_REAL_LLM="yes")
        with self.assertRaises(RealLLMRefused):
            self._reviewer(env)

    def test_refuses_without_api_key(self):
        transport = FakeTransport([])
        env = armed_env()
        del env["OPENAI_API_KEY"]
        with self.assertRaises(RealLLMRefused):
            self._reviewer(env, transport=transport)
        self.assertEqual(transport.calls, [])

    def test_refuses_without_spend_cap(self):
        env = armed_env()
        del env["RB_MAX_SPEND_USD"]
        with self.assertRaises(RealLLMRefused):
            self._reviewer(env)

    def test_refuses_with_non_positive_spend_cap(self):
        with self.assertRaises(RealLLMRefused):
            self._reviewer(armed_env(RB_MAX_SPEND_USD="0"))

    def test_refuses_without_base_url(self):
        env = armed_env()
        del env["RB_MODEL_BASE_URL"]
        with self.assertRaises(RealLLMRefused):
            self._reviewer(env)

    def test_refuses_without_model_in_config(self):
        config = {"effort": "medium"}
        with self.assertRaises(RealLLMRefused):
            self._reviewer(armed_env(), config=config)

    def test_refuses_preflight_when_worst_case_exceeds_cap(self):
        transport = FakeTransport(MODEL_FINDINGS)
        env = armed_env(RB_MAX_SPEND_USD="0.01")
        reviewer = self._reviewer(env, transport=transport)
        diff_text, _ = load_fixture("01_sql")
        from agent.diff_parser import parse_unified_diff

        with self.assertRaises(RealLLMRefused):
            reviewer.review(
                diff_text=diff_text, diff=parse_unified_diff(diff_text), config=CONFIG
            )
        self.assertEqual(transport.calls, [])

    def test_refuses_post_call_when_reported_usage_exceeds_cap(self):
        transport = FakeTransport(
            MODEL_FINDINGS,
            usage={"prompt_tokens": 10_000_000, "completion_tokens": 10},
        )
        reviewer = self._reviewer(armed_env(), transport=transport)
        diff_text, _ = load_fixture("01_sql")
        from agent.diff_parser import parse_unified_diff

        with self.assertRaises(RealLLMRefused):
            reviewer.review(
                diff_text=diff_text, diff=parse_unified_diff(diff_text), config=CONFIG
            )
        self.assertEqual(len(transport.calls), 1)

    def test_refuses_on_http_error(self):
        transport = FakeTransport([], status=500)
        reviewer = self._reviewer(armed_env(), transport=transport)
        diff_text, _ = load_fixture("01_sql")
        from agent.diff_parser import parse_unified_diff

        with self.assertRaises(RealLLMRefused):
            reviewer.review(
                diff_text=diff_text, diff=parse_unified_diff(diff_text), config=CONFIG
            )

    def test_refuses_on_non_json_content(self):
        transport = FakeTransport([], raw_content="I found some issues, trust me.")
        reviewer = self._reviewer(armed_env(), transport=transport)
        diff_text, _ = load_fixture("01_sql")
        from agent.diff_parser import parse_unified_diff

        with self.assertRaises(RealLLMRefused):
            reviewer.review(
                diff_text=diff_text, diff=parse_unified_diff(diff_text), config=CONFIG
            )

    def test_settings_redaction_never_contains_key(self):
        settings = LLMSettings.from_env(armed_env(), CONFIG)
        self.assertNotIn(TEST_KEY, json.dumps(settings.redacted()))
        self.assertTrue(settings.redacted()["key_present"])


class RequestAndGateTests(unittest.TestCase):
    def test_request_shape_and_gate_filtering_via_run_agent(self):
        transport = FakeTransport(
            MODEL_FINDINGS,
            usage={"prompt_tokens": 1000, "completion_tokens": 100},
        )
        diff_text, pr = load_fixture("01_sql")
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="alma-reviewer",
            mode="alma",
            backend="llm",
            config=CONFIG,
            env=armed_env(),
            llm_transport=transport,
        )

        # Exactly one HTTP call, built as registered.
        self.assertEqual(len(transport.calls), 1)
        call = transport.calls[0]
        self.assertEqual(
            call["url"], "https://models.example.test/v1/chat/completions"
        )
        self.assertEqual(call["headers"]["Authorization"], f"Bearer {TEST_KEY}")
        payload = call["payload"]
        self.assertEqual(payload["model"], "gpt-5.6-sol")
        self.assertEqual(payload["reasoning_effort"], "medium")
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertIn("diff --git", payload["messages"][1]["content"])

        # The gate kept only the provable SQL injection (line 4).
        findings = result.output["findings"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["file"], "app/db.py")
        self.assertEqual(findings[0]["start_line"], 4)
        self.assertEqual(findings[0]["producer"], "alma-reviewer")

        # Ledger: 4 parsed candidates, 1 accepted / 3 rejected; 1 malformed.
        statuses = [entry["status"] for entry in result.ledger]
        self.assertEqual(statuses.count("accepted"), 1)
        self.assertEqual(statuses.count("rejected"), 3)
        self.assertIsNotNone(result.llm_run_info)
        self.assertEqual(result.llm_run_info["raw_findings"], 5)
        self.assertEqual(result.llm_run_info["malformed_findings"], 1)
        self.assertAlmostEqual(result.llm_run_info["estimated_cost_usd"], 0.0225)

    def test_base_arm_emits_all_parsed_candidates(self):
        transport = FakeTransport(MODEL_FINDINGS)
        diff_text, pr = load_fixture("01_sql")
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="base-reviewer",
            mode="base",
            backend="llm",
            config=CONFIG,
            env=armed_env(),
            llm_transport=transport,
        )
        self.assertEqual(len(result.output["findings"]), 4)

    def test_run_agent_llm_without_flags_refuses(self):
        diff_text, pr = load_fixture("01_sql")
        env = armed_env()
        del env["ALLOW_REAL_LLM"]
        with self.assertRaises(RealLLMRefused):
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="llm",
                config=CONFIG,
                env=env,
                llm_transport=FakeTransport(MODEL_FINDINGS),
            )


class CliGuardTests(unittest.TestCase):
    def test_cli_backend_llm_unarmed_exits_nonzero_and_writes_nothing(self):
        directory = FIXTURES / "01_sql"
        pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "findings.json"
            env = dict(os.environ)
            env.pop("ALLOW_REAL_LLM", None)
            env.update(
                {
                    "RB_AGENT": "cli-llm-guard",
                    "RB_HEAD": pr["head"],
                    "RB_PR_NUMBER": str(pr["pr_number"]),
                    "RB_CONFIG_BACKEND": "llm",
                    "RB_CONFIG_MODEL": "gpt-5.6-sol",
                    "PYTHONPATH": str(ROOT),
                }
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent",
                    "--diff",
                    str(directory / "diff.patch"),
                    "--pr-json",
                    str(directory / "pr.json"),
                    "--out",
                    str(out),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2, completed.stdout)
            self.assertIn("ALLOW_REAL_LLM", completed.stderr)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
