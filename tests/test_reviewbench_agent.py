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

from agent.alma_gate import POLICY_SHA256, AlmaGate  # noqa: E402
from agent.base_reviewer import BaseReviewer, Candidate  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.main import run_agent, validate_output  # noqa: E402


FIXTURES = ROOT / "fixtures"


def load_fixture(name: str):
    directory = FIXTURES / name
    diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
    pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
    expected = json.loads((directory / "expected.json").read_text(encoding="utf-8"))
    return diff_text, pr, expected


class DiffParserTests(unittest.TestCase):
    def test_head_line_numbers_and_added_context_kinds(self):
        diff_text, _, _ = load_fixture("01_sql")
        diff = parse_unified_diff(diff_text)
        self.assertEqual(
            diff.get_line("app/db.py", 4).text,
            '    query = f"SELECT * FROM users WHERE id = {user_id}"',
        )
        self.assertEqual(diff.get_line("app/db.py", 4).kind, "added")
        self.assertEqual(
            diff.get_line("app/db.py", 9).text,
            "    cursor.execute(query, (user_id,))",
        )
        self.assertIsNone(diff.get_line("app/db.py", 99))


class FixtureGateTests(unittest.TestCase):
    def test_all_fixtures_match_expected_accept_and_reject_rules(self):
        for directory in sorted(path for path in FIXTURES.iterdir() if path.is_dir()):
            with self.subTest(fixture=directory.name):
                diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
                expected = json.loads(
                    (directory / "expected.json").read_text(encoding="utf-8")
                )
                diff = parse_unified_diff(diff_text)
                candidates = BaseReviewer().review(diff)
                result = AlmaGate().validate(candidates, diff, "fixture-agent")
                accepted = {
                    entry.rule_id for entry in result.ledger if entry.status == "accepted"
                }
                rejected = {
                    entry.rule_id for entry in result.ledger if entry.status == "rejected"
                }
                self.assertEqual(accepted, set(expected["accepted_rule_ids"]))
                self.assertEqual(rejected, set(expected["rejected_rule_ids"]))
                self.assertEqual(len(result.findings), len(accepted))

    def test_false_successes_are_proposed_by_base_and_filtered_by_alma(self):
        # SQL: the parameterized call site is tempting but unsupported.
        diff_text, _, _ = load_fixture("01_sql")
        diff = parse_unified_diff(diff_text)
        base_rules = {candidate.rule_id for candidate in BaseReviewer().review(diff)}
        self.assertIn("possible_sql_injection_unverified_call_site", base_rules)

        # The word cache is not evidence of a race.
        diff_text, _, _ = load_fixture("02_error_handling")
        diff = parse_unified_diff(diff_text)
        base_rules = {candidate.rule_id for candidate in BaseReviewer().review(diff)}
        self.assertIn("possible_cache_race_condition", base_rules)

        # A credential-like name backed by os.getenv is not a hardcoded secret.
        diff_text, _, _ = load_fixture("03_mutable_default")
        diff = parse_unified_diff(diff_text)
        base_rules = {candidate.rule_id for candidate in BaseReviewer().review(diff)}
        self.assertIn("possible_hardcoded_secret_from_name", base_rules)

    def test_unknown_claim_fails_closed(self):
        diff_text, _, _ = load_fixture("01_sql")
        diff = parse_unified_diff(diff_text)
        line = diff.get_line("app/db.py", 4)
        candidate = Candidate(
            rule_id="unknown_claim",
            claim_type="not_a_registered_claim",
            file=line.file,
            start_line=line.line_number,
            end_line=line.line_number,
            message="Unsupported claim.",
            evidence_text=(line.text,),
            severity_hint="high",
            category_hint="correctness",
        )
        result = AlmaGate().validate([candidate], diff, "fixture-agent")
        self.assertEqual(result.findings, [])
        self.assertEqual(result.ledger[0].status, "rejected")
        self.assertEqual(len(POLICY_SHA256), 64)


class AgentContractTests(unittest.TestCase):
    def test_output_has_exact_contract_shape(self):
        diff_text, pr, _ = load_fixture("04_secrets_tls")
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="alma-reviewer",
            mode="alma",
            backend="mock",
        )
        validate_output(
            result.output,
            expected_head=pr["head"],
            expected_pr_number=pr["pr_number"],
        )
        self.assertEqual(set(result.output), {"pr", "agent", "findings"})
        self.assertEqual(len(result.output["findings"]), 2)
        for finding in result.output["findings"]:
            self.assertEqual(
                set(finding),
                {"file", "start_line", "end_line", "message", "producer"},
            )
            self.assertEqual(finding["producer"], "alma-reviewer")
            self.assertNotIn("severity", finding)
            self.assertNotIn("category", finding)

    def test_base_arm_includes_the_false_sql_candidate(self):
        diff_text, pr, _ = load_fixture("01_sql")
        base = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="base-reviewer",
            mode="base",
            backend="mock",
        )
        alma = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="alma-reviewer",
            mode="alma",
            backend="mock",
        )
        self.assertEqual(len(base.output["findings"]), 2)
        self.assertEqual(len(alma.output["findings"]), 1)
        self.assertEqual(alma.output["findings"][0]["start_line"], 4)

    def test_cli_writes_contract_file_and_ledger(self):
        directory = FIXTURES / "01_sql"
        pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "findings.json"
            ledger = Path(tmp) / "ledger.json"
            env = dict(os.environ)
            env.update(
                {
                    "RB_AGENT": "cli-fixture-agent",
                    "RB_HEAD": pr["head"],
                    "RB_PR_NUMBER": str(pr["pr_number"]),
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
                    "--ledger",
                    str(ledger),
                    "--mode",
                    "alma",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = json.loads(out.read_text(encoding="utf-8"))
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual(output["agent"], "cli-fixture-agent")
            self.assertEqual(len(output["findings"]), 1)
            self.assertEqual(
                {entry["status"] for entry in ledger_data}, {"accepted", "rejected"}
            )
            self.assertIn("effective_backend=mock", completed.stdout)


class StaticPackageTests(unittest.TestCase):
    def test_dockerfile_uses_no_argument_entrypoint(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("linux/amd64", dockerfile)
        self.assertIn('ENTRYPOINT ["python", "-m", "agent"]', dockerfile)
        self.assertNotIn("OPENAI_API_KEY=", dockerfile)
        self.assertNotIn("ANTHROPIC_API_KEY=", dockerfile)


if __name__ == "__main__":
    unittest.main()
