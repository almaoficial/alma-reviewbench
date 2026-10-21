"""Evidence gate 1.1.0 — extends the frozen 1.0.0, never replaces it.

Provenance: PREREGISTRO-REVIEWBENCH-V2.md, Adenda 1 (2026-10-19, 22:05
EDT, written BEFORE any v2 run).  The v1 experiment's gate
(``agent/alma_gate.py``, ``alma-evidence-gate/1.0.0``) stays frozen
forever; this module is a NEW gate that inherits the 1.0.0's 8 claim
classes with their rules byte-identical (the support check for those
classes delegates to the frozen module's own function, so the rules
cannot drift) and adds 6 classes whose evidence is mechanically
verifiable on the cited lines — the gate's doctrine is unchanged: no
class that requires an opinion.

Added classes (Adenda 1), each with the evidence rule as written there:

- ``resource_leak``: an opener (``open(``, a connection ``connect(``, a
  ``socket`` call) in the cited lines, with no ``with`` manager and no
  ``.close(`` inside the cited range.
- ``swallowed_exception``: a *typed* ``except`` handler whose cited
  body is only ``pass`` (1.0.0 covered the bare ``except:``).
- ``unsafe_xml_parsing``: standard-library XML parsing (``ET.parse`` /
  ``fromstring``, ``xml.dom``, ``xml.sax``) with no ``defusedxml``
  anywhere in the cited evidence.
- ``insecure_tempfile``: ``tempfile.mktemp(`` — insecure by design.
- ``ssl_context_unverified``: ``ssl._create_unverified_context`` or
  ``CERT_NONE`` in the evidence (sibling of the 1.0.0's
  ``tls_verification_disabled``, different evidence).
- ``weak_random_security``: a value assigned to a security name (token,
  secret, password, otp, session, api_key) generated with the
  ``random`` module instead of ``secrets``.

Resolutions where the addendum's prose needed a mechanical reading
(recorded here, in the open, without changing any rule):

- resource_leak openers are the marker set ``open(`` / ``connect(`` /
  ``socket(`` / ``create_connection(`` and the ``with`` exclusion keys
  on a cited line that OPENS a ``with``/``async with`` statement.
- weak_random_security is a same-line rule: the assignment to the
  security name and the ``random.`` call must appear on the same cited
  line (the addendum's wording: a value assigned to a security name
  "generated with the random module").  A value computed on an earlier
  line and merely assigned by name is not mechanically provable from
  the citation and fails closed.
- swallowed_exception requires the handler body lines to be cited:
  an ``except`` line alone, with no cited ``pass`` under it, is not
  evidence of swallowing.

Selection: run configuration ``RB_CONFIG_GATE=v11`` (default ``v1``);
see ``agent/main.py``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re

from .alma_gate import (
    KNOWN_CLAIM_TYPES as _INHERITED_CLAIM_TYPES,
    _claim_support as _claim_support_v10,
    candidate_to_finding,
)
from .base_reviewer import Candidate
from .diff_parser import DiffIndex


POLICY_VERSION = "alma-evidence-gate/1.1.0"
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
        # The 8 classes inherited from alma-evidence-gate/1.0.0, with
        # their descriptions and rules unchanged.
        "command_execution": "shell or dynamic code execution marker",
        "hardcoded_secret": "credential assignment to a non-placeholder literal",
        "mutable_default": "function argument defaulted to a mutable object",
        "race_condition": "concurrency marker plus shared-state marker",
        "silenced_bare_except": "bare except and a pass handler",
        "sql_injection": "SQL text plus interpolation, formatting, or concatenation",
        "tls_verification_disabled": "verify=False",
        "unsafe_deserialization": "unsafe pickle or YAML load marker",
        # The 6 classes added by Adenda 1 of the v2 pre-registration.
        "insecure_tempfile": "tempfile.mktemp( call",
        "resource_leak": (
            "resource opened (open(, connection, socket) without with "
            "or .close( in the cited lines"
        ),
        "ssl_context_unverified": "ssl._create_unverified_context or CERT_NONE",
        "swallowed_exception": "typed except handler whose body is only pass",
        "unsafe_xml_parsing": (
            "standard-library XML parsing (ET.parse/fromstring, xml.dom, "
            "xml.sax) without defusedxml"
        ),
        "weak_random_security": (
            "security-named value (token, secret, password, otp, session, "
            "api_key) generated with the random module"
        ),
    },
}
POLICY_SHA256 = hashlib.sha256(
    json.dumps(_POLICY, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

INHERITED_CLAIM_TYPES = tuple(_INHERITED_CLAIM_TYPES)
NEW_CLAIM_TYPES = (
    "insecure_tempfile",
    "resource_leak",
    "ssl_context_unverified",
    "swallowed_exception",
    "unsafe_xml_parsing",
    "weak_random_security",
)
KNOWN_CLAIM_TYPES_V11 = tuple(sorted(_POLICY["claims"].keys()))

_RESOURCE_OPEN_RE = re.compile(
    r"(?:\bopen|\bconnect|\bsocket|create_connection)\s*\("
)
_EXCEPT_TYPED_RE = re.compile(r"^except\s+[^:\s][^:]*:\s*(?:#.*)?$")
_XML_STDLIB_RE = re.compile(
    r"(?:\b(?:ET|ElementTree|minidom|sax)\s*\.\s*(?:parse|fromstring|parseString)"
    r"|(?<![\w.])fromstring"
    r"|(?<![\w.])parseString)\s*\("
)
_MKTEMP_RE = re.compile(r"\bmktemp\s*\(")
_SECURITY_NAME_RE = re.compile(
    r"(token|secret|password|passwd|otp|session|api[_-]?key)", re.I
)
_RANDOM_CALL_RE = re.compile(r"\brandom\s*\.")
_ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*=(?!=)\s*(.+)$")


@dataclass
class LedgerEntryV11:
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
class GateResultV11:
    findings: list[dict[str, object]]
    ledger: list[LedgerEntryV11]


def _resource_leak_support(text: str, stripped_lines: list[str]) -> tuple[bool, str]:
    if not _RESOURCE_OPEN_RE.search(text):
        return False, "an opened resource (open(, connection, socket) is required"
    if ".close(" in text:
        return False, "the resource is closed (.close() present in the cited lines)"
    if any(
        line.startswith("with ") or line.startswith("async with ")
        for line in stripped_lines
    ):
        return False, "the resource is opened under a with statement in the cited lines"
    return True, "resource opened without with or .close() in the cited lines"


def _swallowed_exception_support(stripped_lines: list[str]) -> tuple[bool, str]:
    nonempty = [line for line in stripped_lines if line]
    for index, line in enumerate(nonempty):
        if _EXCEPT_TYPED_RE.match(line):
            body = nonempty[index + 1 :]
            if body and all(item == "pass" for item in body):
                return True, "typed except handler whose body is only pass"
            return False, (
                "the typed except handler's cited body is not only pass "
                "(it handles the error, or the body is not cited)"
            )
    return False, "a typed except handler (except SomeError:) is required"


def _unsafe_xml_support(text: str) -> tuple[bool, str]:
    if not _XML_STDLIB_RE.search(text):
        return False, (
            "standard-library XML parsing (ET.parse/fromstring, xml.dom, "
            "xml.sax) is required"
        )
    if "defusedxml" in text:
        return False, "defusedxml is present in the cited evidence"
    return True, "standard-library XML parsing without defusedxml"


def _weak_random_support(text: str) -> tuple[bool, str]:
    for line in text.splitlines():
        match = _ASSIGNMENT_RE.match(line)
        if not match:
            continue
        name, value = match.group(1), match.group(2)
        if _SECURITY_NAME_RE.search(name) and _RANDOM_CALL_RE.search(value):
            return True, (
                "a security-named value is generated with the random module"
            )
    return False, (
        "assignment of a random-module value to a security name "
        "(token, secret, password, otp, session, api_key) is required"
    )


def _claim_support_v11(claim_type: str, evidence_text: str) -> tuple[bool, str]:
    """Support check for the 1.1.0: inherited classes delegate to the
    frozen 1.0.0 function (identical rules, by construction); the 6 new
    classes apply the mechanical rules of Adenda 1."""

    if claim_type in _INHERITED_CLAIM_TYPES:
        return _claim_support_v10(claim_type, evidence_text)

    text = evidence_text
    stripped_lines = [line.strip() for line in text.splitlines()]

    if claim_type == "resource_leak":
        return _resource_leak_support(text, stripped_lines)

    if claim_type == "swallowed_exception":
        return _swallowed_exception_support(stripped_lines)

    if claim_type == "unsafe_xml_parsing":
        return _unsafe_xml_support(text)

    if claim_type == "insecure_tempfile":
        supported = bool(_MKTEMP_RE.search(text))
        return supported, "tempfile.mktemp( is required"

    if claim_type == "ssl_context_unverified":
        supported = "_create_unverified_context" in text or bool(
            re.search(r"\bCERT_NONE\b", text)
        )
        return supported, "ssl._create_unverified_context or CERT_NONE is required"

    if claim_type == "weak_random_security":
        return _weak_random_support(text)

    return False, f"unknown claim type {claim_type!r}; failing closed"


class AlmaGateV11:
    """Evidence validator 1.1.0: the frozen 1.0.0's 8 classes plus the
    6 mechanically verifiable classes of Adenda 1.  Same discipline as
    the 1.0.0: a rule name or confident message is not evidence; a
    candidate passes only when its cited lines exist in the diff, its
    stored evidence matches those lines exactly, and the evidence
    itself supports the specific claim."""

    version = POLICY_VERSION
    policy_sha256 = POLICY_SHA256

    def validate(
        self,
        candidates: list[Candidate],
        diff: DiffIndex,
        agent_name: str,
    ) -> GateResultV11:
        findings: list[dict[str, object]] = []
        ledger: list[LedgerEntryV11] = []
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
                supported, support_reason = _claim_support_v11(
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
                LedgerEntryV11(
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

        return GateResultV11(findings=findings, ledger=ledger)


__all__ = [
    "INHERITED_CLAIM_TYPES",
    "KNOWN_CLAIM_TYPES_V11",
    "NEW_CLAIM_TYPES",
    "POLICY_SHA256",
    "POLICY_VERSION",
    "AlmaGateV11",
    "GateResultV11",
    "LedgerEntryV11",
    "candidate_to_finding",
]
