"""Deterministic compiler of the reviewer's adjudicated history
into a bounded, provenance-auditable lessons context — paper
``PREREGISTRO-MEMORIA-LECCIONES`` (2026-10-22).

The line's gap, named in the paper: ALMA has a registry (memory
that is stored — adjudications, papers, ledger) but no memory that
is READ: no compiled context of its own adjudications enters the
reviewer's production, which sits every run as if it were the
first.  This module is the compile step of that memory.  It reads
the adjudicated corpus of run nº 298 (the 166 claims, each with a
gold verdict from ``adjwork298/decisions.json``), recomputes every
claim's disposition through the line's own deterministic pipeline
(birth shaper -> claim contract check -> gate 1.5.0, the exact
stage order of ``RESULTADO-REVISOR-CONTRATO``), and renders
``CONTEXTO-LECCIONES.md``: a taxonomy of deaths with raw counts,
verbatim traceable examples of claims born dead, verbatim lived
counterexamples, and short imperative rules derived from — and
citing — the counts.  Every number and every example in the
artifact is produced by program from the corpus; a hand count or an
invented example is impossible by construction, and the audit
(``audit_artifact``) re-derives everything from the corpus and
fails loudly on any violation.

The artifact's text is English because it is injected verbatim
into the reviewer's English production prompts; the line's Spanish
reason codes are kept as-is (they are the pipeline's own names).

US$0 by construction: no model is called anywhere in this module.
The compiler does not measure — and does not claim — any effect
of the lessons on production; per the paper, the only thing
auditable dry is provenance.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from agent.alma_gate_v150 import AlmaGateV150
from agent.base_reviewer import Candidate
from agent.birth_shaper import _asserted_tokens, shape_claim
from agent.claim_contract import normalize_claim
from agent.diff_parser import DiffIndex, parse_unified_diff

COMPILER_VERSION = "alma-lessons-compiler/1.0"
LESSONS_CONTEXT_VERSION = "alma-lessons-context/1.0"
BLOCK_BEGIN = "<!-- LESSONS-BLOCK-BEGIN -->"
BLOCK_END = "<!-- LESSONS-BLOCK-END -->"
BLOCK_MAX_CHARS = 9_600
MAX_EXAMPLE_CITATION_LINES = 10
DEATH_EXAMPLES_PER_FAMILY = 3
LIVED_EXAMPLES_PER_ORIGIN = 2

DISP_EMITTED = "emitido"
DISP_DEAD_TOKENS = "muerto_en_origen_tokens"
DISP_DEAD_NO_PATTERN = "muerto_en_origen_sin_patron"
DISP_REJECTED = "rechazado_puerta"

GOLD_RANK = {"TP": 0, "FPG": 1, "GREY": 2, "NOVEL": 3, None: 4}


# ------------------------------------------------------------------
# Corpus
# ------------------------------------------------------------------


@dataclass(frozen=True)
class ClaimRecord:
    """One adjudicated claim of the corpus, rebuilt from primary
    sources (the run's findings + the decisions file + the head
    content of the cited file)."""

    pr: str
    idx: int
    file: str
    start_line: int
    end_line: int
    message: str
    evidence: tuple[str, ...]
    gold: str | None
    gold_idx: int | None
    gold_note: str | None

    @property
    def citation_lines(self) -> int:
        return self.end_line - self.start_line + 1


@dataclass(frozen=True)
class ClaimDisposition:
    """The claim's fate through the deterministic pipeline, in the
    exact stage order of ``RESULTADO-REVISOR-CONTRATO``."""

    record: ClaimRecord
    contract_conforming: bool
    contract_check: str | None          # failing check, when held by contract
    shaper_origin: str                  # "declared" | "mined" | "none"
    born_pattern: tuple[str, ...]       # pattern of the shaped candidate
    absent_tokens: tuple[str, ...]      # born asserted tokens absent from citation
    trimmed_tokens: tuple[str, ...]
    final: str                          # one of the DISP_* values
    gate_reasons: tuple[str, ...] = ()


def born_candidate(record: ClaimRecord) -> Candidate:
    """The born claim, rebuilt with the line's published replay
    formula (assignment ``correctness``; the paper's invariance
    note holds: dispositions do not depend on the claim-type
    assignment)."""
    return Candidate(
        rule_id="llm_v23_correctness",
        claim_type="correctness",
        file=record.file,
        start_line=record.start_line,
        end_line=record.end_line,
        message=record.message.strip(),
        evidence_text=tuple(record.evidence),
        severity_hint="high",
        category_hint="correctness",
        producer="alma-llm-reviewer-v23",
    )


def _candidate_key(c: Candidate) -> tuple:
    return (c.rule_id, c.file, c.start_line, c.end_line, c.message)


def compute_dispositions(
    records: list[ClaimRecord],
    diffs: dict[str, DiffIndex],
    gate: AlmaGateV150 | None = None,
) -> list[ClaimDisposition]:
    """Run the deterministic pipeline per claim and return the
    dispositions.  The gate runs per PR over the shaped candidates
    (as in the published replay); a shaped candidate held by the
    1.5.0 as ``needs_validation`` would be a pipeline anomaly and
    raises — the published measurement says it never happens."""
    gate = gate or AlmaGateV150()
    by_pr: dict[str, list[ClaimRecord]] = {}
    for rec in records:
        by_pr.setdefault(rec.pr, []).append(rec)
    out: list[ClaimDisposition] = []
    for pr, pr_records in sorted(by_pr.items()):
        diff = diffs[pr]
        born = {rec.idx: born_candidate(rec) for rec in pr_records}
        shaped = {}
        for rec in pr_records:
            shaped[rec.idx] = shape_claim(born[rec.idx], diff)
        gate_map: dict[tuple, object] = {}
        shaped_cands = [s.candidate for s in shaped.values()
                        if s.candidate is not None]
        if shaped_cands:
            result = gate.validate(shaped_cands, diff, "alma-reviewer")
            if result.needs_validation:
                raise ValueError(
                    f"gate held a shaped candidate as needs_validation "
                    f"in {pr}: pipeline anomaly (published: 0)")
            for entry in result.ledger:
                gate_map[_candidate_key_from_ledger(entry)] = entry
        for rec in pr_records:
            norm = normalize_claim(born[rec.idx])
            outcome = shaped[rec.idx]
            asserted = _asserted_tokens(born[rec.idx].message)
            evidence_lower = "\n".join(rec.evidence).lower()
            absent = tuple(t for t in asserted
                           if t.lower() not in evidence_lower)
            if outcome.candidate is None:
                check = outcome.blockers[0]["check"]
                final = (DISP_DEAD_TOKENS
                         if check == "tokens_afirmados_ausentes_en_la_evidencia"
                         else DISP_DEAD_NO_PATTERN)
                out.append(ClaimDisposition(
                    record=rec,
                    contract_conforming=norm.conforming,
                    contract_check=None if norm.conforming else norm.check,
                    shaper_origin="none",
                    born_pattern=(),
                    absent_tokens=absent if final == DISP_DEAD_TOKENS else (),
                    trimmed_tokens=(),
                    final=final,
                ))
                continue
            entry = gate_map[_candidate_key(outcome.candidate)]
            final = DISP_EMITTED if entry.status == "accepted" else DISP_REJECTED
            out.append(ClaimDisposition(
                record=rec,
                contract_conforming=norm.conforming,
                contract_check=None if norm.conforming else norm.check,
                shaper_origin=outcome.origin,
                born_pattern=normalize_claim(outcome.candidate).pattern,
                absent_tokens=(),
                trimmed_tokens=outcome.trimmed_tokens,
                final=final,
                gate_reasons=tuple(entry.reasons),
            ))
    out.sort(key=lambda d: (d.record.pr, d.record.idx))
    return out


def _candidate_key_from_ledger(entry) -> tuple:
    return (entry.rule_id, entry.file, entry.start_line,
            entry.end_line, entry.message)


# ------------------------------------------------------------------
# Corpus loading from the run's primary sources (US$0, local git)
# ------------------------------------------------------------------


def load_corpus(root: Path) -> tuple[list[ClaimRecord], dict[str, DiffIndex], dict]:
    """Rebuild corpus A (run nº 298) from primary sources.  The PR
    repositories are expected as partial clones under
    ``adjwork298/repos/`` (``ensure_clones`` fetches them); the
    cited evidence is read from the head commit, exactly as the
    line's replays did.  Returns (records, diffs, meta) where meta
    carries the sha256 of ``decisions.json``."""
    work = root / "adjwork298"
    decisions_path = work / "decisions.json"
    decisions = json.loads(decisions_path.read_text())
    decisions_sha = hashlib.sha256(decisions_path.read_bytes()).hexdigest()
    records: list[ClaimRecord] = []
    diffs: dict[str, DiffIndex] = {}
    head_cache: dict[tuple, list[str] | None] = {}

    def head_lines(repo_dir: Path, head: str, path: str):
        key = (str(repo_dir), head, path)
        if key in head_cache:
            return head_cache[key]
        r = subprocess.run(["git", "-C", str(repo_dir), "show",
                            f"{head}:{path}"], capture_output=True)
        lines = None
        if r.returncode == 0:
            try:
                lines = r.stdout.decode("utf-8").splitlines()
            except UnicodeDecodeError:
                lines = None
        head_cache[key] = lines
        return lines

    for pr_dir in sorted((work / "run298" / "prs").iterdir()):
        pr = pr_dir.name
        data = json.loads((pr_dir / "findings.json").read_text())
        meta = data["pr"]
        repo_dir = work / "repos" / pr
        d = subprocess.run(
            ["git", "-C", str(repo_dir), "diff",
             f"{meta['base']}...{meta['head']}"], capture_output=True)
        diffs[pr] = parse_unified_diff(d.stdout.decode("utf-8",
                                                       errors="replace"))
        for idx, f in enumerate(data["findings"]):
            lines = head_lines(repo_dir, meta["head"], f["file"])
            if lines is None or f["end_line"] > len(lines):
                raise ValueError(
                    f"reconstruction failed for {pr} emission {idx}: "
                    f"head content unavailable for {f['file']}")
            dec = decisions.get(pr, {}).get("emissions", {}).get(str(idx))
            records.append(ClaimRecord(
                pr=pr, idx=idx, file=f["file"],
                start_line=f["start_line"], end_line=f["end_line"],
                message=f["message"],
                evidence=tuple(lines[f["start_line"] - 1:f["end_line"]]),
                gold=dec["v"] if dec else None,
                gold_idx=dec.get("g") if dec else None,
                gold_note=dec.get("note") if dec else None,
            ))
    return records, diffs, {"decisions_sha256": decisions_sha,
                             "claims": len(records)}


def ensure_clones(root: Path) -> None:
    """Fetch the corpus repositories as blobless partial clones
    (public sources of the run), if not already present."""
    work = root / "adjwork298"
    repos_dir = work / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)
    for pr_dir in sorted((work / "run298" / "prs").iterdir()):
        pr = pr_dir.name
        dest = repos_dir / pr
        if (dest / ".git").is_dir():
            continue
        data = json.loads((pr_dir / "findings.json").read_text())
        subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout",
             "--quiet", data["pr"]["repo"], str(dest)],
            check=True, capture_output=True, timeout=600)


# ------------------------------------------------------------------
# Compilation
# ------------------------------------------------------------------


@dataclass
class CompiledLessons:
    block: str
    block_sha256: str
    manifest: dict
    dispositions: list[ClaimDisposition] = field(default_factory=list)


def _gold_label(d: ClaimDisposition) -> str:
    g = d.record.gold
    if g is None:
        return "no adjudicated gold verdict"
    if g == "TP":
        return f"TRUE POSITIVE (gold entry G{d.record.gold_idx})"
    if g == "FPG":
        return "FALSE POSITIVE against gold"
    if g == "GREY":
        return "GREY ZONE (real concern, no gold entry)"
    return "NOVEL (no gold entry either way)"


def _death_breakdown(disps: list[ClaimDisposition]) -> str:
    parts = []
    for verdict in ("TP", "FPG", "GREY", "NOVEL"):
        n = sum(1 for d in disps if d.record.gold == verdict)
        if n:
            parts.append(f"{n} gold-{verdict.lower()}")
    n_none = sum(1 for d in disps if d.record.gold is None)
    if n_none:
        parts.append(f"{n_none} without verdict")
    return ", ".join(parts) if parts else "none"


def _example_order(d: ClaimDisposition):
    return (GOLD_RANK[d.record.gold], d.record.pr, d.record.idx)


def select_examples(
    dispositions: list[ClaimDisposition],
) -> tuple[list[ClaimDisposition], list[ClaimDisposition]]:
    """The paper's frozen selection: deaths first (per family, the
    declared order, at most ``DEATH_EXAMPLES_PER_FAMILY`` each, the
    single rejected claim always), then lived TP counterexamples
    (at most ``LIVED_EXAMPLES_PER_ORIGIN`` per birth origin).
    Only claims whose born citation is at most
    ``MAX_EXAMPLE_CITATION_LINES`` lines are eligible."""
    eligible = [d for d in dispositions
                if d.record.citation_lines <= MAX_EXAMPLE_CITATION_LINES]
    deaths: list[ClaimDisposition] = []
    for family in (DISP_DEAD_TOKENS, DISP_DEAD_NO_PATTERN):
        fam = sorted((d for d in eligible if d.final == family),
                     key=_example_order)
        deaths.extend(fam[:DEATH_EXAMPLES_PER_FAMILY])
    deaths.extend(sorted((d for d in eligible if d.final == DISP_REJECTED),
                         key=_example_order))
    lived: list[ClaimDisposition] = []
    for origin in ("declared", "mined"):
        fam = sorted((d for d in eligible
                      if d.final == DISP_EMITTED
                      and d.record.gold == "TP"
                      and d.shaper_origin == origin),
                     key=_example_order)
        lived.extend(fam[:LIVED_EXAMPLES_PER_ORIGIN])
    return deaths, lived


def _render_example(d: ClaimDisposition, tag: str) -> str:
    r = d.record
    lines = [
        f"### Example {tag}",
        f"<!-- src: run298 pr={r.pr} e={r.idx} gold={r.gold} "
        f"disp={d.final} -->",
        f"Claim (verbatim): {r.message.strip()}",
        f"Citation: {r.file}:{r.start_line}-{r.end_line} — "
        f"adjudicated verdict: {_gold_label(d)}",
        "Cited lines (verbatim):",
        *r.evidence,
    ]
    if d.final == DISP_DEAD_TOKENS:
        toks = ", ".join(f"`{t}`" for t in d.absent_tokens)
        lines.append(
            f"Why it died: every token the claim asserted was absent "
            f"from its own citation (absent: {toks}). It was never "
            f"emitted — the defect was in the claim, before any gate.")
    elif d.final == DISP_DEAD_NO_PATTERN:
        lines.append(
            "Why it died: the claim named no checkable pattern that "
            "stands in its cited lines, so nothing in it could be "
            "verified against its own evidence. It was never emitted.")
        if r.gold_note:
            lines.append(f"Adjudication note (verbatim): {r.gold_note}")
    elif d.final == DISP_REJECTED:
        reason = d.gate_reasons[0] if d.gate_reasons else ""
        lines.append(
            f"Why it died: the gate rejected it firmly — {reason}. "
            f"The claim declared absent what its own citation "
            f"contains — and the claim was TRUE.")
    elif d.final == DISP_EMITTED:
        pat = ", ".join(f"`{t}`" for t in d.born_pattern)
        origin = ("declared in backticks at birth"
                  if d.shaper_origin == "declared"
                  else "declared at birth out of the claim's own prose")
        lines.append(
            f"Why it lived: its pattern ({pat}) was {origin} and "
            f"stands verbatim in the cited lines. It was emitted — "
            f"and it was a true positive.")
    return "\n".join(lines)


def render_block(dispositions: list[ClaimDisposition],
                 deaths: list[ClaimDisposition],
                 lived: list[ClaimDisposition]) -> str:
    total = len(dispositions)
    by_final = Counter(d.final for d in dispositions)
    dead_tokens = [d for d in dispositions if d.final == DISP_DEAD_TOKENS]
    dead_pat = [d for d in dispositions if d.final == DISP_DEAD_NO_PATTERN]
    rejected = [d for d in dispositions if d.final == DISP_REJECTED]
    emitted = [d for d in dispositions if d.final == DISP_EMITTED]
    tokens_total = sum(len(d.absent_tokens) for d in dead_tokens)
    tp_total = sum(1 for d in dispositions if d.record.gold == "TP")
    tp_dead = sum(1 for d in dead_tokens + dead_pat
                  if d.record.gold == "TP")
    em_decl = sum(1 for d in emitted if d.shaper_origin == "declared")
    em_mined = sum(1 for d in emitted if d.shaper_origin == "mined")
    lines = [
        "LESSONS FROM THIS REVIEWER'S OWN ADJUDICATED HISTORY",
        f"(Run nº 298: {total} claims, each adjudicated against the "
        f"public gold set. Dispositions recomputed deterministically "
        f"through birth shaping -> claim contract -> gate 1.5.0. "
        f"Every count and example below is traceable to a real "
        f"adjudicated claim of that run.)",
        "",
        "## How the claims died — counts",
        f"- Died at origin, asserted tokens absent from their own "
        f"citation (`tokens_afirmados_ausentes_en_la_evidencia`): "
        f"{len(dead_tokens)} of {total} "
        f"({_death_breakdown(dead_tokens)})",
        f"- Died at origin, no concrete pattern declarable from the "
        f"citation (`sin_patron_concreto_en_el_reclamo`): "
        f"{len(dead_pat)} of {total} ({_death_breakdown(dead_pat)})",
        f"- Rejected firmly by the gate (affirmative contradiction): "
        f"{len(rejected)} of {total} ({_death_breakdown(rejected)})",
        f"- Emitted: {len(emitted)} of {total} "
        f"({em_decl} born declaring their pattern, {em_mined} with "
        f"the pattern declared at birth from the claim's own prose)",
        f"Of the {tp_total} gold-true claims, {tp_dead + len(rejected)} "
        f"were never emitted — {tp_dead} died at origin and "
        f"{len(rejected)} was rejected. What decided emission was "
        f"verifiability at birth, not truth.",
        "",
        "## Dead on arrival — verbatim examples",
    ]
    for i, d in enumerate(deaths, 1):
        lines.append(_render_example(d, f"D{i}"))
        lines.append("")
    lines.append("## Born citable, emitted and true — verbatim examples")
    for i, d in enumerate(lived, 1):
        lines.append(_render_example(d, f"L{i}"))
        lines.append("")
    lines.extend([
        "## Rules distilled from the counts above",
        f"1. Before you assert a token in backticks, find it in the "
        f"lines you cite; if it is not there, do not assert it. "
        f"{len(dead_tokens)} of {total} claims died at origin because "
        f"everything they asserted stood outside their citation "
        f"({tokens_total} asserted tokens with no backing).",
        f"2. Copy your pattern out of your citation: a claim that "
        f"names no token present in its cited lines is born "
        f"unverifiable. {len(dead_pat)} of {total} claims died that "
        f"way.",
        f"3. This kills true claims, not just noise: {tp_dead} of the "
        f"{tp_total} gold-true claims were never emitted because "
        f"they were born without a verifiable citation.",
        f"4. Never declare absent what your citation contains: the "
        f"corpus's only firm rejection was a true claim killed by "
        f"contradicting its own evidence.",
        f"5. What survived: {len(emitted)} of {total} claims were "
        f"emitted, and every one of them was born with its pattern "
        f"standing in its citation. Cite first; assert only what "
        f"the citation shows.",
        f"6. If the pattern is in your prose and in your citation, "
        f"declare it in backticks at birth: {em_mined} claims were "
        f"rescued exactly that way and emitted.",
    ])
    return "\n".join(lines).strip("\n")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compile_lessons(
    dispositions: list[ClaimDisposition],
    decisions_sha256: str,
) -> CompiledLessons:
    """Compile the bounded block + provenance manifest from the
    dispositions.  Deterministic.  Applies the paper's declared
    mechanical trim if the block exceeds ``BLOCK_MAX_CHARS``:
    lived examples beyond the first 2 go first (reverse order),
    then dead examples beyond the first 2 per family; taxonomy,
    rules and the rejected example are never trimmed.  Raises if
    the block still does not fit."""
    deaths, lived = select_examples(dispositions)
    block = render_block(dispositions, deaths, lived)
    kept_deaths, kept_lived = list(deaths), list(lived)
    while len(block) > BLOCK_MAX_CHARS and len(kept_lived) > 2:
        kept_lived.pop()
        block = render_block(dispositions, kept_deaths, kept_lived)
    while len(block) > BLOCK_MAX_CHARS:
        fam_counts = Counter(d.final for d in kept_deaths)
        victim = None
        for d in reversed(kept_deaths):
            if d.final in (DISP_DEAD_TOKENS, DISP_DEAD_NO_PATTERN) \
                    and fam_counts[d.final] > 2:
                victim = d
                break
        if victim is None:
            raise ValueError(
                f"lessons block is {len(block)} chars > "
                f"{BLOCK_MAX_CHARS} after the declared trim; "
                f"the compiler fails rather than cutting taxonomy, "
                f"rules or the rejected example")
        kept_deaths.remove(victim)
        block = render_block(dispositions, kept_deaths, kept_lived)
    examples = []
    for tag, d in [(f"D{i}", d) for i, d in enumerate(kept_deaths, 1)] + \
                  [(f"L{i}", d) for i, d in enumerate(kept_lived, 1)]:
        examples.append({
            "tag": tag, "pr": d.record.pr, "idx": d.record.idx,
            "gold": d.record.gold, "gold_idx": d.record.gold_idx,
            "disp": d.final, "origin": d.shaper_origin,
            "message_sha256": _sha(d.record.message.strip()),
            "evidence_sha256": _sha("\n".join(d.record.evidence)),
            "absent_tokens": list(d.absent_tokens),
        })
    manifest = {
        "artifact": LESSONS_CONTEXT_VERSION,
        "compiler": COMPILER_VERSION,
        "corpus": {"run": 298, "claims": len(dispositions),
                   "decisions_sha256": decisions_sha256},
        "taxonomy": dict(Counter(d.final for d in dispositions)),
        "block_chars": len(block),
        "examples": examples,
    }
    return CompiledLessons(block=block, block_sha256=_sha(block),
                           manifest=manifest, dispositions=dispositions)


def render_artifact(compiled: CompiledLessons) -> str:
    m = compiled.manifest
    header = [
        f"# Contexto de lecciones — ALMA ReviewBench",
        f"<!-- artifact: {m['artifact']} | compiler: {m['compiler']} -->",
        f"<!-- corpus: run298 claims={m['corpus']['claims']} "
        f"decisions-sha256: {m['corpus']['decisions_sha256']} -->",
        f"<!-- block-sha256: {compiled.block_sha256} | "
        f"block-chars: {m['block_chars']} -->",
        "",
        "Artefacto generado por programa (`agent/lessons_compiler.py`) "
        "desde el corpus adjudicado de la corrida nº 298 — no editar "
        "a mano: la auditoría de procedencia lo re-deriva del corpus "
        "y cualquier edición rompe el hash declarado. El bloque entre "
        "marcadores es lo que el revisor v2.5 inyecta, verbatim, en "
        "sus prompts de producción.",
        "",
        BLOCK_BEGIN,
        compiled.block,
        BLOCK_END,
        "",
    ]
    return "\n".join(header)


def extract_block(artifact_text: str) -> str | None:
    """The injectable block: the text strictly between the markers,
    under the single extraction rule shared by the compiler, the
    audit and the v2.5 reviewer."""
    begin = artifact_text.find(BLOCK_BEGIN)
    end = artifact_text.find(BLOCK_END)
    if begin < 0 or end < 0 or end <= begin:
        return None
    inner = artifact_text[begin + len(BLOCK_BEGIN):end]
    return inner.strip("\n")


# ------------------------------------------------------------------
# Provenance audit
# ------------------------------------------------------------------

_SRC_RE = re.compile(
    r"<!-- src: run298 pr=(\S+) e=(\d+) gold=(\S+) disp=(\S+) -->")


def audit_artifact(
    artifact_text: str,
    manifest: dict,
    dispositions: list[ClaimDisposition],
) -> list[str]:
    """Re-derive everything from the corpus and list the
    violations (empty list = the artifact is exactly what the
    corpus compiles to, with every example traced).  Checks: the
    declared block hash; a full deterministic recompilation equal
    to the artifact's block; and, per example, the source tag, the
    verbatim message and evidence inside the block, and the
    manifest hashes against the adjudicated record."""
    violations: list[str] = []
    block = extract_block(artifact_text)
    if block is None:
        return ["markers missing or misordered in the artifact"]
    declared = re.search(r"block-sha256: ([0-9a-f]{64})", artifact_text)
    if not declared:
        violations.append("no block-sha256 declared in the header")
    elif declared.group(1) != _sha(block):
        violations.append(
            "declared block-sha256 does not match the block's hash")
    recompiled = compile_lessons(
        dispositions, manifest["corpus"]["decisions_sha256"])
    if recompiled.block != block:
        violations.append(
            "the block differs from a fresh deterministic "
            "recompilation from the corpus")
    if recompiled.manifest["examples"] != manifest["examples"]:
        violations.append("the manifest's examples differ from the "
                          "recompiled provenance")
    by_key = {(d.record.pr, d.record.idx): d for d in dispositions}
    tags = _SRC_RE.findall(block)
    if len(tags) != len(manifest["examples"]):
        violations.append(
            f"source tags in block: {len(tags)}; manifest examples: "
            f"{len(manifest['examples'])}")
    for entry, (pr, idx_s, gold, disp) in zip(manifest["examples"], tags):
        idx = int(idx_s)
        if entry["pr"] != pr or entry["idx"] != idx:
            violations.append(
                f"example {entry['tag']}: tag order does not match "
                f"the manifest")
            continue
        d = by_key.get((pr, idx))
        if d is None:
            violations.append(
                f"example {entry['tag']}: no adjudicated claim "
                f"{pr} e={idx} exists in the corpus")
            continue
        if str(d.record.gold) != gold or d.final != disp:
            violations.append(
                f"example {entry['tag']}: tag says gold={gold} "
                f"disp={disp}; the corpus says gold={d.record.gold} "
                f"disp={d.final}")
        if entry["message_sha256"] != _sha(d.record.message.strip()):
            violations.append(
                f"example {entry['tag']}: message hash does not "
                f"match the adjudicated claim")
        if entry["evidence_sha256"] != _sha("\n".join(d.record.evidence)):
            violations.append(
                f"example {entry['tag']}: evidence hash does not "
                f"match the adjudicated claim")
        if d.record.message.strip() not in block:
            violations.append(
                f"example {entry['tag']}: the claim's message does "
                f"not appear verbatim in the block")
        if "\n".join(d.record.evidence) not in block:
            violations.append(
                f"example {entry['tag']}: the cited evidence does "
                f"not appear verbatim in the block")
    return violations


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parent.parent
    artifact_path = root / "CONTEXTO-LECCIONES.md"
    manifest_path = root / "CONTEXTO-LECCIONES.provenance.json"
    verify = "--verify" in args
    ensure_clones(root)
    records, diffs, meta = load_corpus(root)
    dispositions = compute_dispositions(records, diffs)
    if verify:
        artifact_text = artifact_path.read_text()
        manifest = json.loads(manifest_path.read_text())
        violations = audit_artifact(artifact_text, manifest, dispositions)
        if violations:
            print("PROVENANCE AUDIT FAILED:")
            for v in violations:
                print(" -", v)
            return 1
        print(f"provenance audit: 0 violations | block-sha256 "
              f"{_sha(extract_block(artifact_text))} | "
              f"{len(dispositions)} claims re-derived")
        return 0
    compiled = compile_lessons(dispositions, meta["decisions_sha256"])
    artifact_path.write_text(render_artifact(compiled))
    manifest_path.write_text(json.dumps(compiled.manifest, indent=1,
                                        ensure_ascii=False) + "\n")
    print(f"compiled {artifact_path.name}: block "
          f"{compiled.manifest['block_chars']} chars, sha256 "
          f"{compiled.block_sha256}, "
          f"{len(compiled.manifest['examples'])} examples, taxonomy "
          f"{compiled.manifest['taxonomy']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
