"""Executability census of gate 1.4.1's waiting room — paper
``PREREGISTRO-CENSO-EJECUTABILIDAD`` (2026-10-22).

The 1.4.1 replay (``REPLAY-PUERTA-141-20261022.md``) left 149 of
the base run nº 298's 166 claims in ``needs_validation``: the gate
verifies by CITATION and has no rule for general categories.  This
module asks the complementary question — how many of those 149
would be DECIDABLE by EXECUTION (an existing test or command, or a
deterministic reproduction anchored in the claim itself) and how
many have no execution route even in principle — and crosses the
answer with the adjudicated gold: whether the executable classes
concentrate the true positives the citation gate could not verify.

The taxonomy is CLOSED and was pre-registered before any claim was
classified (the paper's §4): E1 executable directly (an existing,
identifiable oracle), E2 executable with construction (the claim
itself is a sufficient spec: input + expected observable), E3 not
executable in principle (design judgment, static absence, external
semantics, non-deterministic concurrency), E4 unclassifiable from
the claim as written.  Classification runs over the claim AS
WRITTEN: message + cited evidence + its PR's diff.

Method (paper §5): a deterministic script classifies a claim ONLY
when the rules of exactly one class fire and no rule of another
class fires against it; every other claim is declared DUDA and
goes to assisted review (the executing agent reads it and assigns
E1–E4 with a recorded one-line reason — no model is called).  The
script/review split is reported, never targeted.

US$0 by construction: this module reads local files and runs the
FROZEN gate 1.4.1 over the rebuilt corpus; it executes no
reproduction and calls no model.  Classifying is not verifying:
a class asserts decidability in principle from the claim as
written, nothing about cost or about the execution's verdict.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from agent.alma_gate_v141 import AlmaGateV141
from agent.lessons_compiler import ClaimRecord, born_candidate, load_corpus

CENSUS_VERSION = "alma-executability-census/1.0"

E1 = "E1_ejecutable_directo"
E2 = "E2_ejecutable_con_construccion"
E3 = "E3_no_ejecutable"
E4 = "E4_inclasificable"
CLASSES = (E1, E2, E3, E4)

VIA_SCRIPT = "script"
VIA_REVIEW = "revision"

# Sanity from the published replay (paper §2): the rebuilt corpus
# through the frozen 1.4.1 must reproduce it EXACTLY before any
# classification happens.
SANITY_HELD = 149
SANITY_ACCEPTED = 0
SANITY_REJECTED = 17
SANITY_HELD_GOLD = {"TP": 80, "FPG": 8, "GREY": 16, "NOVEL": 45}


# ------------------------------------------------------------------
# Waiting room: rebuild the corpus, re-derive the 149 from the
# frozen gate (never from a hand list)
# ------------------------------------------------------------------


def _key(rule_id, file, start_line, end_line, message):
    return (rule_id, file, start_line, end_line, message)


def build_waiting_room(root: Path):
    """Returns (held_records, sanity).  held_records are the
    ClaimRecords the frozen 1.4.1 holds as needs_validation, in
    corpus order.  Raises if the replay sanity does not close."""
    records, diffs, _meta = load_corpus(root)
    gate = AlmaGateV141()
    by_pr: dict[str, list[ClaimRecord]] = {}
    for rec in records:
        by_pr.setdefault(rec.pr, []).append(rec)

    held_keys = set()
    n_accepted = 0
    n_rejected = 0
    for pr, recs in by_pr.items():
        candidates = [born_candidate(r) for r in recs]
        result = gate.validate(candidates, diffs[pr], "census")
        n_accepted += len(result.findings)
        n_rejected += sum(1 for e in result.ledger if e.status == "rejected")
        for h in result.needs_validation:
            held_keys.add(_key(h.rule_id, h.file, h.start_line,
                               h.end_line, h.message))

    held = []
    for rec in records:
        cand = born_candidate(rec)
        if _key(cand.rule_id, cand.file, cand.start_line,
                cand.end_line, cand.message) in held_keys:
            held.append(rec)

    sanity = {
        "accepted": n_accepted,
        "held": len(held),
        "rejected": n_rejected,
        "held_gold": dict(Counter(r.gold for r in held)),
    }
    if (sanity["accepted"] != SANITY_ACCEPTED
            or sanity["held"] != SANITY_HELD
            or sanity["rejected"] != SANITY_REJECTED
            or sanity["held_gold"] != SANITY_HELD_GOLD):
        raise ValueError(f"census sanity failed, refusing to classify: {sanity}")
    return held, sanity


# ------------------------------------------------------------------
# Signals (paper §5): computed over message + evidence + file
# ------------------------------------------------------------------

_TEST_SEGMENTS = {"test", "tests", "__tests__", "spec", "specs"}
_DOC_EXTS = (".md", ".rst", ".adoc")


def _is_test_file(file: str) -> bool:
    parts = file.split("/")
    base = parts[-1]
    if any(p in _TEST_SEGMENTS for p in parts[:-1]):
        return True
    return bool(re.match(
        r"(test_.*|.*_test\..*|.*\.test\..*|.*\.spec\..*|.*Tests?\..*)",
        base)) or base == "conftest.py"


def _is_doc_file(file: str) -> bool:
    return file.endswith(_DOC_EXTS) or "/docs/" in file


_RX = {
    "cmd_decides": re.compile(
        r"(does not compile|doesn't compile|fails? to compile|compilation "
        r"error|syntax error|fails? to parse|parse error|cannot be compiled|"
        r"will not compile|invalid (json|xml|yaml)|is not valid (json|xml|yaml)|"
        r"exit code|segmentation fault|segfault)"),
    "test_asis": re.compile(
        r"(test|tests|assertions?|suite)[^.]{0,80}?\b(passes|pass|fails|fail|"
        r"errors?|is skipped|are skipped|never runs?|not executed|does not "
        r"run|do not run)\b"),
    "counterfactual": re.compile(
        r"(even if|still pass|would (still |also )?(pass|fail|succeed|work)|"
        r"regardless of|passes? (even|regardless)|if [^.]{0,80}?(were|was) "
        r"(broken|removed|deleted|changed|disabled))"),
    "input_spec": re.compile(
        r"(when (called|invoked|passed|given|run|used|executed)|with (input|"
        r"argument|args|a value|an empty)|given (a |an |the )|for (input|"
        r"example)|on (input|startup|empty))"),
    "outcome_spec": re.compile(
        r"(returns?|raises?|throws?|produces?|results? in|outputs?|yields?|"
        r"emits?|fails? with|crashes?|hangs?|loops? forever)"),
    "trigger": re.compile(r"\b(when|if|upon|on)\b"),
    "absence": re.compile(
        r"(never (called|used|invoked|referenced|executed|reached)|"
        r"not (called|used|invoked|referenced) anywhere|no (caller|callers|"
        r"usage|references?)|unreachable|is unused|are unused|unused "
        r"(import|variable|function|method|parameter|code))"),
    "run_framing": re.compile(
        r"(coverage|when the (test )?suite runs|running the tests?|test run)"),
    "concurrency": re.compile(
        r"(race condition|deadlock|thread|concurren|atomic|mutex|synchroniz)"),
    "interleaving": re.compile(
        r"(two threads|simultaneous|at the same time|runs before|runs after|"
        r"interleav|ordering)"),
    "perf": re.compile(
        r"(O\(n|quadratic|exponential time|linear time|memory leak|leaks? "
        r"memory|grows? unbounded|inefficient|n\+1|performance)"),
    "numeric": re.compile(r"\b\d+(\.\d+)?\s?(ms|mb|kb|gb|%|seconds?|minutes?|times|x)\b"),
    "exception_named": re.compile(
        r"(\w+(Exception|Error)\b|NullPointer\w*|IndexError|KeyError|"
        r"TypeError|ValueError|AttributeError|RuntimeError|stack ?trace|"
        r"stack overflow)"),
    "doc_subject": re.compile(
        r"\b(documentation|readme|comment|comments|javadoc|docstring|guide|docs)\b"),
    "test_talk": re.compile(r"\b(test|tests|mock|stub|spy|fixture|assert\w*)\b"),
}

_DESIGN_WORDS = (
    "should be", "should use", "should not be", "readab", "maintainab",
    "confusing", "hard to understand", "hard to maintain", "duplicat",
    "dead code", "magic number", "code smell", "naming", "inconsistent",
    "cleanup", "clean up", "tightly coupled", "single responsibility",
    "abstraction", "clutter",
)


def compute_signals(record: ClaimRecord) -> dict:
    m = record.message
    ml = m.lower()
    ev = "\n".join(record.evidence)
    sig = {
        "test_file": _is_test_file(record.file),
        "doc_file": _is_doc_file(record.file),
        "evidence_has_test": bool(re.search(
            r"(def test_|func Test|@Test|it\(|describe\(|assert)", ev)),
    }
    for name, rx in _RX.items():
        sig[name] = bool(rx.search(ml if name != "exception_named" else m))
    sig["design_hits"] = sum(1 for w in _DESIGN_WORDS if w in ml)
    return sig


# ------------------------------------------------------------------
# Script rules (paper §5): a claim is script-classified ONLY when
# exactly one class draws votes and no other class does
# ------------------------------------------------------------------


def script_classify(record: ClaimRecord):
    """Returns (cls_or_None, rules_fired, votes).  None = DUDA."""
    s = compute_signals(record)
    votes: dict[str, list[str]] = {c: [] for c in (E1, E2, E3)}

    # E1 — an existing, identifiable oracle decides it as-is
    if s["test_file"] and s["test_asis"] and not s["counterfactual"]:
        votes[E1].append("e1_test_asis")
    if s["cmd_decides"]:
        votes[E1].append("e1_command_decides")

    # E2 — the claim itself is a sufficient construction spec
    if s["counterfactual"] and (s["test_talk"] or s["outcome_spec"]):
        votes[E2].append("e2_counterfactual")
    if s["input_spec"] and s["outcome_spec"]:
        votes[E2].append("e2_input_outcome")
    if s["exception_named"] and s["trigger"] and s["outcome_spec"]:
        votes[E2].append("e2_exception_trigger")
    if s["perf"] and s["numeric"]:
        votes[E2].append("e2_perf_workload")

    # E3 — no execution oracle, and none constructible from the claim
    if s["doc_file"] and not s["cmd_decides"] and not s["input_spec"]:
        votes[E3].append("e3_doc_file")
    if s["design_hits"] >= 2 and not s["outcome_spec"]:
        votes[E3].append("e3_design_vocab")
    if s["absence"] and not s["run_framing"]:
        votes[E3].append("e3_absence_static")
    if s["concurrency"] and not s["interleaving"]:
        votes[E3].append("e3_concurrency_nondet")
    if s["doc_subject"] and not s["outcome_spec"] and not s["cmd_decides"]:
        votes[E3].append("e3_prose_subject")

    fired = {c: rs for c, rs in votes.items() if rs}
    if len(fired) == 1:
        cls = next(iter(fired))
        return cls, fired[cls], votes
    return None, [], votes


# ------------------------------------------------------------------
# Census assembly: script stage + assisted-review assignments
# ------------------------------------------------------------------


def run_census(root: Path, review: dict | None = None):
    """review maps "PR#idx" -> {"class": E*, "reason": str} for the
    claims the script declared DUDA.  Returns (entries, summary);
    entries keep every claim's class, route and rules/reason."""
    review = review or {}
    held, sanity = build_waiting_room(root)
    entries = []
    for rec in held:
        key = f"{rec.pr}#{rec.idx}"
        cls, rules, _votes = script_classify(rec)
        if cls is not None:
            entries.append({
                "key": key, "pr": rec.pr, "idx": rec.idx,
                "file": rec.file, "gold": rec.gold, "class": cls,
                "via": VIA_SCRIPT, "rules": rules, "reason": None,
            })
        elif key in review:
            asg = review[key]
            if asg["class"] not in CLASSES:
                raise ValueError(f"bad review class for {key}: {asg}")
            entries.append({
                "key": key, "pr": rec.pr, "idx": rec.idx,
                "file": rec.file, "gold": rec.gold,
                "class": asg["class"], "via": VIA_REVIEW,
                "rules": [], "reason": asg["reason"],
            })
        else:
            entries.append({
                "key": key, "pr": rec.pr, "idx": rec.idx,
                "file": rec.file, "gold": rec.gold, "class": None,
                "via": "duda", "rules": [], "reason": None,
            })

    by_class = Counter(e["class"] for e in entries)
    cross = {c: dict(Counter(e["gold"] for e in entries if e["class"] == c))
             for c in CLASSES}
    summary = {
        "census_version": CENSUS_VERSION,
        "sanity": sanity,
        "total": len(entries),
        "by_class": {c: by_class.get(c, 0) for c in CLASSES},
        "unclassified": by_class.get(None, 0),
        "via": dict(Counter(e["via"] for e in entries)),
        "cross_class_gold": cross,
        "review_by_class": {c: sum(1 for e in entries
                                   if e["class"] == c and e["via"] == VIA_REVIEW)
                            for c in CLASSES},
    }
    if summary["unclassified"] == 0:
        col = Counter()
        for c in CLASSES:
            col.update(cross[c])
        assert dict(col) == SANITY_HELD_GOLD, dict(col)
        assert sum(summary["by_class"].values()) == SANITY_HELD
    return entries, summary


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parent.parent
    review = None
    out = None
    i = 0
    while i < len(argv):
        if argv[i] == "--review":
            review = json.loads(Path(argv[i + 1]).read_text())
            i += 2
        elif argv[i] == "--out":
            out = Path(argv[i + 1])
            i += 2
        else:
            raise SystemExit(f"unknown arg: {argv[i]}")
    entries, summary = run_census(root, review)
    payload = {"summary": summary, "entries": entries}
    if out is not None:
        out.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
