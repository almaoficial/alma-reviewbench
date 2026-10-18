"""Real LLM backend for the ReviewBench adapter — disabled by default.

Safety contract (fail-closed, in the ALMA spirit):

- This module is only reachable when the run configuration selects
  ``backend=llm``.  The package default stays ``backend=mock`` (US$0,
  deterministic, no network).
- Even with ``backend=llm``, the reviewer refuses to make any call unless
  ALL of these are present in the environment:
    * ``ALLOW_REAL_LLM=1`` — the explicit human arming flag;
    * an API key in the env var named by ``LLM_API_KEY_ENV``
      (default ``OPENAI_API_KEY``);
    * ``RB_MAX_SPEND_USD`` — a positive spend cap for this single PR run;
    * ``RB_MODEL_BASE_URL`` — the model endpoint registered in ReviewBench;
    * a model name in the run configuration (``RB_CONFIG_MODEL``).
- The spend cap is enforced BEFORE the call with a conservative estimate
  (input tokens estimated from characters, output bounded by
  ``RB_LLM_MAX_OUTPUT_TOKENS``) and checked again after the call against the
  usage the API reports.  Prices come from ``RB_PRICE_INPUT_PER_MTOK_USD`` /
  ``RB_PRICE_OUTPUT_PER_MTOK_USD`` and default to the frontier planning band
  of the pre-registration (US$15/M in, US$75/M out) so the estimate errs on
  the expensive side.
- The model is asked for findings ONLY, as JSON.  Whatever it returns is
  converted into ordinary candidates whose evidence text is filled from the
  real diff (never from the model's words) and then passes through the exact
  same frozen ALMA evidence gate as the mock reviewer: hallucinated lines,
  unknown claim types and unsupported claims are rejected there.

The provider protocol is the OpenAI-compatible Chat Completions shape
(``POST {RB_MODEL_BASE_URL}/chat/completions``), which is what the portal's
OpenAI / Azure OpenAI presets speak.  Set ``RB_LLM_AUTH_STYLE=api-key`` for
endpoints that expect an ``api-key`` header instead of a Bearer token.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from typing import Callable, Mapping
import urllib.error
import urllib.request

from .alma_gate import KNOWN_CLAIM_TYPES
from .base_reviewer import Candidate
from .diff_parser import DiffIndex


class RealLLMRefused(RuntimeError):
    """Raised instead of calling a real model without full authorization."""


# (severity_hint, category_hint) per claim type the gate knows how to verify.
_CLAIM_HINTS: dict[str, tuple[str, str]] = {
    "command_execution": ("high", "security"),
    "hardcoded_secret": ("high", "security"),
    "mutable_default": ("medium", "correctness"),
    "race_condition": ("medium", "reliability"),
    "silenced_bare_except": ("medium", "reliability"),
    "sql_injection": ("high", "security"),
    "tls_verification_disabled": ("high", "security"),
    "unsafe_deserialization": ("high", "security"),
}

_SYSTEM_PROMPT = (
    "You are a code reviewer. You review ONE pull request diff and report "
    "only defects you can prove from the diff itself. Respond with a single "
    "JSON object and nothing else, of the form "
    '{"findings": [{"file": "path/in/repo.py", "start_line": 12, '
    '"end_line": 12, "claim_type": "sql_injection", "message": "what is '
    'wrong and why"}]}. Lines refer to the file at the PR head, exactly as '
    "numbered in the diff context. claim_type must be one of: "
    + ", ".join(KNOWN_CLAIM_TYPES)
    + ". Cite the smallest line range that contains the evidence. If a line "
    "is not visible in the diff, do not cite it. If you find nothing you can "
    'prove from the diff, return {"findings": []}.'
)

# Transport signature: (url, headers, payload, timeout_seconds)
#   -> (http_status, response_body_bytes)
Transport = Callable[[str, dict[str, str], dict[str, object], float], tuple[int, bytes]]


def _urllib_transport(
    url: str, headers: dict[str, str], payload: dict[str, object], timeout: float
) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _estimate_tokens(text: str) -> int:
    """Conservative character-based token estimate (overestimates on code)."""

    return max(1, math.ceil(len(text) / 3.5))


def _env_float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise RealLLMRefused(f"{name}={raw!r} is not a number") from exc


def _env_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RealLLMRefused(f"{name}={raw!r} is not an integer") from exc


@dataclass(frozen=True)
class LLMSettings:
    base_url: str
    model: str
    effort: str | None
    api_key: str
    key_env_name: str
    max_spend_usd: float
    price_input_per_mtok: float
    price_output_per_mtok: float
    max_output_tokens: int
    timeout_seconds: float
    auth_style: str  # "bearer" or "api-key"

    # Never print or log the key itself.
    def redacted(self) -> dict[str, object]:
        return {
            "base_url": self.base_url,
            "model": self.model,
            "effort": self.effort,
            "key_env_name": self.key_env_name,
            "key_present": bool(self.api_key),
            "max_spend_usd": self.max_spend_usd,
            "price_input_per_mtok": self.price_input_per_mtok,
            "price_output_per_mtok": self.price_output_per_mtok,
            "max_output_tokens": self.max_output_tokens,
            "timeout_seconds": self.timeout_seconds,
            "auth_style": self.auth_style,
        }

    @classmethod
    def from_env(
        cls, env: Mapping[str, str], config: Mapping[str, str]
    ) -> "LLMSettings":
        if env.get("ALLOW_REAL_LLM") != "1":
            raise RealLLMRefused(
                "backend=llm refused: ALLOW_REAL_LLM is not '1'; "
                "no model call was made"
            )
        base_url = (env.get("RB_MODEL_BASE_URL") or "").strip()
        if not base_url:
            raise RealLLMRefused(
                "backend=llm refused: RB_MODEL_BASE_URL is missing; "
                "no model call was made"
            )
        model = (config.get("model") or "").strip()
        if not model:
            raise RealLLMRefused(
                "backend=llm refused: no model in the run configuration "
                "(RB_CONFIG_MODEL); no model call was made"
            )
        key_env_name = (env.get("LLM_API_KEY_ENV") or "OPENAI_API_KEY").strip()
        api_key = (env.get(key_env_name) or "").strip()
        if not api_key:
            raise RealLLMRefused(
                f"backend=llm refused: API key env var {key_env_name} is "
                "missing or empty; no model call was made"
            )
        raw_cap = (env.get("RB_MAX_SPEND_USD") or "").strip()
        if not raw_cap:
            raise RealLLMRefused(
                "backend=llm refused: RB_MAX_SPEND_USD is missing; "
                "a named spend cap is required before any paid call"
            )
        try:
            max_spend = float(raw_cap)
        except ValueError as exc:
            raise RealLLMRefused(
                f"backend=llm refused: RB_MAX_SPEND_USD={raw_cap!r} is not a number"
            ) from exc
        if max_spend <= 0:
            raise RealLLMRefused(
                "backend=llm refused: RB_MAX_SPEND_USD must be positive"
            )
        auth_style = (env.get("RB_LLM_AUTH_STYLE") or "bearer").strip().lower()
        if auth_style not in {"bearer", "api-key"}:
            raise RealLLMRefused(
                f"backend=llm refused: RB_LLM_AUTH_STYLE={auth_style!r} "
                "is not 'bearer' or 'api-key'"
            )
        effort = (config.get("effort") or "").strip() or None
        return cls(
            base_url=base_url.rstrip("/"),
            model=model,
            effort=effort,
            api_key=api_key,
            key_env_name=key_env_name,
            max_spend_usd=max_spend,
            price_input_per_mtok=_env_float(env, "RB_PRICE_INPUT_PER_MTOK_USD", 15.0),
            price_output_per_mtok=_env_float(env, "RB_PRICE_OUTPUT_PER_MTOK_USD", 75.0),
            max_output_tokens=_env_int(env, "RB_LLM_MAX_OUTPUT_TOKENS", 4096),
            timeout_seconds=float(_env_int(env, "RB_LLM_TIMEOUT_SECONDS", 600)),
            auth_style=auth_style,
        )

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens / 1_000_000 * self.price_input_per_mtok
            + output_tokens / 1_000_000 * self.price_output_per_mtok
        )

    def chat_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def headers(self) -> dict[str, str]:
        if self.auth_style == "api-key":
            return {"api-key": self.api_key}
        return {"Authorization": f"Bearer {self.api_key}"}


@dataclass
class LLMRunInfo:
    """What the last real call did, for the run log (never the key)."""

    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    estimated_cost_usd: float | None = None
    raw_findings: int = 0
    malformed_findings: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "raw_findings": self.raw_findings,
            "malformed_findings": self.malformed_findings,
        }


class LLMReviewer:
    """Model-backed reviewer whose output still has to pass the ALMA gate."""

    name = "alma-llm-reviewer"

    def __init__(
        self,
        settings: LLMSettings,
        transport: Transport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport or _urllib_transport
        self.last_run_info: LLMRunInfo | None = None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str],
        config: Mapping[str, str],
        transport: Transport | None = None,
    ) -> "LLMReviewer":
        return cls(LLMSettings.from_env(env, config), transport=transport)

    def build_payload(self, diff_text: str) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": self.settings.model,
            "temperature": 0,
            "max_tokens": self.settings.max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Review this pull request diff. Lines are numbered "
                        "at the PR head as shown.\n\n" + diff_text
                    ),
                },
            ],
        }
        if self.settings.effort:
            payload["reasoning_effort"] = self.settings.effort
        return payload

    def review(
        self,
        *,
        diff_text: str,
        diff: DiffIndex,
        config: Mapping[str, str],
    ) -> list[Candidate]:
        settings = self.settings
        payload = self.build_payload(diff_text)

        # Pre-flight spend guard: refuse BEFORE spending anything.
        estimated_input = _estimate_tokens(_SYSTEM_PROMPT) + _estimate_tokens(diff_text)
        worst_case = settings.cost_usd(estimated_input, settings.max_output_tokens)
        if worst_case > settings.max_spend_usd:
            raise RealLLMRefused(
                "backend=llm refused before calling: worst-case estimate "
                f"US${worst_case:.4f} exceeds RB_MAX_SPEND_USD="
                f"US${settings.max_spend_usd:.4f}; no model call was made"
            )

        status, body = self.transport(
            settings.chat_url(),
            settings.headers(),
            payload,
            settings.timeout_seconds,
        )
        if status != 200:
            raise RealLLMRefused(
                f"model endpoint returned HTTP {status}; "
                "failing closed without emitting findings"
            )
        try:
            response = json.loads(body.decode("utf-8"))
            content = response["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError) as exc:
            raise RealLLMRefused(
                "model response is not valid chat-completions JSON; "
                "failing closed without emitting findings"
            ) from exc

        info = LLMRunInfo(model=settings.model)
        usage = response.get("usage") if isinstance(response, dict) else None
        if isinstance(usage, dict):
            info.prompt_tokens = usage.get("prompt_tokens")
            info.completion_tokens = usage.get("completion_tokens")
            if info.prompt_tokens is not None and info.completion_tokens is not None:
                info.estimated_cost_usd = settings.cost_usd(
                    int(info.prompt_tokens), int(info.completion_tokens)
                )
                if info.estimated_cost_usd > settings.max_spend_usd:
                    self.last_run_info = info
                    raise RealLLMRefused(
                        "reported usage cost US$"
                        f"{info.estimated_cost_usd:.4f} exceeds "
                        f"RB_MAX_SPEND_USD=US${settings.max_spend_usd:.4f}; "
                        "failing closed without emitting findings"
                    )
        self.last_run_info = info

        raw_findings = _extract_findings(content)
        info.raw_findings = len(raw_findings)
        candidates: list[Candidate] = []
        for index, raw in enumerate(raw_findings):
            candidate = _to_candidate(raw, index, diff)
            if candidate is None:
                info.malformed_findings += 1
                continue
            candidates.append(candidate)
        return candidates


def _extract_findings(content: object) -> list[object]:
    """Pull the findings array out of the model's content, strictly."""

    if not isinstance(content, str):
        raise RealLLMRefused("model content is not text; failing closed")
    text = content.strip()
    if text.startswith("```"):
        # Tolerate a fenced block despite the JSON-only instruction.
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
    except ValueError as exc:
        raise RealLLMRefused(
            "model did not return parseable JSON findings; failing closed"
        ) from exc
    if isinstance(parsed, dict):
        findings = parsed.get("findings")
    elif isinstance(parsed, list):
        findings = parsed
    else:
        findings = None
    if not isinstance(findings, list):
        raise RealLLMRefused("model JSON has no findings list; failing closed")
    return findings


def _to_candidate(raw: object, index: int, diff: DiffIndex) -> Candidate | None:
    """Convert one raw model finding into a gate-ready candidate.

    Evidence text is filled from the REAL diff index, never from the model's
    words: lines the model cites that are not in the diff simply produce a
    shorter (or empty) evidence tuple, and the frozen gate then rejects the
    candidate for the missing/mismatched evidence exactly as it does for
    the deterministic reviewer's over-broad heuristics.
    """

    if not isinstance(raw, dict):
        return None
    file = raw.get("file")
    start = raw.get("start_line")
    end = raw.get("end_line", start)
    claim_type = raw.get("claim_type")
    message = raw.get("message")
    if not isinstance(file, str) or not file.strip():
        return None
    if not isinstance(start, int) or isinstance(start, bool):
        return None
    if not isinstance(end, int) or isinstance(end, bool):
        return None
    if not isinstance(claim_type, str) or not claim_type.strip():
        return None
    if not isinstance(message, str) or not message.strip():
        return None
    file = file.strip().removeprefix("./")
    if start < 1 or end < start or end - start > 500:
        return None
    evidence: list[str] = []
    for line_number in range(start, end + 1):
        diff_line = diff.get_line(file, line_number)
        if diff_line is not None:
            evidence.append(diff_line.text)
    severity_hint, category_hint = _CLAIM_HINTS.get(
        claim_type.strip(), ("high", "correctness")
    )
    return Candidate(
        rule_id=f"llm_{claim_type.strip()}",
        claim_type=claim_type.strip(),
        file=file,
        start_line=start,
        end_line=end,
        message=message.strip(),
        evidence_text=tuple(evidence),
        severity_hint=severity_hint,
        category_hint=category_hint,
        producer="alma-llm-reviewer",
    )


__all__ = [
    "KNOWN_CLAIM_TYPES",
    "LLMReviewer",
    "LLMRunInfo",
    "LLMSettings",
    "RealLLMRefused",
    "Transport",
]
