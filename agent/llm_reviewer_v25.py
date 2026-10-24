"""LLM reviewer v2.5 — the v2.4 evidence-first producer plus the
system's READ memory: a compiled lessons context injected into
production.  Paper: ``PREREGISTRO-MEMORIA-LECCIONES`` (2026-10-22).

The gap this version exists to close, named in the paper: the
line had a registry (memory that is stored — adjudications,
papers, ledgers) but no memory that is read.  The reviewer
produced every run as if it were the first: no compiled context
of its own adjudications entered production.  v2.5 is the v2.4,
inherited whole — evidence-first emission, the ``unverifiable``
escape, the production ledger, birth shaping as the last
production stage, the generalized selection, the two-stage guard
and the degradation rule, the cumulative spend brake, the gate
resolution — plus exactly the changes declared in the paper:

- **The lessons block in production**: the block compiled
  deterministically by ``agent/lessons_compiler.py`` from the
  adjudicated corpus of run nº 298 (artifact
  ``CONTEXTO-LECCIONES.md``, ``alma-lessons-context/1.0``) is
  appended VERBATIM — after a fixed one-line header — to the
  SYSTEM content of the production payloads ONLY: the deep passes
  (``build_deep_payload``) and the degenerate mixed fallback
  (``build_fallback_payload``).  The selection payload is NOT
  overridden: byte-identical to the v2.4's, as in the whole line
  (marking does not assert; the lessons govern assertion).  User
  content is never modified.  The guard's worst-case arithmetic
  is inherited and prices the armed payload as built, lessons
  included.
- **Fail-closed loading**: constructing the reviewer without an
  explicit block loads the artifact from disk, extracts the block
  between its markers, recomputes its sha256 and compares it with
  the hash declared in the artifact's header; a missing file,
  missing markers, a missing declaration or a hash mismatch all
  raise :class:`RealLLMRefused` at construction — before any
  model call can exist.  A block can also be injected directly
  (``lessons_block=``), for tests.
- **Provenance tags**: candidates are re-tagged
  ``producer="alma-llm-reviewer-v25"`` /
  ``rule_id="llm_v25_<claim_type>"`` between production and the
  birth-shaping stage (the shaper preserves both tags), and the
  run info (``LLMRunInfoV25``) carries ``lessons_sha256`` /
  ``lessons_version`` / ``lessons_block_chars`` next to the
  v2.4's production counters.

THE HONEST CAVEAT (paper §4, binding): the EFFECT of the lessons
on production is NOT measured by anything in this module and must
not be claimed.  What is verified dry is provenance and faithful
injection: the block in the armed prompts is byte-equal to the
audited artifact, and the discipline is the v2.4's.  The paid
measurement is designed in the paper as a third arm of the parked
A/B (v2.4 vs v2.5, same yardstick) and runs only under a new run
paper with Alejandro's line cap.  ``agent/main.py`` is NOT
touched: v2.5 is not mounted and not adopted.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import re

from .base_reviewer import Candidate
from .lessons_compiler import LESSONS_CONTEXT_VERSION, extract_block
from .llm_reviewer import RealLLMRefused
from .llm_reviewer_v24 import LLMReviewerV24, LLMRunInfoV24


REVIEWER_VERSION = "llm-reviewer/2.5.0"

LESSONS_INJECTION_HEADER = (
    "The following lessons were compiled deterministically from "
    "your own previous adjudicated run. Produce findings that "
    "would survive them:"
)

_DEFAULT_LESSONS_PATH = (
    Path(__file__).resolve().parent.parent / "CONTEXTO-LECCIONES.md"
)
_DECLARED_SHA_RE = re.compile(r"block-sha256: ([0-9a-f]{64})")
_DECLARED_VERSION_RE = re.compile(r"artifact: (\S+)")


def load_lessons_block(path: Path) -> tuple[str, str, str]:
    """Load and verify the lessons artifact at ``path``; returns
    (block, block_sha256, artifact_version).  Fail-closed: any
    anomaly raises :class:`RealLLMRefused`."""

    try:
        text = path.read_text()
    except OSError:
        raise RealLLMRefused(
            f"lessons artifact not found at {path}; the v2.5 "
            "reviewer refuses to produce without its compiled "
            "lessons context"
        )
    block = extract_block(text)
    if block is None:
        raise RealLLMRefused(
            "lessons artifact has no marked lessons block; "
            "refusing to produce"
        )
    declared_sha = _DECLARED_SHA_RE.search(text)
    if not declared_sha:
        raise RealLLMRefused(
            "lessons artifact declares no block-sha256; refusing "
            "to produce"
        )
    actual_sha = hashlib.sha256(block.encode("utf-8")).hexdigest()
    if declared_sha.group(1) != actual_sha:
        raise RealLLMRefused(
            "lessons block hash mismatch: the artifact declares "
            f"{declared_sha.group(1)} but the block hashes to "
            f"{actual_sha}; refusing to produce from an unverified "
            "lessons context"
        )
    declared_version = _DECLARED_VERSION_RE.search(text)
    if not declared_version:
        raise RealLLMRefused(
            "lessons artifact declares no artifact version; "
            "refusing to produce"
        )
    return block, actual_sha, declared_version.group(1)


@dataclass
class LLMRunInfoV25(LLMRunInfoV24):
    """The v2.4 run info plus the lessons provenance: which
    compiled context entered production, identified by content."""

    reviewer_version: str = REVIEWER_VERSION
    lessons_sha256: str = ""
    lessons_version: str = ""
    lessons_block_chars: int = 0

    def to_dict(self) -> dict[str, object]:
        data = super().to_dict()
        data["lessons_sha256"] = self.lessons_sha256
        data["lessons_version"] = self.lessons_version
        data["lessons_block_chars"] = self.lessons_block_chars
        return data


class LLMReviewerV25(LLMReviewerV24):
    """v2.4 + the compiled lessons context in production."""

    name = "alma-llm-reviewer-v25"

    def __init__(
        self,
        settings,
        *args,
        lessons_block: str | None = None,
        lessons_path: Path | None = None,
        lessons_sha256: str | None = None,
        lessons_version: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(settings, *args, **kwargs)
        if lessons_block is None:
            block, sha, version = load_lessons_block(
                lessons_path or _DEFAULT_LESSONS_PATH
            )
            lessons_block, lessons_sha256, lessons_version = (
                block,
                sha,
                version,
            )
        self.lessons_block = lessons_block
        self.lessons_sha256 = lessons_sha256 or hashlib.sha256(
            lessons_block.encode("utf-8")
        ).hexdigest()
        self.lessons_version = lessons_version or LESSONS_CONTEXT_VERSION
        self.lessons_block_chars = len(lessons_block)

    # -- payloads: production only; selection inherited untouched -----

    def _inject_lessons(self, payload: dict) -> dict:
        system = payload["messages"][0]
        system["content"] = (
            system["content"]
            + "\n\n"
            + LESSONS_INJECTION_HEADER
            + "\n"
            + self.lessons_block
        )
        return payload

    def build_deep_payload(
        self, pass_name: str, diff_text: str, context_text: str
    ) -> dict:
        return self._inject_lessons(
            super().build_deep_payload(pass_name, diff_text, context_text)
        )

    def build_fallback_payload(
        self, selected: list, diff_text: str
    ) -> dict:
        return self._inject_lessons(
            super().build_fallback_payload(selected, diff_text)
        )

    # -- production: the v2.4's, with v2.5 provenance tags applied
    #    between production and the birth-shaping stage ---------------

    def _produce(self, **kwargs) -> list[Candidate]:
        candidates = super()._produce(**kwargs)
        return [
            replace(
                c,
                producer=self.name,
                rule_id=f"llm_v25_{c.claim_type}",
            )
            for c in candidates
        ]

    def review(self, **kwargs) -> list[Candidate]:
        emitted = super().review(**kwargs)
        base = self.last_run_info
        self.last_run_info = LLMRunInfoV25(
            model=base.model,
            reviewer_version=REVIEWER_VERSION,
            gate_version=base.gate_version,
            prompt_tokens=base.prompt_tokens,
            completion_tokens=base.completion_tokens,
            estimated_cost_usd=base.estimated_cost_usd,
            raw_findings=base.raw_findings,
            malformed_findings=base.malformed_findings,
            unanchored_findings=base.unanchored_findings,
            calls=base.calls,
            passes=base.passes,
            context_token_budget=base.context_token_budget,
            context_estimated_tokens=base.context_estimated_tokens,
            context_files_included=base.context_files_included,
            context_files_skipped_budget=base.context_files_skipped_budget,
            context_files_missing=base.context_files_missing,
            selection_candidates=base.selection_candidates,
            selection_selected=base.selection_selected,
            selection_overflow=base.selection_overflow,
            selection_general=base.selection_general,
            selection_specialty=base.selection_specialty,
            selection_unknown_marks=base.selection_unknown_marks,
            selection_malformed_entries=base.selection_malformed_entries,
            degradation=base.degradation,
            triage_max_output_tokens=base.triage_max_output_tokens,
            parse_failures=base.parse_failures,
            # The run-344 fix's observability, carried through
            # (ADENDA-ARREGLO-TOPE-20261024.md §3).
            deep_max_output_tokens=base.deep_max_output_tokens,
            length_retries=base.length_retries,
            production_ledger=base.production_ledger,
            shaping=base.shaping,
            lessons_sha256=self.lessons_sha256,
            lessons_version=self.lessons_version,
            lessons_block_chars=self.lessons_block_chars,
        )
        return emitted


__all__ = [
    "LESSONS_INJECTION_HEADER",
    "LLMReviewerV25",
    "LLMRunInfoV25",
    "REVIEWER_VERSION",
    "load_lessons_block",
]
