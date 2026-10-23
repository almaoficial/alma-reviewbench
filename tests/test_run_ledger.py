"""Run session ledger tests — PREREGISTRO-REGISTRO-SESION.md §3.

(a) a full simulated run (one ledger instance per PR, the real
    one-process-per-PR pattern) chains and audits complete;
(b) kill mid-run + torn tail + resume loses nothing and
    duplicates nothing;
(c) truncation is detectable two ways — completeness audit for
    a cut tail, chain verification for a cut or altered middle;
(d) the nº 311 scenario does not repeat: every candidate the
    gate disposed of has exactly one seated decision, not only
    the emitted finding;
(e) the portal-mount failure mode, simulated: an unwritable
    ledger path never breaks the run and is never silent, and
    two separate CLI invocations chain into one file.
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

from agent.alma_gate_v141 import POLICY_SHA256 as POLICY_SHA256_V141  # noqa: E402
from agent.alma_gate_v141 import POLICY_VERSION as POLICY_VERSION_V141  # noqa: E402
from agent.main import run_agent  # noqa: E402
from agent.run_ledger import (  # noqa: E402
    RunLedger,
    RunLedgerError,
    audit_completeness,
    candidate_id_for,
    read_events,
    record_gate_decisions,
    record_session_close,
    record_session_open,
    verify_chain,
)

FIXTURES = ROOT / "fixtures"
RUN_ID = "test-run-ledger"


def load_fixture(name: str):
    directory = FIXTURES / name
    diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
    pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
    return diff_text, pr


def open_session(ledger: RunLedger, pr, *, segment: str = "seg-1") -> None:
    record_session_open(
        ledger,
        segment=segment,
        agent="ledger-test-agent",
        mode="alma",
        backend="mock",
        config={"gate": "v141"},
        gate_version=POLICY_VERSION_V141,
        policy_sha256=POLICY_SHA256_V141,
        image_sha256=None,
        max_spend_usd=None,
        pr=pr,
    )


def close_session(ledger: RunLedger, pr, result, *, segment: str = "seg-1"):
    counts = {"accepted": 0, "rejected": 0}
    for entry in result.ledger:
        if entry["status"] in counts:
            counts[entry["status"]] += 1
    record_session_close(
        ledger,
        pr_number=int(pr["pr_number"]),
        segment=segment,
        counts={
            "candidates": len(result.candidates),
            "accepted": counts["accepted"],
            "rejected": counts["rejected"],
            "needs_validation": len(result.needs_validation or []),
        },
        findings_emitted=len(result.output["findings"]),
        spend_estimated_usd=0.0,
        resumed=False,
    )


def run_pr_with_ledger(path: Path, fixture: str, *, mode: str = "alma"):
    """One PR through run_agent with the ledger opened and
    closed around it exactly as main() does — the
    one-process-per-PR pattern of the portal."""

    diff_text, pr = load_fixture(fixture)
    ledger = RunLedger(path, run_id=RUN_ID)
    try:
        open_session(ledger, pr)
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="ledger-test-agent",
            mode=mode,
            backend="mock",
            config={"gate": "v141"},
            run_ledger=ledger,
        )
        close_session(ledger, pr, result)
    finally:
        ledger.close()
    return result


class ChainBasicsTests(unittest.TestCase):
    def test_candidate_id_is_a_content_address(self):
        kwargs = dict(
            rule_id="r",
            claim_type="c",
            file="a.py",
            start_line=1,
            end_line=2,
            message="m",
        )
        self.assertEqual(candidate_id_for(**kwargs), candidate_id_for(**kwargs))
        self.assertEqual(len(candidate_id_for(**kwargs)), 16)
        other = dict(kwargs, message="different")
        self.assertNotEqual(candidate_id_for(**kwargs), candidate_id_for(**other))

    def test_genesis_and_append_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run-ledger.jsonl"
            with RunLedger(path, run_id=RUN_ID) as ledger:
                ledger.append("session_open", {"pr_number": 1})
                ledger.append("session_close", {"pr_number": 1})
            result = verify_chain(path)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["lines"], 2)
            events = read_events(path)
            self.assertEqual(events[0]["prev"], "0" * 64)
            self.assertEqual(events[1]["prev"], events[0]["hash"])
            self.assertEqual(events[1]["seq"], 1)


class FullSimulatedRunTests(unittest.TestCase):
    def test_a_full_run_chains_and_audits_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run-ledger.jsonl"
            run_pr_with_ledger(path, "01_sql")
            run_pr_with_ledger(path, "02_error_handling")
            run_pr_with_ledger(path, "03_mutable_default", mode="base")

            chain = verify_chain(path)
            self.assertTrue(chain["ok"], chain)
            audit = audit_completeness(path)
            self.assertTrue(audit["complete"], audit)
            self.assertEqual(len(audit["per_pr"]), 3)
            for pr in audit["per_pr"]:
                self.assertEqual(pr["candidates"], 2)
                self.assertEqual(pr["decisions"], 2)
                self.assertEqual(pr["decisions_missing"], [])
                self.assertEqual(pr["spend_events"], 1)


class KillAndResumeTests(unittest.TestCase):
    def test_b_kill_torn_tail_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run-ledger.jsonl"
            diff_text, pr = load_fixture("01_sql")
            pr_number = int(pr["pr_number"])

            ledger = RunLedger(path, run_id=RUN_ID)
            open_session(ledger, pr)
            result = run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="ledger-test-agent",
                mode="alma",
                backend="mock",
                config={"gate": "v141"},
                run_ledger=ledger,
            )
            seated = ledger.event_count
            ledger.close()
            # The session was never closed: reopening must see it
            # as unclosed (the kill), then a torn tail simulates
            # the crash landing mid-append.
            probe = RunLedger(path, run_id=RUN_ID)
            self.assertTrue(probe.unclosed_session(pr_number))
            probe.close()
            with open(path, "a", encoding="utf-8") as fh:
                fh.write('{"seq": 99, "ts": "torn mid-wri')

            resumed = RunLedger(path, run_id=RUN_ID)
            self.assertEqual(resumed.recovered_torn_tail, 1)
            self.assertEqual(resumed.event_count, seated)
            # Re-emitting the very same PR (same run_id) seats
            # nothing twice: candidate/decision/spend dedupe.
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="ledger-test-agent",
                mode="alma",
                backend="mock",
                config={"gate": "v141"},
                run_ledger=resumed,
            )
            self.assertEqual(resumed.event_count, seated)
            resumed.close()

            chain = verify_chain(path)
            self.assertTrue(chain["ok"], chain)
            keys = [
                (e.get("data") or {}).get("dedupe_key")
                for e in read_events(path)
            ]
            keys = [k for k in keys if k]
            self.assertEqual(len(keys), len(set(keys)))
            self.assertEqual(len(result.candidates), 2)


class TruncationDetectionTests(unittest.TestCase):
    def _complete_log(self, tmp: str) -> Path:
        path = Path(tmp) / "run-ledger.jsonl"
        run_pr_with_ledger(path, "01_sql")
        run_pr_with_ledger(path, "04_secrets_tls")
        return path

    def test_c_tail_truncation_caught_by_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._complete_log(tmp)
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            path.write_text("".join(lines[:-2]), encoding="utf-8")
            chain = verify_chain(path)
            self.assertTrue(chain["ok"], chain)  # what remains is intact
            audit = audit_completeness(path)
            self.assertFalse(audit["complete"], audit)

    def test_c_middle_truncation_and_tamper_caught_by_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._complete_log(tmp)
            raw = path.read_bytes()
            newline = raw.find(b"\n", len(raw) // 2)
            path.write_bytes(raw[: newline - 5])  # cut mid-line
            chain = verify_chain(path)
            self.assertFalse(chain["ok"], chain)

            path2 = self._complete_log(tmp)
            lines = path2.read_text(encoding="utf-8").splitlines()
            middle = json.loads(lines[2])
            middle["data"]["tampered"] = True
            lines[2] = json.dumps(middle, ensure_ascii=False)
            path2.write_text("\n".join(lines) + "\n", encoding="utf-8")
            chain2 = verify_chain(path2)
            self.assertFalse(chain2["ok"], chain2)
            self.assertTrue(
                any("seq 2" in e for e in chain2["errors"]), chain2
            )


class Scenario311Tests(unittest.TestCase):
    def test_d_every_candidate_has_exactly_one_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run-ledger.jsonl"
            result = run_pr_with_ledger(path, "01_sql")
            # The 311 shape: fewer findings emitted than
            # candidates disposed of — retention is the record.
            self.assertEqual(len(result.candidates), 2)
            self.assertEqual(len(result.output["findings"]), 1)
            events = read_events(path)
            decisions = [
                e for e in events if e["event"] == "gate_decision"
            ]
            self.assertEqual(len(decisions), 2)
            self.assertEqual(
                {d["data"]["status"] for d in decisions},
                {"accepted", "rejected"},
            )
            audit = audit_completeness(path)
            pr_audit = audit["per_pr"][0]
            self.assertEqual(pr_audit["decisions_missing"], [])
            self.assertEqual(pr_audit["decisions"], 2)

    def test_d_needs_validation_decision_keeps_its_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run-ledger.jsonl"
            ledger = RunLedger(path, run_id=RUN_ID)
            held = [
                {
                    "rule_id": "llm_v23_correctness",
                    "claim_type": "correctness",
                    "file": "app/x.py",
                    "start_line": 3,
                    "end_line": 3,
                    "message": "General claim without a gate rule.",
                    "producer": "alma-llm-reviewer-v23",
                    "blockers": [
                        {"code": "sin_regla_de_verificacion_en_puerta"}
                    ],
                    "validator_version": "alma-evidence-gate/1.4.1",
                    "policy_sha256": "0" * 64,
                }
            ]
            counts = record_gate_decisions(
                ledger, pr_number=7, ledger_entries=[], needs_validation=held
            )
            ledger.close()
            self.assertEqual(counts["needs_validation"], 1)
            (event,) = [
                e for e in read_events(path) if e["event"] == "gate_decision"
            ]
            self.assertEqual(event["data"]["status"], "needs_validation")
            self.assertEqual(
                event["data"]["reasons"],
                ["sin_regla_de_verificacion_en_puerta"],
            )
            self.assertEqual(
                event["data"]["blockers"],
                [{"code": "sin_regla_de_verificacion_en_puerta"}],
            )


class PortalMountSimulationTests(unittest.TestCase):
    def _cli_env(self, tmp: str, ledger_path: Path, pr) -> dict:
        env = dict(os.environ)
        env.update(
            {
                "RB_AGENT": "cli-ledger-agent",
                "RB_HEAD": pr["head"],
                "RB_PR_NUMBER": str(pr["pr_number"]),
                "RB_RUN_ID": RUN_ID,
                "ALMA_RUN_LEDGER_PATH": str(ledger_path),
                "PYTHONPATH": str(ROOT),
            }
        )
        return env

    def _cli_run(self, fixture: str, out: Path, env: dict):
        directory = FIXTURES / fixture
        pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
        return subprocess.run(
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
                "--mode",
                "alma",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_e_unwritable_ledger_path_never_breaks_the_run(self):
        # Simulated read-only portal mount: the ledger path's
        # parent is a regular file, so opening it must fail —
        # and the failure must be announced, not silent (311's
        # loss was silent), while findings are still produced.
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "portal-is-a-file"
            blocker.write_text("not a directory", encoding="utf-8")
            ledger_path = blocker / "run-ledger.jsonl"
            _, pr = load_fixture("01_sql")
            env = self._cli_env(tmp, ledger_path, pr)
            out = Path(tmp) / "findings.json"
            completed = self._cli_run("01_sql", out, env)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(out.exists())
            self.assertIn("run-ledger disabled", completed.stderr)

    def test_e_two_cli_invocations_chain_into_one_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "own-side" / "run-ledger.jsonl"
            _, pr1 = load_fixture("01_sql")
            env1 = self._cli_env(tmp, ledger_path, pr1)
            first = self._cli_run(
                "01_sql", Path(tmp) / "f1.json", env1
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            _, pr2 = load_fixture("04_secrets_tls")
            env2 = self._cli_env(tmp, ledger_path, pr2)
            second = self._cli_run(
                "04_secrets_tls", Path(tmp) / "f2.json", env2
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("run_ledger events=", second.stdout)
            chain = verify_chain(ledger_path)
            self.assertTrue(chain["ok"], chain)
            audit = audit_completeness(ledger_path)
            self.assertTrue(audit["complete"], audit)
            self.assertEqual(len(audit["per_pr"]), 2)
            for pr in audit["per_pr"]:
                self.assertEqual(pr["sessions_opened"], 1)
                self.assertEqual(pr["sessions_closed"], 1)
                self.assertEqual(pr["decisions"], pr["candidates"])


class CorruptMiddleTests(unittest.TestCase):
    def test_open_fails_closed_on_a_corrupt_middle(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run-ledger.jsonl"
            with RunLedger(path, run_id=RUN_ID) as ledger:
                ledger.append("session_open", {"pr_number": 1})
                ledger.append("candidate", {"pr_number": 1})
                ledger.append("session_close", {"pr_number": 1})
            lines = path.read_text(encoding="utf-8").splitlines()
            lines[1] = "{not json"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaises(RunLedgerError):
                RunLedger(path, run_id=RUN_ID)


if __name__ == "__main__":
    unittest.main()
