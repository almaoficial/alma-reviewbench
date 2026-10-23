"""Run session ledger — the runner's own append-only record.

Paper: ``PREREGISTRO-REGISTRO-SESION.md`` (2026-10-23).

The defect this module closes, from run nº 311: the gate's
decision ledger was written only when an external flag asked
for it, and the portal's output package did not carry it — of
the ≤165 candidates the gate saw, only the single emitted
finding kept an identity, the retention split never existed in
the record and retention purity stayed UNMEASURED.  The line
closed with a hard precondition for any future run: no launch
without a record persisted on our own side.

This module is that record.  It differs from the gate ledger
in regime, not content: it is part of the runner, written
always, once per candidate and once per decision, in a
hash-chained JSONL format (``alma-run-ledger/1.0``) that makes
any later loss detectable — chain verification proves the
integrity of what came back, and the completeness audit
proves that what should be there is there.  Every append is
one full-line write plus fsync, a torn tail from a killed
process is recovered on open (never silently), a corrupt
middle line fails closed, and re-emitting an event after a
restart dedupes on its declared key instead of duplicating a
decision.

The ledger never changes production behaviour: it observes.
Opening or appending may raise :class:`RunLedgerError`; the
runner catches it, announces the failure on stderr and runs
without the record — announced, never silent.
"""

from __future__ import annotations

from dataclasses import is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping


LEDGER_FORMAT = "alma-run-ledger/1.0"
GENESIS_PREV = "0" * 64


class RunLedgerError(RuntimeError):
    """The session ledger cannot be opened, written or trusted."""


def _canonical(obj: object) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _line_hash(record: Mapping[str, object]) -> str:
    body = {k: v for k, v in record.items() if k != "hash"}
    return hashlib.sha256(_canonical(body)).hexdigest()


def candidate_id_for(
    *,
    rule_id: str,
    claim_type: str,
    file: str,
    start_line: int,
    end_line: int,
    message: str,
) -> str:
    """Content address of a candidate claim: the first 16 hex
    chars of the sha256 of its canonical identity.  The same
    claim has the same id in any run, which is what lets
    decisions be matched against candidates and against gold."""

    identity = {
        "rule_id": rule_id,
        "claim_type": claim_type,
        "file": file,
        "start_line": start_line,
        "end_line": end_line,
        "message": message,
    }
    return hashlib.sha256(_canonical(identity)).hexdigest()[:16]


def _field(obj: object, name: str) -> object:
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name)


def candidate_id_of(candidate: object) -> str:
    return candidate_id_for(
        rule_id=str(_field(candidate, "rule_id")),
        claim_type=str(_field(candidate, "claim_type")),
        file=str(_field(candidate, "file")),
        start_line=int(_field(candidate, "start_line")),
        end_line=int(_field(candidate, "end_line")),
        message=str(_field(candidate, "message")),
    )


def _blocker_code(blocker: object) -> str:
    if isinstance(blocker, Mapping):
        for key in ("code", "blocker", "kind", "reason"):
            value = blocker.get(key)
            if value:
                return str(value)
        return ",".join(sorted(str(k) for k in blocker.keys()))
    return str(blocker)


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _jsonable(v) for k, v in vars(value).items()}
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def read_events(path: Path) -> list[dict]:
    """Parse the complete lines of a ledger file.  A torn final
    line (no trailing newline) is ignored here; verification
    and recovery are the functions that judge it."""

    raw = Path(path).read_bytes()
    if not raw:
        return []
    text = raw.decode("utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    events: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def verify_chain(path: Path) -> dict:
    """Recompute seq/prev/hash over the file as it stands."""

    errors: list[str] = []
    raw = Path(path).read_bytes() if Path(path).exists() else b""
    if not raw:
        return {"ok": True, "lines": 0, "head_hash": GENESIS_PREV, "errors": []}
    torn_tail = not raw.endswith(b"\n")
    text = raw.decode("utf-8", errors="replace")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    prev = GENESIS_PREV
    count = 0
    for idx, line in enumerate(lines):
        is_last = idx == len(lines) - 1
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"seq {idx}: unparseable line")
            if is_last and torn_tail:
                errors[-1] += " (torn tail)"
            break
        if record.get("seq") != idx:
            errors.append(
                f"seq {idx}: recorded seq is {record.get('seq')!r}"
            )
        if record.get("prev") != prev:
            errors.append(f"seq {idx}: prev does not match the chain")
        if _line_hash(record) != record.get("hash"):
            errors.append(f"seq {idx}: hash mismatch")
        prev = str(record.get("hash"))
        count += 1
        if errors:
            break
    if torn_tail and not errors:
        errors.append("file ends in a torn line (no trailing newline)")
    return {
        "ok": not errors,
        "lines": count,
        "head_hash": prev,
        "errors": errors,
    }


def audit_completeness(path: Path) -> dict:
    """What should be there vs what is: per (run_id, pr) —
    sessions opened/closed, candidates seated, decisions
    seated, decision ids missing for seated candidates."""

    events = read_events(path)
    sessions: dict[tuple, dict] = {}
    order: list[tuple] = []

    def bucket(key: tuple) -> dict:
        if key not in sessions:
            sessions[key] = {
                "run_id": key[0],
                "pr_number": key[1],
                "opened": 0,
                "closed": 0,
                "errors": 0,
                "candidates": set(),
                "decisions": set(),
                "spend_events": 0,
            }
            order.append(key)
        return sessions[key]

    for record in events:
        data = record.get("data") or {}
        key = (record.get("run_id"), data.get("pr_number"))
        entry = bucket(key)
        kind = record.get("event")
        if kind == "session_open":
            entry["opened"] += 1
        elif kind == "session_close":
            entry["closed"] += 1
        elif kind == "session_error":
            entry["errors"] += 1
        elif kind == "candidate":
            entry["candidates"].add(data.get("candidate_id"))
        elif kind == "gate_decision":
            entry["decisions"].add(data.get("candidate_id"))
        elif kind == "spend":
            entry["spend_events"] += 1

    per_pr: list[dict] = []
    complete = True
    for key in order:
        entry = sessions[key]
        missing = sorted(entry["candidates"] - entry["decisions"])
        extra = sorted(entry["decisions"] - entry["candidates"])
        unclosed = entry["opened"] - entry["closed"] - entry["errors"]
        if missing or extra or unclosed > 0:
            complete = False
        per_pr.append(
            {
                "run_id": entry["run_id"],
                "pr_number": entry["pr_number"],
                "sessions_opened": entry["opened"],
                "sessions_closed": entry["closed"],
                "session_errors": entry["errors"],
                "candidates": len(entry["candidates"]),
                "decisions": len(entry["decisions"]),
                "decisions_missing": missing,
                "decisions_extra": extra,
                "spend_events": entry["spend_events"],
            }
        )
    return {"complete": complete, "per_pr": per_pr}


class RunLedger:
    """An opened session ledger: scans and verifies what is
    already there, recovers a torn tail, then appends chained
    events with fsync durability and dedupe on declared keys."""

    def __init__(self, path: Path, run_id: str | None = None) -> None:
        self.path = Path(path)
        self.run_id = run_id
        self.recovered_torn_tail = 0
        self._seq = 0
        self._prev = GENESIS_PREV
        self._dedupe: dict[str, int] = {}
        self._events: list[dict] = []
        self._fh = None
        if self.path.exists() and self.path.stat().st_size > 0:
            self._recover()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(self.path, "a", encoding="utf-8")
        except OSError as exc:
            raise RunLedgerError(
                f"cannot open run ledger at {self.path}: {exc}"
            ) from exc

    # -- open / recovery ---------------------------------------------

    def _recover(self) -> None:
        raw = self.path.read_bytes()
        torn = not raw.endswith(b"\n")
        raw_lines = raw.split(b"\n")
        if raw_lines and raw_lines[-1] == b"":
            raw_lines.pop()
        lines: list[str] = []
        for idx, raw_line in enumerate(raw_lines):
            try:
                lines.append(raw_line.decode("utf-8"))
            except UnicodeDecodeError:
                if idx == len(raw_lines) - 1 and torn:
                    # A crash mid-write can split a multi-byte
                    # character: that is a torn tail, handled by
                    # the same path as a torn JSON line below.
                    lines.append("")
                    break
                raise RunLedgerError(
                    f"run ledger {self.path} is not valid UTF-8 "
                    f"at line {idx}"
                )
        good_bytes = 0
        prev = GENESIS_PREV
        for idx, line in enumerate(lines):
            is_last = idx == len(lines) - 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                if is_last:
                    self.recovered_torn_tail += 1
                    break
                raise RunLedgerError(
                    f"run ledger {self.path} is corrupt at line {idx}: "
                    "unparseable line in the middle of the chain"
                )
            if (
                record.get("seq") != idx
                or record.get("prev") != prev
                or _line_hash(record) != record.get("hash")
            ):
                raise RunLedgerError(
                    f"run ledger {self.path} fails verification at "
                    f"line {idx}; refusing to append to a broken chain"
                )
            prev = str(record["hash"])
            self._events.append(record)
            key = (record.get("data") or {}).get("dedupe_key")
            if key:
                self._dedupe[str(key)] = idx
            good_bytes += len(line.encode("utf-8")) + 1
        self._seq = len(self._events)
        self._prev = prev
        if torn and lines:
            # A final line that parsed but was never newline-
            # terminated was not durably seated: drop it too.
            last = self._events[-1] if self._events else None
            if last is not None and len(lines) == len(self._events):
                self._events.pop()
                self._dedupe = {
                    k: v
                    for k, v in self._dedupe.items()
                    if v != last["seq"]
                }
                self._seq = len(self._events)
                self._prev = (
                    str(self._events[-1]["hash"])
                    if self._events
                    else GENESIS_PREV
                )
                self.recovered_torn_tail += 1
                good_bytes -= len(lines[-1].encode("utf-8")) + 1
        if self.recovered_torn_tail:
            with open(self.path, "r+b") as fh:
                fh.truncate(good_bytes)

    # -- append --------------------------------------------------------

    def append(
        self,
        event: str,
        data: Mapping[str, object],
        *,
        dedupe_key: str | None = None,
    ) -> int | None:
        """Append one chained event.  Returns its seq, the
        existing seq when the dedupe key was already seated,
        and raises RunLedgerError on write failure."""

        payload = dict(data)
        if dedupe_key is not None:
            payload["dedupe_key"] = dedupe_key
            if dedupe_key in self._dedupe:
                return self._dedupe[dedupe_key]
        record: dict[str, object] = {
            "seq": self._seq,
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "event": event,
            "data": _jsonable(payload),
            "prev": self._prev,
        }
        record["hash"] = _line_hash(record)
        line = (
            json.dumps(record, ensure_ascii=False, sort_keys=False)
            + "\n"
        )
        try:
            self._fh.write(line)
            self._fh.flush()
            os.fsync(self._fh.fileno())
        except OSError as exc:
            raise RunLedgerError(
                f"cannot append to run ledger {self.path}: {exc}"
            ) from exc
        seq = self._seq
        self._seq += 1
        self._prev = str(record["hash"])
        self._events.append(record)
        if dedupe_key is not None:
            self._dedupe[dedupe_key] = seq
        return seq

    # -- queries -------------------------------------------------------

    @property
    def event_count(self) -> int:
        return self._seq

    @property
    def head_hash(self) -> str:
        return self._prev

    def unclosed_session(self, pr_number: int) -> bool:
        opened = 0
        closed = 0
        for record in self._events:
            if record.get("run_id") != self.run_id:
                continue
            data = record.get("data") or {}
            if data.get("pr_number") != pr_number:
                continue
            if record.get("event") == "session_open":
                opened += 1
            elif record.get("event") in ("session_close", "session_error"):
                closed += 1
        return opened > closed

    def close(self) -> None:
        if self._fh is not None:
            try:
                self._fh.flush()
                os.fsync(self._fh.fileno())
            finally:
                self._fh.close()
                self._fh = None

    def __enter__(self) -> "RunLedger":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# -- emission helpers (plain data in, events out) ----------------------


def _key(run_id: str | None, pr_number: int, *rest: object) -> str:
    parts = [str(run_id), str(pr_number)] + [str(r) for r in rest]
    return ":".join(parts)


def record_session_open(
    ledger: RunLedger,
    *,
    segment: str,
    agent: str,
    mode: str,
    backend: str,
    config: Mapping[str, str],
    gate_version: str,
    policy_sha256: str,
    image_sha256: str | None,
    max_spend_usd: float | None,
    pr: Mapping[str, object],
) -> None:
    ledger.append(
        "session_open",
        {
            "segment": segment,
            "ledger_format": LEDGER_FORMAT,
            "agent": agent,
            "mode": mode,
            "backend": backend,
            "config": dict(sorted(config.items())),
            "gate_version": gate_version,
            "policy_sha256": policy_sha256,
            "image_sha256": image_sha256,
            "max_spend_usd": max_spend_usd,
            "pr_number": int(pr["pr_number"]),
            "pr": {
                "repo": str(pr.get("repo") or ""),
                "pr_number": int(pr["pr_number"]),
                "base": str(pr.get("base") or ""),
                "head": str(pr.get("head") or ""),
            },
        },
    )


def record_candidates(
    ledger: RunLedger, *, pr_number: int, candidates: list
) -> list[str]:
    ids: list[str] = []
    for candidate in candidates:
        cid = candidate_id_of(candidate)
        ids.append(cid)
        ledger.append(
            "candidate",
            {
                "pr_number": pr_number,
                "candidate_id": cid,
                "rule_id": str(_field(candidate, "rule_id")),
                "claim_type": str(_field(candidate, "claim_type")),
                "file": str(_field(candidate, "file")),
                "start_line": int(_field(candidate, "start_line")),
                "end_line": int(_field(candidate, "end_line")),
                "message": str(_field(candidate, "message")),
                "producer": str(_field(candidate, "producer")),
            },
            dedupe_key=_key(ledger.run_id, pr_number, "candidate", cid),
        )
    return ids


def record_gate_decisions(
    ledger: RunLedger,
    *,
    pr_number: int,
    ledger_entries: list,
    needs_validation: list | None,
) -> dict[str, int]:
    """One gate_decision per gate-ledger entry and per held
    record — every candidate the gate disposed of, not only
    the emitted ones.  Returns the status counts."""

    counts = {"accepted": 0, "rejected": 0, "needs_validation": 0}
    for entry in ledger_entries:
        data = entry if isinstance(entry, Mapping) else entry.to_dict()
        cid = candidate_id_for(
            rule_id=str(data["rule_id"]),
            claim_type=str(data["claim_type"]),
            file=str(data["file"]),
            start_line=int(data["start_line"]),
            end_line=int(data["end_line"]),
            message=str(data["message"]),
        )
        status = str(data["status"])
        if status in counts:
            counts[status] += 1
        ledger.append(
            "gate_decision",
            {
                "pr_number": pr_number,
                "candidate_id": cid,
                "status": status,
                "reasons": [str(r) for r in data.get("reasons") or []],
                "validator_version": str(
                    data.get("validator_version") or ""
                ),
                "policy_sha256": str(data.get("policy_sha256") or ""),
            },
            dedupe_key=_key(
                ledger.run_id, pr_number, "decision", cid
            ),
        )
    for record in needs_validation or []:
        data = record if isinstance(record, Mapping) else record.to_dict()
        cid = candidate_id_for(
            rule_id=str(data["rule_id"]),
            claim_type=str(data["claim_type"]),
            file=str(data["file"]),
            start_line=int(data["start_line"]),
            end_line=int(data["end_line"]),
            message=str(data["message"]),
        )
        blockers = list(data.get("blockers") or [])
        counts["needs_validation"] += 1
        ledger.append(
            "gate_decision",
            {
                "pr_number": pr_number,
                "candidate_id": cid,
                "status": "needs_validation",
                "reasons": [_blocker_code(b) for b in blockers],
                "blockers": _jsonable(blockers),
                "validator_version": str(
                    data.get("validator_version") or ""
                ),
                "policy_sha256": str(data.get("policy_sha256") or ""),
            },
            dedupe_key=_key(
                ledger.run_id, pr_number, "decision", cid
            ),
        )
    return counts


def record_spend(
    ledger: RunLedger,
    *,
    pr_number: int,
    estimated_cost_usd: float,
    max_spend_usd: float | None,
) -> None:
    ledger.append(
        "spend",
        {
            "pr_number": pr_number,
            "estimated_cost_usd": estimated_cost_usd,
            "max_spend_usd": max_spend_usd,
            "cost_source": "runner_estimate",
        },
        dedupe_key=_key(ledger.run_id, pr_number, "spend"),
    )


def record_session_close(
    ledger: RunLedger,
    *,
    pr_number: int,
    segment: str,
    counts: Mapping[str, int],
    findings_emitted: int,
    spend_estimated_usd: float,
    resumed: bool,
) -> None:
    ledger.append(
        "session_close",
        {
            "pr_number": pr_number,
            "segment": segment,
            "status": "ok",
            "candidates": counts.get("candidates", 0),
            "accepted": counts.get("accepted", 0),
            "rejected": counts.get("rejected", 0),
            "needs_validation": counts.get("needs_validation", 0),
            "findings_emitted": findings_emitted,
            "spend_estimated_usd": spend_estimated_usd,
            "resumed": resumed,
        },
        dedupe_key=_key(ledger.run_id, pr_number, "close"),
    )


def record_session_error(
    ledger: RunLedger,
    *,
    pr_number: int | None,
    segment: str,
    error: BaseException,
) -> None:
    try:
        ledger.append(
            "session_error",
            {
                "pr_number": pr_number,
                "segment": segment,
                "error_type": type(error).__name__,
                "error": str(error),
            },
        )
    except Exception:
        pass  # best-effort: the error path must not raise again


__all__ = [
    "GENESIS_PREV",
    "LEDGER_FORMAT",
    "RunLedger",
    "RunLedgerError",
    "audit_completeness",
    "candidate_id_for",
    "candidate_id_of",
    "read_events",
    "record_candidates",
    "record_gate_decisions",
    "record_session_close",
    "record_session_error",
    "record_session_open",
    "record_spend",
    "verify_chain",
]
