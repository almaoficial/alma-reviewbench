"""Mounting tests — PREREGISTRO-VALIDACION-20261024.md §3.

What is verified dry (US$0, scripted transports only): the
admissions the 24/10 validation needs and did not have —

- agent/main.py selects reviewers "v24", "v25" and "v26"
  (before this mounting its list ended at "v23");
- agent/main.py's gate selection and gate identity admit
  "v150" (before, they ended at "v141");
- the v2.4-family resolver `_resolve_gate_v24` admits "v150"
  with the 1.5.0's specialty family (the 1.3.0's 19 classes)
  and delegates every other value to `_resolve_gate_v23`
  unchanged;
- the three reviewers construct from env with gate=v150
  (no model call: construction only);
- one full run through run_agent — mode "alma", reviewer
  "v26", gate "v150", scripted transport — is gated by the
  1.5.0 and seats a complete session in the run ledger:
  chain verifies, completeness audits clean (the adjudication
  rule of the pre-registration, §6, exercised dry).

No test here measures any effect of the arms: that is what
the paid run of 2026-10-24 is for.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent import alma_gate_v150  # noqa: E402
from agent.alma_gate_v13 import KNOWN_CLAIM_TYPES_V13  # noqa: E402
from agent.alma_gate_v141 import AlmaGateV141  # noqa: E402
from agent.llm_reviewer import RealLLMRefused  # noqa: E402
from agent.llm_reviewer_v23 import _CLASS_GUIDANCE_V13, _resolve_gate_v23  # noqa: E402
from agent import llm_reviewer_v24, llm_reviewer_v25, llm_reviewer_v26  # noqa: E402
from agent.llm_reviewer_v24 import (  # noqa: E402
    LLMReviewerV24,
    _resolve_gate_v24,
)
from agent.llm_reviewer_v25 import LLMReviewerV25  # noqa: E402
from agent.llm_reviewer_v26 import LLMReviewerV26  # noqa: E402
from agent.main import _select_gate, _selected_gate_identity, run_agent  # noqa: E402
from agent.run_ledger import (  # noqa: E402
    RunLedger,
    audit_completeness,
    record_session_close,
    record_session_open,
    verify_chain,
)
from test_gate_v11 import make_diff  # noqa: E402
from test_llm_reviewer_v23 import armed_env  # noqa: E402
from test_llm_reviewer_v24 import LINES, PATH, EmissionTransport, _finding  # noqa: E402

CONFIG_V150 = {
    "model": "gpt-5.6-sol",
    "effort": "medium",
    "gate": "v150",
}


class GateAdmissionTests(unittest.TestCase):
    def test_select_gate_v150(self):
        gate = _select_gate({"gate": "v150"})
        self.assertIsInstance(gate, alma_gate_v150.AlmaGateV150)
        self.assertEqual(gate.policy_sha256, alma_gate_v150.POLICY_SHA256)
        self.assertEqual(gate.version, "alma-evidence-gate/1.5.0")

    def test_gate_identity_v150(self):
        self.assertEqual(
            _selected_gate_identity({"gate": "v150"}),
            (alma_gate_v150.POLICY_VERSION, alma_gate_v150.POLICY_SHA256),
        )

    def test_prior_gates_unchanged(self):
        self.assertIsInstance(_select_gate({"gate": "v141"}), AlmaGateV141)
        with self.assertRaises(ValueError):
            _select_gate({"gate": "v999"})


class ResolverV24Tests(unittest.TestCase):
    def test_v150_branch(self):
        claim_types, guidance, version = _resolve_gate_v24({"gate": "v150"})
        self.assertEqual(version, "alma-evidence-gate/1.5.0")
        self.assertEqual(claim_types, KNOWN_CLAIM_TYPES_V13)
        self.assertEqual(len(claim_types), 19)
        self.assertIs(guidance, _CLASS_GUIDANCE_V13)

    def test_v150_claim_types_equal_gate_policy_set(self):
        # The premise of the branch, by program: the 1.5.0's own
        # claim set IS the 1.3.0's 19 (its class behaviour is the
        # 1.4.1's by delegation).
        self.assertEqual(
            tuple(sorted(KNOWN_CLAIM_TYPES_V13)),
            alma_gate_v150.KNOWN_CLAIM_TYPES_V150,
        )

    def test_delegation_unchanged(self):
        for value in ("v1", "v11", "v12", "v13", "v14", "v141"):
            self.assertEqual(
                _resolve_gate_v24({"gate": value}),
                _resolve_gate_v23({"gate": value}),
            )
        self.assertEqual(
            _resolve_gate_v24({}), _resolve_gate_v23({})
        )

    def test_unknown_gate_refused(self):
        with self.assertRaises(RealLLMRefused):
            _resolve_gate_v24({"gate": "v999"})


class FromEnvAdmissionTests(unittest.TestCase):
    def test_three_reviewers_construct_with_v150(self):
        for cls, module in (
            (LLMReviewerV24, llm_reviewer_v24),
            (LLMReviewerV25, llm_reviewer_v25),
            (LLMReviewerV26, llm_reviewer_v26),
        ):
            reviewer = cls.from_env(
                armed_env(), dict(CONFIG_V150), transport=EmissionTransport()
            )
            self.assertEqual(reviewer.gate_version, "alma-evidence-gate/1.5.0")
            self.assertTrue(module.REVIEWER_VERSION.startswith("llm-reviewer/"))


class EndToEndMountingTests(unittest.TestCase):
    def test_run_agent_v26_v150_with_run_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            target = repo / PATH
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(LINES) + "\n", encoding="utf-8")
            diff_text = make_diff(PATH, LINES)
            pr = {
                "repo": "example/mounting",
                "pr_number": 7,
                "base": "base-sha",
                "head": "head-sha",
            }
            transport = EmissionTransport(
                marks=["correctness"],
                deep={"correctness": {"findings": [_finding()],
                                      "unverifiable": []}},
            )
            ledger_path = Path(tmp) / "run-ledger.jsonl"
            run_id = "validacion-20261024-v26"
            gate_version, policy_sha = _selected_gate_identity(
                {"gate": "v150"})
            ledger = RunLedger(ledger_path, run_id=run_id)
            try:
                record_session_open(
                    ledger,
                    segment="seg-1",
                    agent="alma-reviewer",
                    mode="alma",
                    backend="llm",
                    config={"reviewer": "v26", "gate": "v150"},
                    gate_version=gate_version,
                    policy_sha256=policy_sha,
                    image_sha256="sha256:mounting-test",
                    max_spend_usd=6.50,
                    pr=pr,
                )
                result = run_agent(
                    diff_text=diff_text,
                    pr_metadata=pr,
                    agent_name="alma-reviewer",
                    mode="alma",
                    backend="llm",
                    config=dict(
                        CONFIG_V150,
                        reviewer="v26",
                        repo_root=str(repo),
                    ),
                    env=armed_env(),
                    llm_transport=transport,
                    run_ledger=ledger,
                )
                counts = {"accepted": 0, "rejected": 0}
                for entry in result.ledger:
                    if entry["status"] in counts:
                        counts[entry["status"]] += 1
                record_session_close(
                    ledger,
                    pr_number=7,
                    segment="seg-1",
                    counts={
                        "candidates": len(result.candidates),
                        "accepted": counts["accepted"],
                        "rejected": counts["rejected"],
                        "needs_validation": len(result.needs_validation or []),
                    },
                    findings_emitted=len(result.output["findings"]),
                    spend_estimated_usd=float(
                        result.llm_run_info.get("estimated_cost_usd") or 0.0
                    ),
                    resumed=False,
                )
            finally:
                ledger.close()

            # The arm produced, and the 1.5.0 gated it.
            self.assertEqual(len(result.candidates), 1)
            self.assertEqual(len(result.output["findings"]), 1)
            self.assertEqual(
                [e["validator_version"] for e in result.ledger],
                ["alma-evidence-gate/1.5.0"],
            )
            self.assertEqual(
                result.llm_run_info["reviewer_version"], "llm-reviewer/2.6.0"
            )
            # The adjudication rule of §6, dry: chain + completeness.
            self.assertTrue(verify_chain(ledger_path)["ok"])
            audit = audit_completeness(ledger_path)
            self.assertTrue(audit["complete"], audit)
            self.assertEqual(audit["per_pr"][0]["candidates"], 1)
            self.assertEqual(audit["per_pr"][0]["decisions"], 1)


class ImageLayoutTests(unittest.TestCase):
    def test_reviewers_construct_from_image_layout(self):
        # The image is /app/agent + the two context artifacts at
        # /app (Dockerfile).  Copy exactly that layout and
        # construct the three reviewers from it in a subprocess
        # whose only package is the copy: if a context artifact
        # were missing from the image, v25/v26 would refuse
        # here, fail-closed, as they would in the portal.
        import shutil
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "agent", root / "agent")
            for name in ("CONTEXTO-LECCIONES.md", "CONTEXTO-AUSENCIAS.md"):
                shutil.copy2(ROOT / name, root / name)
            script = (
                "import sys\n"
                "sys.path.insert(0, '.')\n"
                "from agent.llm_reviewer_v24 import LLMReviewerV24\n"
                "from agent.llm_reviewer_v25 import LLMReviewerV25\n"
                "from agent.llm_reviewer_v26 import LLMReviewerV26\n"
                "cfg = {'model': 'gpt-5.6-sol', 'effort': 'medium',"
                " 'gate': 'v150'}\n"
                "for cls in (LLMReviewerV24, LLMReviewerV25, LLMReviewerV26):\n"
                "    r = cls.from_env(dict(__import__('os').environ), cfg)\n"
                "    assert r.gate_version == 'alma-evidence-gate/1.5.0',"
                " r.gate_version\n"
                "print('IMAGE-LAYOUT-OK')\n"
            )
            env = dict(armed_env())
            import os

            full_env = dict(os.environ)
            full_env.update(env)
            proc = subprocess.run(
                [sys.executable, "-c", script],
                cwd=root,
                env=full_env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("IMAGE-LAYOUT-OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
