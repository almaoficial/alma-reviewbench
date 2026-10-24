"""Reviewer v2.4 tests: evidence-discipline production.

Pre-registration: PREREGISTRO-PRODUCTOR-EVIDENCIA.md §5 — the
emission schema's mechanical correctness, verified dry:

- a finding with a valid citation and a declared pattern that
  stands in its citation is BORN a candidate, and after the
  reviewer's own last production stage (the birth shaper,
  unmodified) it is CONFORMING under claim_contract (unmodified)
  and ACCEPTED by gate 1.5.0 (unmodified);
- a declared token absent from the citation is trimmed at
  origin by the shaping stage, the trim settled in the run
  info, and the claim is emitted with its surviving pattern;
- a finding whose tokens are ALL absent is not emitted: the
  production ledger settles it under
  `tokens_afirmados_ausentes_en_la_evidencia`;
- a finding with no declared pattern is born marked in the
  production ledger under `sin_patron_concreto_en_el_reclamo`;
- a declared pattern that differs from the pattern the message
  asserts is settled under `patron_declarado_distinto_del_mensaje`;
- a model-declared `unverifiable` entry is settled under
  `declarado_no_verificable_en_origen` with the model's reason —
  never a candidate, never malformed;
- class findings pass the shaping stage intact (Case C);
- the inherited discipline does not move (anchor mismatch ->
  unanchored; wrong mark -> malformed; the guard refuses before
  calling when the selection alone exceeds the brake);
- the armed deep and mixed prompts CONTAIN the evidence
  instructions (string inspection, no model call), and the
  selection prompt is byte-identical to the v2.3's;
- the frozen semaphore battery, driven directly through
  LLMReviewerV24.review() (the declared equivalent of
  BatteryDryRunTests — main.py mounting is outside the paper):
  8 cases x 2 gate configs = 16 runs, 16/16;
- the run-344 fix (ADENDA-ARREGLO-TOPE-20261024.md): the deep
  budget is this family's own resolved setting (default 16384;
  config/env override; invalid refuses), the selection budget
  is untouched, and the length-empty mode reproduces and
  repairs — empty content with finish_reason 'length' retries
  ONCE in-agent at double budget and the findings are produced;
  a second length-empty fails closed exactly as before; a
  brake without room refuses the retry (no second call) and
  fails closed as before; no other error retries.

No dry test here measures any EFFECT of the discipline on real
production rates: that is the paper's §3 caveat, and it is why
everything runs on scripted transports at US$0.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent.alma_gate_v150 import (  # noqa: E402
    CHECK_TOKENS_ABSENT,
    AlmaGateV150,
    _is_code_token,
    _normalize_token,
)
from agent.claim_contract import normalize_claim  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402
from agent.llm_reviewer import RealLLMRefused  # noqa: E402
from agent.llm_reviewer_v23 import LLMReviewerV23  # noqa: E402
from agent.llm_reviewer_v24 import (  # noqa: E402
    CODE_DECLARED_UNVERIFIABLE,
    CODE_NO_PATTERN,
    CODE_PATTERN_MISMATCH,
    DEFAULT_DEEP_MAX_OUTPUT_TOKENS,
    LENGTH_RETRY_MULTIPLIER,
    REVIEWER_VERSION,
    LLMReviewerV24,
)
from test_gate_v11 import make_diff  # noqa: E402
from test_llm_reviewer_v22 import load_semaforo_case  # noqa: E402
from test_llm_reviewer_v23 import armed_env, pass_name_of  # noqa: E402

FROZEN_FILE_SHA256 = {
    "alma_gate.py": "4223cb0567fd398eb0c8b0a08e75a606559997823fabbc9bc1b5665f75607318",
    "alma_gate_v11.py": "fdd974f1ab8bd95c7bb24cd062360e0c2869c94f691c447dde900e4daf2c91f0",
    "alma_gate_v12.py": "c5c32bfc25386caeefe0e6ca91532c829710dd992e29d8718a8485cd3b9073f3",
    "alma_gate_v13.py": "d3b993d4d4f26b9df112dfd54abc391e8018faae024d23c63b4924d86d2dc1e0",
    "alma_gate_v14.py": "b16c5a795c56e0961eef596f57ce8b52eae8b1b3218bd3f7fa730e6b1c1347d8",
    "alma_gate_v141.py": "08d813e977dffeb47ea32938827a8babbb658dfc6a9cdc809508f3480cb6e8ff",
    "alma_gate_v150.py": "71b1996b604858b1b071646feb734dfaef361e6c120428b0e68cb88f8206c404",
    "claim_contract.py": "7df8abc77ec1cec46222bd276b739b0d23be4671882e2d96323d11818268f0f8",
    "birth_shaper.py": "2b127b23b58e5b8ad70c05860faf4cc128e715a756d8e44d7d749cb5a7664cd1",
    "llm_reviewer_v23.py": "a78bdd6d0cde6cb81a499085635d4aebbfb8e716d445b71c76684df42bab5b53",
}

PATH = "app/x.py"
LINES = [
    "import subprocess",
    "def run(cmd):",
    "    return subprocess.run(cmd, shell=True)",
]
SQL_LINES = [
    "import sqlite3",
    "def fetch(cursor, query):",
    "    cursor.execute(query)",
    "    return cursor.fetchall()",
]

CONFIG_V14 = {
    "model": "gpt-5.6-sol",
    "effort": "medium",
    "governance": "alma",
    "reviewer": "v24",
    "gate": "v14",
}
CONFIG_V13 = dict(CONFIG_V14, gate="v13")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EmissionTransport:
    """Scripted transport for the v2.4 reviewer: the selection
    pass answers with marks; each deep pass answers with its
    scripted two-array content."""

    USAGE = {"prompt_tokens": 100, "completion_tokens": 10}

    def __init__(self, marks=(), deep=None):
        self.marks = list(marks)
        self.deep = dict(deep or {})
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(payload)
        name = pass_name_of(payload)
        if name == "selection":
            content = {
                "candidates": [
                    {"mark": mark, "reason": "scripted mark"}
                    for mark in self.marks
                ]
            }
        else:
            content = self.deep.get(name, {"findings": []})
        body = {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": self.USAGE,
        }
        return 200, json.dumps(body).encode("utf-8")


def _run_review(lines, transport, config=CONFIG_V14, path=PATH):
    """Drive LLMReviewerV24.review() over a one-file repo whose
    head is `lines`; returns (emitted, run_info_dict, transport)."""

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        diff_text = make_diff(path, lines)
        reviewer = LLMReviewerV24.from_env(
            armed_env(), config, transport=transport
        )
        emitted = reviewer.review(
            diff_text=diff_text,
            diff=parse_unified_diff(diff_text),
            config=config,
            repo_root=repo,
        )
        return emitted, reviewer.last_run_info.to_dict(), transport


def _finding(**overrides):
    finding = {
        "file": PATH,
        "start_line": 3,
        "end_line": 3,
        "claim_type": "correctness",
        "message": "The call passes `shell=True` to the runner.",
        "pattern": ["shell=True"],
        "evidence": [LINES[2]],
    }
    finding.update(overrides)
    return finding


class IdentityAndFrozenTests(unittest.TestCase):
    def test_reviewer_identity(self):
        self.assertEqual(REVIEWER_VERSION, "llm-reviewer/2.4.0")
        self.assertEqual(LLMReviewerV24.name, "alma-llm-reviewer-v24")

    def test_frozen_files_byte_identical(self):
        agent_dir = ROOT / "agent"
        for name, expected in FROZEN_FILE_SHA256.items():
            self.assertEqual(
                _sha256(agent_dir / name), expected, f"{name} changed"
            )


class PromptTests(unittest.TestCase):
    def _reviewer(self):
        return LLMReviewerV24.from_env(
            armed_env(), CONFIG_V14, transport=EmissionTransport()
        )

    def test_deep_prompts_carry_the_evidence_discipline(self):
        reviewer = self._reviewer()
        for pass_name in ("sql_injection", "correctness"):
            with self.subTest(pass_name=pass_name):
                payload = reviewer.build_deep_payload(pass_name, "D", "C")
                system = str(payload["messages"][0]["content"])
                self.assertIn("EVIDENCE DISCIPLINE (binding)", system)
                self.assertIn("copied VERBATIM from the cited lines", system)
                self.assertIn(
                    "asserts ONLY what is visible in the cited lines", system
                )
                self.assertIn('"pattern"', system)
                self.assertIn('"unverifiable"', system)
                self.assertIn(
                    "an unverifiable entry is a declaration, not a finding",
                    system,
                )
                self.assertNotIn("temperature", payload)
                self.assertNotIn("max_tokens", payload)

    def test_mixed_prompt_carries_the_evidence_discipline(self):
        reviewer = self._reviewer()
        payload = reviewer.build_fallback_payload(
            [("class", "sql_injection"), ("category", "security")], "D"
        )
        system = str(payload["messages"][0]["content"])
        self.assertIn("EVIDENCE DISCIPLINE (binding)", system)
        self.assertIn('"unverifiable"', system)
        self.assertIn("--- CLASS sql_injection ---", system)
        self.assertIn("--- CATEGORY security ---", system)

    def test_selection_prompt_is_byte_identical_to_v23(self):
        env = armed_env()
        v24 = LLMReviewerV24.from_env(env, CONFIG_V14, transport=EmissionTransport())
        v23 = LLMReviewerV23.from_env(env, CONFIG_V14, transport=EmissionTransport())
        self.assertEqual(
            v24.build_selection_payload("THE-DIFF"),
            v23.build_selection_payload("THE-DIFF"),
        )


class EmissionSchemaTests(unittest.TestCase):
    def test_valid_citation_born_conforming_and_gate_accepted(self):
        transport = EmissionTransport(
            marks=["correctness"],
            deep={"correctness": {"findings": [_finding()]}},
        )
        emitted, info, _ = _run_review(LINES, transport)

        self.assertEqual(len(emitted), 1)
        candidate = emitted[0]
        self.assertEqual(candidate.producer, "alma-llm-reviewer-v24")
        self.assertEqual(candidate.rule_id, "llm_v24_correctness")
        self.assertEqual(info["production_ledger"], [])
        self.assertEqual(info["shaping"]["emitted"], 1)
        self.assertEqual(info["shaping"]["held_at_origin"], 0)
        self.assertEqual(info["shaping"]["trimmed_tokens"], 0)
        # Born in contract form: the contract check (unmodified)
        # confirms it, and gate 1.5.0 (unmodified) accepts it.
        check = normalize_claim(candidate)
        self.assertTrue(check.conforming)
        self.assertEqual(check.origin, "born")
        diff = parse_unified_diff(make_diff(PATH, LINES))
        result = AlmaGateV150().validate([candidate], diff, "test-agent")
        self.assertEqual(result.ledger[0].status, "accepted")

    def test_absent_token_trimmed_at_origin_and_settled(self):
        finding = _finding(
            start_line=1,
            end_line=3,
            message=(
                "The call passes `shell=True` and relies on "
                "`pickle.loads` internally."
            ),
            pattern=["shell=True", "pickle.loads"],
            evidence=list(LINES),
        )
        transport = EmissionTransport(
            marks=["correctness"],
            deep={"correctness": {"findings": [finding]}},
        )
        emitted, info, _ = _run_review(LINES, transport)

        self.assertEqual(len(emitted), 1)
        self.assertEqual(info["shaping"]["trimmed_tokens"], 1)
        self.assertEqual(info["production_ledger"], [])
        shaped = emitted[0]
        self.assertNotIn("`pickle.loads`", shaped.message)
        self.assertIn("`shell=True`", shaped.message)
        self.assertEqual((shaped.start_line, shaped.end_line), (3, 3))
        self.assertTrue(normalize_claim(shaped).conforming)

    def test_all_tokens_absent_held_in_production_ledger(self):
        finding = _finding(
            start_line=1,
            end_line=2,
            message="The path uses `eval(` on the input.",
            pattern=["eval("],
            evidence=list(LINES[:2]),
        )
        transport = EmissionTransport(
            marks=["correctness"],
            deep={"correctness": {"findings": [finding]}},
        )
        emitted, info, _ = _run_review(LINES, transport)

        self.assertEqual(emitted, [])
        self.assertEqual(info["shaping"]["held_at_origin"], 1)
        self.assertEqual(len(info["production_ledger"]), 1)
        record = info["production_ledger"][0]
        self.assertEqual(record["pass"], "production_shaping")
        self.assertEqual(record["code"], CHECK_TOKENS_ABSENT)
        self.assertEqual(
            info["production_ledger_by_code"], {CHECK_TOKENS_ABSENT: 1}
        )

    def test_no_declared_pattern_settled_not_emitted(self):
        valid = _finding()
        no_pattern = _finding(
            start_line=2,
            end_line=2,
            message="The function ignores its argument.",
            evidence=[LINES[1]],
        )
        del no_pattern["pattern"]
        empty_pattern = _finding(
            start_line=1,
            end_line=1,
            message="An import stands at the top.",
            pattern=[],
            evidence=[LINES[0]],
        )
        transport = EmissionTransport(
            marks=["correctness"],
            deep={
                "correctness": {
                    "findings": [valid, no_pattern, empty_pattern]
                }
            },
        )
        emitted, info, _ = _run_review(LINES, transport)

        self.assertEqual(len(emitted), 1)
        self.assertEqual(info["malformed_findings"], 0)
        codes = [r["code"] for r in info["production_ledger"]]
        self.assertEqual(codes, [CODE_NO_PATTERN, CODE_NO_PATTERN])
        self.assertTrue(
            all(
                r["pass"] == "correctness"
                for r in info["production_ledger"]
            )
        )

    def test_pattern_message_mismatch_settled_not_emitted(self):
        finding = _finding(
            message="The handler reaches `os.system` here.",
            pattern=["shell=True"],
        )
        transport = EmissionTransport(
            marks=["correctness"],
            deep={"correctness": {"findings": [finding]}},
        )
        emitted, info, _ = _run_review(LINES, transport)

        self.assertEqual(emitted, [])
        self.assertEqual(info["malformed_findings"], 0)
        self.assertEqual(len(info["production_ledger"]), 1)
        record = info["production_ledger"][0]
        self.assertEqual(record["code"], CODE_PATTERN_MISMATCH)
        self.assertEqual(record["claim_type"], "correctness")

    def test_model_declared_unverifiable_settled_with_reason(self):
        transport = EmissionTransport(
            marks=["correctness"],
            deep={
                "correctness": {
                    "findings": [],
                    "unverifiable": [
                        {
                            "file": PATH,
                            "start_line": 2,
                            "end_line": 2,
                            "claim_type": "correctness",
                            "message": "A race is suspected on the runner.",
                            "reason": (
                                "the interleaving is not visible in any "
                                "citable line"
                            ),
                        },
                        {"note": "shapeless entry"},
                    ],
                }
            },
        )
        emitted, info, _ = _run_review(LINES, transport)

        self.assertEqual(emitted, [])
        self.assertEqual(info["raw_findings"], 0)
        self.assertEqual(len(info["production_ledger"]), 1)
        record = info["production_ledger"][0]
        self.assertEqual(record["code"], CODE_DECLARED_UNVERIFIABLE)
        self.assertEqual(
            record["reason"],
            "the interleaving is not visible in any citable line",
        )
        # The shapeless entry fails the schema's form: malformed.
        self.assertEqual(info["malformed_findings"], 1)

    def test_class_finding_passes_shaping_intact(self):
        finding = {
            "file": PATH,
            "start_line": 3,
            "end_line": 3,
            "claim_type": "sql_injection",
            "message": "The query reaches `cursor.execute` unsanitized.",
            "pattern": ["cursor.execute"],
            "evidence": [SQL_LINES[2]],
        }
        transport = EmissionTransport(
            marks=["sql_injection"],
            deep={"sql_injection": {"findings": [finding]}},
        )
        emitted, info, _ = _run_review(SQL_LINES, transport)

        self.assertEqual(len(emitted), 1)
        candidate = emitted[0]
        self.assertEqual(candidate.message, finding["message"])
        self.assertEqual((candidate.start_line, candidate.end_line), (3, 3))
        self.assertEqual(info["shaping"]["origins"]["class"], 1)
        self.assertEqual(info["production_ledger"], [])
        check = normalize_claim(candidate)
        self.assertTrue(check.conforming)
        self.assertEqual(check.origin, "class")

    def test_inherited_discipline_unanchored_and_wrong_mark(self):
        unanchored = _finding(evidence=["this text is not the head line"])
        wrong_mark = _finding(claim_type="reliability")
        transport = EmissionTransport(
            marks=["correctness"],
            deep={"correctness": {"findings": [unanchored, wrong_mark]}},
        )
        emitted, info, _ = _run_review(LINES, transport)

        self.assertEqual(emitted, [])
        self.assertEqual(info["unanchored_findings"], 1)
        self.assertEqual(info["malformed_findings"], 1)
        self.assertEqual(info["production_ledger"], [])

    def test_guard_refuses_before_calling_when_selection_exceeds_brake(self):
        transport = EmissionTransport(marks=["correctness"])
        env = armed_env(RB_MAX_SPEND_USD="0.0001")
        reviewer = LLMReviewerV24.from_env(env, CONFIG_V14, transport=transport)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target = repo / PATH
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(LINES) + "\n", encoding="utf-8")
            diff_text = make_diff(PATH, LINES)
            with self.assertRaises(RealLLMRefused) as caught:
                reviewer.review(
                    diff_text=diff_text,
                    diff=parse_unified_diff(diff_text),
                    config=CONFIG_V14,
                    repo_root=repo,
                )
        self.assertIn("refused before calling", str(caught.exception))
        self.assertEqual(transport.calls, [])


class ScriptedDeepTransport:
    """Scripted transport for the run-344 fix: the selection
    pass answers with marks; each deep pass consumes, in order,
    a script of response specs — {"content": dict|str,
    "finish_reason": str, "status": int} — so a test can script
    the exact death of run nº 344 (an empty body closed by
    'length') and what the in-agent retry then sees."""

    USAGE = {"prompt_tokens": 100, "completion_tokens": 10}

    def __init__(self, marks=(), deep_scripts=None):
        self.marks = list(marks)
        self.deep_scripts = {
            name: list(specs) for name, specs in (deep_scripts or {}).items()
        }
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(payload)
        name = pass_name_of(payload)
        if name == "selection":
            content = {
                "candidates": [
                    {"mark": mark, "reason": "scripted mark"}
                    for mark in self.marks
                ]
            }
            body = {
                "choices": [
                    {
                        "message": {"content": json.dumps(content)},
                        "finish_reason": "stop",
                    }
                ],
                "usage": self.USAGE,
            }
            return 200, json.dumps(body).encode("utf-8")
        script = self.deep_scripts.get(name) or []
        spec = script.pop(0) if script else {"content": {"findings": []}}
        status = spec.get("status", 200)
        if status != 200:
            return status, b"scripted endpoint error"
        content = spec.get("content", {"findings": []})
        if not isinstance(content, str):
            content = json.dumps(content)
        body = {
            "choices": [
                {
                    "message": {"content": content},
                    "finish_reason": spec.get("finish_reason", "stop"),
                }
            ],
            "usage": self.USAGE,
        }
        return 200, json.dumps(body).encode("utf-8")

    def deep_calls(self, name="correctness"):
        return [p for p in self.calls if pass_name_of(p) == name]


def _run_review_env(lines, transport, env, config=CONFIG_V14, path=PATH):
    """_run_review with an explicit env, returning the reviewer
    itself so a refusal's settled run info stays inspectable."""

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        diff_text = make_diff(path, lines)
        reviewer = LLMReviewerV24.from_env(env, config, transport=transport)
        try:
            emitted = reviewer.review(
                diff_text=diff_text,
                diff=parse_unified_diff(diff_text),
                config=config,
                repo_root=repo,
            )
            return emitted, reviewer, None
        except RealLLMRefused as exc:
            return None, reviewer, exc


class DeepBudgetTests(unittest.TestCase):
    def test_default_deep_budget_and_selection_untouched(self):
        reviewer = LLMReviewerV24.from_env(
            armed_env(), CONFIG_V14, transport=EmissionTransport()
        )
        self.assertEqual(DEFAULT_DEEP_MAX_OUTPUT_TOKENS, 16384)
        self.assertEqual(reviewer.deep_max_output_tokens, 16384)
        self.assertEqual(
            reviewer.length_retry_max_output_tokens,
            16384 * LENGTH_RETRY_MULTIPLIER,
        )
        deep = reviewer.build_deep_payload("correctness", "D", "C")
        self.assertEqual(deep["max_completion_tokens"], 16384)
        fallback = reviewer.build_fallback_payload(
            [("category", "correctness")], "D"
        )
        self.assertEqual(fallback["max_completion_tokens"], 16384)
        # The selection keeps its own triage line (fix v2.3.1's).
        selection = reviewer.build_selection_payload("D")
        self.assertEqual(selection["max_completion_tokens"], 4096)

    def test_deep_budget_resolution_config_env_invalid(self):
        config = dict(CONFIG_V14, deep_max_output_tokens="8192")
        reviewer = LLMReviewerV24.from_env(
            armed_env(), config, transport=EmissionTransport()
        )
        self.assertEqual(reviewer.deep_max_output_tokens, 8192)
        self.assertEqual(reviewer.length_retry_max_output_tokens, 16384)

        env = armed_env(RB_LLM_V24_DEEP_MAX_OUTPUT_TOKENS="2048")
        reviewer = LLMReviewerV24.from_env(
            env, CONFIG_V14, transport=EmissionTransport()
        )
        self.assertEqual(reviewer.deep_max_output_tokens, 2048)

        for bad in ("abc", "0", "-5"):
            with self.subTest(bad=bad):
                env = armed_env(RB_LLM_V24_DEEP_MAX_OUTPUT_TOKENS=bad)
                with self.assertRaises(RealLLMRefused):
                    LLMReviewerV24.from_env(
                        env, CONFIG_V14, transport=EmissionTransport()
                    )


class LengthRetryTests(unittest.TestCase):
    def test_length_empty_retries_at_double_budget_and_recovers(self):
        transport = ScriptedDeepTransport(
            marks=["correctness"],
            deep_scripts={
                "correctness": [
                    {"content": "", "finish_reason": "length"},
                    {"content": {"findings": [_finding()]}},
                ]
            },
        )
        emitted, info, _ = _run_review(LINES, transport)

        self.assertEqual(len(emitted), 1)
        self.assertEqual(info["calls"], 3)
        self.assertEqual(info["passes"], ["selection", "correctness"])
        self.assertEqual(info["deep_max_output_tokens"], 16384)
        self.assertEqual(info["parse_failures"], [])
        self.assertEqual(
            info["length_retries"],
            [
                {
                    "pass": "correctness",
                    "first_max_output_tokens": 16384,
                    "retry_max_output_tokens": 32768,
                    "outcome": "recovered",
                }
            ],
        )
        deep_payloads = transport.deep_calls()
        self.assertEqual(len(deep_payloads), 2)
        self.assertEqual(deep_payloads[0]["max_completion_tokens"], 16384)
        self.assertEqual(deep_payloads[1]["max_completion_tokens"], 32768)

    def test_length_empty_twice_fails_closed_as_before(self):
        transport = ScriptedDeepTransport(
            marks=["correctness"],
            deep_scripts={
                "correctness": [
                    {"content": "", "finish_reason": "length"},
                    {"content": "", "finish_reason": "length"},
                ]
            },
        )
        emitted, reviewer, exc = _run_review_env(LINES, transport, armed_env())

        self.assertIsNone(emitted)
        self.assertIsNotNone(exc)
        self.assertIn("parse failure settled", str(exc))
        self.assertIn("finish_reason='length'", str(exc))
        self.assertIn("content_length=0", str(exc))
        self.assertEqual(len(transport.deep_calls()), 2)
        info = reviewer.last_run_info.to_dict()
        self.assertEqual(info["length_retries"][0]["outcome"], "still_empty")
        self.assertEqual(len(info["parse_failures"]), 1)
        self.assertEqual(info["parse_failures"][0]["finish_reason"], "length")
        self.assertEqual(info["parse_failures"][0]["content_length"], 0)

    def test_length_retry_refused_when_brake_has_no_room(self):
        # Cap US$2.00: the deep pass is admitted (its worst case
        # at 16384 fits), but the retry's worst case at 32768
        # does not — so no second call exists and the original
        # empty response fails closed exactly as before the fix.
        transport = ScriptedDeepTransport(
            marks=["correctness"],
            deep_scripts={
                "correctness": [
                    {"content": "", "finish_reason": "length"},
                    {"content": {"findings": [_finding()]}},
                ]
            },
        )
        env = armed_env(RB_MAX_SPEND_USD="2.00")
        emitted, reviewer, exc = _run_review_env(LINES, transport, env)

        self.assertIsNone(emitted)
        self.assertIsNotNone(exc)
        self.assertIn("parse failure settled", str(exc))
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(len(transport.deep_calls()), 1)
        info = reviewer.last_run_info.to_dict()
        self.assertEqual(
            info["length_retries"][0]["outcome"], "refused_spend_cap"
        )

    def test_other_errors_do_not_retry(self):
        # HTTP error on the deep pass: one call, refusal, no retry.
        transport = ScriptedDeepTransport(
            marks=["correctness"],
            deep_scripts={"correctness": [{"status": 500}]},
        )
        emitted, reviewer, exc = _run_review_env(LINES, transport, armed_env())
        self.assertIsNone(emitted)
        self.assertIn("HTTP 500", str(exc))
        self.assertEqual(len(transport.deep_calls()), 1)
        self.assertEqual(reviewer.last_run_info.to_dict()["length_retries"], [])

        # Non-empty unparseable content closed by 'length': the
        # mode is the EMPTY response, not the finish reason
        # alone — no retry, the parse failure settles as before.
        transport = ScriptedDeepTransport(
            marks=["correctness"],
            deep_scripts={
                "correctness": [
                    {"content": "this is not json", "finish_reason": "length"}
                ]
            },
        )
        emitted, reviewer, exc = _run_review_env(LINES, transport, armed_env())
        self.assertIsNone(emitted)
        self.assertIn("parse failure settled", str(exc))
        self.assertEqual(len(transport.deep_calls()), 1)
        self.assertEqual(reviewer.last_run_info.to_dict()["length_retries"], [])


_TOKEN_RES = [
    re.compile(r"[A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]+"),
    re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+"),
    re.compile(r"[A-Za-z_][A-Za-z0-9_]*=[A-Za-z0-9_]+"),
]


def _citable_token(line: str) -> str:
    """A code token copied from the planted line itself (snake_case
    first, then dotted, then assignment) — the token the scripted
    deep pass declares as its pattern, exactly as the schema
    requires a real model to copy it from its citation."""

    for regex in _TOKEN_RES:
        for match in regex.finditer(line):
            piece = match.group(0)
            if _normalize_token(piece) == piece and _is_code_token(piece):
                return piece
    raise AssertionError(f"no citable token in planted line: {line!r}")


class BatteryTransport:
    """The semaphore echo under the v2.4 schema: the selection
    marks the planted class; the deep pass returns the planted
    defect with its pattern copied from the cited line."""

    USAGE = {"prompt_tokens": 100, "completion_tokens": 10}

    def __init__(self, planted, token):
        self.planted = planted
        self.token = token
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append(payload)
        name = pass_name_of(payload)
        if name == "selection":
            content = {
                "candidates": [
                    {"mark": self.planted["claim_type"], "reason": "scripted"}
                ]
            }
        else:
            finding = dict(self.planted)
            finding["message"] = (
                f"mock echo of the planted defect: `{self.token}` "
                "stands on the cited line"
            )
            finding["pattern"] = [self.token]
            content = {"findings": [finding], "unverifiable": []}
        body = {
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": self.USAGE,
        }
        return 200, json.dumps(body).encode("utf-8")


class BatteryDryRunV24Tests(unittest.TestCase):
    """The declared battery equivalent (paper §5.2): the frozen
    semaphore battery driven directly through
    LLMReviewerV24.review() — 8 cases x 2 gate configs, 16 runs."""

    def test_battery_16_of_16_without_refusals(self):
        fixtures = ROOT / "fixtures_semaforo"
        cases = sorted(p.name for p in fixtures.iterdir() if p.is_dir())
        self.assertEqual(len(cases), 8)
        runs = 0
        for case in cases:
            directory, diff_text, _pr, truth, planted = load_semaforo_case(case)
            token = _citable_token(planted["evidence"][0])
            for config in (CONFIG_V13, CONFIG_V14):
                with self.subTest(case=case, gate=config["gate"]):
                    transport = BatteryTransport(planted, token)
                    reviewer = LLMReviewerV24.from_env(
                        armed_env(), config, transport=transport
                    )
                    emitted = reviewer.review(
                        diff_text=diff_text,
                        diff=parse_unified_diff(diff_text),
                        config=config,
                        repo_root=directory / "repo",
                    )
                    info = reviewer.last_run_info.to_dict()
                    self.assertEqual(
                        info["reviewer_version"], "llm-reviewer/2.4.0"
                    )
                    self.assertEqual(info["calls"], 2)
                    self.assertEqual(
                        info["selection_specialty"], [truth["planted_class"]]
                    )
                    self.assertEqual(info["selection_general"], [])
                    self.assertIsNone(info["degradation"])
                    self.assertEqual(info["production_ledger"], [])
                    self.assertEqual(len(emitted), 1)
                    self.assertTrue(normalize_claim(emitted[0]).conforming)
                    runs += 1
        self.assertEqual(runs, 16)


if __name__ == "__main__":
    unittest.main()
