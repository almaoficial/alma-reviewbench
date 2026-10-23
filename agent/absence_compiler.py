"""Deterministic compiler of the reviewer's ABSENCES — the gold
true defects it never claimed — into a bounded, provenance-
auditable context artifact, sibling of ``lessons_compiler`` —
paper ``PREREGISTRO-LECCIONES-AUSENCIA`` (2026-10-22).

The lessons compiler distills the 166 claims that were born; the
grounded recall of run nº 298 was 66/352 (18.75%), so 286 gold
true defects were never claimed at all and no lesson could be
distilled from them.  This module compiles that omission side:
it loads the public gold set of the run's 25 PRs, the base
reviewer's emissions and the grounded adjudication
(``adjwork298/decisions.json``), applies the adjudication's own
matching criterion (a gold TP is touched iff a decision with
``v == "TP"`` points at its index — the criterion of
``adjwork298/aggregate298.py``, not a new one), and renders
``CONTEXTO-AUSENCIAS.md``: raw absence counts by declared
dimension, verbatim traceable examples of missed defects with
what the reviewer looked at instead, and short imperative rules
derived from — and citing — the counts.

US$0 by construction: no model is called anywhere in this
module, and no git clone is needed (gold + findings +
decisions are plain JSON).  The compiler does not measure —
and does not claim — any effect of the absence lessons on
recall; per the paper, that is a property of a real model run,
and the paid run stays parked.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from agent.lessons_compiler import _sha

COMPILER_VERSION = "alma-absence-compiler/1.0"
ABSENCE_CONTEXT_VERSION = "alma-absence-context/1.0"
BLOCK_BEGIN = "<!-- ABSENCE-BLOCK-BEGIN -->"
BLOCK_END = "<!-- ABSENCE-BLOCK-END -->"
BLOCK_MAX_CHARS = 9_600
MAX_EXAMPLE_CITATION_LINES = 12
EXAMPLES_PER_FAMILY = 3
TOP_PRS_SHOWN = 5

FAMILY_NEVER_VISITED = "A1_archivo_nunca_visitado"
FAMILY_VISITED_MISSED = "A2_archivo_visitado_no_reclamado"


# ------------------------------------------------------------------
# Corpus: gold entries, base emissions, adjudication decisions
# ------------------------------------------------------------------


@dataclass(frozen=True)
class GoldRecord:
    """One gold true-positive entry of the run's 25 PRs, with its
    grounded touched/absent status and the absence dimensions."""

    pr: str
    gold_idx: int                 # index in the gold file's findings list
    file: str
    start_line: int
    end_line: int
    message: str
    severity: str
    category: str
    scope: str
    difficulty: str
    context_required: str
    touched: bool
    family: str | None            # A1/A2 when absent, None when touched
    file_emissions: int           # base emissions on the same file (this PR)
    overlap_emission: int | None  # first same-file emission idx overlapping
    grey_grazes: int              # GREY decisions whose ref points here

    @property
    def citation_lines(self) -> int:
        return self.end_line - self.start_line + 1


@dataclass(frozen=True)
class PrEmissions:
    pr: str
    messages: tuple[str, ...]
    files: tuple[str, ...]
    ranges: tuple[tuple[int, int], ...]


def load_absence_corpus(root: Path) -> tuple[list[GoldRecord],
                                              dict[str, PrEmissions],
                                              dict]:
    """Load gold + emissions + decisions for the 25 PRs of run
    nº 298 and derive every gold TP's touched/absent status by
    the adjudication's grounded criterion.  Raises if the
    adjudication does not close (the published aggregate's own
    sanity checks, re-run): a decision per emission, TP
    decisions pointing at TP entries, FPG at FP entries."""
    work = root / "adjwork298"
    decisions_path = work / "decisions.json"
    decisions = json.loads(decisions_path.read_text())
    decisions_sha = hashlib.sha256(
        decisions_path.read_bytes()).hexdigest()

    records: list[GoldRecord] = []
    emissions_by_pr: dict[str, PrEmissions] = {}
    gold_tp = touched = 0
    grey_refs_total = grey_refs_parsed = 0

    for pr_dir in sorted((work / "run298" / "prs").iterdir()):
        pr = pr_dir.name
        run_data = json.loads((pr_dir / "findings.json").read_text())
        ems = run_data["findings"]
        gold_data = json.loads(
            (work / "gold" / "golden" / f"{pr}.json").read_text())
        gold = gold_data["findings"]
        dec = decisions.get(pr, {}).get("emissions", {})
        if len(dec) != len(ems):
            raise ValueError(
                f"{pr}: decisions {len(dec)} != emissions {len(ems)} "
                f"— the adjudication does not close")
        covered: set[int] = set()
        grey_targets: Counter = Counter()
        for idx_s, d in dec.items():
            v = d["v"]
            if v == "TP":
                if gold[d["g"]]["tp_fp"] != "tp":
                    raise ValueError(
                        f"{pr} E{idx_s}: TP points at a non-TP gold entry")
                covered.add(d["g"])
            elif v == "FPG":
                if gold[d["g"]]["tp_fp"] != "fp":
                    raise ValueError(
                        f"{pr} E{idx_s}: FPG points at a non-FP gold entry")
            elif v == "GREY":
                grey_refs_total += 1
                m = re.fullmatch(r"G(\d+)", str(d.get("ref", "")))
                if m:
                    grey_refs_parsed += 1
                    grey_targets[int(m.group(1))] += 1
        emissions_by_pr[pr] = PrEmissions(
            pr=pr,
            messages=tuple(e["message"] for e in ems),
            files=tuple(e["file"] for e in ems),
            ranges=tuple((e["start_line"], e["end_line"]) for e in ems),
        )
        for g_idx, g in enumerate(gold):
            if g["tp_fp"] != "tp":
                continue
            gold_tp += 1
            is_touched = g_idx in covered
            if is_touched:
                touched += 1
            same_file = [i for i, f in enumerate(
                emissions_by_pr[pr].files) if f == g["file"]]
            overlap = None
            for i in same_file:
                s, e = emissions_by_pr[pr].ranges[i]
                if s <= g["end_line"] and g["start_line"] <= e:
                    overlap = i
                    break
            family = None
            if not is_touched:
                family = (FAMILY_VISITED_MISSED if same_file
                          else FAMILY_NEVER_VISITED)
            records.append(GoldRecord(
                pr=pr, gold_idx=g_idx, file=g["file"],
                start_line=g["start_line"], end_line=g["end_line"],
                message=g["message"], severity=g["severity"],
                category=g["category"], scope=g["scope"],
                difficulty=g["difficulty"],
                context_required=g["context_required"],
                touched=is_touched, family=family,
                file_emissions=len(same_file),
                overlap_emission=overlap,
                grey_grazes=grey_targets.get(g_idx, 0),
            ))
    meta = {
        "decisions_sha256": decisions_sha,
        "gold_tp": gold_tp,
        "touched": touched,
        "absent": gold_tp - touched,
        "grey_refs_total": grey_refs_total,
        "grey_refs_parsed": grey_refs_parsed,
    }
    return records, emissions_by_pr, meta


# ------------------------------------------------------------------
# Dimensions
# ------------------------------------------------------------------


def dimension_table(records: list[GoldRecord],
                    key) -> dict[str, dict[str, int]]:
    """{value: {gold_tp, absent}} in deterministic (sorted) order."""
    out: dict[str, dict[str, int]] = {}
    for value in sorted({key(r) for r in records}):
        sub = [r for r in records if key(r) == value]
        out[value] = {
            "gold_tp": len(sub),
            "absent": sum(1 for r in sub if not r.touched),
        }
    return out


def compute_dimensions(records: list[GoldRecord]) -> dict:
    absent = [r for r in records if not r.touched]
    by_pr: dict[str, dict[str, int]] = {}
    for pr in sorted({r.pr for r in records}):
        sub = [r for r in records if r.pr == pr]
        by_pr[pr] = {
            "gold_tp": len(sub),
            "absent": sum(1 for r in sub if not r.touched),
        }
    return {
        "by_pr": by_pr,
        "by_category": dimension_table(records, lambda r: r.category),
        "by_context_required": dimension_table(
            records, lambda r: r.context_required),
        "by_scope": dimension_table(records, lambda r: r.scope),
        "by_severity": dimension_table(records, lambda r: r.severity),
        "by_difficulty": dimension_table(records, lambda r: r.difficulty),
        "families": dict(Counter(r.family for r in absent)),
        "a2_with_overlap": sum(
            1 for r in absent
            if r.family == FAMILY_VISITED_MISSED
            and r.overlap_emission is not None),
        "grey_grazed_absent": sum(1 for r in absent if r.grey_grazes > 0),
    }


# ------------------------------------------------------------------
# Compilation
# ------------------------------------------------------------------


@dataclass
class CompiledAbsences:
    block: str
    block_sha256: str
    manifest: dict
    records: list[GoldRecord] = field(default_factory=list)


def select_examples(records: list[GoldRecord]) -> list[GoldRecord]:
    """The paper's frozen selection: absent TPs whose gold
    citation spans at most ``MAX_EXAMPLE_CITATION_LINES`` lines,
    ordered by (family, PR, gold index), at most
    ``EXAMPLES_PER_FAMILY`` per family (A1 first, then A2)."""
    eligible = [r for r in records
                if not r.touched
                and r.citation_lines <= MAX_EXAMPLE_CITATION_LINES]
    out: list[GoldRecord] = []
    for family in (FAMILY_NEVER_VISITED, FAMILY_VISITED_MISSED):
        fam = sorted((r for r in eligible if r.family == family),
                     key=lambda r: (r.pr, r.gold_idx))
        out.extend(fam[:EXAMPLES_PER_FAMILY])
    return out


def _pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "—"


def _dim_lines(title: str, table: dict[str, dict[str, int]]) -> list[str]:
    lines = [f"- By {title}:"]
    for value, c in table.items():
        lines.append(
            f"  - {value}: {c['absent']} of {c['gold_tp']} true "
            f"defects never claimed ({_pct(c['absent'], c['gold_tp'])})")
    return lines


def _quoted_emission(rec: GoldRecord,
                     emissions: PrEmissions) -> int | None:
    """The reviewer's same-file emission quoted for an A2
    example: the first by (start_line, emission index), or None.
    Deterministic; the manifest records its index."""
    same = [i for i, f in enumerate(emissions.files) if f == rec.file]
    if not same:
        return None
    return min(same, key=lambda i: (emissions.ranges[i][0], i))


def _render_example(rec: GoldRecord, tag: str,
                    emissions: PrEmissions) -> tuple[str, dict]:
    lines = [
        f"### Example {tag}",
        f"<!-- src: gold298 pr={rec.pr} g={rec.gold_idx} "
        f"family={rec.family} -->",
        f"Missed defect (verbatim, from the public gold set): "
        f"{rec.message.strip()}",
        f"Location: {rec.file}:{rec.start_line}-{rec.end_line} — "
        f"category: {rec.category}; context required: "
        f"{rec.context_required}; scope: {rec.scope}; difficulty: "
        f"{rec.difficulty}; severity: {rec.severity}.",
    ]
    quoted = None
    if rec.family == FAMILY_NEVER_VISITED:
        files = sorted(set(emissions.files))
        lines.append(
            f"What the reviewer did on this PR instead: it emitted "
            f"{len(emissions.messages)} claims, on "
            f"{len(files)} file(s) — {', '.join(files)} — and never "
            f"on this file.")
    else:
        quoted = _quoted_emission(rec, emissions)
        q = emissions
        lines.append(
            f"What the reviewer did on this PR instead: it emitted "
            f"{len(q.messages)} claims, {rec.file_emissions} of them "
            f"on this very file. One of them (verbatim):")
        lines.append(q.messages[quoted].strip())
        s, e = q.ranges[quoted]
        lines.append(
            f"(That claim points at {rec.file}:{s}-{e}; the missed "
            f"defect lives at {rec.start_line}-{rec.end_line}.)")
    entry = {
        "tag": tag, "pr": rec.pr, "gold_idx": rec.gold_idx,
        "family": rec.family, "file": rec.file,
        "message_sha256": _sha(rec.message.strip()),
        "quoted_emission": quoted,
        "quoted_emission_sha256": (
            _sha(emissions.messages[quoted].strip())
            if quoted is not None else None),
    }
    return "\n".join(lines), entry


def render_block(records: list[GoldRecord], dims: dict, meta: dict,
                 examples: list[GoldRecord],
                 emissions_by_pr: dict[str, PrEmissions],
                 ) -> tuple[str, list[dict]]:
    absent = [r for r in records if not r.touched]
    total = meta["gold_tp"]
    a1 = dims["families"].get(FAMILY_NEVER_VISITED, 0)
    a2 = dims["families"].get(FAMILY_VISITED_MISSED, 0)
    lines = [
        "WHAT THIS REVIEWER NEVER CLAIMED — ABSENCE LESSONS FROM "
        "ITS OWN ADJUDICATED HISTORY",
        f"(Run nº 298, grounded adjudication against the public "
        f"gold set: of {total} true defects, {meta['touched']} "
        f"were claimed and {meta['absent']} were never claimed. "
        f"Absence is adjudicated by the benchmark's own matching: "
        f"a true defect counts as claimed only when a finding was "
        f"adjudicated as that very defect.)",
        "",
        "## The absences — counts",
        f"- Never claimed, in a file the reviewer never emitted "
        f"on in that PR (A1): {a1} of {meta['absent']} absences "
        f"({_pct(a1, meta['absent'])})",
        f"- Never claimed, in a file the reviewer did emit on "
        f"(A2): {a2} of {meta['absent']} "
        f"({_pct(a2, meta['absent'])}); in "
        f"{dims['a2_with_overlap']} of those, one of its claims "
        f"points at lines overlapping the missed defect",
        f"- Grazed but not claimed: {dims['grey_grazed_absent']} "
        f"absent defects were referenced by a finding the "
        f"adjudication filed as grey-zone, not as the defect "
        f"itself",
    ]
    worst = sorted(dims["by_pr"].items(),
                   key=lambda kv: (-kv[1]["absent"], kv[0]))
    worst = [(pr, c) for pr, c in worst if c["absent"] > 0][:TOP_PRS_SHOWN]
    lines.append("- PRs with the most absences: " + "; ".join(
        f"{pr} ({c['absent']} of {c['gold_tp']})" for pr, c in worst))
    lines.extend(_dim_lines("category", dims["by_category"]))
    lines.extend(_dim_lines("context required",
                            dims["by_context_required"]))
    lines.extend(_dim_lines("scope", dims["by_scope"]))
    lines.extend(_dim_lines("difficulty", dims["by_difficulty"]))
    lines.append("")
    lines.append("## Missed true defects — verbatim examples")
    entries = []
    for i, rec in enumerate(examples, 1):
        fam_tag = "A1" if rec.family == FAMILY_NEVER_VISITED else "A2"
        n = sum(1 for e in entries if e["tag"].startswith(fam_tag))
        text, entry = _render_example(
            rec, f"{fam_tag}-{n + 1}", emissions_by_pr[rec.pr])
        entries.append(entry)
        lines.append(text)
        lines.append("")
    lines.extend(_rules(records, dims, meta))
    return "\n".join(lines).strip("\n"), entries


def _top(table: dict[str, dict[str, int]], by: str) -> tuple[str, dict]:
    return max(table.items(), key=lambda kv: (kv[1][by], kv[0]))


def _rules(records: list[GoldRecord], dims: dict, meta: dict) -> list[str]:
    absent = meta["absent"]
    a1 = dims["families"].get(FAMILY_NEVER_VISITED, 0)
    cat_name, cat = _top(dims["by_category"], "absent")
    ctx_name, ctx = _top(dims["by_context_required"], "absent")
    scope_worst = max(
        dims["by_scope"].items(),
        key=lambda kv: (kv[1]["absent"] / kv[1]["gold_tp"]
                        if kv[1]["gold_tp"] else 0, kv[0]))
    rules = [
        "## Rules distilled from the counts above",
        f"1. Sweep the files you did not flag: {a1} of {absent} "
        f"missed true defects ({_pct(a1, absent)}) sat in files "
        f"you never emitted on in that PR. Silence on a file is "
        f"not a verdict on it.",
        f"2. Your largest blind spot by count is {cat_name}: "
        f"{cat['absent']} of {cat['gold_tp']} true {cat_name} "
        f"defects were never claimed "
        f"({_pct(cat['absent'], cat['gold_tp'])}). When a change "
        f"touches that surface, slow down.",
        f"3. Most misses needed {ctx_name}: {ctx['absent']} of "
        f"{ctx['gold_tp']} such defects were never claimed "
        f"({_pct(ctx['absent'], ctx['gold_tp'])}). Do not judge a "
        f"hunk without the context its defect class needs.",
        f"4. The scope you miss most, proportionally, is "
        f"{scope_worst[0]}: {scope_worst[1]['absent']} of "
        f"{scope_worst[1]['gold_tp']} never claimed "
        f"({_pct(scope_worst[1]['absent'], scope_worst[1]['gold_tp'])}). "
        f"A defect does not have to be born in this diff to be "
        f"yours to report.",
        f"5. You can stand on the very lines and still miss it: "
        f"in {dims['a2_with_overlap']} absences, one of your "
        f"claims pointed at lines overlapping the missed defect. "
        f"When you flag a line, ask what else those lines break.",
    ]
    return rules


def compile_absences(records: list[GoldRecord],
                     emissions_by_pr: dict[str, PrEmissions],
                     meta: dict) -> CompiledAbsences:
    """Compile the bounded block + provenance manifest.
    Deterministic.  Applies the paper's declared mechanical
    trim if the block exceeds ``BLOCK_MAX_CHARS``: A2 examples
    beyond the first 2 go first, then A1 beyond the first 2;
    counts and rules are never trimmed.  Raises if the block
    still does not fit."""
    dims = compute_dimensions(records)
    examples = select_examples(records)
    block, entries = render_block(records, dims, meta, examples,
                                  emissions_by_pr)
    kept = list(examples)
    for family in (FAMILY_VISITED_MISSED, FAMILY_NEVER_VISITED):
        while len(block) > BLOCK_MAX_CHARS:
            fam_kept = [e for e in kept if e.family == family]
            if len(fam_kept) <= 2:
                break
            kept.remove(fam_kept[-1])
            block, entries = render_block(records, dims, meta, kept,
                                          emissions_by_pr)
    if len(block) > BLOCK_MAX_CHARS:
        raise ValueError(
            f"absence block is {len(block)} chars > "
            f"{BLOCK_MAX_CHARS} after the declared trim; the "
            f"compiler fails rather than cutting counts or rules")
    manifest = {
        "artifact": ABSENCE_CONTEXT_VERSION,
        "compiler": COMPILER_VERSION,
        "corpus": {"run": 298, "gold_tp": meta["gold_tp"],
                   "touched": meta["touched"], "absent": meta["absent"],
                   "decisions_sha256": meta["decisions_sha256"],
                   "grey_refs_total": meta["grey_refs_total"],
                   "grey_refs_parsed": meta["grey_refs_parsed"]},
        "families": dims["families"],
        "a2_with_overlap": dims["a2_with_overlap"],
        "grey_grazed_absent": dims["grey_grazed_absent"],
        "by_category": dims["by_category"],
        "by_context_required": dims["by_context_required"],
        "by_scope": dims["by_scope"],
        "by_severity": dims["by_severity"],
        "by_difficulty": dims["by_difficulty"],
        "block_chars": len(block),
        "examples": entries,
    }
    return CompiledAbsences(block=block, block_sha256=_sha(block),
                            manifest=manifest, records=records)


def render_artifact(compiled: CompiledAbsences) -> str:
    m = compiled.manifest
    header = [
        "# Contexto de ausencias — ALMA ReviewBench",
        f"<!-- artifact: {m['artifact']} | compiler: {m['compiler']} -->",
        f"<!-- corpus: run298 gold-tp={m['corpus']['gold_tp']} "
        f"touched={m['corpus']['touched']} "
        f"absent={m['corpus']['absent']} "
        f"decisions-sha256: {m['corpus']['decisions_sha256']} -->",
        f"<!-- block-sha256: {compiled.block_sha256} | "
        f"block-chars: {m['block_chars']} -->",
        "",
        "Artefacto generado por programa (`agent/absence_compiler.py`) "
        "desde el oro público y la adjudicación grounded de la "
        "corrida nº 298 — no editar a mano: la auditoría de "
        "procedencia lo re-deriva de las fuentes y cualquier "
        "edición rompe el hash declarado. Hermano de "
        "`CONTEXTO-LECCIONES.md`: aquel destila los reclamos que "
        "nacieron; este, los defectos verdaderos que nunca fueron "
        "reclamados.",
        "",
        BLOCK_BEGIN,
        compiled.block,
        BLOCK_END,
        "",
    ]
    return "\n".join(header)


def extract_block(artifact_text: str) -> str | None:
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
    r"<!-- src: gold298 pr=(\S+) g=(\d+) family=(\S+) -->")


def audit_artifact(
    artifact_text: str,
    manifest: dict,
    records: list[GoldRecord],
    emissions_by_pr: dict[str, PrEmissions],
    meta: dict,
) -> list[str]:
    """Re-derive everything from the sources and list the
    violations (empty list = the artifact is exactly what the
    sources compile to, with every example traced to a gold
    entry).  Checks: closure of the corpus (gold TP = touched +
    absent), the declared block hash, a full deterministic
    recompilation equal to the artifact's block, and, per
    example, the source tag, the verbatim gold message and the
    verbatim quoted emission inside the block, and the manifest
    hashes against the source records."""
    violations: list[str] = []
    if meta["gold_tp"] != meta["touched"] + meta["absent"]:
        violations.append(
            f"corpus does not close: {meta['gold_tp']} gold TP != "
            f"{meta['touched']} touched + {meta['absent']} absent")
    block = extract_block(artifact_text)
    if block is None:
        return violations + ["markers missing or misordered in "
                             "the artifact"]
    declared = re.search(r"block-sha256: ([0-9a-f]{64})", artifact_text)
    if not declared:
        violations.append("no block-sha256 declared in the header")
    elif declared.group(1) != _sha(block):
        violations.append(
            "declared block-sha256 does not match the block's hash")
    recompiled = compile_absences(records, emissions_by_pr, meta)
    if recompiled.block != block:
        violations.append(
            "the block differs from a fresh deterministic "
            "recompilation from the sources")
    if recompiled.manifest["examples"] != manifest["examples"]:
        violations.append("the manifest's examples differ from the "
                          "recompiled provenance")
    by_key = {(r.pr, r.gold_idx): r for r in records}
    tags = _SRC_RE.findall(block)
    if len(tags) != len(manifest["examples"]):
        violations.append(
            f"source tags in block: {len(tags)}; manifest examples: "
            f"{len(manifest['examples'])}")
    for entry, (pr, g_s, family) in zip(manifest["examples"], tags):
        g = int(g_s)
        if entry["pr"] != pr or entry["gold_idx"] != g:
            violations.append(
                f"example {entry['tag']}: tag order does not match "
                f"the manifest")
            continue
        rec = by_key.get((pr, g))
        if rec is None:
            violations.append(
                f"example {entry['tag']}: no gold TP entry "
                f"{pr} g={g} exists in the corpus")
            continue
        if rec.touched:
            violations.append(
                f"example {entry['tag']}: gold entry {pr} g={g} "
                f"was TOUCHED — it is not an absence")
        if rec.family != family or entry["family"] != family:
            violations.append(
                f"example {entry['tag']}: tag says family={family}; "
                f"the sources say {rec.family}")
        if entry["message_sha256"] != _sha(rec.message.strip()):
            violations.append(
                f"example {entry['tag']}: gold message hash does "
                f"not match the gold entry")
        if rec.message.strip() not in block:
            violations.append(
                f"example {entry['tag']}: the gold message does "
                f"not appear verbatim in the block")
        q = entry["quoted_emission"]
        if q is None:
            if rec.family == FAMILY_VISITED_MISSED:
                violations.append(
                    f"example {entry['tag']}: A2 example without a "
                    f"quoted same-file emission")
        else:
            ems = emissions_by_pr[pr]
            if ems.messages[q].strip() not in block:
                violations.append(
                    f"example {entry['tag']}: the quoted emission "
                    f"does not appear verbatim in the block")
            if entry["quoted_emission_sha256"] != _sha(
                    ems.messages[q].strip()):
                violations.append(
                    f"example {entry['tag']}: quoted emission hash "
                    f"does not match the run's findings")
    return violations


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parent.parent
    artifact_path = root / "CONTEXTO-AUSENCIAS.md"
    manifest_path = root / "CONTEXTO-AUSENCIAS.provenance.json"
    verify = "--verify" in args
    records, emissions_by_pr, meta = load_absence_corpus(root)
    if verify:
        artifact_text = artifact_path.read_text()
        manifest = json.loads(manifest_path.read_text())
        violations = audit_artifact(artifact_text, manifest, records,
                                    emissions_by_pr, meta)
        if violations:
            print("PROVENANCE AUDIT FAILED:")
            for v in violations:
                print(" -", v)
            return 1
        print(f"provenance audit: 0 violations | block-sha256 "
              f"{_sha(extract_block(artifact_text))} | "
              f"{meta['gold_tp']} gold TP re-derived "
              f"({meta['touched']} touched, {meta['absent']} absent)")
        return 0
    compiled = compile_absences(records, emissions_by_pr, meta)
    artifact_path.write_text(render_artifact(compiled))
    manifest_path.write_text(json.dumps(compiled.manifest, indent=1,
                                        ensure_ascii=False) + "\n")
    print(f"compiled {artifact_path.name}: block "
          f"{compiled.manifest['block_chars']} chars, sha256 "
          f"{compiled.block_sha256}, "
          f"{len(compiled.manifest['examples'])} examples, "
          f"families {compiled.manifest['families']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
