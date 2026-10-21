"""Evidence gate 1.2.0 — the hardened successor of the 1.1.0, built
from the red team's battery, never by editing a frozen gate.

Provenance: PREREGISTRO-REVIEWBENCH-V2.md, Adenda 2 (2026-10-20, 00:22
EDT, written BEFORE any v2 run; Alejandro: «Hacelo ahora»), on the
measured finding of the structural-study red team
(``estudio-estructura-20261020/equipo-rojo.md``): 46 well-formed fake
findings were run against the 1.1.0 and 27 against the 1.0.0; **95.7%
and 96.3% were accepted**.  The classes checked the PRESENCE of
markers in the cited text without distinguishing code from
comments/docstrings, without requiring the citation to contain lines
the change actually added, and two classes (hardcoded_secret,
race_condition) had nearly vacuous rules.  The gates caught vagueness,
not well-formed lies.

The 1.0.0 (``agent/alma_gate.py``) and the 1.1.0
(``agent/alma_gate_v11.py``) are NOT touched: v1 and the intermediate
measurement stay reproducible byte-for-byte.  This gate inherits the
1.1.0's 14 classes (its claim descriptions are reused verbatim) and
applies the red team's minimal mechanical fixes — Adenda 2 (a)–(f):

(a) TOKENIZATION — before any support check, the cited evidence (and
    its surrounding diff block) is tokenized with the standard
    ``tokenize`` module and rebuilt in two views per line: a CODE view
    (comments and every string literal removed) and a CODE+STRINGS
    view (comments and statement-position strings — docstrings and
    bare text constants — removed; strings that are part of an
    expression, e.g. assigned literals, are kept, because legitimate
    SQL text and secret literals live inside them).  Each class checks
    the view its markers belong to: structural markers (verify=False,
    shell=True, pickle.loads(, except/pass, CERT_NONE…) are searched
    in the CODE view; sql_injection and hardcoded_secret, whose
    evidence lives inside literals, use the CODE+STRINGS view.
(b) NAME FILTER — hardcoded_secret applies the same credential-name
    check the base reviewer already used (``_SECRET_NAME_RE`` in
    ``agent/base_reviewer.py``): a quoted literal assigned to
    ``DEFAULT_REGION`` or ``BASE_URL`` is not a secret.  The red
    team's additional mitigation for its H3 residual is also applied:
    placeholder VALUES are extended with the prefixes ``test-``,
    ``fake-``, ``dummy-``, ``example-``.
(c) SHARED-STATE ASSIGNMENT — race_condition requires an assignment
    to shared state (``self.x = …`` / ``cls.x = …``, or an assignment
    to a name declared ``global``), not a bare ``self.`` mention.
(d) CO-OCCURRENCE — conjunctive classes need their markers related,
    not bag-of-lines: sql_injection requires a recognizable SQL
    skeleton (``SELECT … FROM`` / ``INSERT INTO`` / ``UPDATE … SET``
    / ``DELETE FROM``) AND an unsafe-construction marker on the SAME
    cited line; race_condition requires the concurrency marker and
    the shared-state assignment on the SAME cited line.
    The SQL skeleton is one notch tighter than the 1.0.0 keyword
    (which matched a bare ``SELECT``): the red team's S4 attack
    (``report = "SELECT summary: " + suffix`` — a label string, not a
    query) was assigned no family in the report, but it is the same
    defect shape as the bag-of-lines family and the skeleton kills
    it without touching any legitimate fixture: every real fixture
    query carries a full skeleton.
(e) ANTIDOTE IN THE WHOLE BLOCK — for classes with a known safe form,
    the antidote is searched in the whole diff BLOCK (the maximal
    run of consecutive head lines of the file's diff that contains
    the citation), not only in the cited range: ``SafeLoader``
    (unsafe_deserialization), ``.close(`` (resource_leak),
    ``defusedxml`` (unsafe_xml_parsing), and the handler body itself
    (silenced_bare_except / swallowed_exception: the body is read
    from the block, so a ``raise`` one line below the cited ``pass``
    defeats the claim).
(f) ADDED LINE — the cited evidence must contain at least one line
    the change ADDED (``kind == "added"``); citing only pre-existing
    context lines fails closed.

Plus the red report's per-class minimal rules for its families G/H:
weak_random_security excludes names ending in non-credential suffixes
(``_count``, ``_length``, ``_ttl``, ``_delay``, ``_size``, ``_limit``,
``_retries``); swallowed_exception excludes the idiomatic
``except ImportError`` / ``ModuleNotFoundError`` optional-dependency
fallback; insecure_tempfile requires the ``tempfile.`` receiver (or a
``from tempfile import mktemp`` in the block), so a project's own
``mktemp`` method is not the stdlib's insecure one; resource_leak's
bare ``connect(`` counts as opening a resource only with network /
socket context in the block (``socket``, ``ssl.``, ``http.client``,
``create_connection``), so a Qt signal ``.connect(...)`` is not a
leaked connection.

DECLARED RESIDUALS (from the red report and Adenda 2 — NOT fixed,
because no mechanical rule on cited lines can fix them):
- C3, dead code: an ``eval(`` under ``if False:`` is real text with
  the real pattern; defeating it needs reachability analysis.
- X2, input provenance: ``ET.parse(BUNDLED_CONSTANT)`` — the gate
  cannot know whether the parsed input is external or trusted; that
  is a data-flow question, already declared as a limit in Adenda 1.

TENSIONS found while implementing (recorded, per the build order;
none was forced):
- Race co-occurrence is same-line (the report's prescription).  A
  plausible legitimate shape — ``async def`` on one line and a
  ``self.x = …`` on the next — is therefore REJECTED.  The project's
  own v1.0/v1.1 unit pair for race_condition (``import threading`` /
  ``self.cache = {}``, markers on separate lines) diverges here by
  design; the real fixture (fixtures_v2/v2_08) satisfies same-line
  co-occurrence (``self.lock = threading.Lock()``) and stays
  accepted.  Cost: some true async-race citations need the lock/state
  line cited together with a concurrency marker.
- Block-level antidotes are block-granular: an unrelated ``.close(``
  for a DIFFERENT resource in the same diff block defeats a genuine
  resource_leak claim.  Accepted cost of fix (e) as prescribed.
- The ``connect(`` network-context heuristic fails closed the other
  way: a genuine socket leak in a file whose diff shows no socket
  context (e.g. the import predates the PR and is outside the diff)
  is rejected.
- If a diff block cannot be tokenized (a hunk cutting through a
  bracket or string in a way even the dedented retry cannot parse),
  the views degrade to a naive scanner (quote-aware comment
  stripping, triple-quote tracking; multi-line string contents are
  dropped from both views).  Every fixture and every red-team attack
  block tokenizes cleanly; the fallback exists so exotic hunks still
  get a deterministic answer instead of an exception.
- Multi-line SQL construction (skeleton on one line, concatenation
  on the next) fails the same-line co-occurrence rule and is
  rejected; citations must put skeleton and construction on one line.

Selection: run configuration ``RB_CONFIG_GATE=v12`` (default ``v1``);
see ``agent/main.py``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import io
import json
import re
import textwrap
import tokenize
from typing import NamedTuple

from .alma_gate import (
    _PLACEHOLDER_VALUES,
    _SECRET_LITERAL_RE,
    _UNSAFE_SQL_RE,
    candidate_to_finding,
)
from .alma_gate_v11 import (
    _ASSIGNMENT_RE as _ASSIGNMENT_RE_V11,
    _EXCEPT_TYPED_RE,
    _POLICY as _POLICY_V11,
    _RANDOM_CALL_RE,
    _SECURITY_NAME_RE as _SECURITY_NAME_RE_V11,
    _XML_STDLIB_RE,
    KNOWN_CLAIM_TYPES_V11,
)
from .base_reviewer import Candidate, _SECRET_NAME_RE
from .diff_parser import DiffIndex, DiffLine, FileDiff


POLICY_VERSION = "alma-evidence-gate/1.2.0"
_POLICY = {
    "version": POLICY_VERSION,
    "required_checks": [
        "candidate file and every cited line are present in the diff",
        "stored evidence text exactly equals the text at the cited head lines",
        "the cited evidence contains claim-specific support",
        "unknown claim types fail closed",
        "accepted findings are deduplicated by file, range, and message",
        "comments and statement-position strings are stripped from the evidence before the support check (assigned string contents are preserved)",
        "hardcoded_secret requires a credential-like variable name and a non-placeholder value",
        "race_condition requires a shared-state assignment co-occurring with a concurrency marker on one cited line",
        "sql_injection requires a SQL skeleton and an unsafe construction marker on the same cited line",
        "known safe forms (antidotes) are searched in the whole diff block, not only in the cited range",
        "at least one cited line must be a line added by the change",
    ],
    # The 14 claim classes of the 1.1.0, descriptions reused verbatim:
    # the 1.2.0 adds no class, it hardens the checks of the same 14.
    "claims": dict(_POLICY_V11["claims"]),
}
POLICY_SHA256 = hashlib.sha256(
    json.dumps(_POLICY, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

KNOWN_CLAIM_TYPES_V12 = KNOWN_CLAIM_TYPES_V11

# ---------------------------------------------------------------------------
# Evidence views (fix (a)): tokenize the diff block, rebuild each line as
# CODE (no comments, no string literals) and CODE+STRINGS (no comments,
# no statement-position strings; expression strings preserved).
# ---------------------------------------------------------------------------


class _LineView(NamedTuple):
    number: int
    kind: str
    raw: str
    code: str
    plus: str


def _contiguous_block(
    file_diff: FileDiff, start_line: int, end_line: int
) -> list[DiffLine]:
    """The maximal run of consecutive head lines containing the range."""

    low = start_line
    while low - 1 in file_diff.lines:
        low -= 1
    high = end_line
    while high + 1 in file_diff.lines:
        high += 1
    return [file_diff.lines[n] for n in range(low, high + 1)]


def _cut_spans(line: str, spans: list[tuple[int, int]]) -> str:
    """Remove the [start, end) column spans from a line."""

    if not spans:
        return line
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        start = max(0, min(start, len(line)))
        end = max(start, min(end, len(line)))
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    pieces: list[str] = []
    cursor = 0
    for start, end in merged:
        pieces.append(line[cursor:start])
        cursor = end
    pieces.append(line[cursor:])
    return "".join(pieces)


_STATEMENT_BOUNDARY_OPS = {";"}


def _spans_from_tokens(
    texts: list[str], source: str, shifts: list[int]
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]] | None:
    """Tokenize ``source`` (the block lines joined, possibly dedented).

    Returns (code_spans, plus_spans): per-line lists of column spans to
    remove, in ORIGINAL line coordinates.  ``shifts[row]`` maps a token
    column on the tokenized row back to the original line.  Returns
    None when the source does not tokenize."""

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return None

    code_spans: list[list[tuple[int, int]]] = [[] for _ in texts]
    plus_spans: list[list[tuple[int, int]]] = [[] for _ in texts]

    def add_span(
        target: list[list[tuple[int, int]]],
        srow: int,
        scol: int,
        erow: int,
        ecol: int,
    ) -> None:
        for row in range(srow, erow + 1):
            index = row - 1
            if index < 0 or index >= len(texts):
                continue
            line_len = len(texts[index])
            if row == srow == erow:
                span = (scol + shifts[index], ecol + shifts[index])
            elif row == srow:
                span = (scol + shifts[index], line_len)
            elif row == erow:
                span = (0, ecol + shifts[index])
            else:
                span = (0, line_len)
            target[index].append(span)

    prev_boundary = True  # start of input is a statement boundary
    fstring_start: tuple[int, int] | None = None
    fstring_depth = 0
    fstring_boundary = True

    for tok in tokens:
        ttype = tok.type
        if ttype == tokenize.COMMENT:
            row, col = tok.start
            if 1 <= row <= len(texts):
                span = (col + shifts[row - 1], len(texts[row - 1]))
                code_spans[row - 1].append(span)
                plus_spans[row - 1].append(span)
            continue
        if ttype in (tokenize.NL, tokenize.ENCODING):
            continue
        if ttype == tokenize.FSTRING_START:
            if fstring_depth == 0:
                fstring_start = tok.start
                fstring_boundary = prev_boundary
            fstring_depth += 1
            continue
        if ttype == tokenize.FSTRING_END:
            fstring_depth -= 1
            if fstring_depth == 0 and fstring_start is not None:
                (srow, scol), (erow, ecol) = fstring_start, tok.end
                add_span(code_spans, srow, scol, erow, ecol)
                if fstring_boundary:
                    add_span(plus_spans, srow, scol, erow, ecol)
                fstring_start = None
                prev_boundary = False
            continue
        if fstring_depth > 0:
            # FSTRING_MIDDLE and the tokens of replacement fields are
            # part of the f-string span already being tracked.
            continue
        if ttype == tokenize.STRING:
            (srow, scol), (erow, ecol) = tok.start, tok.end
            add_span(code_spans, srow, scol, erow, ecol)
            if prev_boundary:
                add_span(plus_spans, srow, scol, erow, ecol)
            prev_boundary = False
            continue
        if ttype == tokenize.NEWLINE:
            prev_boundary = True
        elif ttype in (tokenize.INDENT, tokenize.DEDENT):
            prev_boundary = True
        elif ttype == tokenize.OP and tok.string in _STATEMENT_BOUNDARY_OPS:
            prev_boundary = True
        elif ttype == tokenize.ENDMARKER:
            pass
        else:
            prev_boundary = False

    return (
        [tuple(spans) for spans in code_spans],
        [tuple(spans) for spans in plus_spans],
    )


_TRIPLE_QUOTES = ('"""', "'''")


def _fallback_views(texts: list[str]) -> list[tuple[str, str]]:
    """Naive scanner used only when a block does not tokenize: strip
    comments outside quotes and drop the contents of triple-quoted
    strings from both views (see the module docstring's tensions).
    Returns (code, plus) per line — in the fallback they coincide."""

    views: list[tuple[str, str]] = []
    open_triple: str | None = None
    for raw in texts:
        if open_triple is not None:
            if open_triple in raw:
                open_triple = None
            views.append(("", ""))
            continue
        # Find a comment start outside quotes on this line.
        cut = len(raw)
        quote: str | None = None
        i = 0
        while i < len(raw):
            ch = raw[i]
            if quote is not None:
                if ch == "\\":
                    i += 2
                    continue
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in ("'", '"'):
                if raw.startswith(_TRIPLE_QUOTES[0], i) or raw.startswith(
                    _TRIPLE_QUOTES[1], i
                ):
                    triple = raw[i : i + 3]
                    if raw.find(triple, i + 3) == -1:
                        open_triple = triple
                        cut = i
                    break
                quote = ch
                i += 1
                continue
            if ch == "#":
                cut = i
                break
            i += 1
        cleaned = raw[:cut]
        views.append((cleaned, cleaned))
    return views


def _build_views(block: list[DiffLine]) -> list[_LineView]:
    texts = [line.text for line in block]
    source = "\n".join(texts) + "\n"
    built = _spans_from_tokens(texts, source, [0] * len(texts))
    if built is None:
        dedented = textwrap.dedent(source)
        ded_lines = dedented.split("\n")[: len(texts)]
        if len(ded_lines) == len(texts):
            shifts = [
                max(0, len(texts[i]) - len(ded_lines[i])) for i in range(len(texts))
            ]
            built = _spans_from_tokens(texts, dedented, shifts)
    if built is None:
        fallback = _fallback_views(texts)
        return [
            _LineView(
                number=dl.line_number,
                kind=dl.kind,
                raw=dl.text,
                code=code,
                plus=plus,
            )
            for dl, (code, plus) in zip(block, fallback)
        ]
    code_spans, plus_spans = built
    return [
        _LineView(
            number=dl.line_number,
            kind=dl.kind,
            raw=dl.text,
            code=_cut_spans(dl.text, list(code_spans[i])),
            plus=_cut_spans(dl.text, list(plus_spans[i])),
        )
        for i, dl in enumerate(block)
    ]


# ---------------------------------------------------------------------------
# Claim support checks on the tokenized views.
# ---------------------------------------------------------------------------

_SQL_SKELETON_RE = re.compile(
    r"(?:\bSELECT\b[^\"']*?\bFROM\b"
    r"|\bINSERT\s+INTO\b"
    r"|\bUPDATE\b[^\"']*?\bSET\b"
    r"|\bDELETE\s+FROM\b)",
    re.I,
)
_PLACEHOLDER_PREFIXES = ("test-", "fake-", "dummy-", "example-")

_CONCURRENCY_RE = re.compile(
    r"\b(threading|multiprocessing|concurrent|async|await|Lock\s*\()"
)
_SHARED_ASSIGN_RE = re.compile(r"\b(?:self|cls)\.[A-Za-z_]\w*\s*[+\-*/%]?=(?!=)")
_GLOBAL_DECL_RE = re.compile(r"\bglobal\s+([A-Za-z_]\w*)")

_NONCREDENTIAL_SUFFIXES = (
    "_count",
    "_length",
    "_ttl",
    "_delay",
    "_size",
    "_limit",
    "_retries",
)
_IDIOMATIC_FALLBACK_RE = re.compile(r"\b(ImportError|ModuleNotFoundError)\b")

_RESOURCE_OPEN_RE = re.compile(
    r"(?P<open>\bopen\s*\()"
    r"|(?P<conn>\bconnect\s*\()"
    r"|(?P<sock>\bsocket\s*\()"
    r"|(?P<cc>create_connection\s*\()"
)
_NETWORK_CONTEXT_RE = re.compile(
    r"\bsocket\b|create_connection|\bssl\s*\.|http\.client"
)
_MKTEMP_RECEIVER_RE = re.compile(r"\btempfile\s*\.\s*mktemp\s*\(")
_MKTEMP_BARE_RE = re.compile(r"\bmktemp\s*\(")
_FROM_TEMPLE_IMPORT_RE = re.compile(
    r"\bfrom\s+tempfile\s+import\s+[^\n#]*\bmktemp\b"
)


def _block_code_text(block: list[_LineView]) -> str:
    return "\n".join(view.code for view in block)


def _handler_body(
    block: list[_LineView], except_number: int
) -> list[tuple[int, str]] | None:
    """The handler body read from the whole block (fix (e)): the
    non-blank CODE lines after ``except_number`` that are more
    indented than the except line, up to the first dedent.  Returns
    [(line_number, stripped_code)], or None if the except line is not
    in the block."""

    anchor = next((v for v in block if v.number == except_number), None)
    if anchor is None:
        return None
    indent = len(anchor.raw) - len(anchor.raw.lstrip())
    body: list[tuple[int, str]] = []
    for view in block:
        if view.number <= except_number:
            continue
        if not view.code.strip():
            # Blank lines and comment-only lines are not body
            # statements and do not end the handler's block.
            continue
        line_indent = len(view.raw) - len(view.raw.lstrip())
        if line_indent <= indent:
            break
        body.append((view.number, view.code.strip()))
    return body


def _sql_support(cited: list[_LineView]) -> tuple[bool, str]:
    for view in cited:
        if _SQL_SKELETON_RE.search(view.plus) and _UNSAFE_SQL_RE.search(view.plus):
            return True, (
                "a SQL skeleton and an unsafe construction marker "
                "co-occur on one cited line"
            )
    return False, (
        "a SQL skeleton (SELECT..FROM, INSERT INTO, UPDATE..SET, "
        "DELETE FROM) and an unsafe construction marker must co-occur "
        "on the same cited line"
    )


def _secret_support(cited: list[_LineView]) -> tuple[bool, str]:
    for view in cited:
        match = _SECRET_LITERAL_RE.match(view.plus)
        if not match:
            continue
        name_part = view.plus.split("=", 1)[0]
        if not _SECRET_NAME_RE.search(name_part):
            return False, (
                "the assigned name is not credential-like; a literal "
                "assigned to a non-credential name is not a hardcoded "
                "secret"
            )
        value = match.group("value").strip().lower()
        if (
            value in _PLACEHOLDER_VALUES
            or value.startswith(_PLACEHOLDER_PREFIXES)
            or value.startswith("${")
            or value.startswith("os.")
        ):
            return False, (
                "placeholder and environment-derived values are not "
                "hardcoded secrets"
            )
        return True, (
            "a credential-like name is assigned to a non-placeholder "
            "literal"
        )
    return False, "a credential assignment to a quoted literal is required"


def _silenced_support(
    cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    cited_numbers = {view.number for view in cited}
    for view in cited:
        if view.code.strip() != "except:":
            continue
        body = _handler_body(block, view.number)
        if body is None or len(body) != 1 or body[0][1] != "pass":
            return False, (
                "the bare except handler's body in the diff block is "
                "not exactly one pass (it handles, re-raises, or is "
                "not shown)"
            )
        if body[0][0] not in cited_numbers:
            return False, "the pass body line must be cited"
        return True, "a bare except whose whole handler body is a cited pass"
    return False, "a bare except and a pass handler are both required"


def _swallowed_support(
    cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    cited_numbers = {view.number for view in cited}
    for view in cited:
        if not _EXCEPT_TYPED_RE.match(view.code.strip()):
            continue
        if _IDIOMATIC_FALLBACK_RE.search(view.code):
            return False, (
                "an except ImportError/ModuleNotFoundError with a "
                "pass body is the idiomatic optional-dependency "
                "fallback, not a swallowed error"
            )
        body = _handler_body(block, view.number)
        if body is None or len(body) != 1 or body[0][1] != "pass":
            return False, (
                "the typed except handler's body in the diff block "
                "is not exactly one pass (it handles the error, "
                "re-raises, or the body is not shown)"
            )
        if body[0][0] not in cited_numbers:
            return False, (
                "the pass body must be cited (an except line alone "
                "is not evidence of swallowing)"
            )
        after = [
            item.code.strip()
            for item in cited
            if item.number > view.number and item.code.strip()
        ]
        if after != ["pass"]:
            return False, "the cited body of the handler is not only pass"
        return True, "typed except handler whose whole body is only pass"
    return False, "a typed except handler (except SomeError:) is required"


def _race_support(cited: list[_LineView]) -> tuple[bool, str]:
    cited_code = [view.code for view in cited]
    for line in cited_code:
        if _CONCURRENCY_RE.search(line) and _SHARED_ASSIGN_RE.search(line):
            return True, (
                "a concurrency marker and a shared-state assignment "
                "co-occur on one cited line"
            )
    # Fallback shape: a `global` declaration plus an assignment to the
    # declared name, with a concurrency marker in the citation.
    joined = "\n".join(cited_code)
    decl = _GLOBAL_DECL_RE.search(joined)
    if decl and _CONCURRENCY_RE.search(joined):
        name = re.escape(decl.group(1))
        if re.search(rf"^\s*{name}\s*[+\-*/%]?=(?!=)", joined, re.M):
            return True, (
                "a concurrency marker with an assignment to a "
                "global-declared shared name"
            )
    return False, (
        "a concurrency marker and a shared-state assignment "
        "(self.x = ...) must co-occur on the same cited line"
    )


def _resource_leak_support(
    cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    block_code = _block_code_text(block)
    opener_found = False
    for view in cited:
        for match in _RESOURCE_OPEN_RE.finditer(view.code):
            kind = match.lastgroup
            if kind == "conn" and not _NETWORK_CONTEXT_RE.search(block_code):
                # A bare .connect( with no network/socket context in
                # the block is a signal/slot-style call, not a
                # resource opening (red report, family H).
                continue
            stripped = view.code.strip()
            if stripped.startswith("with ") or stripped.startswith("async with "):
                # This opener is managed by its with statement.
                continue
            opener_found = True
    if not opener_found:
        return False, (
            "an opened resource (open(, a socket, a network "
            "connection) outside a with statement is required"
        )
    if ".close(" in block_code:
        return False, (
            "the resource is closed (.close() present in the diff block)"
        )
    return True, (
        "resource opened without with and without .close() in the "
        "diff block"
    )


def _deserialization_support(
    cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    cited_code = "\n".join(view.code for view in cited)
    if "pickle.loads(" in cited_code:
        return True, "an unsafe deserialization call is required"
    if "yaml.load(" in cited_code:
        if "SafeLoader" in _block_code_text(block):
            return False, (
                "yaml.load uses SafeLoader in the diff block (the "
                "safe form is present outside the cited range)"
            )
        return True, "an unsafe deserialization call is required"
    return False, "an unsafe deserialization call is required"


def _xml_support(
    cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    cited_code = "\n".join(view.code for view in cited)
    if not _XML_STDLIB_RE.search(cited_code):
        return False, (
            "standard-library XML parsing (ET.parse/fromstring, "
            "xml.dom, xml.sax) is required"
        )
    if "defusedxml" in _block_code_text(block):
        return False, "defusedxml is present in the diff block"
    return True, "standard-library XML parsing without defusedxml"


def _tempfile_support(
    cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    cited_code = "\n".join(view.code for view in cited)
    if _MKTEMP_RECEIVER_RE.search(cited_code):
        return True, "tempfile.mktemp( is required"
    if _MKTEMP_BARE_RE.search(cited_code) and _FROM_TEMPLE_IMPORT_RE.search(
        _block_code_text(block)
    ):
        return True, "tempfile.mktemp( is required"
    return False, (
        "tempfile.mktemp( is required (a same-named method of another "
        "class is not the stdlib's insecure mktemp)"
    )


def _weak_random_support(cited: list[_LineView]) -> tuple[bool, str]:
    for view in cited:
        match = _ASSIGNMENT_RE_V11.match(view.code)
        if not match:
            continue
        name, value = match.group(1), match.group(2)
        if not (
            _SECURITY_NAME_RE_V11.search(name) and _RANDOM_CALL_RE.search(value)
        ):
            continue
        if name.lower().endswith(_NONCREDENTIAL_SUFFIXES):
            return False, (
                "the security-word name denotes a non-credential "
                "quantity (count/ttl/delay/size/limit/retries), not a "
                "generated credential"
            )
        return True, (
            "a security-named value is generated with the random module"
        )
    return False, (
        "assignment of a random-module value to a security name "
        "(token, secret, password, otp, session, api_key) is required"
    )


def _claim_support_v12(
    claim_type: str, cited: list[_LineView], block: list[_LineView]
) -> tuple[bool, str]:
    """Support check for the 1.2.0: the 14 classes of the 1.1.0, with
    the red team's hardening (Adenda 2) applied on the tokenized
    views."""

    cited_code = "\n".join(view.code for view in cited)

    if claim_type == "sql_injection":
        return _sql_support(cited)

    if claim_type == "hardcoded_secret":
        return _secret_support(cited)

    if claim_type == "tls_verification_disabled":
        supported = bool(re.search(r"\bverify\s*=\s*False\b", cited_code))
        return supported, "verify=False is required"

    if claim_type == "silenced_bare_except":
        return _silenced_support(cited, block)

    if claim_type == "mutable_default":
        supported = bool(
            re.search(r"\bdef\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\(\))", cited_code)
        )
        return supported, "a mutable function default is required"

    if claim_type == "command_execution":
        supported = bool(
            "os.system(" in cited_code
            or re.search(r"\b(?:eval|exec)\s*\(", cited_code)
            or "shell=True" in cited_code
        )
        return supported, "a shell or dynamic execution marker is required"

    if claim_type == "unsafe_deserialization":
        return _deserialization_support(cited, block)

    if claim_type == "race_condition":
        return _race_support(cited)

    if claim_type == "resource_leak":
        return _resource_leak_support(cited, block)

    if claim_type == "swallowed_exception":
        return _swallowed_support(cited, block)

    if claim_type == "unsafe_xml_parsing":
        return _xml_support(cited, block)

    if claim_type == "insecure_tempfile":
        return _tempfile_support(cited, block)

    if claim_type == "ssl_context_unverified":
        supported = "_create_unverified_context" in cited_code or bool(
            re.search(r"\bCERT_NONE\b", cited_code)
        )
        return supported, "ssl._create_unverified_context or CERT_NONE is required"

    if claim_type == "weak_random_security":
        return _weak_random_support(cited)

    return False, f"unknown claim type {claim_type!r}; failing closed"



@dataclass
class LedgerEntryV12:
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
class GateResultV12:
    findings: list[dict[str, object]]
    ledger: list[LedgerEntryV12]


_FAILURE_MARKERS = (
    "invalid line range",
    "not present in the diff",
    "does not exactly match",
    "evidence check failed",
    "no line added by this change",
)


class AlmaGateV12:
    """Evidence validator 1.2.0: the 1.1.0's 14 classes with the red
    team's hardening (Adenda 2 of the v2 pre-registration).  Same
    discipline as its predecessors — a rule name or confident message
    is not evidence — plus the distinctions the red team showed were
    missing: the evidence must be CODE (not comments or docstrings),
    its markers must be RELATED (co-occurrence, real handler bodies),
    its antidotes are searched in the whole diff block, and the
    defect must be one this change INTRODUCES (at least one cited
    line added by the change)."""

    version = POLICY_VERSION
    policy_sha256 = POLICY_SHA256

    def validate(
        self,
        candidates: list[Candidate],
        diff: DiffIndex,
        agent_name: str,
    ) -> GateResultV12:
        findings: list[dict[str, object]] = []
        ledger: list[LedgerEntryV12] = []
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
                # Fix (f): the defect must be introduced by THIS
                # change; a citation of pure context proves nothing
                # about the PR.
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
                supported, support_reason = _claim_support_v12(
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
                LedgerEntryV12(
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

        return GateResultV12(findings=findings, ledger=ledger)


__all__ = [
    "KNOWN_CLAIM_TYPES_V12",
    "POLICY_SHA256",
    "POLICY_VERSION",
    "AlmaGateV12",
    "GateResultV12",
    "LedgerEntryV12",
    "candidate_to_finding",
]
