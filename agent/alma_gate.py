from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re

from .base_reviewer import Candidate
from .diff_parser import DiffIndex


POLICY_VERSION = "alma-evidence-gate/1.0.0"
_POLICY = {
    "version": POLICY_VERSION,
    "required_checks": [
        "candidate file and every cited line are present in the diff",
        "stored evidence text exactly equals the text at the cited head lines",
        "the cited evidence contains claim-specific support",
        "unknown claim types fail closed",
        "accepted findings are deduplicated by file, range, and message",
    ],
    "claims": {
        "command_execution": "shell or dynamic code execution marker",
        "hardcoded_secret": "credential assignment to a non-placeholder literal",
        "mutable_default": "function argument defaulted to a mutable object",
        "race_condition": "concurrency marker plus shared-state marker",
        "silenced_bare_except": "bare except and a pass handler",
        "sql_injection": "SQL text plus interpolation, formatting, or concatenation",
        "tls_verification_disabled": "verify=False",
        "unsafe_deserialization": "unsafe pickle or YAML load marker",
    },
}
POLICY_SHA256 = hashlib.sha256(
    json.dumps(_POLICY, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

# Claim types the gate can verify.  Derived from the frozen policy above, so
# this constant does not change POLICY_SHA256.  Candidate producers (the
# deterministic reviewer, a future LLM adapter) must use these values: any
# other claim type fails closed in the gate.
KNOWN_CLAIM_TYPES = tuple(sorted(_POLICY["claims"].keys()))

_SQL_RE = re.compile(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", re.I)
_UNSAFE_SQL_RE = re.compile(
    r"(?:\bf[\"']|\bf'''|\.format\s*\(|%\s*\(|[\"']\s*\+|\+\s*[A-Za-z_][\w.\[\]]*)",
    re.I,
)
_SECRET_LITERAL_RE = re.compile(
    r"^\s*[A-Za-z_][\w.]*\s*=\s*([\"'])(?P<value>[^\"']{6,})\1\s*(?:#.*)?$"
)
_PLACEHOLDER_VALUES = {"changeme", "example", "password", "redacted", "xxxxxxxx", "********"}


@dataclass
class LedgerEntry:
    rule_id: str
    claim_type: str
    file: str
    start_line: int
    end_line: int
    message: str
    severity_hint: str
    category_hint: str
    evidence: list[dict[str, object]]
    status: str
    reasons: list[str] = field(default_factory=list)
    validator_version: str = POLICY_VERSION
    policy_sha256: str = POLICY_SHA256

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class GateResult:
    findings: list[dict[str, object]]
    ledger: list[LedgerEntry]


def candidate_to_finding(candidate: Candidate, agent_name: str) -> dict[str, object]:
    """Convert an internal candidate to the exact ReviewBench finding schema."""

    return {
        "file": candidate.file,
        "start_line": candidate.start_line,
        "end_line": candidate.end_line,
        "message": candidate.message,
        "producer": agent_name,
    }


def _claim_support(claim_type: str, evidence_text: str) -> tuple[bool, str]:
    text = evidence_text
    stripped_lines = [line.strip() for line in text.splitlines()]

    if claim_type == "sql_injection":
        supported = bool(_SQL_RE.search(text) and _UNSAFE_SQL_RE.search(text))
        return supported, "SQL text and an unsafe construction marker are required"

    if claim_type == "hardcoded_secret":
        match = _SECRET_LITERAL_RE.search(text)
        if not match:
            return False, "a credential assignment to a quoted literal is required"
        value = match.group("value").strip().lower()
        if value in _PLACEHOLDER_VALUES or value.startswith("${") or value.startswith("os."):
            return False, "placeholder and environment-derived values are not hardcoded secrets"
        return True, "credential is assigned to a non-placeholder literal"

    if claim_type == "tls_verification_disabled":
        supported = bool(re.search(r"\bverify\s*=\s*False\b", text))
        return supported, "verify=False is required"

    if claim_type == "silenced_bare_except":
        supported = "except:" in stripped_lines and "pass" in stripped_lines
        return supported, "a bare except and a pass handler are both required"

    if claim_type == "mutable_default":
        supported = bool(re.search(r"\bdef\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\(\))", text))
        return supported, "a mutable function default is required"

    if claim_type == "command_execution":
        supported = bool(
            "os.system(" in text
            or re.search(r"\b(?:eval|exec)\s*\(", text)
            or "shell=True" in text
        )
        return supported, "a shell or dynamic execution marker is required"

    if claim_type == "unsafe_deserialization":
        supported = "pickle.loads(" in text or (
            "yaml.load(" in text and "SafeLoader" not in text
        )
        return supported, "an unsafe deserialization call is required"

    if claim_type == "race_condition":
        concurrency = bool(
            re.search(r"\b(threading|multiprocessing|concurrent|async|await|Lock\s*\()", text)
        )
        shared_state = bool(re.search(r"\b(global|shared|cache|self\.)\b", text, re.I))
        return concurrency and shared_state, (
            "both concurrency and shared-state evidence are required"
        )

    return False, f"unknown claim type {claim_type!r}; failing closed"


class AlmaGate:
    """Frozen evidence validator for candidate review findings.

    The gate is intentionally independent of the base reviewer's heuristics:
    a rule name or confident message is not evidence.  A candidate passes
    only when its cited lines exist in the diff, its stored evidence matches
    those lines byte-for-byte at the text-line level, and the evidence itself
    supports the specific claim.
    """

    version = POLICY_VERSION
    policy_sha256 = POLICY_SHA256

    def validate(
        self,
        candidates: list[Candidate],
        diff: DiffIndex,
        agent_name: str,
    ) -> GateResult:
        findings: list[dict[str, object]] = []
        ledger: list[LedgerEntry] = []
        accepted_keys: set[tuple[str, int, int, str]] = set()

        for candidate in candidates:
            reasons: list[str] = []
            evidence: list[dict[str, object]] = []
            actual_text: list[str] = []

            if candidate.start_line < 1 or candidate.end_line < candidate.start_line:
                reasons.append("invalid line range")

            for line_number in range(candidate.start_line, candidate.end_line + 1):
                diff_line = diff.get_line(candidate.file, line_number)
                if diff_line is None:
                    reasons.append(
                        f"cited line {candidate.file}:{line_number} is not present in the diff"
                    )
                    continue
                actual_text.append(diff_line.text)
                evidence.append(
                    {
                        "file": diff_line.file,
                        "line": diff_line.line_number,
                        "kind": diff_line.kind,
                        "text": diff_line.text,
                    }
                )

            if tuple(actual_text) != candidate.evidence_text:
                reasons.append("stored evidence text does not exactly match the cited diff lines")

            if not reasons:
                supported, support_reason = _claim_support(
                    candidate.claim_type, "\n".join(actual_text)
                )
                if not supported:
                    reasons.append(f"claim-specific evidence check failed: {support_reason}")
                else:
                    reasons.append(f"claim-specific evidence check passed: {support_reason}")

            is_duplicate = False
            if not any("evidence check failed" in reason or "not present" in reason or "does not exactly" in reason for reason in reasons):
                key = (
                    candidate.file,
                    candidate.start_line,
                    candidate.end_line,
                    candidate.message.strip().lower(),
                )
                if key in accepted_keys:
                    is_duplicate = True
                    reasons.append("duplicate of an already accepted finding")
                else:
                    accepted_keys.add(key)

            rejected = bool(
                is_duplicate
                or any(
                    marker in reason
                    for reason in reasons
                    for marker in (
                        "invalid line range",
                        "not present in the diff",
                        "does not exactly match",
                        "evidence check failed",
                    )
                )
            )
            status = "rejected" if rejected else "accepted"
            if status == "accepted":
                findings.append(candidate_to_finding(candidate, agent_name))

            ledger.append(
                LedgerEntry(
                    rule_id=candidate.rule_id,
                    claim_type=candidate.claim_type,
                    file=candidate.file,
                    start_line=candidate.start_line,
                    end_line=candidate.end_line,
                    message=candidate.message,
                    severity_hint=candidate.severity_hint,
                    category_hint=candidate.category_hint,
                    evidence=evidence,
                    status=status,
                    reasons=reasons,
                )
            )

        return GateResult(findings=findings, ledger=ledger)
