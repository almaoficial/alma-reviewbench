"""ALMA evidence gate 1.4.0: the third state, ``needs_validation``.

Pre-registered in PREREGISTRO-PUERTA-140.md (§3) and put to work for
the ALMA arm only by PREREGISTRO-REVIEWBENCH-V23.md (§3(d), §4).  The
1.4.0 inherits the 19 classes and every evidence rule of the 1.3.0 BY
DELEGATION — validating a candidate through ``AlmaGateV13`` first —
and adds one thing: a candidate the 1.3.0 rejects ONLY for evidence
completeness, with the class's primary marker present in the cited
evidence and nothing in the diff block refuting the claim, is not
discarded.  It is held as ``needs_validation``: not emitted, carrying
NO severity (the record type does not even define the field, by
construction), recorded in a separate section of the ledger with the
exact blockers — the completeness checks that failed, in the gate's
own reason texts — and the mechanical confirmation each blocker
requires.

The frontier (paper 140 §3, all five conditions, mechanical, no
judgement):

1. the claim type is one of the 19 known classes;
2. the candidate is well-formed (no invalid line range);
3. the citation anchors: every cited line is present in the diff and
   the stored evidence matches the diff's lines exactly;
4. nothing refutes the claim: the primary marker is present AND no
   antidote is present anywhere the gate itself looks for one;
5. the only failing checks are completeness checks of three kinds:
   (a) co-occurrence — marker and construction both stand in the
       cited evidence but not joined the way the class rule demands
       (for sql_injection and race_condition: present in the citation,
       inside ONE statement span by bracket balance, but not on the
       same cited line);
   (b) construction outside the cited span — the missing piece exists
       in the claim's natural unit over the whole diff block (the
       statement span, the call span, the handler body) but was not
       cited;
   (c) the citation contains no line added by this change
       (Adenda 2(f) of the v2 paper).

Anything else — unknown class, malformed, false anchor, absent
marker, antidote present, duplicate of an accepted finding — stays
exactly where the 1.3.0 left it.  accepted(1.4.0) == accepted(1.3.0)
by construction: the frontier only moves REJECTED candidates, and
only to the holding state, never to emission.

General categories (the v2.3 reviewer's nine public labels): the gate
has no verification rule for them, and inventing one is forbidden by
both papers.  A general candidate that is well-formed and anchored is
therefore held as needs_validation with the mechanical blocker
``sin_regla_de_verificacion_en_puerta`` (plus ``no_added_line`` when
its citation also lacks an added line); a malformed or unanchored one
is rejected like any other.  Claim types that are neither a known
class nor a general category fail closed, exactly as the 1.3.0
treats unknown classes.

The gates 1.0.0–1.3.0 are never touched: this module only imports
them.  Frozen POLICY_SHA256 values: 1.0.0
3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35,
1.1.0 6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9,
1.2.0 a768afa46136ba1bf542da65006a946d11cb39e8db73fbd484c3f021b7994211,
1.3.0 0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass

from .alma_gate import _PLACEHOLDER_VALUES, _SECRET_LITERAL_RE, _UNSAFE_SQL_RE
from .alma_gate_v11 import (
    _ASSIGNMENT_RE,
    _EXCEPT_TYPED_RE,
    _RANDOM_CALL_RE,
    _SECURITY_NAME_RE,
    _XML_STDLIB_RE,
)
from .alma_gate_v12 import (
    _CONCURRENCY_RE,
    _FROM_TEMPLE_IMPORT_RE,
    _GLOBAL_DECL_RE,
    _IDIOMATIC_FALLBACK_RE,
    _MKTEMP_BARE_RE,
    _MKTEMP_RECEIVER_RE,
    _NETWORK_CONTEXT_RE,
    _NONCREDENTIAL_SUFFIXES,
    _PLACEHOLDER_PREFIXES,
    _RESOURCE_OPEN_RE,
    _SHARED_ASSIGN_RE,
    _SQL_SKELETON_RE,
    _LineView,
    _block_code_text,
    _build_views,
    _contiguous_block,
    _handler_body,
)
from .alma_gate_v13 import (
    _DEBUG_ASSIGN_RE,
    _DEBUG_ATTR_RE,
    _DEBUG_KWARG_TRUE_RE,
    _EXTRACTALL_RE,
    _FILTER_KWARG_RE,
    _HASHLIB_NEW_ALG_RE,
    _HASHLIB_NEW_RE,
    _HASHLIB_WEAK_RE,
    _JWT_DECODE_RE,
    _JWT_NONE_ALGORITHM_RE,
    _JWT_VERIFY_FALSE_RE,
    _JWT_VERIFY_SIGNATURE_FALSE_RE,
    _PASSWORD_KWARG_CODE_RE,
    _PASSWORD_KWARG_LITERAL_RE,
    _POLICY as _POLICY_V13,
    _RUN_CALL_RE,
    _USEDFORSECURITY_FALSE_RE,
    _antidote_in_call_span,
    _call_span,
    _claim_support_v13,
    _inside_string,
    AlmaGateV13,
    GateResultV13,
    LedgerEntryV13,
)
from .base_reviewer import Candidate, _SECRET_NAME_RE
from .diff_parser import DiffIndex

POLICY_VERSION = "alma-evidence-gate/1.4.0"

# The nine general categories of the v2.3 paper §3(a): the
# benchmark's own public taxonomy labels, in the paper's order.
GENERAL_CATEGORIES_V14 = (
    "correctness",
    "reliability",
    "maintainability",
    "testing",
    "security",
    "documentation",
    "api-architecture",
    "performance",
    "accessibility",
)

_POLICY = {
    "version": POLICY_VERSION,
    "required_checks": list(_POLICY_V13["required_checks"])
    + [
        "a candidate the 1.3.0 rejects only for evidence completeness — marker and construction present in the citation but not joined as the class rule demands, the missing piece present in the claim's natural unit over the diff block but uncited, or no cited line added by this change — with the primary marker present and no antidote in the block is held as needs_validation: never emitted, carrying no severity, recorded apart from the ledger with its blockers and the confirmation each blocker requires",
        "a general-category candidate (the v2.3 taxonomy) that is well-formed and anchored is held as needs_validation with the blocker sin_regla_de_verificacion_en_puerta: this gate defines no verification rule for general categories",
    ],
    "claims": dict(_POLICY_V13["claims"]),
}
POLICY_SHA256 = hashlib.sha256(
    json.dumps(_POLICY, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

KNOWN_CLAIM_TYPES_V14 = tuple(sorted(_POLICY["claims"].keys()))

# Blocker check ids (paper 140 §3 completeness families + the v2.3
# paper §4 blocker for general findings).
CHECK_CO_OCCURRENCE = "co_occurrence"
CHECK_CONSTRUCTION_OUTSIDE = "construction_outside_cited_span"
CHECK_NO_ADDED_LINE = "no_added_line"
CHECK_NO_RULE = "sin_regla_de_verificacion_en_puerta"

_REQUIREMENTS = {
    CHECK_CO_OCCURRENCE: (
        "una cita donde la marca primaria y la construcción "
        "co-ocurran según la regla de la clase"
    ),
    CHECK_CONSTRUCTION_OUTSIDE: (
        "el bloque completo del archivo alrededor de la cita, para "
        "verificar la construcción, la ausencia de antídoto y la "
        "línea agregada"
    ),
    CHECK_NO_ADDED_LINE: (
        "una cita que incluya al menos una línea agregada por el cambio"
    ),
    CHECK_NO_RULE: (
        "una regla de verificación para la categoría, definida y "
        "medida en una pasada de validación aparte (no definida ni "
        "autorizada por los papeles vigentes)"
    ),
}

_NO_ADDED_REASON = (
    "cited evidence contains no line added by this change "
    "(every cited line is pre-existing context)"
)


def _blocker(check: str, reason: str) -> dict:
    return {
        "check": check,
        "reason": reason,
        "requirement": _REQUIREMENTS[check],
    }


@dataclass(frozen=True)
class EvidenceLineV14:
    """One cited line, mirrored from the 1.3.0 ledger's evidence."""

    file: str
    line: int
    kind: str
    text: str


@dataclass(frozen=True)
class NeedsValidationRecord:
    """A held candidate.  NOTE: there is deliberately NO severity
    field of any kind on this type — a held finding with a severity
    is a schema error under paper 140 §3 (the Cloudflare
    ``security-audit`` schema the third state is imported from)."""

    rule_id: str
    claim_type: str
    file: str
    start_line: int
    end_line: int
    message: str
    evidence: tuple[EvidenceLineV14, ...]
    producer: str
    blockers: tuple[dict, ...]
    validator_version: str
    policy_sha256: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LedgerEntryV14:
    """The 1.3.0 ledger entry shape, re-stamped with the 1.4.0
    identity.  Statuses here are only accepted / rejected: held
    candidates live in ``needs_validation``, never in this ledger."""

    rule_id: str
    claim_type: str
    file: str
    start_line: int
    end_line: int
    message: str
    severity_hint: str
    category_hint: str
    evidence: tuple[EvidenceLineV14, ...]
    status: str
    reasons: tuple[str, ...]
    validator_version: str
    policy_sha256: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GateResultV14:
    findings: tuple[dict, ...]
    ledger: tuple[LedgerEntryV14, ...]
    needs_validation: tuple[NeedsValidationRecord, ...]


def _statement_spans(code_texts: list[str]) -> list[list[int]]:
    """Group line indices into statement spans by bracket balance
    (the same naive scan the gates use for call spans) plus backslash
    continuation.  Two cited lines are 'in one statement' when they
    share a span: the mechanical form of co-occurrence across the
    lines of one multi-line statement."""

    spans: list[list[int]] = []
    current: list[int] = []
    depth = 0
    for index, text in enumerate(code_texts):
        current.append(index)
        for char in text:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
        if depth <= 0 and not text.rstrip().endswith("\\"):
            spans.append(current)
            current = []
            depth = 0
    if current:
        spans.append(current)
    return spans


@dataclass(frozen=True)
class _Probe:
    """Frontier probe outcome for one class candidate.

    marker: the class's primary marker is present in the citation.
    refuted: something in the citation or the block refutes the claim
        (antidote, placeholder, safe form, non-defect shape).
    completeness: when the support check failed only for
        completeness, which kind — CHECK_CO_OCCURRENCE or
        CHECK_CONSTRUCTION_OUTSIDE; None when the failure is not a
        completeness failure (or the support passed)."""

    marker: bool
    refuted: bool
    completeness: str | None = None


def _probe_sql(
    cited: list[_LineView], block: list[_LineView]
) -> _Probe:
    cited_numbers = {view.number for view in cited}
    skeleton = [
        i for i, v in enumerate(cited) if _SQL_SKELETON_RE.search(v.plus)
    ]
    if not skeleton:
        return _Probe(False, False)
    construction = [
        i for i, v in enumerate(cited) if _UNSAFE_SQL_RE.search(v.plus)
    ]
    if construction:
        spans = _statement_spans([v.code for v in cited])
        span_of = {}
        for span in spans:
            for i in span:
                span_of[i] = span
        if any(
            any(c in span_of[s] for c in construction) for s in skeleton
        ):
            return _Probe(True, False, CHECK_CO_OCCURRENCE)
        return _Probe(True, False)
    # (b): the construction stands in the block statement span of a
    # cited skeleton line, on a line the citation left out.
    block_spans = _statement_spans([v.code for v in block])
    block_index = {v.number: i for i, v in enumerate(block)}
    for s in skeleton:
        target = block_index.get(cited[s].number)
        if target is None:
            continue
        span = next(sp for sp in block_spans if target in sp)
        for j in span:
            if block[j].number in cited_numbers:
                continue
            if _UNSAFE_SQL_RE.search(block[j].plus):
                return _Probe(True, False, CHECK_CONSTRUCTION_OUTSIDE)
    return _Probe(True, False)


def _probe_race(
    cited: list[_LineView], block: list[_LineView]
) -> _Probe:
    concurrency = [
        i for i, v in enumerate(cited) if _CONCURRENCY_RE.search(v.code)
    ]
    if not concurrency:
        return _Probe(False, False)
    assignments = [
        i
        for i, v in enumerate(cited)
        if _SHARED_ASSIGN_RE.search(v.code)
    ]
    if assignments:
        spans = _statement_spans([v.code for v in cited])
        span_of = {}
        for span in spans:
            for i in span:
                span_of[i] = span
        if any(
            any(a in span_of[c] for a in assignments) for c in concurrency
        ):
            return _Probe(True, False, CHECK_CO_OCCURRENCE)
        return _Probe(True, False)
    # (b): an assignment line to shared state stands in the block,
    # inside the statement span of a cited concurrency line, uncited.
    cited_numbers = {view.number for view in cited}
    block_spans = _statement_spans([v.code for v in block])
    block_index = {v.number: i for i, v in enumerate(block)}
    for c in concurrency:
        target = block_index.get(cited[c].number)
        if target is None:
            continue
        span = next(sp for sp in block_spans if target in sp)
        for j in span:
            if block[j].number in cited_numbers:
                continue
            if _SHARED_ASSIGN_RE.search(block[j].code):
                return _Probe(True, False, CHECK_CONSTRUCTION_OUTSIDE)
    return _Probe(True, False)


def _probe_jwt(cited: list[_LineView], block: list[_LineView]) -> _Probe:
    marker = None
    for view in cited:
        match = _JWT_DECODE_RE.search(view.code)
        if match:
            marker = (view, match.start())
            break
    if marker is None:
        return _Probe(False, False)
    marker_view, marker_col = marker
    cited_numbers = {view.number for view in cited}
    start = next(
        (i for i, v in enumerate(block) if v.number == marker_view.number),
        None,
    )
    if start is None:
        return _Probe(True, False)
    block_code = [v.code for v in block]
    block_plus = [v.plus for v in block]
    for index in _call_span(block_code, start, marker_col):
        if block[index].number in cited_numbers:
            continue
        if (
            _JWT_VERIFY_SIGNATURE_FALSE_RE.search(block_plus[index])
            or _JWT_VERIFY_FALSE_RE.search(block_code[index])
            or _JWT_NONE_ALGORITHM_RE.search(block_plus[index])
        ):
            return _Probe(True, False, CHECK_CONSTRUCTION_OUTSIDE)
    return _Probe(True, False)


def _probe_debug(cited: list[_LineView], block: list[_LineView]) -> _Probe:
    for view in cited:
        if _DEBUG_ASSIGN_RE.match(view.code) or _DEBUG_ATTR_RE.search(
            view.code
        ):
            # The assignment forms pass the 1.3.0 support outright;
            # reaching the frontier with one means it was refuted
            # nowhere and something else failed — not completeness.
            return _Probe(True, False)
    marker = None
    for view in cited:
        match = _RUN_CALL_RE.search(view.code)
        if match:
            marker = (view, match.start())
            break
    if marker is None:
        return _Probe(False, False)
    marker_view, marker_col = marker
    cited_numbers = {view.number for view in cited}
    start = next(
        (i for i, v in enumerate(block) if v.number == marker_view.number),
        None,
    )
    if start is None:
        return _Probe(True, False)
    block_code = [v.code for v in block]
    for index in _call_span(block_code, start, marker_col):
        if block[index].number in cited_numbers:
            continue
        if _DEBUG_KWARG_TRUE_RE.search(block_code[index]):
            return _Probe(True, False, CHECK_CONSTRUCTION_OUTSIDE)
    return _Probe(True, False)


def _probe_handler(
    claim_type: str, cited: list[_LineView], block: list[_LineView]
) -> _Probe:
    """silenced_bare_except / swallowed_exception: the completeness
    shape is the handler body — present in the block as a bare
    ``pass`` but not (fully) cited."""

    marker_view = None
    for view in cited:
        if claim_type == "silenced_bare_except":
            if view.code.strip() == "except:":
                marker_view = view
                break
        else:
            match = _EXCEPT_TYPED_RE.match(view.code.strip())
            if match:
                if _IDIOMATIC_FALLBACK_RE.search(view.code):
                    return _Probe(True, True)
                marker_view = view
                break
    if marker_view is None:
        return _Probe(False, False)
    body = _handler_body(block, marker_view.number)
    if body is None or len(body) == 0:
        # The handler's body is not shown: the citation cannot
        # complete the claim either way — a completeness gap.
        return _Probe(True, False, CHECK_CONSTRUCTION_OUTSIDE)
    if len(body) == 1 and body[0][1] == "pass":
        cited_numbers = {view.number for view in cited}
        if body[0][0] not in cited_numbers:
            return _Probe(True, False, CHECK_CONSTRUCTION_OUTSIDE)
        # Body cited whole: a swallowed_exception can still fail the
        # 1.3.0's 'nothing but pass was cited after the except'
        # check when the citation runs past the handler — again a
        # citation-shape (completeness) failure.
        return _Probe(True, False, CHECK_CONSTRUCTION_OUTSIDE)
    # A real body: it handles or re-raises — the claim is refuted.
    return _Probe(True, True)


def _probe_secret(cited: list[_LineView], block: list[_LineView]) -> _Probe:
    for view in cited:
        match = _SECRET_LITERAL_RE.match(view.plus)
        if not match:
            continue
        name_part = view.plus.split("=", 1)[0]
        if not _SECRET_NAME_RE.search(name_part):
            return _Probe(False, False)
        value = match.group("value").strip().lower()
        if (
            value in _PLACEHOLDER_VALUES
            or value.startswith(tuple(_PLACEHOLDER_PREFIXES))
            or value.startswith("${")
            or value.startswith("os.")
        ):
            return _Probe(True, True)
        return _Probe(True, False)
    return _Probe(False, False)


def _probe_password_argument(
    cited: list[_LineView], block: list[_LineView]
) -> _Probe:
    # Mirrors _password_argument_support (1.3.0) exactly: a security
    # keyword in CODE position on the line, then the first
    # keyword+literal pair in the PLUS view that is not itself inside
    # a string; placeholders (incl. all-x / all-* masks) refute.
    for view in cited:
        if not _PASSWORD_KWARG_CODE_RE.search(view.code):
            continue
        for literal in _PASSWORD_KWARG_LITERAL_RE.finditer(view.plus):
            if _inside_string(view.plus, literal.start()):
                continue
            value = literal.group("value").strip().lower()
            if (
                value in _PLACEHOLDER_VALUES
                or value.startswith(_PLACEHOLDER_PREFIXES)
                or value.startswith("${")
                or value.startswith("os.")
                or set(value) <= {"x"}
                or set(value) <= {"*"}
            ):
                return _Probe(True, True)
            return _Probe(True, False)
    return _Probe(False, False)


def _probe_weak_hash(
    cited: list[_LineView], block: list[_LineView]
) -> _Probe:
    # Mirrors _weak_hash_support (1.3.0): hashlib.md5/sha1, or
    # hashlib.new( in CODE with the 'md5'/'sha1' literal in PLUS on
    # the same line; usedforsecurity=False in the call span refutes.
    marker = None
    for view in cited:
        match = _HASHLIB_WEAK_RE.search(view.code)
        if match:
            marker = (view, match.start())
            break
        match = _HASHLIB_NEW_RE.search(view.code)
        if match and _HASHLIB_NEW_ALG_RE.search(view.plus):
            marker = (view, match.start())
            break
    if marker is None:
        return _Probe(False, False)
    antidote = _antidote_in_call_span(
        block, marker[0], marker[1], _USEDFORSECURITY_FALSE_RE
    )
    return _Probe(True, antidote)


def _probe_tarfile(cited: list[_LineView], block: list[_LineView]) -> _Probe:
    marker = None
    for view in cited:
        match = _EXTRACTALL_RE.search(view.code)
        if match:
            marker = (view, match)
            break
    if marker is None:
        return _Probe(False, False)
    view, match = marker
    receiver = match.group(1).rsplit(".", 1)[-1].lower()
    block_code = _block_code_text(block)
    if receiver.startswith("zip") or re.search(r"\bzipfile\b", block_code):
        return _Probe(True, True)
    antidote = _antidote_in_call_span(
        block, view, match.start(), _FILTER_KWARG_RE
    )
    return _Probe(True, antidote)


def _probe_generic(
    claim_type: str, cited: list[_LineView], block: list[_LineView]
) -> _Probe:
    """Marker / refutation probes for the classes whose 1.3.0 support
    is a conjunction the citation either satisfies or not: for these
    classes a support failure means the marker is absent or an
    antidote is present, so no completeness kind is ever returned —
    their only road to the holding state is (c), no added line."""

    cited_code = "\n".join(view.code for view in cited)
    block_code = _block_code_text(block)
    if claim_type == "hardcoded_secret":
        return _probe_secret(cited, block)
    if claim_type == "hardcoded_password_argument":
        return _probe_password_argument(cited, block)
    if claim_type == "weak_hash":
        return _probe_weak_hash(cited, block)
    if claim_type == "tarfile_unsafe_extract":
        return _probe_tarfile(cited, block)
    if claim_type == "tls_verification_disabled":
        marker = bool(re.search(r"\bverify\s*=\s*False\b", cited_code))
        return _Probe(marker, False)
    if claim_type == "mutable_default":
        marker = bool(
            re.search(
                r"\bdef\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\(\))", cited_code
            )
        )
        return _Probe(marker, False)
    if claim_type == "command_execution":
        marker = bool(
            "os.system(" in cited_code
            or re.search(r"\b(?:eval|exec)\s*\(", cited_code)
            or "shell=True" in cited_code
        )
        return _Probe(marker, False)
    if claim_type == "unsafe_deserialization":
        if "pickle.loads(" in cited_code:
            return _Probe(True, False)
        if "yaml.load(" in cited_code:
            return _Probe(True, "SafeLoader" in block_code)
        return _Probe(False, False)
    if claim_type == "unsafe_xml_parsing":
        if _XML_STDLIB_RE.search(cited_code):
            return _Probe(True, "defusedxml" in block_code)
        return _Probe(False, False)
    if claim_type == "insecure_tempfile":
        if _MKTEMP_RECEIVER_RE.search(cited_code):
            return _Probe(True, False)
        if _MKTEMP_BARE_RE.search(cited_code):
            # A bare mktemp( only names the stdlib function when the
            # block imports it from tempfile; without the import the
            # marker is not established at all (declared choice).
            return _Probe(bool(_FROM_TEMPLE_IMPORT_RE.search(block_code)), False)
        return _Probe(False, False)
    if claim_type == "ssl_context_unverified":
        marker = "_create_unverified_context" in cited_code or bool(
            re.search(r"\bCERT_NONE\b", cited_code)
        )
        return _Probe(marker, False)
    if claim_type == "weak_random_security":
        # Mirrors _weak_random_support (1.2.0): anchored assignment,
        # security name, random-module value; a non-credential suffix
        # (count/ttl/delay/...) refutes.
        for view in cited:
            match = _ASSIGNMENT_RE.match(view.code)
            if not match:
                continue
            name, value = match.group(1), match.group(2)
            if not (
                _SECURITY_NAME_RE.search(name)
                and _RANDOM_CALL_RE.search(value)
            ):
                continue
            if name.lower().endswith(_NONCREDENTIAL_SUFFIXES):
                return _Probe(True, True)
            return _Probe(True, False)
        return _Probe(False, False)
    if claim_type == "resource_leak":
        # Mirrors _resource_leak_support (1.2.0): every opener match
        # counts unless it is a bare .connect( with no network
        # context in the block, or the line itself opens a with.
        opener = False
        for view in cited:
            for match in _RESOURCE_OPEN_RE.finditer(view.code):
                if match.lastgroup == "conn" and not _NETWORK_CONTEXT_RE.search(
                    block_code
                ):
                    continue
                stripped = view.code.strip()
                if stripped.startswith("with ") or stripped.startswith(
                    "async with "
                ):
                    continue
                opener = True
        if not opener:
            return _Probe(False, False)
        return _Probe(True, ".close(" in block_code)
    return _Probe(False, False)


_BESPOKE_PROBES = {
    "sql_injection": _probe_sql,
    "race_condition": _probe_race,
    "jwt_verification_disabled": _probe_jwt,
    "debug_mode_enabled": _probe_debug,
}


def _probe(
    claim_type: str, cited: list[_LineView], block: list[_LineView]
) -> _Probe:
    if claim_type in _BESPOKE_PROBES:
        return _BESPOKE_PROBES[claim_type](cited, block)
    if claim_type in ("silenced_bare_except", "swallowed_exception"):
        return _probe_handler(claim_type, cited, block)
    return _probe_generic(claim_type, cited, block)


def _evidence_lines(entry: LedgerEntryV13) -> tuple[EvidenceLineV14, ...]:
    return tuple(
        EvidenceLineV14(
            file=item["file"],
            line=item["line"],
            kind=item["kind"],
            text=item["text"],
        )
        for item in entry.evidence
    )


def _restamp(entry: LedgerEntryV13) -> LedgerEntryV14:
    return LedgerEntryV14(
        rule_id=entry.rule_id,
        claim_type=entry.claim_type,
        file=entry.file,
        start_line=entry.start_line,
        end_line=entry.end_line,
        message=entry.message,
        severity_hint=entry.severity_hint,
        category_hint=entry.category_hint,
        evidence=_evidence_lines(entry),
        status=entry.status,
        reasons=tuple(entry.reasons),
        validator_version=POLICY_VERSION,
        policy_sha256=POLICY_SHA256,
    )


def _frontier_blockers(
    candidate: Candidate, entry: LedgerEntryV13, diff: DiffIndex
) -> list[dict] | None:
    """Paper 140 §3 applied to one candidate the 1.3.0 rejected.
    Returns the blocker list when the candidate belongs in the
    holding state, None when it stays rejected."""

    reasons = list(entry.reasons)
    joined = "\n".join(reasons)
    # Conditions 1–3 and the declared exclusions: malformed, false
    # anchor and duplicates never move.
    if "invalid line range" in joined:
        return None
    if "not present in the diff" in joined:
        return None
    if "does not exactly match" in joined:
        return None
    if "duplicate of an already accepted finding" in joined:
        return None
    file_diff = diff.file(candidate.file)
    if file_diff is None:
        return None
    block_lines = _contiguous_block(
        file_diff, candidate.start_line, candidate.end_line
    )
    views = _build_views(block_lines)
    cited = [
        view
        for view in views
        if candidate.start_line <= view.number <= candidate.end_line
    ]
    supported, support_reason = _claim_support_v13(
        candidate.claim_type, cited, views
    )
    no_added = "no line added by this change" in joined
    blockers: list[dict] = []
    if not supported:
        # Conditions 4–5: marker present, nothing refutes, and the
        # failure is a completeness failure of kind (a) or (b).
        probe = _probe(candidate.claim_type, cited, views)
        if not probe.marker or probe.refuted or probe.completeness is None:
            return None
        blockers.append(
            _blocker(
                probe.completeness,
                f"claim-specific evidence check failed: {support_reason}",
            )
        )
    if no_added:
        blockers.append(_blocker(CHECK_NO_ADDED_LINE, _NO_ADDED_REASON))
    if supported and not no_added:
        # The 1.3.0 accepted this candidate; the frontier is never
        # consulted for it (defensive: validate() only calls here
        # for rejected entries).
        return None
    return blockers or None


class AlmaGateV14:
    """Evidence validator 1.4.0: the 1.3.0 by delegation, plus the
    third state.  Class candidates are judged by an AlmaGateV13
    instance untouched; the frontier then re-examines its rejections.
    General-category candidates (v2.3) have no rule in this gate and
    are held when well-formed and anchored.  Everything else fails
    closed exactly as the 1.3.0 fails it."""

    version = POLICY_VERSION
    policy_sha256 = POLICY_SHA256

    def validate(
        self,
        candidates: list[Candidate],
        diff: DiffIndex,
        agent_name: str,
    ) -> GateResultV14:
        delegated = [
            candidate
            for candidate in candidates
            if candidate.claim_type not in GENERAL_CATEGORIES_V14
        ]
        v13_result = AlmaGateV13().validate(delegated, diff, agent_name)
        v13_entries = {
            id(candidate): entry
            for candidate, entry in zip(delegated, v13_result.ledger)
        }
        accepted_iter = iter(v13_result.findings)

        findings: list[dict] = []
        ledger: list[LedgerEntryV14] = []
        held: list[NeedsValidationRecord] = []

        for candidate in candidates:
            if candidate.claim_type in GENERAL_CATEGORIES_V14:
                outcome = self._validate_general(candidate, diff)
                if isinstance(outcome, NeedsValidationRecord):
                    held.append(outcome)
                else:
                    ledger.append(outcome)
                continue
            entry = v13_entries[id(candidate)]
            if entry.status == "accepted":
                findings.append(next(accepted_iter))
                ledger.append(_restamp(entry))
                continue
            blockers = None
            if candidate.claim_type in KNOWN_CLAIM_TYPES_V14:
                blockers = _frontier_blockers(candidate, entry, diff)
            if blockers:
                held.append(
                    NeedsValidationRecord(
                        rule_id=candidate.rule_id,
                        claim_type=candidate.claim_type,
                        file=candidate.file,
                        start_line=candidate.start_line,
                        end_line=candidate.end_line,
                        message=candidate.message,
                        evidence=_evidence_lines(entry),
                        producer=candidate.producer,
                        blockers=tuple(blockers),
                        validator_version=POLICY_VERSION,
                        policy_sha256=POLICY_SHA256,
                    )
                )
            else:
                ledger.append(_restamp(entry))

        return GateResultV14(
            findings=tuple(findings),
            ledger=tuple(ledger),
            needs_validation=tuple(held),
        )

    def _validate_general(
        self, candidate: Candidate, diff: DiffIndex
    ) -> LedgerEntryV14 | NeedsValidationRecord:
        """A general-category candidate: the pipeline's anchoring
        checks, mirrored from the 1.3.0, then the holding state —
        this gate has no verification rule for general categories
        and must not invent one."""

        reasons: list[str] = []
        evidence: list[EvidenceLineV14] = []
        actual_text: list[str] = []
        if candidate.start_line < 1 or candidate.end_line < candidate.start_line:
            reasons.append("invalid line range")
        for line_number in range(
            candidate.start_line, candidate.end_line + 1
        ):
            diff_line = diff.get_line(candidate.file, line_number)
            if diff_line is None:
                reasons.append(
                    f"cited line {candidate.file}:{line_number} "
                    "is not present in the diff"
                )
                continue
            actual_text.append(diff_line.text)
            evidence.append(
                EvidenceLineV14(
                    file=diff_line.file,
                    line=diff_line.line_number,
                    kind=diff_line.kind,
                    text=diff_line.text,
                )
            )
        if tuple(actual_text) != candidate.evidence_text:
            reasons.append(
                "stored evidence text does not exactly match the "
                "cited diff lines"
            )
        if reasons:
            return LedgerEntryV14(
                rule_id=candidate.rule_id,
                claim_type=candidate.claim_type,
                file=candidate.file,
                start_line=candidate.start_line,
                end_line=candidate.end_line,
                message=candidate.message,
                severity_hint=candidate.severity_hint,
                category_hint=candidate.category_hint,
                evidence=tuple(evidence),
                status="rejected",
                reasons=tuple(reasons),
                validator_version=POLICY_VERSION,
                policy_sha256=POLICY_SHA256,
            )
        blockers = [
            _blocker(
                CHECK_NO_RULE,
                "the gate defines no verification rule for general "
                f"category {candidate.claim_type!r}",
            )
        ]
        if not any(item.kind == "added" for item in evidence):
            blockers.append(
                _blocker(CHECK_NO_ADDED_LINE, _NO_ADDED_REASON)
            )
        return NeedsValidationRecord(
            rule_id=candidate.rule_id,
            claim_type=candidate.claim_type,
            file=candidate.file,
            start_line=candidate.start_line,
            end_line=candidate.end_line,
            message=candidate.message,
            evidence=tuple(evidence),
            producer=candidate.producer,
            blockers=tuple(blockers),
            validator_version=POLICY_VERSION,
            policy_sha256=POLICY_SHA256,
        )


__all__ = [
    "GENERAL_CATEGORIES_V14",
    "KNOWN_CLAIM_TYPES_V14",
    "POLICY_SHA256",
    "POLICY_VERSION",
    "AlmaGateV14",
    "GateResultV14",
    "LedgerEntryV14",
    "NeedsValidationRecord",
]
