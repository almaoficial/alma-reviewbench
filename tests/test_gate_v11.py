"""Tests for the gate alma-evidence-gate/1.1.0 (agent/alma_gate_v11.py).

Provenance: PREREGISTRO-REVIEWBENCH-V2.md, Adenda 1 (2026-10-19).  The
1.1.0 inherits the frozen 1.0.0's 8 classes with identical rules and
adds 6 mechanically verifiable classes.  Everything runs offline.

What this suite proves:

- the frozen gate is untouched (its POLICY_SHA256 is the literal of
  record) and the 1.1.0 carries its own version and hash;
- each NEW class accepts a correct candidate and rejects the
  adversarial look-alikes named in the addendum (open( under a with,
  a typed except that actually handles, defusedxml present, mktemp
  absent, CERT_NONE absent, random for a non-security name);
- the 8 inherited classes accept/reject IDENTICALLY under the 1.0.0
  and the 1.1.0 — unit-level evidence pairs plus an end-to-end
  cross-check over the existing fixtures_v2;
- end to end, with RB_CONFIG_GATE=v11 the v2 reviewer makes one pass
  per 1.1.0 class (14 in the ALMA arm) and its candidates are accepted
  by the 1.1.0 (fixtures_v11, one per new class, three of them with an
  in-file adversarial the gate must reject);
- gate selection defaults to v1 and fails closed on unknown values.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import alma_gate  # noqa: E402
from agent.alma_gate import AlmaGate  # noqa: E402
from agent.alma_gate_v11 import (  # noqa: E402
    INHERITED_CLAIM_TYPES,
    KNOWN_CLAIM_TYPES_V11,
    NEW_CLAIM_TYPES,
    POLICY_SHA256 as POLICY_SHA256_V11,
    POLICY_VERSION as POLICY_VERSION_V11,
    AlmaGateV11,
)
from agent.base_reviewer import Candidate  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused  # noqa: E402
from agent.main import run_agent  # noqa: E402


FIXTURES_V2 = ROOT / "fixtures_v2"
FIXTURES_V11 = ROOT / "fixtures_v11"
TEST_KEY = "test-key-not-a-real-secret"
USAGE = {"prompt_tokens": 100, "completion_tokens": 10}
FROZEN_V10_SHA256 = "3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35"

CONFIG_V11_ALMA = {
    "model": "gpt-5.6-sol",
    "effort": "medium",
    "governance": "alma",
    "reviewer": "v2",
    "gate": "v11",
}
CONFIG_V10_ALMA = {
    "model": "gpt-5.6-sol",
    "effort": "medium",
    "governance": "alma",
    "reviewer": "v2",
}


def armed_env(**overrides):
    env = {
        "ALLOW_REAL_LLM": "1",
        "RB_MODEL_BASE_URL": "https://models.example.test/v1",
        "OPENAI_API_KEY": TEST_KEY,
        "RB_MAX_SPEND_USD": "5.00",
    }
    env.update(overrides)
    return env


class PassTransport:
    """Fake transport that answers per pass, keyed by the PASS marker."""

    def __init__(self, responses=None, usage=USAGE):
        self.calls: list[dict[str, object]] = []
        self.responses = responses or {}
        self.usage = usage

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
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
        return 200, json.dumps(body).encode("utf-8")

    def pass_names(self) -> list[str]:
        names = []
        for call in self.calls:
            marker = call["payload"]["messages"][1]["content"].splitlines()[0]
            names.append(marker[len("PASS: ") :].strip())
        return names


def load_fixture(root: Path, name: str):
    directory = root / name
    diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
    pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
    responses_doc = json.loads(
        (directory / "model_responses.json").read_text(encoding="utf-8")
    )
    responses = dict(responses_doc.get("passes", {}))
    responses["general"] = responses_doc.get("general", [])
    return directory, diff_text, pr, responses


def make_diff(path: str, lines: list[str]) -> str:
    body = "\n".join("+" + line for line in lines)
    return (
        f"diff --git a/{path} b/{path}\nnew file mode 100644\n"
        f"--- /dev/null\n+++ b/{path}\n@@ -0,0 +1,{len(lines)} @@\n{body}\n"
    )


def candidate_for(claim_type, path, lines, start, end, message="test claim"):
    return Candidate(
        rule_id=f"test_{claim_type}",
        claim_type=claim_type,
        file=path,
        start_line=start,
        end_line=end,
        message=message,
        evidence_text=tuple(lines[start - 1 : end]),
        severity_hint="high",
        category_hint="security",
        producer="test-producer",
    )


def gate_status(gate, claim_type, lines, start=1, end=None, path="app/x.py"):
    end = len(lines) if end is None else end
    diff = parse_unified_diff(make_diff(path, lines))
    candidate = candidate_for(claim_type, path, lines, start, end)
    result = gate.validate([candidate], diff, "test-agent")
    assert len(result.ledger) == 1
    return result.ledger[0].status


class PolicyTests(unittest.TestCase):
    def test_frozen_gate_untouched(self):
        self.assertEqual(alma_gate.POLICY_SHA256, FROZEN_V10_SHA256)
        self.assertEqual(alma_gate.POLICY_VERSION, "alma-evidence-gate/1.0.0")

    def test_v11_policy_identity(self):
        self.assertEqual(POLICY_VERSION_V11, "alma-evidence-gate/1.1.0")
        self.assertNotEqual(POLICY_SHA256_V11, FROZEN_V10_SHA256)
        self.assertEqual(len(KNOWN_CLAIM_TYPES_V11), 14)
        self.assertEqual(len(NEW_CLAIM_TYPES), 6)
        self.assertEqual(
            set(INHERITED_CLAIM_TYPES), set(alma_gate.KNOWN_CLAIM_TYPES)
        )
        self.assertEqual(
            set(KNOWN_CLAIM_TYPES_V11),
            set(INHERITED_CLAIM_TYPES) | set(NEW_CLAIM_TYPES),
        )

    def test_unknown_claim_still_fails_closed(self):
        status = gate_status(
            AlmaGateV11(), "general_correctness", ["    x = compute()"]
        )
        self.assertEqual(status, "rejected")


class NewClassGateTests(unittest.TestCase):
    """Gate-level accept + adversarial reject per new class (Adenda 1)."""

    gate = None

    @classmethod
    def setUpClass(cls):
        cls.gate = AlmaGateV11()

    def status(self, claim_type, lines, start=1, end=None):
        return gate_status(self.gate, claim_type, lines, start=start, end=end)

    # resource_leak --------------------------------------------------
    def test_resource_leak_accepts_unclosed_open(self):
        lines = ["    handle = open(path)", "    return handle.read()"]
        self.assertEqual(self.status("resource_leak", lines, 1, 1), "accepted")

    def test_resource_leak_accepts_socket_connect(self):
        lines = ["    sock = socket.socket()", "    sock.connect(addr)"]
        self.assertEqual(self.status("resource_leak", lines, 1, 2), "accepted")

    def test_resource_leak_rejects_open_under_with(self):
        lines = ["    with open(path) as handle:", "        return handle.read()"]
        self.assertEqual(self.status("resource_leak", lines, 1, 1), "rejected")

    def test_resource_leak_rejects_close_in_range(self):
        lines = ["    handle = open(path)", "    handle.close()"]
        self.assertEqual(self.status("resource_leak", lines, 1, 2), "rejected")

    def test_resource_leak_rejects_without_opener(self):
        lines = ["    data = handle.read()"]
        self.assertEqual(self.status("resource_leak", lines), "rejected")

    # swallowed_exception ---------------------------------------------
    def test_swallowed_exception_accepts_typed_pass_only(self):
        lines = ["    except ValueError:", "        pass"]
        self.assertEqual(self.status("swallowed_exception", lines), "accepted")

    def test_swallowed_exception_rejects_handler_that_handles(self):
        lines = ["    except ValueError:", "        job.mark_failed()"]
        self.assertEqual(self.status("swallowed_exception", lines), "rejected")

    def test_swallowed_exception_rejects_bare_except_class_claim(self):
        # The bare except: belongs to the 1.0.0 class, not this one.
        lines = ["    except:", "        pass"]
        self.assertEqual(self.status("swallowed_exception", lines), "rejected")

    def test_swallowed_exception_rejects_uncited_body(self):
        lines = ["    except ValueError:", "        pass"]
        self.assertEqual(
            self.status("swallowed_exception", lines, 1, 1), "rejected"
        )

    # unsafe_xml_parsing ----------------------------------------------
    def test_unsafe_xml_accepts_stdlib_fromstring(self):
        lines = ["    return ET.fromstring(raw)"]
        self.assertEqual(self.status("unsafe_xml_parsing", lines), "accepted")

    def test_unsafe_xml_accepts_minidom_parse(self):
        lines = ["    doc = minidom.parse(path)"]
        self.assertEqual(self.status("unsafe_xml_parsing", lines), "accepted")

    def test_unsafe_xml_rejects_defusedxml_present(self):
        lines = [
            "import defusedxml.ElementTree as ET",
            "    return ET.fromstring(raw)",
        ]
        self.assertEqual(self.status("unsafe_xml_parsing", lines), "rejected")

    def test_unsafe_xml_rejects_non_xml(self):
        lines = ["    return json.loads(raw)"]
        self.assertEqual(self.status("unsafe_xml_parsing", lines), "rejected")

    # insecure_tempfile -------------------------------------------------
    def test_insecure_tempfile_accepts_mktemp(self):
        lines = ['    return tempfile.mktemp(suffix=".tmp")']
        self.assertEqual(self.status("insecure_tempfile", lines), "accepted")

    def test_insecure_tempfile_rejects_mkstemp(self):
        # mktemp absent: mkstemp is the safe API and must not match.
        lines = ["    fd, path = tempfile.mkstemp()"]
        self.assertEqual(self.status("insecure_tempfile", lines), "rejected")

    def test_insecure_tempfile_rejects_named_temporary_file(self):
        lines = ["    handle = tempfile.NamedTemporaryFile()"]
        self.assertEqual(self.status("insecure_tempfile", lines), "rejected")

    # ssl_context_unverified ---------------------------------------------
    def test_ssl_context_accepts_unverified_context(self):
        lines = ["    return ssl._create_unverified_context()"]
        self.assertEqual(self.status("ssl_context_unverified", lines), "accepted")

    def test_ssl_context_accepts_cert_none(self):
        lines = ["    ctx.verify_mode = ssl.CERT_NONE"]
        self.assertEqual(self.status("ssl_context_unverified", lines), "accepted")

    def test_ssl_context_rejects_cert_required(self):
        # CERT_NONE absent.
        lines = ["    ctx.verify_mode = ssl.CERT_REQUIRED"]
        self.assertEqual(self.status("ssl_context_unverified", lines), "rejected")

    def test_ssl_context_rejects_default_context(self):
        lines = ["    return ssl.create_default_context()"]
        self.assertEqual(self.status("ssl_context_unverified", lines), "rejected")

    # weak_random_security -------------------------------------------------
    def test_weak_random_accepts_security_name(self):
        lines = ['    session_token = "".join(random.choices(chars, k=16))']
        self.assertEqual(self.status("weak_random_security", lines), "accepted")

    def test_weak_random_rejects_non_security_name(self):
        lines = ["    lucky_number = random.randint(1, 100)"]
        self.assertEqual(self.status("weak_random_security", lines), "rejected")

    def test_weak_random_rejects_secrets_module(self):
        lines = ["    api_token = secrets.token_hex(16)"]
        self.assertEqual(self.status("weak_random_security", lines), "rejected")

    def test_weak_random_rejects_split_generation_and_assignment(self):
        # Documented same-line rule: generation on one line, bare-name
        # assignment on the next is not mechanically provable.
        lines = ["    raw = random.randint(1, 999999)", "    otp = str(raw)"]
        self.assertEqual(self.status("weak_random_security", lines), "rejected")


# One (accept, reject) evidence pair per inherited class.
INHERITED_PAIRS = {
    "sql_injection": (
        ['    q = f"SELECT * FROM t WHERE id = {x}"'],
        ['    q = "SELECT * FROM t WHERE id = ?"'],
    ),
    "hardcoded_secret": (
        ['API_KEY = "sk-live-123456"'],
        ['API_KEY = "changeme"'],
    ),
    "tls_verification_disabled": (
        ["    requests.get(url, verify=False)"],
        ["    requests.get(url, verify=True)"],
    ),
    "silenced_bare_except": (
        ["    except:", "        pass"],
        ["    except:", "        raise"],
    ),
    "mutable_default": (
        ["def f(items=[]):"],
        ["def f(items=None):"],
    ),
    "command_execution": (
        ["    os.system(cmd)"],
        ["    subprocess.run(cmd)"],
    ),
    "unsafe_deserialization": (
        ["    return pickle.loads(data)"],
        ["    return yaml.load(data, Loader=SafeLoader)"],
    ),
    "race_condition": (
        ["import threading", "    self.cache = {}"],
        ["    self.cache = {}"],
    ),
}


class InheritedCrossCheckUnitTests(unittest.TestCase):
    def test_inherited_pairs_agree_between_gates(self):
        self.assertEqual(set(INHERITED_PAIRS), set(INHERITED_CLAIM_TYPES))
        for claim_type, (accept_lines, reject_lines) in INHERITED_PAIRS.items():
            with self.subTest(claim_type=claim_type):
                for lines, expected in (
                    (accept_lines, "accepted"),
                    (reject_lines, "rejected"),
                ):
                    status_v10 = gate_status(AlmaGate(), claim_type, lines)
                    status_v11 = gate_status(AlmaGateV11(), claim_type, lines)
                    self.assertEqual(status_v10, expected)
                    self.assertEqual(status_v11, expected)


class NewClassFixtureE2ETests(unittest.TestCase):
    """fixtures_v11: reviewer (v2 + gate v11) -> gate 1.1.0, per class."""

    # fixture dir -> (pass class, expected findings, expected rejected)
    EXPECTED = {
        "v11_01_resource_leak": ("resource_leak", 1, 1),
        "v11_02_swallowed_exception": ("swallowed_exception", 1, 1),
        "v11_03_unsafe_xml_parsing": ("unsafe_xml_parsing", 1, 0),
        "v11_04_insecure_tempfile": ("insecure_tempfile", 1, 0),
        "v11_05_ssl_context_unverified": ("ssl_context_unverified", 1, 0),
        "v11_06_weak_random_security": ("weak_random_security", 1, 1),
    }

    def test_each_new_class_fixture_end_to_end(self):
        fixture_dirs = sorted(
            path.name for path in FIXTURES_V11.iterdir() if path.is_dir()
        )
        self.assertEqual(fixture_dirs, sorted(self.EXPECTED))
        for name, (claim_type, n_findings, n_rejected) in self.EXPECTED.items():
            with self.subTest(fixture=name):
                directory, diff_text, pr, responses = load_fixture(
                    FIXTURES_V11, name
                )
                transport = PassTransport(responses)
                result = run_agent(
                    diff_text=diff_text,
                    pr_metadata=pr,
                    agent_name="alma-reviewer",
                    mode="alma",
                    backend="llm",
                    config=CONFIG_V11_ALMA,
                    env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
                    llm_transport=transport,
                )
                # One pass per 1.1.0 class, in the gate's class order.
                self.assertEqual(
                    transport.pass_names(), list(KNOWN_CLAIM_TYPES_V11)
                )
                self.assertEqual(len(transport.calls), 14)
                self.assertEqual(
                    result.llm_run_info["gate_version"], POLICY_VERSION_V11
                )
                self.assertEqual(len(result.output["findings"]), n_findings)

                entries = [
                    entry
                    for entry in result.ledger
                    if entry["claim_type"] == claim_type
                ]
                accepted = [e for e in entries if e["status"] == "accepted"]
                rejected = [e for e in entries if e["status"] == "rejected"]
                self.assertEqual(len(accepted), 1)
                self.assertEqual(len(rejected), n_rejected)
                for entry in entries:
                    self.assertEqual(
                        entry["validator_version"], POLICY_VERSION_V11
                    )
                    self.assertEqual(entry["policy_sha256"], POLICY_SHA256_V11)


class InheritedCrossCheckE2ETests(unittest.TestCase):
    """Requirement: the 8 inherited classes behave identically under
    the 1.0.0 and the 1.1.0 on the existing fixtures_v2."""

    def test_fixtures_v2_identical_outcomes_under_both_gates(self):
        fixture_dirs = sorted(
            path for path in FIXTURES_V2.iterdir() if path.is_dir()
        )
        self.assertEqual(len(fixture_dirs), len(INHERITED_CLAIM_TYPES))
        for directory in fixture_dirs:
            with self.subTest(fixture=directory.name):
                _, diff_text, pr, responses = load_fixture(
                    FIXTURES_V2, directory.name
                )
                env = armed_env(RB_REPO_ROOT=str(directory / "repo"))

                transport_v10 = PassTransport(responses)
                result_v10 = run_agent(
                    diff_text=diff_text,
                    pr_metadata=pr,
                    agent_name="alma-reviewer",
                    mode="alma",
                    backend="llm",
                    config=CONFIG_V10_ALMA,
                    env=env,
                    llm_transport=transport_v10,
                )
                transport_v11 = PassTransport(responses)
                result_v11 = run_agent(
                    diff_text=diff_text,
                    pr_metadata=pr,
                    agent_name="alma-reviewer",
                    mode="alma",
                    backend="llm",
                    config=CONFIG_V11_ALMA,
                    env=env,
                    llm_transport=transport_v11,
                )

                self.assertEqual(len(transport_v10.calls), 8)
                self.assertEqual(len(transport_v11.calls), 14)
                self.assertEqual(
                    result_v10.output["findings"], result_v11.output["findings"]
                )
                self.assertEqual(
                    [entry["status"] for entry in result_v10.ledger],
                    [entry["status"] for entry in result_v11.ledger],
                )
                # Same verdicts; only the validator stamp differs.
                self.assertTrue(
                    all(
                        entry["validator_version"] == "alma-evidence-gate/1.0.0"
                        for entry in result_v10.ledger
                    )
                )
                self.assertTrue(
                    all(
                        entry["validator_version"] == POLICY_VERSION_V11
                        for entry in result_v11.ledger
                    )
                )


class GateSelectionTests(unittest.TestCase):
    def test_default_gate_is_v1(self):
        _, diff_text, pr, responses = load_fixture(
            FIXTURES_V2, "v2_01_sql_injection"
        )
        directory = FIXTURES_V2 / "v2_01_sql_injection"
        transport = PassTransport(responses)
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="alma-reviewer",
            mode="alma",
            backend="llm",
            config=CONFIG_V10_ALMA,
            env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
            llm_transport=transport,
        )
        self.assertEqual(len(transport.calls), 8)
        self.assertTrue(
            all(
                entry["policy_sha256"] == alma_gate.POLICY_SHA256
                for entry in result.ledger
            )
        )

    def test_unknown_gate_fails_closed(self):
        _, diff_text, pr, _ = load_fixture(FIXTURES_V2, "v2_01_sql_injection")
        config = dict(CONFIG_V11_ALMA, gate="v9")
        # The v2 reviewer refuses first (it resolves the same config
        # key to build its pass list); either way: fail closed, and
        # crucially no model call is made.
        transport = PassTransport({})
        with self.assertRaises(RealLLMRefused):
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="llm",
                config=config,
                env=armed_env(),
                llm_transport=transport,
            )
        self.assertEqual(transport.calls, [])
        # The gate selection in main validates the same key on paths
        # that never reach the reviewer (mock backend).
        with self.assertRaises(ValueError):
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="mock",
                config={"gate": "v9"},
                env=armed_env(),
            )

    def test_base_arm_with_v11_bypasses_and_stamps_v11(self):
        directory, diff_text, pr, responses = load_fixture(
            FIXTURES_V11, "v11_04_insecure_tempfile"
        )
        transport = PassTransport(responses)
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="base-reviewer",
            mode="base",
            backend="llm",
            config=dict(CONFIG_V11_ALMA, governance="base"),
            env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
            llm_transport=transport,
        )
        # 14 class passes + the base arm's general pass.
        self.assertEqual(len(transport.calls), 15)
        self.assertEqual(transport.pass_names()[-1], "general")
        self.assertEqual(len(result.output["findings"]), 1)
        self.assertTrue(
            all(
                entry["validator_version"] == "bypassed-base-arm"
                and entry["policy_sha256"] == POLICY_SHA256_V11
                for entry in result.ledger
            )
        )


if __name__ == "__main__":
    unittest.main()
