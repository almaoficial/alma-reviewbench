"""LLM reviewer v2.6 — the v2.5 (evidence-first production plus the
read lessons memory) plus the system's ABSENCE memory: the
compiled context of the true defects the reviewer never claimed,
mounted in production.  Paper: ``ADENDA-V26.md`` (2026-10-23).

The v2.5 reads the memory of COMMISSION: the adjudicated claims
that were born, how they died and how they survived.  What it did
not read — because no reviewer had it mounted — is the memory of
OMISSION.  The absence compilation (``agent/absence_compiler.py``,
artifact ``CONTEXTO-AUSENCIAS.md``, ``alma-absence-context/1.0``,
provenance audit 0 violations) measured it on run nº 298: of 352
gold true defects the base claimed 66 and never claimed 286
(81.3%), and the dominant pattern is not file coverage but
RECOGNITION over what was already looked at (A2 = 182/286,
63.6%, visited-but-not-claimed, against A1 = 104/286 never
visited).  v2.6 is the v2.5, inherited whole — evidence-first
emission, the ``unverifiable`` escape, the production ledger,
birth shaping as the last production stage, the lessons context
in production, the generalized selection, the two-stage guard
and the degradation rule, the cumulative spend brake, the gate
resolution — plus exactly the delta declared in the paper:

- **The absence block in production, after the lessons**: the
  absence block is appended VERBATIM — after its own fixed
  one-line header — to the SYSTEM content of the production
  payloads ONLY (the deep passes, ``build_deep_payload``, and
  the degenerate mixed fallback, ``build_fallback_payload``),
  AFTER the lessons header and block the v2.5 injects: fixed
  order, birth discipline first, omission memory second.  The
  selection payload is NOT overridden: byte-identical to the
  v2.5's / v2.4's, as in the whole line (marking does not
  assert; no memory context governs marking).  User content is
  never modified.  The guard's worst-case arithmetic is
  inherited and prices the armed payload as built, both blocks
  included.
- **Fail-closed loading, per block**: constructing the reviewer
  without an explicit absence block loads the artifact from
  disk, extracts the block between its markers, recomputes its
  sha256 and compares it with the hash declared in the
  artifact's header; a missing file, missing markers, a missing
  declaration or a hash mismatch all raise
  :class:`RealLLMRefused` at construction — before any model
  call can exist.  The lessons block keeps failing closed on
  its own side, inherited from the v2.5.  A block can also be
  injected directly (``absence_block=``), for tests.
- **Combined context budget, verified in the paper (§4)**: both
  blocks together are 17,479 chars ≈ 4,994 estimated tokens
  under the line's own estimator — inside both declared fit
  criteria (≤ 19,200 chars, the sum of the two standing
  per-block caps; ≤ 6,000 estimated tokens, 10% of the line's
  60,000-token context budget).  No shrink was applied; neither
  artifact is modified by this module.
- **Provenance tags**: candidates are re-tagged
  ``producer="alma-llm-reviewer-v26"`` /
  ``rule_id="llm_v26_<claim_type>"`` between production and the
  birth-shaping stage (the shaper preserves both tags), and the
  run info (``LLMRunInfoV26``) carries ``absence_sha256`` /
  ``absence_version`` / ``absence_block_chars`` next to the
  v2.5's ``lessons_*`` fields.

THE HONEST CAVEAT (paper §5, binding): the EFFECT of the absence
context on production is NOT measured by anything in this module
and must not be claimed — exactly as for the lessons.  What is
verified dry is provenance and faithful injection: both blocks
in the armed prompts are byte-equal to their audited artifacts,
and the discipline is the v2.5's.  The paid measurement is the
parked A/B of ``PREREGISTRO-PRODUCTOR-EVIDENCIA`` §4 plus the
third arm of ``PREREGISTRO-MEMORIA-LECCIONES`` §5: v2.6 is
registered by the paper as the candidate arm whose comparison
against v2.5 isolates the absence context, and it runs only
under a run paper with Alejandro's line cap.  ``agent/main.py``
is NOT touched: v2.6 is not mounted and not adopted.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import re

from .absence_compiler import ABSENCE_CONTEXT_VERSION, extract_block as extract_absence_block
from .base_reviewer import Candidate
from .llm_reviewer import RealLLMRefused
from .llm_reviewer_v25 import LLMReviewerV25, LLMRunInfoV25


REVIEWER_VERSION = "llm-reviewer/2.6.0"

ABSENCE_INJECTION_HEADER = (
    "The following absence lessons were compiled deterministically "
    "from the same adjudicated run: the true defects this reviewer "
    "never claimed. Look for what you would otherwise walk past:"
)

_DEFAULT_ABSENCE_PATH = (
    Path(__file__).resolve().parent.parent / "CONTEXTO-AUSENCIAS.md"
)
_DECLARED_SHA_RE = re.compile(r"block-sha256: ([0-9a-f]{64})")
_DECLARED_VERSION_RE = re.compile(r"artifact: (\S+)")


def load_absence_block(path: Path) -> tuple[str, str, str]:
    """Load and verify the absence artifact at ``path``; returns
    (block, block_sha256, artifact_version).  Fail-closed: any
    anomaly raises :class:`RealLLMRefused`."""

    try:
        text = path.read_text()
    except OSError:
        raise RealLLMRefused(
            f"absence artifact not found at {path}; the v2.6 "
            "reviewer refuses to produce without its compiled "
            "absence context"
        )
    block = extract_absence_block(text)
    if block is None:
        raise RealLLMRefused(
            "absence artifact has no marked absence block; "
            "refusing to produce"
        )
    declared_sha = _DECLARED_SHA_RE.search(text)
    if not declared_sha:
        raise RealLLMRefused(
            "absence artifact declares no block-sha256; refusing "
            "to produce"
        )
    actual_sha = hashlib.sha256(block.encode("utf-8")).hexdigest()
    if declared_sha.group(1) != actual_sha:
        raise RealLLMRefused(
            "absence block hash mismatch: the artifact declares "
            f"{declared_sha.group(1)} but the block hashes to "
            f"{actual_sha}; refusing to produce from an unverified "
            "absence context"
        )
    declared_version = _DECLARED_VERSION_RE.search(text)
    if not declared_version:
        raise RealLLMRefused(
            "absence artifact declares no artifact version; "
            "refusing to produce"
        )
    return block, actual_sha, declared_version.group(1)


@dataclass
class LLMRunInfoV26(LLMRunInfoV25):
    """The v2.5 run info plus the absence provenance: which
    compiled omission context entered production, identified by
    content, next to the lessons provenance it inherits."""

    reviewer_version: str = REVIEWER_VERSION
    absence_sha256: str = ""
    absence_version: str = ""
    absence_block_chars: int = 0

    def to_dict(self) -> dict[str, object]:
        data = super().to_dict()
        data["absence_sha256"] = self.absence_sha256
        data["absence_version"] = self.absence_version
        data["absence_block_chars"] = self.absence_block_chars
        return data


class LLMReviewerV26(LLMReviewerV25):
    """v2.5 + the compiled absence context in production."""

    name = "alma-llm-reviewer-v26"

    def __init__(
        self,
        settings,
        *args,
        absence_block: str | None = None,
        absence_path: Path | None = None,
        absence_sha256: str | None = None,
        absence_version: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(settings, *args, **kwargs)
        if absence_block is None:
            block, sha, version = load_absence_block(
                absence_path or _DEFAULT_ABSENCE_PATH
            )
            absence_block, absence_sha256, absence_version = (
                block,
                sha,
                version,
            )
        self.absence_block = absence_block
        self.absence_sha256 = absence_sha256 or hashlib.sha256(
            absence_block.encode("utf-8")
        ).hexdigest()
        self.absence_version = absence_version or ABSENCE_CONTEXT_VERSION
        self.absence_block_chars = len(absence_block)

    # -- payloads: production only; selection inherited untouched -----

    def _inject_absence(self, payload: dict) -> dict:
        system = payload["messages"][0]
        system["content"] = (
            system["content"]
            + "\n\n"
            + ABSENCE_INJECTION_HEADER
            + "\n"
            + self.absence_block
        )
        return payload

    def build_deep_payload(
        self, pass_name: str, diff_text: str, context_text: str
    ) -> dict:
        return self._inject_absence(
            super().build_deep_payload(pass_name, diff_text, context_text)
        )

    def build_fallback_payload(
        self, selected: list, diff_text: str
    ) -> dict:
        return self._inject_absence(
            super().build_fallback_payload(selected, diff_text)
        )

    # -- production: the v2.5's, with v2.6 provenance tags applied
    #    between production and the birth-shaping stage ---------------

    def _produce(self, **kwargs) -> list[Candidate]:
        candidates = super()._produce(**kwargs)
        return [
            replace(
                c,
                producer=self.name,
                rule_id=f"llm_v26_{c.claim_type}",
            )
            for c in candidates
        ]

    def review(self, **kwargs) -> list[Candidate]:
        emitted = super().review(**kwargs)
        base = self.last_run_info
        self.last_run_info = LLMRunInfoV26(
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
            lessons_sha256=base.lessons_sha256,
            lessons_version=base.lessons_version,
            lessons_block_chars=base.lessons_block_chars,
            absence_sha256=self.absence_sha256,
            absence_version=self.absence_version,
            absence_block_chars=self.absence_block_chars,
        )
        return emitted


__all__ = [
    "ABSENCE_INJECTION_HEADER",
    "LLMReviewerV26",
    "LLMRunInfoV26",
    "REVIEWER_VERSION",
    "load_absence_block",
]
