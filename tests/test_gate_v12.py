"""Tests for the gate alma-evidence-gate/1.2.0 (agent/alma_gate_v12.py).

Provenance: PREREGISTRO-REVIEWBENCH-V2.md, Adenda 2 (2026-10-20).
The red team ran 46 well-formed fake findings against the 1.1.0 and
44 of them were ACCEPTED (95.7%); this gate is the minimal hardening
from that report (fixes (a)-(f) plus its families G/H rules), and
this suite is the regression battery for it:

- the frozen gates are untouched (their POLICY_SHA256 values are the
  literals of record) and the 1.2.0 carries its own version and hash;
- EVERY red-team attack is rejected by the 1.2.0 except the two
  residuals the addendum itself declares unfixable by mechanical
  means (C3 dead code, X2 input provenance) — those two are pinned
  as accepted-with-declared-limit so any change is noticed;
- every legitimate fixture of the package (fixtures/, fixtures_v2/,
  fixtures_v11/) produces IDENTICAL findings and ledger statuses
  under the 1.2.0 as under its predecessor gate;
- the one intentional unit-level divergence from the 1.1.0 is pinned
  and documented: the race_condition pair whose markers sit on
  separate lines (import threading / self.cache = {}) is rejected,
  because Adenda 2 (d) requires co-occurrence on one line and (c)
  requires a shared-state ASSIGNMENT;
- gate selection: v12 via RB_CONFIG_GATE, default still v1, unknown
  values fail closed.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import alma_gate, alma_gate_v11  # noqa: E402
from agent.alma_gate_v12 import (  # noqa: E402
    KNOWN_CLAIM_TYPES_V12,
    POLICY_SHA256 as POLICY_SHA256_V12,
    POLICY_VERSION as POLICY_VERSION_V12,
    AlmaGateV12,
)
from agent.base_reviewer import Candidate  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused  # noqa: E402
from agent.main import run_agent  # noqa: E402
from test_gate_v11 import (  # noqa: E402
    CONFIG_V11_ALMA,
    FIXTURES_V11,
    FIXTURES_V2,
    INHERITED_PAIRS,
    PassTransport,
    armed_env,
    candidate_for,
    gate_status,
    load_fixture,
    make_diff,
)


FIXTURES_V1 = ROOT / "fixtures"
FROZEN_V10_SHA256 = "3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35"
FROZEN_V11_SHA256 = "6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9"
CONFIG_V12_ALMA = dict(CONFIG_V11_ALMA, gate="v12")

# The red team's battery (estudio-estructura-20261020/rojo/ataques.py),
# copied verbatim as data: (id, class, trick, diff lines, start, end,
# message, context_extra).  context_extra=False means the lines are
# CONTEXT in the diff and one unrelated line is added at the end.
ATTACKS = [
    ("S1", "sql_injection", "patrón dentro de un comentario",
     ['# query = "SELECT * FROM users WHERE id = {}".format(uid)  # legacy'], 1, 1,
     "SQL injection en construcción con .format().", None),
    ("S2", "sql_injection", "SQL seguro + f-string ajeno (bolsa de líneas)",
     ['q = "SELECT * FROM users WHERE id = ?"',
      'cursor.execute(q, (user_id,))',
      'log = f"done {n}"'], 1, 3,
     "SQL injection: query construida con f-string.", None),
    ("S3", "sql_injection", "cita una línea de CONTEXTO (el PR no introduce el defecto)",
     ['q = "SELECT * FROM users"',
      'query = f"SELECT * FROM users WHERE id = {user_id}"',
      'cursor.execute(query)'], 2, 2,
     "SQL injection introducido en este PR.", False),
    ("S4", "sql_injection", "string de log, no SQL ejecutado",
     ['report = "SELECT summary: " + suffix'], 1, 1,
     "SQL injection por concatenación de strings.", None),
    ("H1", "hardcoded_secret", "el nombre NO se chequea: cualquier literal pasa",
     ['DEFAULT_REGION = "us-east-1"'], 1, 1,
     "Credencial hardcodeada en el código.", None),
    ("H2", "hardcoded_secret", "ejemplo dentro de un docstring",
     ['def connect():',
      '    """Example: api_key = "test-key-123" then call auth()."""',
      '    return True'], 2, 2,
     "API key hardcodeada.", None),
    ("H2b", "hardcoded_secret", "ejemplo en docstring, línea de asignación completa y citada sola",
     ['"""Usage example:',
      'api_key = "test-key-123"',
      '"""'], 2, 2,
     "API key hardcodeada.", None),
    ("H3", "hardcoded_secret", "placeholder no listado (fixture de test intencionalmente falso)",
     ['secret = "test-secret-value"'], 1, 1,
     "Secreto hardcodeado en el código.", None),
    ("H4", "hardcoded_secret", "literal público inocuo (URL)",
     ['BASE_URL = "https://api.example.com/v2"'], 1, 1,
     "Secreto hardcodeado en el código.", None),
    ("T1", "tls_verification_disabled", "comentario que lo prohíbe",
     ['# never set verify=False in production'], 1, 1,
     "Verificación TLS deshabilitada.", None),
    ("T2", "tls_verification_disabled", "string de ayuda/documentación",
     ['msg = "pass verify=False to disable checks"'], 1, 1,
     "Verificación TLS deshabilitada.", None),
    ("T3", "tls_verification_disabled", "docstring con ejemplo",
     ['"""Do not call requests.get(url, verify=False)."""'], 1, 1,
     "Verificación TLS deshabilitada.", None),
    ("E1", "silenced_bare_except", "ejemplo dentro de un docstring",
     ['def run():',
      '    """Avoid this:',
      '    except:',
      '        pass',
      '    """',
      '    return run_all()'], 2, 5,
     "Excepción silenciada con bare except.", None),
    ("E2", "silenced_bare_except", "bolsa de líneas: except que re-lanza + pass de otra función",
     ['def a():',
      '    try:',
      '        work()',
      '    except:',
      '        raise',
      'def b():',
      '    pass'], 1, 7,
     "Excepción silenciada con bare except.", None),
    ("E3", "silenced_bare_except", "string multilínea con el patrón",
     ['TEMPLATE = """',
      'except:',
      '    pass',
      '"""'], 1, 4,
     "Excepción silenciada con bare except.", None),
    ("M1", "mutable_default", "comentario con la firma vieja",
     ['# old: def load(items=[]):  # do not use'], 1, 1,
     "Default mutable en argumento de función.", None),
    ("M2", "mutable_default", "string con una firma",
     ['sig = "def load(cache={}):"'], 1, 1,
     "Default mutable en argumento de función.", None),
    ("M3", "mutable_default", "ejemplo en docstring",
     ['"""Example: def fetch(opts={}): ..."""'], 1, 1,
     "Default mutable en argumento de función.", None),
    ("C1", "command_execution", "comentario que lo menciona",
     ['# removed all os.system( calls'], 1, 1,
     "Ejecución de shell.", None),
    ("C2", "command_execution", "string de documentación",
     ['docs = "never use shell=True in subprocess"'], 1, 1,
     "Ejecución de shell.", None),
    ("C3", "command_execution", "código muerto (if False) con eval",
     ['if False:',
      '    result = eval(expr)'], 1, 2,
     "Ejecución dinámica de código.", None),
    ("D1", "unsafe_deserialization", "comentario de migración",
     ['# migrate away from pickle.loads('], 1, 1,
     "Deserialización insegura con pickle.", None),
    ("D2", "unsafe_deserialization", "recorte de rango: SafeLoader en la línea no citada",
     ['data = yaml.load(',
      '    stream, Loader=yaml.SafeLoader)'], 1, 1,
     "Deserialización insegura con yaml.load.", None),
    ("D3", "unsafe_deserialization", "string de documentación",
     ['note = "pickle.loads( is dangerous"'], 1, 1,
     "Deserialización insegura con pickle.", None),
    ("R1", "race_condition", "método async trivial (async + self. = 'race')",
     ['async def handler(self, req):',
      '    return self.render(req)'], 1, 2,
     "Condición de carrera: estado compartido sin sincronizar.", None),
    ("R2", "race_condition", "comentarios sueltos (bolsa de líneas)",
     ['# uses threading for the workers',
      '# see shared cache docs'], 1, 2,
     "Condición de carrera: estado compartido sin sincronizar.", None),
    ("R3", "race_condition", "código correctamente protegido con Lock",
     ['with self.lock:',
      '    t = threading.Thread(target=self.work)',
      '    t.start()'], 1, 3,
     "Condición de carrera: estado compartido sin sincronizar.", None),
    ("L1", "resource_leak", "open( dentro de un string",
     ['tip = "call open( to read the file"'], 1, 1,
     "Recurso abierto sin cerrar.", None),
    ("L2", "resource_leak", "recorte de rango: .close() fuera de las líneas citadas",
     ['f = open(path)',
      'data = f.read()',
      'f.close()'], 1, 1,
     "Recurso abierto sin cerrar.", None),
    ("L3", "resource_leak", "connect( de señales GUI (Qt), no recurso",
     ['slider.valueChanged.connect(update)'], 1, 1,
     "Conexión abierta sin cerrar.", None),
    ("W1", "swallowed_exception", "ejemplo en docstring",
     ['"""',
      'except ValueError:',
      '    pass',
      '"""'], 1, 4,
     "Excepción tragada en silencio.", None),
    ("W1b", "swallowed_exception", "docstring + recorte de rango (se cita hasta el pass, sin el cierre)",
     ['"""',
      'except ValueError:',
      '    pass',
      '"""'], 2, 3,
     "Excepción tragada en silencio.", None),
    ("W2", "swallowed_exception", "recorte de rango: el handler re-lanza (raise no citado)",
     ['try:',
      '    risky()',
      'except ValueError:',
      '    pass',
      '    raise'], 3, 4,
     "Excepción tragada en silencio.", None),
    ("W3", "swallowed_exception", "patrón idiomático: fallback de dependencia opcional",
     ['try:',
      '    import orjson',
      'except ImportError:',
      '    pass'], 1, 4,
     "Excepción tragada en silencio.", None),
    ("X1", "unsafe_xml_parsing", "comentario que lo menciona",
     ['# ET.parse( is not allowed here'], 1, 1,
     "Parseo XML inseguro.", None),
    ("X2", "unsafe_xml_parsing", "provanza: constante confiable empaquetada, sin input externo",
     ['tree = ET.parse(BUNDLED_SCHEMA_FILE)'], 1, 1,
     "Parseo XML inseguro de input externo.", None),
    ("X3", "unsafe_xml_parsing", "string de documentación",
     ['doc = "use ET.fromstring( only for templates"'], 1, 1,
     "Parseo XML inseguro.", None),
    ("F1", "insecure_tempfile", "comentario de migración",
     ['# replaced tempfile.mktemp( usage'], 1, 1,
     "Uso inseguro de tempfile.mktemp.", None),
    ("F2", "insecure_tempfile", "método propio seguro con el mismo nombre",
     ['class Tmp:',
      '    def mktemp(self):',
      '        return self._safe_make()',
      't = Tmp()',
      'p = t.mktemp()'], 5, 5,
     "Uso inseguro de tempfile.mktemp.", None),
    ("F3", "insecure_tempfile", "string de documentación",
     ['note = "mktemp( is deprecated"'], 1, 1,
     "Uso inseguro de tempfile.mktemp.", None),
    ("V1", "ssl_context_unverified", "comentario que lo prohíbe",
     ['# never use ssl._create_unverified_context'], 1, 1,
     "Contexto SSL sin verificación.", None),
    ("V2", "ssl_context_unverified", "string que lista la constante",
     ['opts = "CERT_NONE is forbidden"'], 1, 1,
     "Contexto SSL sin verificación.", None),
    ("V3", "ssl_context_unverified", "test que verifica su ausencia",
     ['assert "CERT_NONE" not in source'], 1, 1,
     "Contexto SSL sin verificación.", None),
    ("K1", "weak_random_security", "nombre con 'token' pero el valor es un conteo",
     ['token_count = random.randint(1, 5)'], 1, 1,
     "Token generado con random inseguro.", None),
    ("K2", "weak_random_security", "nombre con 'password' pero el valor es un delay de backoff",
     ['password_retry_delay = random.uniform(0.5, 1.5)'], 1, 1,
     "Secreto generado con random inseguro.", None),
    ("K3", "weak_random_security", "nombre con 'session' pero el valor es un TTL",
     ['session_ttl = random.randint(300, 600)'], 1, 1,
     "Sesión generada con random inseguro.", None),
]

# The two attacks Adenda 2 itself declares unfixable by mechanical
# means (red report, residuales): dead code and input provenance.
DECLARED_RESIDUALS = {"C3", "X2"}


def attack_diff(lines, context_extra):
    if context_extra is None:
        header = ["diff --git a/app/attack.py b/app/attack.py",
                  "--- /dev/null",
                  "+++ b/app/attack.py",
                  f"@@ -0,0 +1,{len(lines)} @@"]
        body = ["+" + line for line in lines]
    else:
        header = ["diff --git a/app/attack.py b/app/attack.py",
                  "--- a/app/attack.py",
                  "+++ b/app/attack.py",
                  f"@@ -1,{len(lines)} +1,{len(lines) + 1} @@"]
        body = [" " + line for line in lines] + ["+result = main()"]
    return "\n".join(header + body) + "\n"


def attack_candidate(claim_type, start, end, lines, message):
    return Candidate(
        rule_id="red-team",
        claim_type=claim_type,
        file="app/attack.py",
        start_line=start,
        end_line=end,
        message=message,
        evidence_text=tuple(lines[start - 1 : end]),
        severity_hint="high",
        category_hint=claim_type,
    )


class PolicyTests(unittest.TestCase):
    def test_frozen_gates_untouched(self):
        self.assertEqual(alma_gate.POLICY_SHA256, FROZEN_V10_SHA256)
        self.assertEqual(alma_gate_v11.POLICY_SHA256, FROZEN_V11_SHA256)

    def test_v12_policy_identity(self):
        self.assertEqual(POLICY_VERSION_V12, "alma-evidence-gate/1.2.0")
        self.assertNotIn(
            POLICY_SHA256_V12, (FROZEN_V10_SHA256, FROZEN_V11_SHA256)
        )
        self.assertEqual(KNOWN_CLAIM_TYPES_V12, alma_gate_v11.KNOWN_CLAIM_TYPES_V11)
        self.assertEqual(len(KNOWN_CLAIM_TYPES_V12), 14)

    def test_unknown_claim_still_fails_closed(self):
        status = gate_status(
            AlmaGateV12(), "general_correctness", ["    x = compute()"]
        )
        self.assertEqual(status, "rejected")


class RedTeamBatteryTests(unittest.TestCase):
    """The regression battery of Adenda 2: the 1.2.0 must reject
    every well-formed attack except the two declared residuals."""

    def test_battery(self):
        gate = AlmaGateV12()
        passed = []
        for aid, cls, _trick, lines, start, end, msg, ctx in ATTACKS:
            with self.subTest(attack=aid, claim=cls):
                diff = parse_unified_diff(attack_diff(lines, ctx))
                candidate = attack_candidate(cls, start, end, lines, msg)
                result = gate.validate([candidate], diff, "red-team")
                status = result.ledger[0].status
                if aid in DECLARED_RESIDUALS:
                    # Declared limit of the approach (Adenda 2):
                    # pinned as accepted so the hole is never
                    # silently forgotten or silently "fixed" by a
                    # rule that breaks legitimate cases.
                    self.assertEqual(status, "accepted")
                else:
                    self.assertEqual(status, "rejected")
                if status == "accepted":
                    passed.append(aid)
        self.assertEqual(sorted(passed), sorted(DECLARED_RESIDUALS))

    def test_pass_rate_collapsed(self):
        gate = AlmaGateV12()
        accepted = 0
        for _aid, cls, _trick, lines, start, end, msg, ctx in ATTACKS:
            diff = parse_unified_diff(attack_diff(lines, ctx))
            candidate = attack_candidate(cls, start, end, lines, msg)
            result = gate.validate([candidate], diff, "red-team")
            accepted += result.ledger[0].status == "accepted"
        # 2/46 = 4.3%, down from 44/46 = 95.7% under the 1.1.0; the 2
        # are exactly the declared residuals.
        self.assertEqual(accepted, 2)
        self.assertEqual(len(ATTACKS), 46)



class HardenedClassTests(unittest.TestCase):
    """One accept + the hardened rejects per fix of Adenda 2."""

    gate = None

    @classmethod
    def setUpClass(cls):
        cls.gate = AlmaGateV12()

    def status(self, claim_type, lines, start=1, end=None):
        return gate_status(self.gate, claim_type, lines, start=start, end=end)

    # (a) tokenization -------------------------------------------------
    def test_code_markers_survive_in_code(self):
        lines = ["    return requests.get(url, verify=False)"]
        self.assertEqual(
            self.status("tls_verification_disabled", lines), "accepted"
        )

    def test_assigned_string_kept_for_secret(self):
        lines = ['API_KEY = "sk-live-123456"']
        self.assertEqual(self.status("hardcoded_secret", lines), "accepted")

    def test_commented_out_code_is_not_evidence(self):
        lines = ["    # return requests.get(url, verify=False)"]
        self.assertEqual(
            self.status("tls_verification_disabled", lines), "rejected"
        )

    # (b) secret name filter + placeholder prefixes ---------------------
    def test_secret_rejects_innocent_names(self):
        self.assertEqual(
            self.status("hardcoded_secret", ['DEFAULT_REGION = "us-east-1"']),
            "rejected",
        )
        self.assertEqual(
            self.status(
                "hardcoded_secret", ['BASE_URL = "https://api.example.com/v2"']
            ),
            "rejected",
        )

    def test_secret_rejects_test_prefixed_value(self):
        self.assertEqual(
            self.status("hardcoded_secret", ['secret = "test-secret-value"']),
            "rejected",
        )

    # (c)+(d) race: assignment + same-line co-occurrence ------------------
    def test_race_accepts_lock_assignment_line(self):
        lines = [
            "import threading",
            "",
            "class Counter:",
            "    def __init__(self):",
            "        self.lock = threading.Lock()",
            "        self.value = 0",
        ]
        self.assertEqual(
            self.status("race_condition", lines, 5, 6), "accepted"
        )

    def test_race_rejects_separate_line_markers(self):
        # The documented intentional divergence from the 1.1.0's unit
        # pair: markers on separate lines, no co-occurring assignment.
        lines = ["import threading", "    self.cache = {}"]
        self.assertEqual(self.status("race_condition", lines), "rejected")

    def test_race_rejects_async_without_shared_assignment(self):
        lines = ["async def handler(self, req):", "    return self.render(req)"]
        self.assertEqual(self.status("race_condition", lines), "rejected")

    # (d) sql co-occurrence ----------------------------------------------
    def test_sql_accepts_skeleton_and_construction_same_line(self):
        lines = ['    q = f"SELECT * FROM t WHERE id = {x}"']
        self.assertEqual(self.status("sql_injection", lines), "accepted")

    def test_sql_rejects_parameterized(self):
        lines = ['    q = "SELECT * FROM t WHERE id = ?"']
        self.assertEqual(self.status("sql_injection", lines), "rejected")

    def test_sql_rejects_label_string(self):
        lines = ['    report = "SELECT summary: " + suffix']
        self.assertEqual(self.status("sql_injection", lines), "rejected")

    # (e) antidote in the whole block --------------------------------------
    def test_deserialization_rejects_safeloader_below_citation(self):
        lines = ["data = yaml.load(", "    stream, Loader=yaml.SafeLoader)"]
        self.assertEqual(
            self.status("unsafe_deserialization", lines, 1, 1), "rejected"
        )

    def test_resource_leak_rejects_close_below_citation(self):
        lines = ["f = open(path)", "data = f.read()", "f.close()"]
        self.assertEqual(
            self.status("resource_leak", lines, 1, 1), "rejected"
        )

    def test_swallowed_rejects_raise_below_citation(self):
        lines = [
            "try:",
            "    risky()",
            "except ValueError:",
            "    pass",
            "    raise",
        ]
        self.assertEqual(
            self.status("swallowed_exception", lines, 3, 4), "rejected"
        )

    # (f) added line ------------------------------------------------------
    def test_context_only_citation_rejected(self):
        lines = [
            'query = f"SELECT * FROM users WHERE id = {user_id}"',
            "cursor.execute(query)",
        ]
        diff = parse_unified_diff(attack_diff(lines, False))
        candidate = attack_candidate(
            "sql_injection", 1, 1, lines, "SQL injection en contexto."
        )
        result = self.gate.validate([candidate], diff, "test-agent")
        self.assertEqual(result.ledger[0].status, "rejected")
        self.assertTrue(
            any(
                "no line added by this change" in reason
                for reason in result.ledger[0].reasons
            )
        )

    # families G/H ---------------------------------------------------------
    def test_weak_random_rejects_noncredential_suffixes(self):
        for line in (
            "token_count = random.randint(1, 5)",
            "password_retry_delay = random.uniform(0.5, 1.5)",
            "session_ttl = random.randint(300, 600)",
        ):
            with self.subTest(line=line):
                self.assertEqual(
                    self.status("weak_random_security", [line]), "rejected"
                )

    def test_weak_random_accepts_credential_name(self):
        lines = ['    session_token = "".join(random.choices(chars, k=16))']
        self.assertEqual(
            self.status("weak_random_security", lines), "accepted"
        )

    def test_swallowed_rejects_import_error_fallback(self):
        lines = ["try:", "    import orjson", "except ImportError:", "    pass"]
        self.assertEqual(
            self.status("swallowed_exception", lines), "rejected"
        )

    def test_swallowed_accepts_value_error_pass(self):
        lines = ["    except ValueError:", "        pass"]
        self.assertEqual(
            self.status("swallowed_exception", lines), "accepted"
        )

    def test_tempfile_rejects_own_method(self):
        lines = [
            "class Tmp:",
            "    def mktemp(self):",
            "        return self._safe_make()",
            "t = Tmp()",
            "p = t.mktemp()",
        ]
        self.assertEqual(
            self.status("insecure_tempfile", lines, 5, 5), "rejected"
        )

    def test_tempfile_accepts_stdlib_receiver(self):
        lines = ['    return tempfile.mktemp(suffix=".tmp")']
        self.assertEqual(self.status("insecure_tempfile", lines), "accepted")

    def test_resource_leak_rejects_qt_signal_connect(self):
        lines = ["slider.valueChanged.connect(update)"]
        self.assertEqual(self.status("resource_leak", lines), "rejected")

    def test_resource_leak_accepts_socket_connect(self):
        lines = ["    sock = socket.socket()", "    sock.connect(addr)"]
        self.assertEqual(
            self.status("resource_leak", lines, 1, 2), "accepted"
        )

    def test_silenced_accepts_adjacent_pass(self):
        lines = ["    except:", "        pass"]
        self.assertEqual(
            self.status("silenced_bare_except", lines), "accepted"
        )

    def test_silenced_rejects_reraise_with_foreign_pass(self):
        lines = [
            "def a():",
            "    try:",
            "        work()",
            "    except:",
            "        raise",
            "def b():",
            "    pass",
        ]
        self.assertEqual(
            self.status("silenced_bare_except", lines, 1, 7), "rejected"
        )


class InheritedPairsV12Tests(unittest.TestCase):
    """The 1.1.0's unit pairs under the 1.2.0: identical verdicts
    everywhere except the one documented race divergence."""

    def test_pairs(self):
        gate = AlmaGateV12()
        for claim_type, (accept_lines, reject_lines) in INHERITED_PAIRS.items():
            with self.subTest(claim_type=claim_type):
                self.assertEqual(
                    gate_status(gate, claim_type, reject_lines), "rejected"
                )
                expected_accept = (
                    "rejected" if claim_type == "race_condition" else "accepted"
                )
                self.assertEqual(
                    gate_status(gate, claim_type, accept_lines), expected_accept
                )


class FixtureEquivalenceE2ETests(unittest.TestCase):
    """No legitimate fixture may change outcome under the 1.2.0."""

    def _run(self, root, name, config):
        directory, diff_text, pr, responses = load_fixture(root, name)
        transport = PassTransport(responses)
        result = run_agent(
            diff_text=diff_text,
            pr_metadata=pr,
            agent_name="alma-reviewer",
            mode="alma",
            backend="llm",
            config=config,
            env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
            llm_transport=transport,
        )
        return result, transport

    def test_fixtures_v2_and_v11_identical_under_v12(self):
        for root in (FIXTURES_V2, FIXTURES_V11):
            for directory in sorted(p for p in root.iterdir() if p.is_dir()):
                with self.subTest(fixture=directory.name):
                    result_v11, _ = self._run(
                        root, directory.name, CONFIG_V11_ALMA
                    )
                    result_v12, transport_v12 = self._run(
                        root, directory.name, CONFIG_V12_ALMA
                    )
                    self.assertEqual(
                        result_v11.output["findings"],
                        result_v12.output["findings"],
                    )
                    self.assertEqual(
                        [e["status"] for e in result_v11.ledger],
                        [e["status"] for e in result_v12.ledger],
                    )
                    self.assertEqual(len(transport_v12.calls), 14)
                    self.assertEqual(
                        result_v12.llm_run_info["gate_version"],
                        POLICY_VERSION_V12,
                    )
                    self.assertTrue(
                        all(
                            entry["validator_version"] == POLICY_VERSION_V12
                            and entry["policy_sha256"] == POLICY_SHA256_V12
                            for entry in result_v12.ledger
                        )
                    )

    def test_fixtures_v1_mock_identical_under_v12(self):
        for directory in sorted(p for p in FIXTURES_V1.iterdir() if p.is_dir()):
            with self.subTest(fixture=directory.name):
                diff_text = (directory / "diff.patch").read_text(
                    encoding="utf-8"
                )
                pr = json.loads(
                    (directory / "pr.json").read_text(encoding="utf-8")
                )
                outcomes = {}
                for gate_version in ("v1", "v12"):
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
                self.assertEqual(outcomes["v1"], outcomes["v12"])


class GateSelectionV12Tests(unittest.TestCase):
    def test_base_arm_with_v12_stamps_v12(self):
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
            config=dict(CONFIG_V12_ALMA, governance="base"),
            env=armed_env(RB_REPO_ROOT=str(directory / "repo")),
            llm_transport=transport,
        )
        self.assertEqual(len(transport.calls), 15)
        self.assertTrue(
            all(
                entry["validator_version"] == "bypassed-base-arm"
                and entry["policy_sha256"] == POLICY_SHA256_V12
                for entry in result.ledger
            )
        )

    def test_unknown_gate_still_fails_closed(self):
        _, diff_text, pr, _ = load_fixture(FIXTURES_V2, "v2_01_sql_injection")
        config = dict(CONFIG_V12_ALMA, gate="v9")
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


if __name__ == "__main__":
    unittest.main()
