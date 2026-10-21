"""Evidence gate 1.3.0 — the 1.2.0's hardened checks plus the
hunter's five best-ranked classes, built as a NEW gate, never by
editing a frozen one.

Provenance: PREREGISTRO-REVIEWBENCH-V2.md, Adenda 3 (2026-10-20,
00:37 EDT, written BEFORE any v2 run; Alejandro: «Lo hagamos» on the
two US$0 levers).  The 1.0.0 (``agent/alma_gate.py``), the 1.1.0
(``agent/alma_gate_v11.py``) and the 1.2.0 (``agent/alma_gate_v12.py``)
are NOT touched: every earlier measurement stays reproducible
byte-for-byte.  This gate inherits the 1.2.0's 14 classes by
DELEGATING their support check to the 1.2.0's own function (identical
hardened rules, by construction — the same pattern the 1.1.0 used
with the frozen 1.0.0) and adds the 5 classes ranked highest by the
structural-study class hunter
(``estudio-estructura-20261020/cazador-clases.md``), each with the
mechanical rule as that report writes it:

- ``weak_hash``: ``hashlib.md5(`` / ``hashlib.sha1(`` or
  ``hashlib.new(`` with the literal ``"md5"``/``"sha1"``, and NOT
  ``usedforsecurity=False`` (Bandit B303/B324, CodeQL
  py/weak-sensitive-data-hashing).
- ``tarfile_unsafe_extract``: ``.extractall(`` with no ``filter=``
  in the same call (CVE-2007-4559, CWE-22).
- ``hardcoded_password_argument``: a ``password``/``passwd``/``pwd``
  (or equivalent security name: ``secret``, ``api_key``, ``token``)
  keyword argument or ``def`` default set to a quoted literal of 6+
  characters that is not a placeholder and does not come from the
  environment (Bandit B106/B107, CWE-798) — the shape the 1.0.0's
  ``hardcoded_secret`` cannot see, because its regex requires the
  assignment at the start of the line.
- ``jwt_verification_disabled``: a ``jwt.decode(`` call with
  ``"verify_signature": False``, ``verify=False``, or the ``"none"``
  algorithm (CWE-347).
- ``debug_mode_enabled``: ``DEBUG = True``, ``<obj>.debug = True``,
  or ``.run(..., debug=True)`` with the literal ``True`` written in
  the cited line (Bandit B201, CodeQL py/flask-debug, CWE-489).

COMPOSITION with the 1.2.0 hardening (Adenda 2, inherited by Adenda
3) — the hunter's WHAT on the 1.2.0's HOW:

- Markers are searched on the TOKENIZED VIEWS built by the 1.2.0:
  pure-code markers (``hashlib.md5(``, ``.extractall(``,
  ``jwt.decode(``, ``DEBUG = True``, ``.run(``) in the CODE view
  (comments and every string literal removed), so a comment, help
  string or docstring quoting the pattern is not evidence — red-team
  family A cannot recur for the new classes.
- Markers that live inside expression literals
  (``hashlib.new("md5")``, ``password="..."``,
  ``"verify_signature": False``, ``algorithms=["none"]``) are
  searched in the CODE+STRINGS view, ALWAYS paired with the code-side
  marker (the call or the keyword name) present in the CODE view of
  the same line, so documentation text that merely quotes the
  pattern cannot support a claim either.
- Co-occurrence (Adenda 2 (d)), generalized from same-line to
  same-CALL where a call is the natural unit: a JWT disabling option
  counts only inside the ``jwt.decode(`` call span — the cited lines
  from the decode line until its brackets balance — so a
  ``verify=False`` belonging to a neighbouring ``requests.get`` in
  the same citation is not JWT evidence (bag-of-lines).  The
  ``.run(..., debug=True)`` form uses the same span rule.
- Antidotes (Adenda 2 (e)) are searched in the marker call's span
  computed over the WHOLE DIFF BLOCK (bracket balance on the code
  view), not only in the cited range — the range-trim trick (guard
  on the uncited continuation line of the call) dies, while an
  antidote belonging to a DIFFERENT call in the same block does not
  defeat a genuine claim.
- The added-line requirement (Adenda 2 (f)) and the exact-evidence
  and diff-presence checks are the 1.2.0's, unchanged.

TENSIONS between the hunter's rule text and the inherited hardening,
and how each was resolved (recorded, per the build order; none was
forced silently):

- Antidote scope: the hunter writes the ``weak_hash`` guard as "not
  in the CITED lines" and the tarfile guard as "not in the same
  call".  The 1.3.0 searches both antidotes in the call span over
  the whole block (the inherited Adenda 2 (e) discipline): strictly
  stronger against range-trimming, and it changes no hunter verdict
  — none of the hunter's ACCEPT examples has the antidote anywhere
  in its file.
- tarfile receiver: the hunter's rule is a bare ``.extractall(``
  marker, yet its own adversary list requires the ZIP call
  (``zipf.extractall(...)``) to be rejected — indistinguishable by
  the bare marker, because CPython neutralizes ``..`` for zip but
  not for tar.  Minimal distinguisher added, in the spirit of the
  red report's family H: reject when the receiver name contains
  "zip" or the block's code mentions ``zipfile``/``ZipFile``.
  DECLARED LIMIT: a ``ZipFile`` held in a neutrally named variable
  still passes the marker; the name/context heuristic is the same
  order of approximation as the 1.2.0's ``connect(`` network rule.
- JWT call marker: the hunter allows ``decode(`` "of jose/pyjwt";
  an UNQUALIFIED ``decode(`` is undecidable from cited lines (any
  object can grow one), so the gate requires the ``jwt.`` receiver —
  which also matches ``jose.jwt.decode(``.  Options passed by
  variable (``options=opts`` defined elsewhere) are likewise not
  decidable from the citation and fail closed.
- ``hardcoded_password_argument`` same-line occurrence: the keyword
  in the CODE view and the literal in the CODE+STRINGS view of the
  same line can still belong to DIFFERENT keyword arguments on that
  line (a real ``password=<variable>`` next to a string containing
  ``token='...'``).  A quote-parity scan of the CODE+STRINGS line
  therefore verifies that the matched keyword starts OUTSIDE any
  string literal before the pair counts as support.
- ``weak_hash`` via ``hashlib.new`` requires the algorithm literal
  on the marker line (CODE+STRINGS view); ``hashlib.new(name)`` with
  the algorithm in a variable is not mechanically provable and
  fails closed, as the hunter's bare-``md5(`` adversary does.

The 1.2.0's own declared residuals and tensions (dead code,
XML input provenance, block-granular antidotes, same-line SQL/race
co-occurrence) are inherited unchanged; see that module's docstring.

Selection: run configuration ``RB_CONFIG_GATE=v13`` (default
``v1``); see ``agent/main.py``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re

from .alma_gate import _PLACEHOLDER_VALUES, candidate_to_finding
from .alma_gate_v12 import (
    _PLACEHOLDER_PREFIXES,
    _POLICY as _POLICY_V12,
    KNOWN_CLAIM_TYPES_V12,
    _LineView,
    _block_code_text,
    _build_views,
    _claim_support_v12,
    _contiguous_block,
)
from .base_reviewer import Candidate
from .diff_parser import DiffIndex


POLICY_VERSION = "alma-evidence-gate/1.3.0"
_POLICY = {
    "version": POLICY_VERSION,
    "required_checks": list(_POLICY_V12["required_checks"])
    + [
        "the five classes added by Adenda 3 check code markers in the code view and literal arguments in the code+strings view of the same cited line, their disabling options inside the call span, and their safe forms (usedforsecurity=False, filter=) in the marker call's span over the whole diff block",
    ],
    "claims": {
        **_POLICY_V12["claims"],
        # The 5 classes added by Adenda 3 of the v2 pre-registration,
        # with the hunter report's mechanical rules.
        "debug_mode_enabled": (
            "DEBUG = True, <obj>.debug = True, or .run(..., debug=True) "
            "with the literal True"
        ),
        "hardcoded_password_argument": (
            "password/passwd/pwd/secret/api_key/token keyword argument "
            "or default set to a non-placeholder quoted literal"
        ),
        "jwt_verification_disabled": (
            "jwt.decode with verify_signature False, verify=False, or "
            "the none algorithm"
        ),
        "tarfile_unsafe_extract": ".extractall( without filter= in the call",
        "weak_hash": (
            "hashlib.md5/sha1 or hashlib.new('md5'/'sha1') without "
            "usedforsecurity=False"
        ),
    },
}
POLICY_SHA256 = hashlib.sha256(
    json.dumps(_POLICY, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

NEW_CLAIM_TYPES_V13 = (
    "weak_hash",
    "tarfile_unsafe_extract",
    "hardcoded_password_argument",
    "jwt_verification_disabled",
    "debug_mode_enabled",
)
KNOWN_CLAIM_TYPES_V13 = tuple(sorted(_POLICY["claims"].keys()))

# ---------------------------------------------------------------------------
# Call spans: bracket balance on the code view.  Used for JWT/debug
# co-occurrence over the CITED lines (positive support comes from the
# citation) and for antidote search over the whole BLOCK (negative
# evidence may come from the block, per Adenda 2 (e)).
# ---------------------------------------------------------------------------


def _call_span(code_lines: list[str], start: int, col: int = 0) -> list[int]:
    """Indices of the lines forming the call that opens at
    ``code_lines[start]`` (counting from column ``col`` on that
    line), by bracket balance.  If the brackets never balance within
    the available lines, the span runs to the last available line:
    the markers shown are still inside the call as far as the
    evidence reaches."""

    depth = 0
    span: list[int] = []
    for index in range(start, len(code_lines)):
        span.append(index)
        segment = code_lines[index][col:] if index == start else code_lines[index]
        for char in segment:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
        if depth <= 0:
            break
    return span


def _block_index(block: list[_LineView], line_number: int) -> int | None:
    for index, view in enumerate(block):
        if view.number == line_number:
            return index
    return None


def _antidote_in_call_span(
    block: list[_LineView],
    marker_view: _LineView,
    marker_col: int,
    antidote_re: "re.Pattern[str]",
) -> bool:
    """Search ``antidote_re`` in the marker call's span over the
    whole diff block (Adenda 2 (e), refined from block-wide to the
    call's own lines)."""

    start = _block_index(block, marker_view.number)
    if start is None:
        # The marker line is not in the block (cannot happen for a
        # validated citation); fall back to the cited line itself.
        return bool(antidote_re.search(marker_view.code))
    block_code = [view.code for view in block]
    span = _call_span(block_code, start, marker_col)
    return any(antidote_re.search(block_code[index]) for index in span)


# ---------------------------------------------------------------------------
# The 5 classes of Adenda 3, on the tokenized views.
# ---------------------------------------------------------------------------

_HASHLIB_WEAK_RE = re.compile(r"\bhashlib\s*\.\s*(?:md5|sha1)\s*\(")
_HASHLIB_NEW_RE = re.compile(r"\bhashlib\s*\.\s*new\s*\(")
_HASHLIB_NEW_ALG_RE = re.compile(
    r"\bhashlib\s*\.\s*new\s*\(\s*[\"']\s*(?:md5|sha1)\s*[\"']", re.I
)
_USEDFORSECURITY_FALSE_RE = re.compile(r"\busedforsecurity\s*=\s*False\b")


def _weak_hash_support(
    cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    marker: tuple[_LineView, int] | None = None
    for view in cited:
        match = _HASHLIB_WEAK_RE.search(view.code)
        if match:
            marker = (view, match.start())
            break
        match = _HASHLIB_NEW_RE.search(view.code)
        if match and _HASHLIB_NEW_ALG_RE.search(view.plus):
            # hashlib.new( is code (CODE view) and its algorithm
            # literal is an expression string (CODE+STRINGS view) on
            # the same line: the pair is the marker.
            marker = (view, match.start())
            break
    if marker is None:
        return False, (
            "hashlib.md5(/hashlib.sha1( or hashlib.new( with the "
            "literal 'md5'/'sha1' is required (a bare md5( not "
            "resolved to hashlib is not decidable)"
        )
    marker_view, marker_col = marker
    if _antidote_in_call_span(
        block, marker_view, marker_col, _USEDFORSECURITY_FALSE_RE
    ):
        return False, (
            "the call declares usedforsecurity=False (non-security "
            "checksum) in the diff block"
        )
    return True, (
        "a weak hash (md5/sha1) is constructed without "
        "usedforsecurity=False"
    )


_EXTRACTALL_RE = re.compile(r"([A-Za-z_][\w.]*)\s*\.\s*extractall\s*\(")
_FILTER_KWARG_RE = re.compile(r"\bfilter\s*=")


def _tarfile_support(
    cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    marker: tuple[_LineView, "re.Match[str]"] | None = None
    for view in cited:
        match = _EXTRACTALL_RE.search(view.code)
        if match:
            marker = (view, match)
            break
    if marker is None:
        return False, "a .extractall( call is required"
    marker_view, match = marker
    receiver = match.group(1)
    block_code = _block_code_text(block)
    if "zip" in receiver.lower() or re.search(
        r"\bzipfile\b", block_code
    ) or "ZipFile" in block_code:
        return False, (
            "the receiver is a zip archive: CPython neutralizes "
            "'..' and absolute paths for zipfile, so .extractall( "
            "does not prove the tar traversal defect"
        )
    if _antidote_in_call_span(block, marker_view, match.start(), _FILTER_KWARG_RE):
        return False, (
            "the extractall call passes filter= (an extraction "
            "filter is present in the diff block)"
        )
    return True, "tar extraction via .extractall( without filter="


_PASSWORD_KWARG_NAMES = r"(?:password|passwd|pwd|secret|api_key|token)"
_PASSWORD_KWARG_CODE_RE = re.compile(rf"\b{_PASSWORD_KWARG_NAMES}\s*=", re.I)
_PASSWORD_KWARG_LITERAL_RE = re.compile(
    rf"\b{_PASSWORD_KWARG_NAMES}\s*=\s*([\"'])(?P<value>[^\"']{{6,}})\1",
    re.I,
)


def _inside_string(text: str, pos: int) -> bool:
    """True when ``text[pos]`` sits inside a string literal, by a
    quote-parity scan of the single line (escapes honoured).  Used
    for the same-line occurrence check of
    hardcoded_password_argument: a keyword that only exists inside a
    string on that line is documentation, not an argument."""

    quote: str | None = None
    index = 0
    while index < pos:
        char = text[index]
        if quote is not None:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in ("'", '"'):
            quote = char
        index += 1
    return quote is not None


def _password_argument_support(cited: list[_LineView]) -> tuple[bool, str]:
    for view in cited:
        if not _PASSWORD_KWARG_CODE_RE.search(view.code):
            # No security keyword in CODE position on this line:
            # anything that looks like one lives inside a comment
            # or a string and is not an argument.
            continue
        for match in _PASSWORD_KWARG_LITERAL_RE.finditer(view.plus):
            if _inside_string(view.plus, match.start()):
                # The keyword+literal pair itself sits inside a
                # string literal on this line (documentation quoting
                # an example call): not an argument of real code.
                continue
            value = match.group("value").strip().lower()
            if (
                value in _PLACEHOLDER_VALUES
                or value.startswith(_PLACEHOLDER_PREFIXES)
                or value.startswith("${")
                or value.startswith("os.")
                or set(value) <= {"x"}
                or set(value) <= {"*"}
            ):
                return False, (
                    "the literal is a placeholder (or environment-"
                    "derived), not a hardcoded password"
                )
            return True, (
                "a security keyword argument is set to a "
                "non-placeholder quoted literal"
            )
    return False, (
        "a password/passwd/pwd/secret/api_key/token keyword argument "
        "or default set to a quoted literal of 6+ characters is "
        "required"
    )


_JWT_DECODE_RE = re.compile(r"\bjwt\s*\.\s*decode\s*\(")
_JWT_VERIFY_SIGNATURE_FALSE_RE = re.compile(
    r"[\"']verify_signature[\"']\s*:\s*False\b"
)
_JWT_VERIFY_FALSE_RE = re.compile(r"\bverify\s*=\s*False\b")
_JWT_NONE_ALGORITHM_RE = re.compile(
    r"\balgorithms?\s*=\s*(?:\[[^\]]*[\"']none[\"']|[\"']none[\"'])", re.I
)


def _jwt_support(cited: list[_LineView]) -> tuple[bool, str]:
    cited_code = [view.code for view in cited]
    cited_plus = [view.plus for view in cited]
    for index, code in enumerate(cited_code):
        match = _JWT_DECODE_RE.search(code)
        if not match:
            continue
        span = _call_span(cited_code, index, match.start())
        span_code = "\n".join(cited_code[i] for i in span)
        span_plus = "\n".join(cited_plus[i] for i in span)
        if (
            _JWT_VERIFY_SIGNATURE_FALSE_RE.search(span_plus)
            or _JWT_VERIFY_FALSE_RE.search(span_code)
            or _JWT_NONE_ALGORITHM_RE.search(span_plus)
        ):
            return True, (
                "jwt.decode is called with signature verification "
                "disabled (verify_signature False, verify=False, or "
                "the none algorithm) inside the call"
            )
    return False, (
        "a jwt.decode( call with 'verify_signature': False, "
        "verify=False, or the 'none' algorithm inside the call is "
        "required"
    )


_DEBUG_ASSIGN_RE = re.compile(r"^\s*DEBUG\s*=(?!=)\s*True\b")
_DEBUG_ATTR_RE = re.compile(r"(?i:\b[A-Za-z_][\w.]*\.debug)\s*=(?!=)\s*True\b")
_RUN_CALL_RE = re.compile(r"\.run\s*\(")
_DEBUG_KWARG_TRUE_RE = re.compile(r"\bdebug\s*=(?!=)\s*True\b")


def _debug_support(cited: list[_LineView]) -> tuple[bool, str]:
    cited_code = [view.code for view in cited]
    for line in cited_code:
        if _DEBUG_ASSIGN_RE.match(line) or _DEBUG_ATTR_RE.search(line):
            return True, (
                "debug mode is assigned the literal True "
                "(DEBUG = True / <obj>.debug = True)"
            )
    for index, line in enumerate(cited_code):
        match = _RUN_CALL_RE.search(line)
        if not match:
            continue
        span = _call_span(cited_code, index, match.start())
        joined = "\n".join(cited_code[i] for i in span)
        if _DEBUG_KWARG_TRUE_RE.search(joined):
            return True, "a .run( call passes debug=True"
    return False, (
        "DEBUG = True, <obj>.debug = True, or .run(..., debug=True) "
        "with the literal True is required"
    )


def _claim_support_v13(
    claim_type: str, cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    """Support check for the 1.3.0: the 1.2.0's 14 classes delegate
    to the 1.2.0's own function (identical hardened checks, by
    construction); the 5 classes of Adenda 3 apply the hunter's
    mechanical rules on the same tokenized views."""

    if claim_type in KNOWN_CLAIM_TYPES_V12:
        return _claim_support_v12(claim_type, cited, block)

    if claim_type == "weak_hash":
        return _weak_hash_support(cited, block)

    if claim_type == "tarfile_unsafe_extract":
        return _tarfile_support(cited, block)

    if claim_type == "hardcoded_password_argument":
        return _password_argument_support(cited)

    if claim_type == "jwt_verification_disabled":
        return _jwt_support(cited)

    if claim_type == "debug_mode_enabled":
        return _debug_support(cited)

    return False, f"unknown claim type {claim_type!r}; failing closed"


@dataclass
class LedgerEntryV13:
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
class GateResultV13:
    findings: list[dict[str, object]]
    ledger: list[LedgerEntryV13]


_FAILURE_MARKERS = (
    "invalid line range",
    "not present in the diff",
    "does not exactly match",
    "evidence check failed",
    "no line added by this change",
)


class AlmaGateV13:
    """Evidence validator 1.3.0: the 1.2.0's 14 hardened classes
    (delegated to the 1.2.0's own checks) plus the hunter's five
    best-ranked mechanically verifiable classes (Adenda 3 of the v2
    pre-registration).  Same discipline as its predecessors — a rule
    name or confident message is not evidence — with the new classes
    checked on the same tokenized views, call spans and block-level
    antidotes the red team's hardening established."""

    version = POLICY_VERSION
    policy_sha256 = POLICY_SHA256

    def validate(
        self,
        candidates: list[Candidate],
        diff: DiffIndex,
        agent_name: str,
    ) -> GateResultV13:
        findings: list[dict[str, object]] = []
        ledger: list[LedgerEntryV13] = []
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

            if not reasons and not any(
                item["kind"] == "added" for item in evidence
            ):
                # Adenda 2 (f), inherited: the defect must be
                # introduced by THIS change.
                reasons.append(
                    "cited evidence contains no line added by this "
                    "change (every cited line is pre-existing context)"
                )

            if not reasons:
                file_diff = diff.file(candidate.file)
                block_lines = _contiguous_block(
                    file_diff, candidate.start_line, candidate.end_line
                )
                views = _build_views(block_lines)
                cited_views = [
                    view
                    for view in views
                    if candidate.start_line <= view.number <= candidate.end_line
                ]
                supported, support_reason = _claim_support_v13(
                    candidate.claim_type, cited_views, views
                )
                if not supported:
                    reasons.append(f"claim-specific evidence check failed: {support_reason}")
                else:
                    reasons.append(f"claim-specific evidence check passed: {support_reason}")

            failed = any(
                marker in reason for reason in reasons for marker in _FAILURE_MARKERS
            )

            is_duplicate = False
            if not failed:
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

            status = "rejected" if (failed or is_duplicate) else "accepted"
            if status == "accepted":
                findings.append(candidate_to_finding(candidate, agent_name))

            ledger.append(
                LedgerEntryV13(
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

        return GateResultV13(findings=findings, ledger=ledger)


__all__ = [
    "KNOWN_CLAIM_TYPES_V13",
    "NEW_CLAIM_TYPES_V13",
    "POLICY_SHA256",
    "POLICY_VERSION",
    "AlmaGateV13",
    "GateResultV13",
    "LedgerEntryV13",
    "candidate_to_finding",
]
