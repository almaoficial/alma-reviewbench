"""Tests for the gate alma-evidence-gate/1.3.0 (agent/alma_gate_v13.py)
and for Adenda 3's lever 1 (the v2 reviewer's citation guidance).

Provenance: PREREGISTRO-REVIEWBENCH-V2.md, Adenda 3 (2026-10-20).
The 1.3.0 inherits the 1.2.0's 14 classes by delegating to the
1.2.0's own support function and adds the class hunter's 5
best-ranked classes (weak_hash, tarfile_unsafe_extract,
hardcoded_password_argument, jwt_verification_disabled,
debug_mode_enabled), each with the hunter report's mechanical rule
checked on the 1.2.0's tokenized views.  What this suite proves:

- the frozen gates are untouched (their POLICY_SHA256 values are
  the literals of record) and the 1.3.0 carries its own version and
  hash over 19 classes;
- each NEW class accepts the hunter report's examples and rejects
  its adversaries;
- the red team's battery, EXTENDED with attacks on the 5 new
  classes (>= 3 tricks each: comment/string/docstring pattern,
  bag-of-lines, range trim, misleading name), keeps the pass rate
  at or below the 1.2.0's 4.3%: the only accepted attacks in the
  whole battery are the two residuals Adenda 2 itself declares
  unfixable (C3 dead code, X2 input provenance);
- every legitimate fixture of the package (fixtures_v2,
  fixtures_v11) produces IDENTICAL findings and ledger statuses
  under the 1.3.0 as under the 1.2.0, and fixtures_v13 (one per new
  class, plus the two lever-1 citation fixtures) run end to end
  with 19 passes and 1.3.0 stamps;
- lever 1: the citation-discipline guidance exists ONLY under
  RB_CONFIG_GATE=v13 — the v1/v11/v12 reviewer configurations keep
  their previous guidance text and pass lists — and the citation
  shapes it teaches are accepted by the 1.2.0 AND the 1.3.0 while
  the unguided shapes and false equivalents stay rejected;
- gate selection: v13 via RB_CONFIG_GATE, default still v1,
  unknown values fail closed.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import alma_gate, alma_gate_v11, alma_gate_v12  # noqa: E402
from agent.alma_gate_v12 import AlmaGateV12  # noqa: E402
from agent.alma_gate_v13 import (  # noqa: E402
    KNOWN_CLAIM_TYPES_V13,
    NEW_CLAIM_TYPES_V13,
    POLICY_SHA256 as POLICY_SHA256_V13,
    POLICY_VERSION as POLICY_VERSION_V13,
    AlmaGateV13,
)
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused  # noqa: E402
from agent.llm_reviewer_v2 import (  # noqa: E402
    LLMReviewerV2,
    _CLASS_GUIDANCE,
    _CLASS_GUIDANCE_V11,
)
from agent.main import run_agent  # noqa: E402
from test_gate_v11 import (  # noqa: E402
    CONFIG_V11_ALMA,
    FIXTURES_V11,
    FIXTURES_V2,
    INHERITED_PAIRS,
    PassTransport,
    armed_env,
    gate_status,
    load_fixture,
)
from test_gate_v12 import (  # noqa: E402
    ATTACKS,
    DECLARED_RESIDUALS,
    attack_candidate,
    attack_diff,
)


FIXTURES_V13 = ROOT / "fixtures_v13"
FIXTURES_V1 = ROOT / "fixtures"
FROZEN_V10_SHA256 = "3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35"
FROZEN_V11_SHA256 = "6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9"
FROZEN_V12_SHA256 = "a768afa46136ba1bf542da65006a946d11cb39e8db73fbd484c3f021b7994211"
CONFIG_V12_ALMA = dict(CONFIG_V11_ALMA, gate="v12")
CONFIG_V13_ALMA = dict(CONFIG_V11_ALMA, gate="v13")


def armed_env_v13(**overrides):
    """armed_env with a higher harness spend cap: the reviewer's
    worst-case estimate grows with the pass count (19 passes under
    v13), and the shared US$5.00 cap would refuse the run before the
    fake transport answers anything.  All calls in this suite go to
    the in-memory PassTransport — nothing is spent."""
    overrides.setdefault("RB_MAX_SPEND_USD", "10.00")
    return armed_env(**overrides)


class PolicyTests(unittest.TestCase):
    def test_frozen_gates_untouched(self):
        self.assertEqual(alma_gate.POLICY_SHA256, FROZEN_V10_SHA256)
        self.assertEqual(alma_gate_v11.POLICY_SHA256, FROZEN_V11_SHA256)
        self.assertEqual(alma_gate_v12.POLICY_SHA256, FROZEN_V12_SHA256)

    def test_v13_policy_identity(self):
        self.assertEqual(POLICY_VERSION_V13, "alma-evidence-gate/1.3.0")
        self.assertNotIn(
            POLICY_SHA256_V13,
            (FROZEN_V10_SHA256, FROZEN_V11_SHA256, FROZEN_V12_SHA256),
        )
        self.assertEqual(len(KNOWN_CLAIM_TYPES_V13), 19)
        self.assertEqual(len(NEW_CLAIM_TYPES_V13), 5)
        self.assertTrue(
            set(alma_gate_v12.KNOWN_CLAIM_TYPES_V12)
            < set(KNOWN_CLAIM_TYPES_V13)
        )
        self.assertEqual(
            set(KNOWN_CLAIM_TYPES_V13) - set(alma_gate_v12.KNOWN_CLAIM_TYPES_V12),
            set(NEW_CLAIM_TYPES_V13),
        )

    def test_unknown_claim_still_fails_closed(self):
        status = gate_status(
            AlmaGateV13(), "general_correctness", ["    x = compute()"]
        )
        self.assertEqual(status, "rejected")


class NewClassGateTests(unittest.TestCase):
    """Accept + adversarial reject per new class (hunter report)."""

    gate = None

    @classmethod
    def setUpClass(cls):
        cls.gate = AlmaGateV13()

    def status(self, claim_type, lines, start=1, end=None):
        return gate_status(self.gate, claim_type, lines, start=start, end=end)

    # weak_hash -----------------------------------------------------
    def test_weak_hash_accepts_md5_and_sha1(self):
        self.assertEqual(
            self.status(
                "weak_hash",
                ["digest = hashlib.md5(password.encode()).hexdigest()"],
            ),
            "accepted",
        )
        self.assertEqual(
            self.status("weak_hash", ["digest = hashlib.sha1(data).hexdigest()"]),
            "accepted",
        )

    def test_weak_hash_accepts_new_with_weak_literal(self):
        self.assertEqual(
            self.status("weak_hash", ['h = hashlib.new("md5", data)']),
            "accepted",
        )
        self.assertEqual(
            self.status("weak_hash", ["h = hashlib.new('SHA1', data)"]),
            "accepted",
        )

    def test_weak_hash_rejects_usedforsecurity_false(self):
        lines = ["digest = hashlib.md5(file_bytes, usedforsecurity=False).hexdigest()"]
        self.assertEqual(self.status("weak_hash", lines), "rejected")

    def test_weak_hash_rejects_strong_and_unresolved(self):
        self.assertEqual(
            self.status(
                "weak_hash", ["digest = hashlib.sha256(password.encode()).hexdigest()"]
            ),
            "rejected",
        )
        # md5 not resolved to hashlib: no import resolution, fail closed.
        self.assertEqual(
            self.status("weak_hash", ["h = md5(password)"]), "rejected"
        )
        self.assertEqual(
            self.status("weak_hash", ['h = hashlib.new("sha256", data)']),
            "rejected",
        )
        self.assertEqual(
            self.status("weak_hash", ["h = hashlib.new(algorithm, data)"]),
            "rejected",
        )

    def test_weak_hash_rejects_guard_on_uncited_continuation(self):
        # Range trim: the antidote sits on the call's second line,
        # outside the citation; the block-level span search sees it.
        lines = [
            "digest = hashlib.md5(",
            "    data, usedforsecurity=False).hexdigest()",
        ]
        self.assertEqual(self.status("weak_hash", lines, 1, 1), "rejected")
        # ... while the same call WITHOUT the guard is accepted cited whole.
        lines = ["digest = hashlib.md5(", "    data).hexdigest()"]
        self.assertEqual(self.status("weak_hash", lines, 1, 2), "accepted")

    # tarfile_unsafe_extract -----------------------------------------
    def test_tarfile_accepts_extractall_without_filter(self):
        lines = [
            'with tarfile.open(uploaded, "r:gz") as tar:',
            '    tar.extractall(path="/var/app/data")',
        ]
        self.assertEqual(
            self.status("tarfile_unsafe_extract", lines, 1, 2), "accepted"
        )

    def test_tarfile_rejects_filter_in_call(self):
        lines = [
            'with tarfile.open(uploaded, "r:gz") as tar:',
            '    tar.extractall(path="/var/app/data", filter="data")',
        ]
        self.assertEqual(
            self.status("tarfile_unsafe_extract", lines, 1, 2), "rejected"
        )

    def test_tarfile_rejects_filter_on_uncited_continuation(self):
        lines = [
            "tar.extractall(",
            '    path="/var/app/data", filter="data")',
        ]
        self.assertEqual(
            self.status("tarfile_unsafe_extract", lines, 1, 1), "rejected"
        )

    def test_tarfile_rejects_zip_and_member_extract(self):
        # CPython neutralizes '..' for zip: the marker does not
        # prove the tar defect (hunter adversary).
        self.assertEqual(
            self.status("tarfile_unsafe_extract", ['zipf.extractall("/tmp/z")']),
            "rejected",
        )
        # Member-by-member extract() is not the class (fail closed).
        self.assertEqual(
            self.status("tarfile_unsafe_extract", ['tar.extract("member")']),
            "rejected",
        )

    # hardcoded_password_argument --------------------------------------
    def test_password_argument_accepts_kwarg_and_default(self):
        lines = [
            'conn = psycopg2.connect(host="db", user="app", password="s3cr3t-produccion")'
        ]
        self.assertEqual(
            self.status("hardcoded_password_argument", lines), "accepted"
        )
        lines = ['def login(user, password="default_pwd"):']
        self.assertEqual(
            self.status("hardcoded_password_argument", lines), "accepted"
        )
        lines = ['client = ApiClient(api_key="live-key-123456")']
        self.assertEqual(
            self.status("hardcoded_password_argument", lines), "accepted"
        )

    def test_password_argument_rejects_non_literals(self):
        self.assertEqual(
            self.status(
                "hardcoded_password_argument",
                ['conn = psycopg2.connect(password=os.environ["DB_PASSWORD"])'],
            ),
            "rejected",
        )
        self.assertEqual(
            self.status(
                "hardcoded_password_argument", ["password = read_from_vault()"]
            ),
            "rejected",
        )
        self.assertEqual(
            self.status(
                "hardcoded_password_argument", ['conn = connect(password="abc")']
            ),
            "rejected",
        )

    def test_password_argument_rejects_placeholders(self):
        for line in (
            'conn = connect(password="changeme")',
            'conn = connect(password="example-password")',
            'conn = connect(password="xxxxxxxx")',
            'conn = connect(password="${DB_PASSWORD}")',
        ):
            with self.subTest(line=line):
                self.assertEqual(
                    self.status("hardcoded_password_argument", [line]),
                    "rejected",
                )

    # jwt_verification_disabled -----------------------------------------
    def test_jwt_accepts_disabling_forms(self):
        self.assertEqual(
            self.status(
                "jwt_verification_disabled",
                ['payload = jwt.decode(token, options={"verify_signature": False})'],
            ),
            "accepted",
        )
        self.assertEqual(
            self.status(
                "jwt_verification_disabled",
                ['payload = jwt.decode(token, key, algorithms=["none"])'],
            ),
            "accepted",
        )
        self.assertEqual(
            self.status(
                "jwt_verification_disabled",
                ["payload = jwt.decode(token, verify=False)"],
            ),
            "accepted",
        )

    def test_jwt_accepts_multiline_call_cited_whole(self):
        lines = [
            "payload = jwt.decode(",
            '    token, options={"verify_signature": False})',
        ]
        self.assertEqual(
            self.status("jwt_verification_disabled", lines, 1, 2), "accepted"
        )

    def test_jwt_rejects_verifying_calls(self):
        self.assertEqual(
            self.status(
                "jwt_verification_disabled",
                ['payload = jwt.decode(token, SECRET, algorithms=["HS256"])'],
            ),
            "rejected",
        )
        # Decoding only the header is legitimate pre-verification.
        self.assertEqual(
            self.status(
                "jwt_verification_disabled",
                ["header = jwt.get_unverified_header(token)"],
            ),
            "rejected",
        )
        # Options passed by variable: not decidable from the citation.
        self.assertEqual(
            self.status(
                "jwt_verification_disabled",
                ["payload = jwt.decode(token, options=opts)"],
            ),
            "rejected",
        )

    # debug_mode_enabled --------------------------------------------------
    def test_debug_accepts_literal_true_forms(self):
        self.assertEqual(
            self.status("debug_mode_enabled", ["DEBUG = True"]), "accepted"
        )
        self.assertEqual(
            self.status(
                "debug_mode_enabled", ['app.run(host="0.0.0.0", debug=True)']
            ),
            "accepted",
        )
        self.assertEqual(
            self.status("debug_mode_enabled", ["app.debug = True"]), "accepted"
        )

    def test_debug_rejects_non_literal_and_false(self):
        self.assertEqual(
            self.status(
                "debug_mode_enabled",
                ['DEBUG = os.environ.get("DJANGO_DEBUG", "false") == "true"'],
            ),
            "rejected",
        )
        self.assertEqual(
            self.status("debug_mode_enabled", ["app.run(debug=False)"]),
            "rejected",
        )
        self.assertEqual(
            self.status(
                "debug_mode_enabled", ['app.run(host="0.0.0.0")']
            ),
            "rejected",
        )
        self.assertEqual(
            self.status("debug_mode_enabled", ["DEBUGGER = True"]), "rejected"
        )


# The red team's battery, EXTENDED to the 5 classes of Adenda 3
# (>= 3 tricks per class: pattern in comment/string/docstring,
# bag-of-lines, range trim, misleading name).  Same tuple shape as
# test_gate_v12.ATTACKS.
NEW_ATTACKS = [
    # ---------------- weak_hash ----------------
    ("WH1", "weak_hash", "patrón dentro de un comentario",
     ['# digest = hashlib.md5(password)  # legacy'], 1, 1,
     "Hash débil MD5.", None),
    ("WH2", "weak_hash", "string de ayuda/documentación",
     ['note = "avoid hashlib.sha1( for passwords"'], 1, 1,
     "Hash débil SHA1.", None),
    ("WH3", "weak_hash", "recorte de rango: usedforsecurity=False fuera de la cita",
     ['digest = hashlib.md5(',
      '    data, usedforsecurity=False).hexdigest()'], 1, 1,
     "Hash débil MD5 sin marca de no-seguridad.", None),
    ("WH4", "weak_hash", "nombre engañoso: hashlib.new con algoritmo sano",
     ['h = hashlib.new("sha256", data)'], 1, 1,
     "Hash débil vía hashlib.new.", None),
    # ---------------- tarfile_unsafe_extract ----------------
    ("TF1", "tarfile_unsafe_extract", "comentario que lo prohíbe",
     ['# tar.extractall( is banned in this codebase'], 1, 1,
     "Extracción tar sin filtro.", None),
    ("TF2", "tarfile_unsafe_extract", "string de documentación",
     ['docs = "call tar.extractall(path) to unpack"'], 1, 1,
     "Extracción tar sin filtro.", None),
    ("TF3", "tarfile_unsafe_extract", "recorte de rango: filter= fuera de la cita",
     ['tar.extractall(',
      '    path="/var/app/data", filter="data")'], 1, 1,
     "Extracción tar sin filtro.", None),
    ("TF4", "tarfile_unsafe_extract", "receptor zip: CPython neutraliza '..'",
     ['zipf.extractall("/tmp/z")'], 1, 1,
     "Extracción de archivo sin filtro.", None),
    # ---------------- hardcoded_password_argument ----------------
    ("HP1", "hardcoded_password_argument", "comentario con el ejemplo",
     ['# connect(password="s3cr3t-produccion")  # example'], 1, 1,
     "Contraseña hardcodeada como argumento.", None),
    ("HP2", "hardcoded_password_argument", "ejemplo dentro de un docstring",
     ['def login(user):',
      '    """Example: login(user, password="default_pwd")"""',
      '    return None'], 2, 2,
     "Contraseña hardcodeada como argumento.", None),
    ("HP3", "hardcoded_password_argument", "string de documentación asignado",
     ['docs = "use password=\\"s3cr3t-produccion\\" in the call"'], 1, 1,
     "Contraseña hardcodeada como argumento.", None),
    ("HP4", "hardcoded_password_argument", "placeholder listado",
     ['conn = connect(password="changeme")'], 1, 1,
     "Contraseña hardcodeada como argumento.", None),
    ("HP5", "hardcoded_password_argument", "bolsa en una línea: kwarg real con variable + literal ajeno en un string",
     ['conn = connect(password=pw, note="token=\'s3cr3t99\'")'], 1, 1,
     "Token hardcodeado como argumento.", None),
    # ---------------- jwt_verification_disabled ----------------
    ("JW1", "jwt_verification_disabled", "comentario con el ejemplo",
     ['# payload = jwt.decode(token, options={"verify_signature": False})'], 1, 1,
     "Verificación JWT deshabilitada.", None),
    ("JW2", "jwt_verification_disabled", "string de ayuda/documentación",
     ['msg = "never call jwt.decode with verify=False"'], 1, 1,
     "Verificación JWT deshabilitada.", None),
    ("JW3", "jwt_verification_disabled", "algoritmo fijado y verificación activa",
     ['payload = jwt.decode(token, SECRET, algorithms=["HS256"])'], 1, 1,
     "Verificación JWT deshabilitada.", None),
    ("JW4", "jwt_verification_disabled", "bolsa de líneas: el verify=False es de otra llamada",
     ['payload = jwt.decode(token, SECRET, algorithms=["HS256"])',
      'resp = requests.get(url, verify=False)'], 1, 2,
     "Verificación JWT deshabilitada.", None),
    ("JW5", "jwt_verification_disabled", "solo decodifica el header (legítimo)",
     ['header = jwt.get_unverified_header(token)'], 1, 1,
     "Verificación JWT deshabilitada.", None),
    # ---------------- debug_mode_enabled ----------------
    ("DB1", "debug_mode_enabled", "comentario que lo prohíbe",
     ['# DEBUG = True  # never in production'], 1, 1,
     "Modo debug habilitado.", None),
    ("DB2", "debug_mode_enabled", "string de ayuda/documentación",
     ['hint = "run it with app.run(debug=True) locally"'], 1, 1,
     "Modo debug habilitado.", None),
    ("DB3", "debug_mode_enabled", "valor computado desde el entorno (sin literal True)",
     ['DEBUG = os.environ.get("DJANGO_DEBUG", "false") == "true"'], 1, 1,
     "Modo debug habilitado.", None),
    ("DB4", "debug_mode_enabled", "debug explícitamente en False",
     ['app.run(debug=False)'], 1, 1,
     "Modo debug habilitado.", None),
    ("DB5", "debug_mode_enabled", "nombre engañoso: DEBUGGER no es DEBUG",
     ['DEBUGGER = True'], 1, 1,
     "Modo debug habilitado.", None),
]


class ExtendedRedTeamBatteryTests(unittest.TestCase):
    """Adenda 3's condition: over the EXTENDED battery (the 46 of
    Adenda 2 plus the new-class attacks), the 1.3.0's pass rate
    stays <= the 1.2.0's 4.3% — the only accepted attacks are the
    two residuals Adenda 2 declares unfixable."""

    ALL_ATTACKS = ATTACKS + NEW_ATTACKS

    def test_battery(self):
        gate = AlmaGateV13()
        passed = []
        for aid, cls, _trick, lines, start, end, msg, ctx in self.ALL_ATTACKS:
            with self.subTest(attack=aid, claim=cls):
                diff = parse_unified_diff(attack_diff(lines, ctx))
                candidate = attack_candidate(cls, start, end, lines, msg)
                result = gate.validate([candidate], diff, "red-team")
                status = result.ledger[0].status
                if aid in DECLARED_RESIDUALS:
                    self.assertEqual(status, "accepted")
                else:
                    self.assertEqual(status, "rejected")
                if status == "accepted":
                    passed.append(aid)
        self.assertEqual(sorted(passed), sorted(DECLARED_RESIDUALS))

    def test_pass_rate_within_budget(self):
        gate = AlmaGateV13()
        accepted = 0
        for _aid, cls, _trick, lines, start, end, msg, ctx in self.ALL_ATTACKS:
            diff = parse_unified_diff(attack_diff(lines, ctx))
            candidate = attack_candidate(cls, start, end, lines, msg)
            result = gate.validate([candidate], diff, "red-team")
            accepted += result.ledger[0].status == "accepted"
        rate = accepted / len(self.ALL_ATTACKS)
        self.assertLessEqual(rate, 0.043)
        # The extended battery is strictly larger than the 1.2.0's.
        self.assertEqual(len(ATTACKS), 46)
        self.assertGreaterEqual(len(NEW_ATTACKS), 15)


class InheritedEquivalenceTests(unittest.TestCase):
    """The 14 inherited classes under the 1.3.0: identical verdicts
    to the 1.2.0, including its one documented race divergence."""

    def test_inherited_pairs_match_v12(self):
        gate13 = AlmaGateV13()
        gate12 = AlmaGateV12()
        for claim_type, (accept_lines, reject_lines) in INHERITED_PAIRS.items():
            with self.subTest(claim_type=claim_type):
                for lines in (accept_lines, reject_lines):
                    self.assertEqual(
                        gate_status(gate13, claim_type, lines),
                        gate_status(gate12, claim_type, lines),
                    )

    def _run(self, root, name, config):
        directory, diff_text, pr, responses = load_fixture(root, name)
        transport = PassTransport(responses)
        env = (
            armed_env_v13(RB_REPO_ROOT=str(directory / "repo"))
            if config.get("gate") == "v13"
            else armed_env(RB_REPO_ROOT=str(directory / "repo"))
        )
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="alma-reviewer",
            mode="alma",
            backend="llm",
            config=config,
            env=env,
            llm_transport=transport,
        )
        return result, transport

    def test_fixtures_v2_and_v11_identical_under_v13(self):
        for root in (FIXTURES_V2, FIXTURES_V11):
            for directory in sorted(p for p in root.iterdir() if p.is_dir()):
                with self.subTest(fixture=directory.name):
                    result_v12, _ = self._run(
                        root, directory.name, CONFIG_V12_ALMA
                    )
                    result_v13, transport_v13 = self._run(
                        root, directory.name, CONFIG_V13_ALMA
                    )
                    self.assertEqual(
                        result_v12.output["findings"],
                        result_v13.output["findings"],
                    )
                    self.assertEqual(
                        [e["status"] for e in result_v12.ledger],
                        [e["status"] for e in result_v13.ledger],
                    )
                    # 19 class passes under v13; stamps are the 1.3.0's.
                    self.assertEqual(len(transport_v13.calls), 19)
                    self.assertEqual(
                        result_v13.llm_run_info["gate_version"],
                        POLICY_VERSION_V13,
                    )
                    self.assertTrue(
                        all(
                            entry["validator_version"] == POLICY_VERSION_V13
                            and entry["policy_sha256"] == POLICY_SHA256_V13
                            for entry in result_v13.ledger
                        )
                    )

    def test_fixtures_v1_mock_identical_under_v13(self):
        import json

        for directory in sorted(p for p in FIXTURES_V1.iterdir() if p.is_dir()):
            with self.subTest(fixture=directory.name):
                diff_text = (directory / "diff.patch").read_text(encoding="utf-8")
                pr = json.loads((directory / "pr.json").read_text(encoding="utf-8"))
                outcomes = {}
                for gate_version in ("v1", "v13"):
                    result = run_agent(
                        diff_text=diff_text,
                        pr_metadata=pr,
                        agent_name="alma-reviewer",
                        mode="alma",
                        backend="mock",
                        config={"gate": gate_version},
                        env={},
                    )
                    outcomes[gate_version] = (
                        result.output["findings"],
                        [e["status"] for e in result.ledger],
                    )
                self.assertEqual(outcomes["v1"], outcomes["v13"])


class NewClassFixtureE2ETests(unittest.TestCase):
    """fixtures_v13: reviewer (v2 + gate v13) -> gate 1.3.0.

    One fixture per new class, plus the two lever-1 citation
    fixtures (race cited together, SQL cited whole)."""

    EXPECTED = {
        "v13_01_weak_hash": "weak_hash",
        "v13_02_tarfile_unsafe_extract": "tarfile_unsafe_extract",
        "v13_03_hardcoded_password_argument": "hardcoded_password_argument",
        "v13_04_jwt_verification_disabled": "jwt_verification_disabled",
        "v13_05_debug_mode_enabled": "debug_mode_enabled",
        "v13_06_race_guided_citation": "race_condition",
        "v13_07_sql_complete_citation": "sql_injection",
    }

    def test_each_fixture_end_to_end(self):
        fixture_dirs = sorted(
            path.name for path in FIXTURES_V13.iterdir() if path.is_dir()
        )
        self.assertEqual(fixture_dirs, sorted(self.EXPECTED))
        for name, claim_type in self.EXPECTED.items():
            with self.subTest(fixture=name):
                directory, diff_text, pr, responses = load_fixture(
                    FIXTURES_V13, name
                )
                transport = PassTransport(responses)
                result = run_agent(
                    diff_text=diff_text,
                    pr_metadata=pr,
                    agent_name="alma-reviewer",
                    mode="alma",
                    backend="llm",
                    config=CONFIG_V13_ALMA,
                    env=armed_env_v13(RB_REPO_ROOT=str(directory / "repo")),
                    llm_transport=transport,
                )
                # One pass per 1.3.0 class, in the gate's class order.
                self.assertEqual(
                    transport.pass_names(), list(KNOWN_CLAIM_TYPES_V13)
                )
                self.assertEqual(len(transport.calls), 19)
                self.assertEqual(
                    result.llm_run_info["gate_version"], POLICY_VERSION_V13
                )
                self.assertEqual(len(result.output["findings"]), 1)
                entries = [
                    entry
                    for entry in result.ledger
                    if entry["claim_type"] == claim_type
                ]
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]["status"], "accepted")
                self.assertEqual(
                    entries[0]["validator_version"], POLICY_VERSION_V13
                )
                self.assertEqual(entries[0]["policy_sha256"], POLICY_SHA256_V13)


class GateSelectionV13Tests(unittest.TestCase):
    def test_base_arm_with_v13_stamps_v13(self):
        directory, diff_text, pr, responses = load_fixture(
            FIXTURES_V13, "v13_01_weak_hash"
        )
        transport = PassTransport(responses)
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="base-reviewer",
            mode="base",
            backend="llm",
            config=dict(CONFIG_V13_ALMA, governance="base"),
            env=armed_env_v13(RB_REPO_ROOT=str(directory / "repo")),
            llm_transport=transport,
        )
        # 19 class passes + the base arm's general pass.
        self.assertEqual(len(transport.calls), 20)
        self.assertTrue(
            all(
                entry["validator_version"] == "bypassed-base-arm"
                and entry["policy_sha256"] == POLICY_SHA256_V13
                for entry in result.ledger
            )
        )

    def test_unknown_gate_still_fails_closed(self):
        _, diff_text, pr, _ = load_fixture(FIXTURES_V2, "v2_01_sql_injection")
        config = dict(CONFIG_V13_ALMA, gate="v9")
        transport = PassTransport({})
        with self.assertRaises(RealLLMRefused):
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="llm",
                config=config,
                env=armed_env_v13(),
                llm_transport=transport,
            )
        self.assertEqual(transport.calls, [])
        with self.assertRaises(ValueError):
            run_agent(
                diff_text=diff_text,
                pr_metadata=pr,
                agent_name="alma-reviewer",
                mode="alma",
                backend="mock",
                config={"gate": "v9"},
                env=armed_env_v13(),
            )


class CitationGuidanceTests(unittest.TestCase):
    """Adenda 3, lever 1: the citation guidance exists only under
    v13, and the citation shapes it teaches are accepted by the
    hardened gates while the unguided shapes stay rejected."""

    def _reviewer(self, gate):
        return LLMReviewerV2.from_env(
            armed_env(),
            {"gate": gate, "model": "gpt-5.6-sol", "effort": "medium"},
        )

    def _system_prompt(self, reviewer, pass_name):
        payload = reviewer.build_payload(pass_name, "diff", "context")
        return payload["messages"][0]["content"]

    def test_v13_prompts_carry_citation_guidance(self):
        reviewer = self._reviewer("v13")
        for pass_name in (
            "sql_injection",
            "race_condition",
            "resource_leak",
            "swallowed_exception",
            "unsafe_deserialization",
        ):
            with self.subTest(pass_name=pass_name):
                self.assertIn(
                    "CITATION (required by the gate)",
                    self._system_prompt(reviewer, pass_name),
                )
        # Guidance for the 5 new classes is present in their passes.
        self.assertIn("hashlib.md5", self._system_prompt(reviewer, "weak_hash"))
        self.assertIn(
            "extractall", self._system_prompt(reviewer, "tarfile_unsafe_extract")
        )
        self.assertIn(
            "verify_signature",
            self._system_prompt(reviewer, "jwt_verification_disabled"),
        )
        self.assertEqual(len(reviewer.claim_types), 19)
        self.assertEqual(reviewer.gate_version, POLICY_VERSION_V13)

    def test_old_gates_keep_previous_guidance_unchanged(self):
        for gate, expected_guidance, n_passes in (
            ("v1", _CLASS_GUIDANCE, 8),
            ("v11", _CLASS_GUIDANCE_V11, 14),
            ("v12", _CLASS_GUIDANCE_V11, 14),
        ):
            with self.subTest(gate=gate):
                reviewer = self._reviewer(gate)
                self.assertEqual(reviewer.class_guidance, expected_guidance)
                self.assertEqual(len(reviewer.claim_types), n_passes)
                for pass_name in reviewer.claim_types:
                    self.assertNotIn(
                        "CITATION (required by the gate)",
                        self._system_prompt(reviewer, pass_name),
                    )

    # -- the citation shapes the guidance teaches --------------------

    RACE_LINES = [
        "class SessionCache:",
        "    async def refresh(self):",
        "        self.token = await fetch_token()",
    ]

    def test_race_cited_together_accepted_by_hardened_gates(self):
        for gate in (AlmaGateV12(), AlmaGateV13()):
            with self.subTest(gate=gate.version):
                # Guided shape: def + the line where concurrency and
                # the shared-state assignment coincide, cited together.
                self.assertEqual(
                    gate_status(gate, "race_condition", self.RACE_LINES, 2, 3),
                    "accepted",
                )
                # Unguided shapes stay rejected: the async def alone
                # (no assignment), and the trivial async handler.
                self.assertEqual(
                    gate_status(gate, "race_condition", self.RACE_LINES, 2, 2),
                    "rejected",
                )
                self.assertEqual(
                    gate_status(
                        gate,
                        "race_condition",
                        [
                            "async def handler(self, req):",
                            "    return self.render(req)",
                        ],
                    ),
                    "rejected",
                )

    SQL_LINES = [
        "def find_user(conn, name):",
        "    query = (",
        "        \"SELECT * FROM users WHERE name = '\" + name + \"'\"",
        "    )",
        "    return conn.execute(query)",
    ]

    def test_sql_cited_whole_accepted_by_hardened_gates(self):
        for gate in (AlmaGateV12(), AlmaGateV13()):
            with self.subTest(gate=gate.version):
                # Guided shape: the whole multi-line statement cited,
                # so the line carrying skeleton + construction is in
                # the range.
                self.assertEqual(
                    gate_status(gate, "sql_injection", self.SQL_LINES, 2, 4),
                    "accepted",
                )
                # Fragments without the marker line prove nothing.
                self.assertEqual(
                    gate_status(gate, "sql_injection", self.SQL_LINES, 2, 2),
                    "rejected",
                )
                self.assertEqual(
                    gate_status(gate, "sql_injection", self.SQL_LINES, 4, 4),
                    "rejected",
                )

    def test_antidote_shapes_stay_rejected_under_v13(self):
        # The false equivalents of the block-antidote classes: the
        # antidote sits in the block, outside the citation.
        gate = AlmaGateV13()
        self.assertEqual(
            gate_status(
                gate,
                "resource_leak",
                ["f = open(path)", "data = f.read()", "f.close()"],
                1,
                1,
            ),
            "rejected",
        )
        self.assertEqual(
            gate_status(
                gate,
                "swallowed_exception",
                ["try:", "    risky()", "except ValueError:", "    pass", "    raise"],
                3,
                4,
            ),
            "rejected",
        )
        self.assertEqual(
            gate_status(
                gate,
                "unsafe_deserialization",
                ["data = yaml.load(", "    stream, Loader=yaml.SafeLoader)"],
                1,
                1,
            ),
            "rejected",
        )


if __name__ == "__main__":
    unittest.main()
