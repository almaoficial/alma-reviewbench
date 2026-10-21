"""LLM reviewer v2 — built to speak the frozen gate's language.

Why this module exists (pre-registration: PREREGISTRO-REVIEWBENCH-V2.md,
frozen 2026-10-19): the v1 reviewer (``agent/llm_reviewer.py``) asked the
model for a free-form review of the diff in a single call.  In the v1
practice the ALMA arm emitted exactly 1 finding in 25 PRs: the frozen gate
(``alma-evidence-gate/1.0.0``) verifies only 8 claim classes, each with its
own specific evidence, and nearly everything a general reviewer proposes
falls outside those classes and is rejected fail-closed.  The v1 reviewer
also saw only the diff (base-arm grounded recall 0.7%).

The v2 reviewer changes the REVIEWER ONLY.  The gate is not touched: same
``POLICY_SHA256``, same checks.  What changes:

- **Full-file context.**  Besides the diff, the model receives the complete
  head contents of every file the PR touches, read from the mounted repo
  (ReviewBench mounts it at ``/work/repo``; override with
  ``RB_REPO_ROOT`` / ``RB_CONFIG_REPO_ROOT``).  Inclusion is bounded by a
  per-PR context token budget — config ``RB_CONFIG_CONTEXT_TOKEN_BUDGET``,
  env ``RB_LLM_V2_CONTEXT_TOKEN_BUDGET``, default 60000 estimated tokens.
  Files are included whole, in diff order, until the budget runs out; what
  was included / skipped / missing is declared in the run info.
- **One pass per verifiable claim class.**  The model is called once per
  class of the ACTIVE gate (``KNOWN_CLAIM_TYPES`` of the frozen gate by
  default; the 1.1.0's 14 under ``RB_CONFIG_GATE=v11``) and asked ONLY
  for findings of that class,
  with the class's evidence requirement spelled out.  In the ALMA arm every
  candidate is therefore born inside a verifiable class or not at all.  A
  returned finding whose ``claim_type`` does not match its pass is dropped
  as malformed.  The BASE arm (``governance=base``) gets one extra
  free-form "general" pass, as the pre-registration allows.
- **Anchor verification in the reviewer.**  The model must quote the exact
  text of every line it cites (``evidence`` array).  A candidate is kept
  only if the cited range exists in the head file and the quoted text
  matches the head file byte-for-byte at the line level.  Failures are
  dropped here (counted as unanchored) instead of reaching the gate; the
  stored ``evidence_text`` is filled from the head file, never from the
  model's words.  The frozen gate still applies its own diff-presence
  check on top — anchoring (head file) and gating (diff) are separate
  authorities by design.

Selection: run configuration ``RB_CONFIG_REVIEWER=v2`` (default ``v1``);
see ``agent/main.py``.  The v1 module is untouched so the v1 experiment
stays reproducible.

Gate selection (Adenda 1 of the pre-registration): the passes follow
the ACTIVE gate's class list — run configuration ``RB_CONFIG_GATE``:
``v1`` (default) targets the frozen gate's 8 classes; ``v11`` targets
``alma-evidence-gate/1.1.0``'s 14 (the same 8 plus 6 mechanically
verifiable classes defined in ``agent/alma_gate_v11.py``); ``v12``
targets ``alma-evidence-gate/1.2.0`` (Adenda 2), which verifies the
same 14 classes with hardened checks, so its pass list is the
1.1.0's; ``v13`` targets ``alma-evidence-gate/1.3.0`` (Adenda 3):
the 1.2.0's 14 plus the hunter's 5 (weak_hash,
tarfile_unsafe_extract, hardcoded_password_argument,
jwt_verification_disabled, debug_mode_enabled), and — Adenda 3's
lever 1 — the per-class guidance gains a citation-discipline
addendum for the classes whose hardened checks are citation-shaped
(sql_injection, race_condition) or block-antidote-shaped
(resource_leak, swallowed_exception, unsafe_deserialization).  The
addendum is guidance TEXT only: with ``v1``/``v11``/``v12`` the
passes, prompts and candidates are byte-identical to before.  The
gate itself is selected in ``agent/main.py`` from the same config
key, so reviewer and gate cannot disagree about which classes
exist.

Safety contract: identical to v1 — same ``LLMSettings`` arming rules
(ALLOW_REAL_LLM=1, API key, RB_MODEL_BASE_URL, model, positive
RB_MAX_SPEND_USD), same payload corrections (no ``temperature``, no
``max_tokens``; ``max_completion_tokens``; the HTTP error body excerpt is
included in refusals), same fail-closed behaviour.  The spend cap is now
enforced across the whole multi-pass run: a worst-case pre-flight over
ALL passes refuses before the first call, and cumulative reported cost is
checked after every pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Mapping

from .alma_gate import KNOWN_CLAIM_TYPES, POLICY_VERSION as GATE_V1_VERSION
from .alma_gate_v11 import (
    KNOWN_CLAIM_TYPES_V11,
    POLICY_VERSION as GATE_V11_VERSION,
)
from .alma_gate_v12 import (
    KNOWN_CLAIM_TYPES_V12,
    POLICY_VERSION as GATE_V12_VERSION,
)
from .alma_gate_v13 import (
    KNOWN_CLAIM_TYPES_V13,
    POLICY_VERSION as GATE_V13_VERSION,
)
from .base_reviewer import Candidate
from .diff_parser import DiffIndex
from .llm_reviewer import (
    LLMSettings,
    RealLLMRefused,
    Transport,
    _CLAIM_HINTS,
    _estimate_tokens,
    _extract_findings,
    _urllib_transport,
)


REVIEWER_VERSION = "llm-reviewer/2.0.0"
DEFAULT_CONTEXT_TOKEN_BUDGET = 60000
GENERAL_PASS = "general"

# The evidence each class must show, in the gate's own terms (the claim
# descriptions and checks of alma-evidence-gate/1.0.0, restated as search
# instructions).  This is the "same language" the pre-registration means:
# the reviewer hunts exactly what the gate knows how to verify.
_CLASS_GUIDANCE: dict[str, str] = {
    "command_execution": (
        "shell or dynamic code execution: a line calling os.system(...), "
        "eval(...), exec(...), or passing shell=True"
    ),
    "hardcoded_secret": (
        "a credential (api key, token, password, secret) assigned in source "
        "to a quoted literal value of at least 6 characters that is not a "
        "placeholder (not changeme/example/redacted, not ${...}, not read "
        "from os.environ/os.getenv)"
    ),
    "mutable_default": (
        "a function definition whose argument defaults to a mutable "
        "object: = [], = {} or = set()"
    ),
    "race_condition": (
        "concurrency plus shared state in the SAME cited lines: a "
        "threading/multiprocessing/async/await/Lock marker together with "
        "a global/shared/cache/self. state marker"
    ),
    "silenced_bare_except": (
        "a bare 'except:' line whose handler body is only 'pass'; cite "
        "the range covering both lines"
    ),
    "sql_injection": (
        "SQL text (SELECT / INSERT INTO / UPDATE / DELETE FROM) built "
        "unsafely in the cited line: an f-string, .format(...), % "
        "formatting, or string concatenation"
    ),
    "tls_verification_disabled": (
        "a call passing verify=False, disabling TLS certificate "
        "verification"
    ),
    "unsafe_deserialization": (
        "pickle.loads(...) on data, or yaml.load(...) without SafeLoader"
    ),
}

# Guidance for the 6 classes added by gate 1.1.0 (Adenda 1), in that
# gate's own terms.  Used only when RB_CONFIG_GATE=v11 selects them.
_NEW_CLASS_GUIDANCE: dict[str, str] = {
    "insecure_tempfile": (
        "a call to tempfile.mktemp(...), which is insecure by design; "
        "cite the line with the mktemp( call"
    ),
    "resource_leak": (
        "a resource opened in the cited lines — open(...), a connection "
        "connect(...), a socket — that is neither managed by a 'with' "
        "statement nor closed with .close() inside the cited range; "
        "cite the range covering the opening"
    ),
    "ssl_context_unverified": (
        "an SSL context created with ssl._create_unverified_context(...) "
        "or a verify_mode set to CERT_NONE in the cited lines"
    ),
    "swallowed_exception": (
        "a typed 'except SomeError:' handler whose body is only 'pass', "
        "silently swallowing the error; cite the range covering the "
        "except line and its pass body"
    ),
    "unsafe_xml_parsing": (
        "XML parsed with the standard library — ET.parse / "
        "ET.fromstring, xml.dom, xml.sax — without defusedxml anywhere "
        "in the cited lines"
    ),
    "weak_random_security": (
        "a value assigned to a security name (token, secret, password, "
        "otp, session, api_key) that is generated on the same line with "
        "the 'random' module instead of 'secrets'"
    ),
}

_CLASS_GUIDANCE_V11: dict[str, str] = {**_CLASS_GUIDANCE, **_NEW_CLASS_GUIDANCE}

# Guidance for the 5 classes added by gate 1.3.0 (Adenda 3), in that
# gate's own terms (the hunter report's mechanical rules, restated as
# search instructions).  Used only when RB_CONFIG_GATE=v13.
_NEW_CLASS_GUIDANCE_V13: dict[str, str] = {
    "weak_hash": (
        "a weak hash constructed with hashlib.md5(...) or "
        "hashlib.sha1(...), or hashlib.new('md5'/'sha1'), WITHOUT "
        "usedforsecurity=False in the call; a bare md5(...) that is "
        "not resolved to hashlib does not count, and neither does "
        "hashlib.sha256"
    ),
    "tarfile_unsafe_extract": (
        "a .extractall(...) call on a tar archive WITHOUT filter= "
        "in the same call; a zipfile's extractall does not count "
        "(CPython neutralizes '..' for zip archives)"
    ),
    "hardcoded_password_argument": (
        "a password/passwd/pwd/secret/api_key/token keyword argument "
        "(or function default) set to a quoted literal of at least 6 "
        "characters that is not a placeholder (not changeme/example/"
        "redacted, not ${...}) and is not read from os.environ, "
        "another variable, or a vault"
    ),
    "jwt_verification_disabled": (
        "a jwt.decode(...) call that disables signature "
        "verification: options containing 'verify_signature': False, "
        "a verify=False argument, or an algorithms list containing "
        "'none'; cite the whole decode call, including the line "
        "carrying the disabling option"
    ),
    "debug_mode_enabled": (
        "debug mode switched on with the literal True: a DEBUG = "
        "True setting, an app.debug = True assignment, or a "
        ".run(..., debug=True) call; a value computed from the "
        "environment does not count"
    ),
}

# Citation discipline (Adenda 3, lever 1): how to CITE so the
# hardened gates (1.2.0 checks, inherited by the 1.3.0) can verify
# the finding.  Appended to the class guidance ONLY under
# RB_CONFIG_GATE=v13; the older configurations keep their previous
# guidance text byte for byte.
_CITATION_ADDENDA: dict[str, str] = {
    "sql_injection": (
        "CITATION (required by the gate): cite the line where the "
        "SQL skeleton (SELECT ... FROM / INSERT INTO / UPDATE ... "
        "SET / DELETE FROM) and the unsafe construction (f-string, "
        ".format(...), % formatting, concatenation) appear "
        "TOGETHER; if the statement is written across several "
        "lines, cite the WHOLE statement so the line carrying both "
        "is inside the range"
    ),
    "race_condition": (
        "CITATION (required by the gate): cite together the lines "
        "showing the concurrency and the shared-state mutation; the "
        "range must include a line where a concurrency marker "
        "(threading, async, await, Lock) and an assignment to "
        "shared state (self.x = ...) COINCIDE — e.g. the "
        "'self.lock = threading.Lock()' line or an "
        "'self.cache = await ...' line — not only the 'async def' "
        "or 'import threading' line"
    ),
    "resource_leak": (
        "CITATION (required by the gate): BEFORE proposing, scan "
        "the whole changed block in the diff: if a .close() for the "
        "resource appears ANYWHERE in the block, or the opening is "
        "managed by a 'with', do NOT propose this finding — the "
        "gate searches the antidote in the whole block, not only "
        "inside your cited range"
    ),
    "swallowed_exception": (
        "CITATION (required by the gate): cite the except line AND "
        "its pass body together; BEFORE proposing, read the whole "
        "handler in the block — if it re-raises (raise) or handles "
        "the error on a line below your range, do NOT propose; an "
        "'except ImportError' optional-dependency fallback is "
        "idiomatic and is NOT this class"
    ),
    "unsafe_deserialization": (
        "CITATION (required by the gate): BEFORE proposing a "
        "yaml.load finding, scan the whole changed block for "
        "SafeLoader — if it appears ANYWHERE in the block, even "
        "outside your cited range, do NOT propose this finding"
    ),
}


def _guidance_with_citation(
    base: dict[str, str], addenda: dict[str, str]
) -> dict[str, str]:
    merged = dict(base)
    for claim_type, addendum in addenda.items():
        merged[claim_type] = merged[claim_type] + ". " + addendum
    return merged


_CLASS_GUIDANCE_V13: dict[str, str] = _guidance_with_citation(
    {**_CLASS_GUIDANCE_V11, **_NEW_CLASS_GUIDANCE_V13},
    _CITATION_ADDENDA,
)

# Severity/category hints for the new classes (reviewer-side metadata;
# the v1 _CLAIM_HINTS cover the inherited 8).
_NEW_CLAIM_HINTS: dict[str, tuple[str, str]] = {
    "insecure_tempfile": ("medium", "security"),
    "resource_leak": ("medium", "reliability"),
    "ssl_context_unverified": ("high", "security"),
    "swallowed_exception": ("medium", "reliability"),
    "unsafe_xml_parsing": ("high", "security"),
    "weak_random_security": ("high", "security"),
}

# Severity/category hints for the 5 classes of gate 1.3.0 (Adenda 3).
_NEW_CLAIM_HINTS_V13: dict[str, tuple[str, str]] = {
    "weak_hash": ("high", "security"),
    "tarfile_unsafe_extract": ("high", "security"),
    "hardcoded_password_argument": ("high", "security"),
    "jwt_verification_disabled": ("high", "security"),
    "debug_mode_enabled": ("medium", "security"),
}

_ALL_CLAIM_HINTS: dict[str, tuple[str, str]] = {
    **_CLAIM_HINTS,
    **_NEW_CLAIM_HINTS,
    **_NEW_CLAIM_HINTS_V13,
}


def _general_guidance(claim_types: tuple[str, ...]) -> str:
    return (
        "any defect you can prove from the cited lines; claim_type may "
        "be any of: " + ", ".join(claim_types) + ", or another precise name"
    )


def _resolve_gate(
    config: Mapping[str, str],
) -> tuple[tuple[str, ...], dict[str, str], str]:
    """Resolve the active gate's (claim types, guidance, version) from
    RB_CONFIG_GATE — the same key agent/main.py selects the gate with.
    Default "v1": the frozen gate's 8 classes, unchanged behaviour."""

    gate_version = (config.get("gate") or "v1").strip().lower()
    if gate_version == "v1":
        return KNOWN_CLAIM_TYPES, _CLASS_GUIDANCE, GATE_V1_VERSION
    if gate_version == "v11":
        return KNOWN_CLAIM_TYPES_V11, _CLASS_GUIDANCE_V11, GATE_V11_VERSION
    if gate_version == "v12":
        # Gate 1.2.0 (Adenda 2) verifies the SAME 14 classes as the
        # 1.1.0 with hardened checks, so the pass list and the
        # per-class guidance are the 1.1.0's; only the gate that will
        # judge the candidates — and the version stamped on the run —
        # changes.
        return KNOWN_CLAIM_TYPES_V12, _CLASS_GUIDANCE_V11, GATE_V12_VERSION
    if gate_version == "v13":
        # Gate 1.3.0 (Adenda 3) verifies the 1.2.0's 14 classes with
        # the same hardened checks plus the hunter's 5, and its
        # guidance adds the citation-discipline addendum (lever 1)
        # for the citation-shaped and block-antidote-shaped classes.
        return KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V13_VERSION
    raise RealLLMRefused(
        f"backend=llm v2 refused: unknown gate version {gate_version!r}; "
        "expected 'v1', 'v11', 'v12' or 'v13' (RB_CONFIG_GATE); "
        "no model call was made"
    )

_SYSTEM_PROMPT_TEMPLATE = (
    "You are a code reviewer examining ONE pull request. This pass looks "
    "for exactly one class of defect: {claim_type} — {guidance}. Report "
    "ONLY findings of this class. Respond with a single JSON object and "
    'nothing else, of the form {{"findings": [{{"file": "path/in/repo.py", '
    '"start_line": 12, "end_line": 12, "claim_type": "{claim_type}", '
    '"message": "what is wrong and why", "evidence": ["the exact text '
    'of line 12"]}}]}}. Lines refer to the file at the PR head, numbered '
    "exactly as shown. The evidence array must reproduce the cited lines "
    "EXACTLY as they appear in the file, one entry per line from "
    "start_line to end_line, without the line-number prefix. Cite the "
    "smallest line range that contains the evidence, and prefer lines "
    "that appear in the diff (added or context lines): the full files are "
    "context so you can judge the changed lines. If you find nothing of "
    'this class that you can prove, return {{"findings": []}}.'
)


@dataclass
class LLMRunInfoV2:
    """What the v2 run did, for the run log (never the key)."""

    model: str
    reviewer_version: str = REVIEWER_VERSION
    gate_version: str = GATE_V1_VERSION
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    estimated_cost_usd: float | None = None
    raw_findings: int = 0
    malformed_findings: int = 0
    unanchored_findings: int = 0
    calls: int = 0
    passes: list[str] = field(default_factory=list)
    context_token_budget: int = 0
    context_estimated_tokens: int = 0
    context_files_included: list[str] = field(default_factory=list)
    context_files_skipped_budget: list[str] = field(default_factory=list)
    context_files_missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "reviewer_version": self.reviewer_version,
            "gate_version": self.gate_version,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "raw_findings": self.raw_findings,
            "malformed_findings": self.malformed_findings,
            "unanchored_findings": self.unanchored_findings,
            "calls": self.calls,
            "passes": list(self.passes),
            "context_token_budget": self.context_token_budget,
            "context_estimated_tokens": self.context_estimated_tokens,
            "context_files_included": list(self.context_files_included),
            "context_files_skipped_budget": list(
                self.context_files_skipped_budget
            ),
            "context_files_missing": list(self.context_files_missing),
        }


def _resolve_context_budget(
    env: Mapping[str, str], config: Mapping[str, str]
) -> int:
    raw = (config.get("context_token_budget") or "").strip()
    source = "RB_CONFIG_CONTEXT_TOKEN_BUDGET"
    if not raw:
        raw = (env.get("RB_LLM_V2_CONTEXT_TOKEN_BUDGET") or "").strip()
        source = "RB_LLM_V2_CONTEXT_TOKEN_BUDGET"
    if not raw:
        return DEFAULT_CONTEXT_TOKEN_BUDGET
    try:
        budget = int(raw)
    except ValueError as exc:
        raise RealLLMRefused(
            f"backend=llm v2 refused: {source}={raw!r} is not an integer"
        ) from exc
    if budget <= 0:
        raise RealLLMRefused(
            f"backend=llm v2 refused: {source} must be positive"
        )
    return budget


def _load_head_files(
    repo_root: Path, paths: list[str]
) -> tuple[dict[str, list[str]], list[str]]:
    """Read the head contents of the touched files from the mounted repo.

    Returns ({path: [line, ...]}, [paths that could not be read]).  Paths
    that would escape the repo root are treated as missing: PR paths are
    untrusted input.
    """

    root = repo_root.resolve()
    files: dict[str, list[str]] = {}
    missing: list[str] = []
    for path in paths:
        candidate = (root / path).resolve()
        if candidate != root and root not in candidate.parents:
            missing.append(path)
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            missing.append(path)
            continue
        files[path] = text.splitlines()
    return files, missing


def _render_context(
    head_files: Mapping[str, list[str]],
    order: list[str],
    budget: int,
) -> tuple[str, int, list[str], list[str]]:
    """Render full head files into the prompt until the token budget ends.

    Whole files only, in diff order.  Returns (text, estimated_tokens,
    included_paths, skipped_paths).
    """

    sections: list[str] = []
    included: list[str] = []
    skipped: list[str] = []
    used = 0
    for path in order:
        lines = head_files.get(path)
        if lines is None:
            continue
        body = "\n".join(
            f"{number}: {text}" for number, text in enumerate(lines, start=1)
        )
        section = f"=== FILE {path} (full contents at PR head) ===\n{body}"
        estimate = _estimate_tokens(section)
        if used + estimate > budget:
            skipped.append(path)
            continue
        sections.append(section)
        included.append(path)
        used += estimate
    return "\n\n".join(sections), used, included, skipped


class LLMReviewerV2:
    """Multi-pass, full-context reviewer aligned with the frozen gate."""

    name = "alma-llm-reviewer-v2"

    def __init__(
        self,
        settings: LLMSettings,
        context_token_budget: int = DEFAULT_CONTEXT_TOKEN_BUDGET,
        repo_root: str | Path | None = None,
        transport: Transport | None = None,
        claim_types: tuple[str, ...] | None = None,
        class_guidance: Mapping[str, str] | None = None,
        gate_version: str = GATE_V1_VERSION,
    ) -> None:
        self.settings = settings
        self.context_token_budget = context_token_budget
        self.repo_root = Path(repo_root) if repo_root is not None else Path("/work/repo")
        self.transport = transport or _urllib_transport
        # The passes this reviewer makes: the ACTIVE gate's classes.
        # Defaults preserve the original behaviour (frozen gate, 8).
        self.claim_types = (
            tuple(claim_types) if claim_types is not None else KNOWN_CLAIM_TYPES
        )
        self.class_guidance = (
            dict(class_guidance)
            if class_guidance is not None
            else dict(_CLASS_GUIDANCE)
        )
        self.gate_version = gate_version
        self.last_run_info: LLMRunInfoV2 | None = None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str],
        config: Mapping[str, str],
        transport: Transport | None = None,
    ) -> "LLMReviewerV2":
        claim_types, class_guidance, gate_version = _resolve_gate(config)
        return cls(
            LLMSettings.from_env(env, config),
            context_token_budget=_resolve_context_budget(env, config),
            repo_root=(config.get("repo_root") or env.get("RB_REPO_ROOT") or "/work/repo"),
            transport=transport,
            claim_types=claim_types,
            class_guidance=class_guidance,
            gate_version=gate_version,
        )

    # -- prompt / payload ------------------------------------------------

    def build_payload(
        self, pass_name: str, diff_text: str, context_text: str
    ) -> dict[str, object]:
        # Same payload contract as v1 (see llm_reviewer.build_payload):
        # no "temperature", no "max_tokens" — OpenAI reasoning models
        # reject both with HTTP 400; the output cap is
        # "max_completion_tokens".
        if pass_name == GENERAL_PASS:
            guidance = _general_guidance(self.claim_types)
        else:
            guidance = self.class_guidance[pass_name]
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            claim_type=pass_name, guidance=guidance
        )
        user_content = (
            f"PASS: {pass_name}\n\n"
            "Review this pull request. First the diff, then the full "
            "contents of the touched files at the PR head.\n\n"
            f"=== DIFF ===\n{diff_text}\n\n{context_text}"
        )
        payload: dict[str, object] = {
            "model": self.settings.model,
            "max_completion_tokens": self.settings.max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        if self.settings.effort:
            payload["reasoning_effort"] = self.settings.effort
        return payload

    # -- one model call ---------------------------------------------------

    def _call_pass(self, payload: dict[str, object]) -> tuple[object, dict | None]:
        """Run one chat-completions call; return (content, usage-or-None)."""

        settings = self.settings
        status, body = self.transport(
            settings.chat_url(),
            settings.headers(),
            payload,
            settings.timeout_seconds,
        )
        if status != 200:
            # Same rule as v1: include a bounded excerpt of the error
            # body — the bare status cost an afternoon on 2026-10-19.
            excerpt = " ".join(body.decode("utf-8", errors="replace").split())[:400]
            detail = f" — body: {excerpt}" if excerpt else ""
            raise RealLLMRefused(
                f"model endpoint returned HTTP {status}; "
                f"failing closed without emitting findings{detail}"
            )
        try:
            response = json.loads(body.decode("utf-8"))
            content = response["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError) as exc:
            raise RealLLMRefused(
                "model response is not valid chat-completions JSON; "
                "failing closed without emitting findings"
            ) from exc
        usage = response.get("usage") if isinstance(response, dict) else None
        return content, usage if isinstance(usage, dict) else None

    # -- the review --------------------------------------------------------

    def review(
        self,
        *,
        diff_text: str,
        diff: DiffIndex,
        config: Mapping[str, str],
        mode: str = "alma",
        repo_root: str | Path | None = None,
    ) -> list[Candidate]:
        settings = self.settings
        root = Path(repo_root) if repo_root is not None else self.repo_root
        if not root.is_dir():
            raise RealLLMRefused(
                f"backend=llm v2 refused: repo root {root} is not a "
                "directory; the v2 reviewer requires the mounted head "
                "checkout (RB_REPO_ROOT); no model call was made"
            )

        order = list(diff.files.keys())
        head_files, missing = _load_head_files(root, order)
        context_text, context_tokens, included, skipped = _render_context(
            head_files, order, self.context_token_budget
        )

        passes = list(self.claim_types)
        if mode == "base":
            # The pre-registration allows the free-form pass only in the
            # base arm; in the ALMA arm every candidate must be born
            # inside a verifiable class.
            passes.append(GENERAL_PASS)

        info = LLMRunInfoV2(
            model=settings.model,
            gate_version=self.gate_version,
            passes=passes,
            context_token_budget=self.context_token_budget,
            context_estimated_tokens=context_tokens,
            context_files_included=included,
            context_files_skipped_budget=skipped,
            context_files_missing=missing,
        )
        self.last_run_info = info

        payloads = {
            name: self.build_payload(name, diff_text, context_text)
            for name in passes
        }

        # Pre-flight spend guard over ALL passes: refuse BEFORE spending.
        worst_case = 0.0
        for payload in payloads.values():
            messages = payload["messages"]
            estimated_input = sum(
                _estimate_tokens(str(message["content"])) for message in messages
            )
            worst_case += settings.cost_usd(
                estimated_input, settings.max_output_tokens
            )
        if worst_case > settings.max_spend_usd:
            raise RealLLMRefused(
                "backend=llm v2 refused before calling: worst-case "
                f"estimate US${worst_case:.4f} over {len(passes)} passes "
                f"exceeds RB_MAX_SPEND_USD=US${settings.max_spend_usd:.4f}; "
                "no model call was made"
            )

        total_prompt = 0
        total_completion = 0
        total_cost = 0.0
        candidates: list[Candidate] = []
        seen: set[tuple[str, int, int, str, str]] = set()

        for pass_name in passes:
            payload = payloads[pass_name]
            content, usage = self._call_pass(payload)
            info.calls += 1

            if usage is not None and usage.get("prompt_tokens") is not None:
                prompt_tokens = int(usage["prompt_tokens"])
                completion_tokens = int(usage.get("completion_tokens") or 0)
            else:
                prompt_tokens = sum(
                    _estimate_tokens(str(m["content"]))
                    for m in payload["messages"]
                )
                completion_tokens = _estimate_tokens(str(content))
            total_prompt += prompt_tokens
            total_completion += completion_tokens
            total_cost += settings.cost_usd(prompt_tokens, completion_tokens)
            info.prompt_tokens = total_prompt
            info.completion_tokens = total_completion
            info.estimated_cost_usd = total_cost
            if total_cost > settings.max_spend_usd:
                raise RealLLMRefused(
                    "cumulative reported cost US$"
                    f"{total_cost:.4f} exceeds RB_MAX_SPEND_USD="
                    f"US${settings.max_spend_usd:.4f}; failing closed "
                    "without emitting findings"
                )

            raw_findings = _extract_findings(content)
            info.raw_findings += len(raw_findings)
            for raw in raw_findings:
                candidate = self._to_candidate_v2(
                    raw, pass_name, head_files, info
                )
                if candidate is None:
                    continue
                key = (
                    candidate.file,
                    candidate.start_line,
                    candidate.end_line,
                    candidate.claim_type,
                    candidate.message.strip().lower(),
                )
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(candidate)
        return candidates

    # -- candidate conversion + anchoring ----------------------------------

    def _to_candidate_v2(
        self,
        raw: object,
        pass_name: str,
        head_files: Mapping[str, list[str]],
        info: LLMRunInfoV2,
    ) -> Candidate | None:
        """Convert one raw finding, verifying its anchor against the head file.

        Malformed shapes and wrong-class returns in a class pass are
        counted as malformed; findings whose cited lines do not exist in
        the head file or whose quoted evidence does not match it exactly
        are counted as unanchored.  Both are dropped here, in the
        reviewer, before the frozen gate ever sees them.
        """

        if not isinstance(raw, dict):
            info.malformed_findings += 1
            return None
        file = raw.get("file")
        start = raw.get("start_line")
        end = raw.get("end_line", start)
        claim_type = raw.get("claim_type")
        message = raw.get("message")
        evidence = raw.get("evidence")
        if not isinstance(file, str) or not file.strip():
            info.malformed_findings += 1
            return None
        if not isinstance(start, int) or isinstance(start, bool):
            info.malformed_findings += 1
            return None
        if not isinstance(end, int) or isinstance(end, bool):
            info.malformed_findings += 1
            return None
        if not isinstance(claim_type, str) or not claim_type.strip():
            info.malformed_findings += 1
            return None
        if not isinstance(message, str) or not message.strip():
            info.malformed_findings += 1
            return None
        if start < 1 or end < start or end - start > 500:
            info.malformed_findings += 1
            return None
        claim_type = claim_type.strip()
        if pass_name != GENERAL_PASS and claim_type != pass_name:
            # A class pass produces candidates of its class or none:
            # in the ALMA arm this is the pre-registered discipline,
            # and the base arm's class passes follow the same rule
            # (its free-form findings come from the general pass).
            info.malformed_findings += 1
            return None

        file = file.strip().removeprefix("./")
        lines = head_files.get(file)
        if lines is None or end > len(lines):
            info.unanchored_findings += 1
            return None
        actual = tuple(lines[start - 1 : end])
        if (
            not isinstance(evidence, list)
            or len(evidence) != end - start + 1
            or any(not isinstance(item, str) for item in evidence)
            or tuple(evidence) != actual
        ):
            info.unanchored_findings += 1
            return None

        severity_hint, category_hint = _ALL_CLAIM_HINTS.get(
            claim_type, ("high", "correctness")
        )
        rule_prefix = (
            "llm_v2_general" if pass_name == GENERAL_PASS else "llm_v2"
        )
        return Candidate(
            rule_id=f"{rule_prefix}_{claim_type}",
            claim_type=claim_type,
            file=file,
            start_line=start,
            end_line=end,
            message=message.strip(),
            evidence_text=actual,
            severity_hint=severity_hint,
            category_hint=category_hint,
            producer="alma-llm-reviewer-v2",
        )


__all__ = [
    "DEFAULT_CONTEXT_TOKEN_BUDGET",
    "GENERAL_PASS",
    "LLMReviewerV2",
    "LLMRunInfoV2",
    "REVIEWER_VERSION",
]
