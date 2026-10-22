"""Reviewer v2.3.1 fix tests: the selection completion ceiling and
parse-failure observability.

Source: DIAGNOSTICO-PRACTICA-V23-20261021.md — practice run #296
died at the generalized selection's JSON parse in 20 of 35 attempts
(cause (d)): the selection inherited the 1,024-token completion
ceiling unchanged from v2–v2.2, and on real diffs the reasoning
over 28 marks exhausts it, so the content returns empty or
truncated.  The code settled neither the body nor the
finish_reason, so the fine mechanism stayed inference.

The fix, two pieces and nothing else:
(i) the selection ceiling defaults to 4,096 — the deep passes'
    own ceiling — via the existing configuration path; pinning it
    to 1024 reproduces the measured v2.3.0 budget exactly;
(ii) every unparseable/empty response settles a parse_failures
    record in the run info (pass, finish_reason, content length,
    bounded excerpt) and the refusal message carries the same
    data.  Fail-closed does not move.

Everything runs on scripted transports: no real model call, US$0.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused  # noqa: E402
from agent.llm_reviewer_v23 import (  # noqa: E402
    DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS,
    PARSE_FAILURE_EXCERPT_CHARS,
    LLMReviewerV23,
)
from test_llm_reviewer_v22 import make_repo  # noqa: E402
from test_llm_reviewer_v23 import (  # noqa: E402
    CONFIG_ALMA_V14,
    GeneralizedTransport,
    armed_env,
    pass_name_of,
)


class RawContentTransport:
    """Answers each pass with a RAW content string and a
    finish_reason — the shape a truncated real response takes,
    which GeneralizedTransport (always valid JSON) cannot make."""

    USAGE = {"prompt_tokens": 100, "completion_tokens": 10}

    def __init__(self, answers):
        # answers: {pass_name: (content_str, finish_reason)}
        self.answers = dict(answers)
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(payload)
        name = pass_name_of(payload)
        content, finish_reason = self.answers.get(
            name, ('{"findings": []}', "stop")
        )
        body = {
            "choices": [
                {
                    "message": {"content": content},
                    "finish_reason": finish_reason,
                }
            ],
            "usage": self.USAGE,
        }
        return 200, json.dumps(body).encode("utf-8")


def _review(reviewer, repo, diff_text):
    return reviewer.review(
        diff_text=diff_text,
        diff=parse_unified_diff(diff_text),
        config=CONFIG_ALMA_V14,
        mode="alma",
        repo_root=repo,
    )


class SelectionCeilingTests(unittest.TestCase):
    def test_default_ceiling_is_4096_and_applies_only_to_selection(self):
        reviewer = LLMReviewerV23.from_env(
            armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
        )
        self.assertEqual(DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS, 4096)
        self.assertEqual(reviewer.triage_max_output_tokens, 4096)
        selection = reviewer.build_selection_payload("DIFF")
        self.assertEqual(selection["max_completion_tokens"], 4096)
        # The deep passes keep their own ceiling, untouched: the
        # settings default the v2.3.0 runs already used.
        deep = reviewer.build_deep_payload("weak_hash", "DIFF", "CONTEXT")
        self.assertEqual(
            deep["max_completion_tokens"], reviewer.settings.max_output_tokens
        )
        self.assertEqual(deep["max_completion_tokens"], 4096)

    def test_measured_v230_budget_reproducible_by_env_pin(self):
        reviewer = LLMReviewerV23.from_env(
            armed_env(RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS="1024"),
            CONFIG_ALMA_V14,
            transport=GeneralizedTransport(),
        )
        self.assertEqual(reviewer.triage_max_output_tokens, 1024)
        payload = reviewer.build_selection_payload("DIFF")
        self.assertEqual(payload["max_completion_tokens"], 1024)

    def test_measured_v230_budget_reproducible_by_config_pin(self):
        config = dict(CONFIG_ALMA_V14, triage_max_output_tokens="1024")
        reviewer = LLMReviewerV23.from_env(
            armed_env(), config, transport=GeneralizedTransport()
        )
        self.assertEqual(reviewer.triage_max_output_tokens, 1024)
        payload = reviewer.build_selection_payload("DIFF")
        self.assertEqual(payload["max_completion_tokens"], 1024)

    def test_ceiling_delta_is_exactly_the_output_price_of_3072_tokens(self):
        # The fix's whole worst-case price: (4096 - 1024) output
        # tokens at the planning band of US$75/Mtok = US$0.2304,
        # on any selection payload (same input estimate).
        pinned = LLMReviewerV23.from_env(
            armed_env(RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS="1024"),
            CONFIG_ALMA_V14,
            transport=GeneralizedTransport(),
        )
        fixed = LLMReviewerV23.from_env(
            armed_env(), CONFIG_ALMA_V14, transport=GeneralizedTransport()
        )
        delta = fixed.worst_case_estimate(
            fixed.build_selection_payload("DIFF")
        ) - pinned.worst_case_estimate(pinned.build_selection_payload("DIFF"))
        self.assertAlmostEqual(delta, 0.2304, places=6)


class ParseFailureObservabilityTests(unittest.TestCase):
    def test_selection_truncated_json_settles_finish_reason_and_excerpt(self):
        truncated = '{"candidates": [{"mark": "sql_injection", "reas'
        transport = RawContentTransport({"selection": (truncated, "length")})
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, _ = make_repo(tmp)
            reviewer = LLMReviewerV23.from_env(
                armed_env(), CONFIG_ALMA_V14, transport=transport
            )
            with self.assertRaises(RealLLMRefused) as caught:
                _review(reviewer, repo, diff_text)
            info = reviewer.last_run_info
            self.assertIsNotNone(info)
            self.assertEqual(len(info.parse_failures), 1)
            record = info.parse_failures[0]
            self.assertEqual(record["pass"], "selection")
            self.assertEqual(record["finish_reason"], "length")
            self.assertEqual(record["content_length"], len(truncated))
            self.assertEqual(record["content_excerpt"], truncated)
            # The refusal message carries the settled data too, so
            # the agent log (which prints only the exception) shows
            # it — and the original fail-closed text stays the
            # prefix, exactly as in run #296's logs.
            message = str(caught.exception)
            self.assertTrue(
                message.startswith(
                    "selection pass did not return parseable JSON; "
                    "failing closed"
                )
            )
            self.assertIn("finish_reason='length'", message)
            self.assertIn("pass=selection", message)

    def test_selection_empty_content_settles_instead_of_blind_refusal(self):
        transport = RawContentTransport({"selection": ("", "length")})
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, _ = make_repo(tmp)
            reviewer = LLMReviewerV23.from_env(
                armed_env(), CONFIG_ALMA_V14, transport=transport
            )
            with self.assertRaises(RealLLMRefused):
                _review(reviewer, repo, diff_text)
            record = reviewer.last_run_info.parse_failures[0]
            self.assertEqual(record["pass"], "selection")
            self.assertEqual(record["finish_reason"], "length")
            self.assertEqual(record["content_length"], 0)
            self.assertEqual(record["content_excerpt"], "")

    def test_excerpt_is_bounded_at_500_chars(self):
        garbage = "x" * 5000
        transport = RawContentTransport({"selection": (garbage, "stop")})
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, _ = make_repo(tmp)
            reviewer = LLMReviewerV23.from_env(
                armed_env(), CONFIG_ALMA_V14, transport=transport
            )
            with self.assertRaises(RealLLMRefused):
                _review(reviewer, repo, diff_text)
            record = reviewer.last_run_info.parse_failures[0]
            self.assertEqual(record["content_length"], 5000)
            self.assertEqual(
                len(record["content_excerpt"]), PARSE_FAILURE_EXCERPT_CHARS
            )

    def test_deep_pass_parse_failure_settles_and_still_fails_closed(self):
        selection = json.dumps(
            {"candidates": [{"mark": "weak_hash", "reason": "scripted"}]}
        )
        transport = RawContentTransport(
            {
                "selection": (selection, "stop"),
                "weak_hash": ("this is not json at all", "stop"),
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, _ = make_repo(tmp)
            reviewer = LLMReviewerV23.from_env(
                armed_env(), CONFIG_ALMA_V14, transport=transport
            )
            with self.assertRaises(RealLLMRefused) as caught:
                _review(reviewer, repo, diff_text)
            info = reviewer.last_run_info
            self.assertEqual(len(info.parse_failures), 1)
            record = info.parse_failures[0]
            self.assertEqual(record["pass"], "weak_hash")
            self.assertEqual(record["finish_reason"], "stop")
            self.assertEqual(record["content_excerpt"], "this is not json at all")
            self.assertIn("pass=weak_hash", str(caught.exception))

    def test_successful_run_settles_ceiling_and_no_parse_failures(self):
        transport = GeneralizedTransport(marks=["weak_hash"])
        with tempfile.TemporaryDirectory() as tmp:
            repo, diff_text, _ = make_repo(tmp)
            reviewer = LLMReviewerV23.from_env(
                armed_env(), CONFIG_ALMA_V14, transport=transport
            )
            _review(reviewer, repo, diff_text)
            settled = reviewer.last_run_info.to_dict()
            self.assertEqual(settled["triage_max_output_tokens"], 4096)
            self.assertEqual(settled["parse_failures"], [])
            self.assertEqual(settled["reviewer_version"], "llm-reviewer/2.3.1")


if __name__ == "__main__":
    unittest.main()
