"""Medición de adopción de la puerta 1.4.0 — PREREGISTRO-PUERTA-140.md §6.

Offline y determinista (US$0): re-juzga con la 1.3.0 y la 1.4.0 los
candidatos de tres universos y aplica el criterio de adopción escrito
antes de medir:

  se adopta SI Y SOLO SI  VP recuperados >= 1  Y  falsos nuevos = 0
  Y equivalencia exacta de aceptados en los tres universos
  Y la suite previa sigue verde con los tests nuevos en verde.

Universo 1 — candidatos asentados en los ledgers de los semáforos
corridos (primario: semáforo v2.1, runs/semaforo-v21-20261021/;
secundario: semáforo v2 intento 3, runs/semaforo-intento3/), ambos
brazos.  Chequeo de sanidad: el re-juicio offline con la 1.3.0 debe
reproducir EXACTAMENTE los estados de los ledgers ALMA asentados.
Un candidato es "real" (verdad de terreno) si su claim_type es la
clase plantada de su fixture, su archivo es el del ground truth y su
rango citado cubre la línea del defecto.  VP recuperado: rechazado
por la 1.3.0, needs_validation en la 1.4.0, y real.  Falso nuevo:
rechazado por la 1.3.0, needs_validation en la 1.4.0, y NO real.

Universo 2 — la batería roja de la 1.3.0 (69 ataques: 46 de la 1.2.0 +
23 de la 1.3.0).  Falso nuevo: cualquier ataque que cambie de estado
(de rechazado a needs_validation o aceptado, o de aceptado a otro).

Universo 3 — equivalencia de aceptados: (i) los pares heredados
aceptar/rechazar de la suite (INHERITED_PAIRS); (ii) los candidatos
del revisor mock (BaseReviewer) sobre todos los diffs de fixtures del
paquete.  Se enumeran además todos los movimientos a needs_validation.

Uso:  python3 medir_adopcion_v14.py [--json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent.alma_gate_v13 import AlmaGateV13  # noqa: E402
from agent.alma_gate_v14 import AlmaGateV14  # noqa: E402
from agent.base_reviewer import BaseReviewer, Candidate  # noqa: E402
from agent.diff_parser import parse_unified_diff  # noqa: E402

GATE13 = AlmaGateV13()
GATE14 = AlmaGateV14()

RUNS = (
    ("semáforo v2.1 (primario)", ROOT / "runs" / "semaforo-v21-20261021", "alma-llm-reviewer-v21"),
    ("semáforo v2 intento 3 (secundario)", ROOT / "runs" / "semaforo-intento3", "alma-llm-reviewer-v2"),
)
FIXTURE_ROOTS = ("fixtures", "fixtures_v2", "fixtures_v11", "fixtures_v13", "fixtures_semaforo")


def _key(candidate) -> tuple:
    return (
        candidate.rule_id,
        candidate.file,
        candidate.start_line,
        candidate.end_line,
        candidate.message,
    )


def statuses(result, candidates) -> list[str]:
    """Estados paralelos a `candidates` para un resultado de puerta.

    La 1.3.0 asienta un ledger paralelo a los candidatos.  La 1.4.0
    NO: los retenidos viven fuera del ledger, así que el estado se
    reconstruye por clave (rule_id, archivo, rango, mensaje)."""

    if hasattr(result, "needs_validation"):
        held = {
            (r.rule_id, r.file, r.start_line, r.end_line, r.message)
            for r in result.needs_validation
        }
        by_key = {
            (e.rule_id, e.file, e.start_line, e.end_line, e.message): e.status
            for e in result.ledger
        }
        return [
            "needs_validation" if _key(c) in held else by_key[_key(c)]
            for c in candidates
        ]
    return [entry.status for entry in result.ledger]


def judge(gate, candidates, diff):
    result = gate.validate(candidates, diff, "medicion-adopcion")
    return result, statuses(result, candidates)


def universe1() -> dict:
    report = {"runs": {}, "vp": [], "falsos": [], "accepted_equal": True, "sanity_ok": True}
    for label, run_dir, producer in RUNS:
        run = {"candidates": 0, "vp": 0, "falsos": 0, "moves": [], "sanity_mismatches": []}
        for ledger_path in sorted(run_dir.glob("*-ledger.json")):
            stem = ledger_path.name[: -len("-ledger.json")]
            arm, case = stem.split("-", 1)
            fixture_dir = ROOT / "fixtures_semaforo" / case
            truth = json.loads((fixture_dir / "ground_truth.json").read_text(encoding="utf-8"))
            diff = parse_unified_diff((fixture_dir / "diff.patch").read_text(encoding="utf-8"))
            settled = json.loads(ledger_path.read_text(encoding="utf-8"))
            if isinstance(settled, dict):  # forma 1.4.0 (no esperada en corridas viejas)
                settled_entries = settled["ledger"]
            else:
                settled_entries = settled
            candidates = []
            for entry in settled_entries:
                candidates.append(
                    Candidate(
                        rule_id=entry["rule_id"],
                        claim_type=entry["claim_type"],
                        file=entry["file"],
                        start_line=entry["start_line"],
                        end_line=entry["end_line"],
                        message=entry["message"],
                        evidence_text=tuple(e["text"] for e in entry["evidence"]),
                        severity_hint=entry.get("severity_hint", "high"),
                        category_hint=entry.get("category_hint", entry["claim_type"]),
                        producer=producer,
                    )
                )
            _, states13 = judge(GATE13, candidates, diff)
            result14, states14 = judge(GATE14, candidates, diff)
            held14 = {_key(r): r for r in result14.needs_validation}
            for candidate, settled_entry, s13, s14 in zip(
                candidates, settled_entries, states13, states14
            ):
                run["candidates"] += 1
                key = _key(candidate)
                if arm == "alma" and s13 != settled_entry["status"]:
                    run["sanity_mismatches"].append(
                        f"{stem}: re-juicio 1.3.0={s13} != asentado={settled_entry['status']}"
                    )
                real = (
                    candidate.claim_type == truth["planted_class"]
                    and candidate.file == truth["file"]
                    and candidate.start_line <= truth["defect_line"] <= candidate.end_line
                )
                if (s13 == "accepted") != (s14 == "accepted"):
                    report["accepted_equal"] = False
                    run["moves"].append(f"{stem}: ACEPTADO difiere 1.3.0={s13} 1.4.0={s14}")
                if s13 == "rejected" and s14 == "needs_validation":
                    blockers = [b["check"] for b in held14[key].blockers]
                    item = f"{stem} ({candidate.claim_type}, real={real}, blockers={blockers})"
                    if real:
                        run["vp"] += 1
                        report["vp"].append(item)
                    else:
                        run["falsos"] += 1
                        report["falsos"].append("U1 " + item)
                    run["moves"].append(f"{stem}: rejected -> needs_validation real={real} blockers={blockers}")
        report["runs"][label] = run
        if run["sanity_mismatches"]:
            report["sanity_ok"] = False
    return report


def universe2() -> dict:
    from test_gate_v12 import ATTACKS, attack_candidate, attack_diff
    from test_gate_v13 import NEW_ATTACKS

    moves = []
    falsos = []
    accepted_equal = True
    total = 0
    for attacks in (ATTACKS, NEW_ATTACKS):
        for attack_id, claim_type, _trick, lines, start, end, message, ctx in attacks:
            total += 1
            diff = parse_unified_diff(attack_diff(lines, ctx))
            candidate = attack_candidate(claim_type, start, end, lines, message)
            _, states13 = judge(GATE13, [candidate], diff)
            result14, states14 = judge(GATE14, [candidate], diff)
            s13 = states13[0]
            s14 = states14[0]
            if (s13 == "accepted") != (s14 == "accepted"):
                accepted_equal = False
            if s13 != s14:
                blockers = (
                    [b["check"] for b in result14.needs_validation[0].blockers]
                    if result14.needs_validation
                    else []
                )
                moves.append(f"{attack_id} ({claim_type}): {s13} -> {s14} blockers={blockers}")
                falsos.append(f"U2 {attack_id} ({claim_type}): {s13} -> {s14}")
    return {"total": total, "moves": moves, "falsos": falsos, "accepted_equal": accepted_equal}


def universe3() -> dict:
    from test_gate_v11 import INHERITED_PAIRS, candidate_for, make_diff

    moves = []
    accepted_equal = True
    total = 0

    def compare(candidates, diff, label):
        nonlocal accepted_equal, total
        _, states13 = judge(GATE13, candidates, diff)
        _, states14 = judge(GATE14, candidates, diff)
        for candidate, s13, s14 in zip(candidates, states13, states14):
            total += 1
            if (s13 == "accepted") != (s14 == "accepted"):
                accepted_equal = False
                moves.append(f"{label}: ACEPTADO difiere ({candidate.claim_type}) 1.3.0={s13} 1.4.0={s14}")
            elif s13 != s14:
                moves.append(f"{label}: {candidate.claim_type} {s13} -> {s14}")

    for claim_type, (accept_lines, reject_lines) in INHERITED_PAIRS.items():
        for lines in (accept_lines, reject_lines):
            diff = parse_unified_diff(make_diff("app/x.py", lines))
            compare([candidate_for(claim_type, "app/x.py", lines, 1, len(lines))], diff, f"INHERITED_PAIRS/{claim_type}")

    fixture_count = 0
    for root_name in FIXTURE_ROOTS:
        root = ROOT / root_name
        for fixture_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            diff_path = fixture_dir / "diff.patch"
            if not diff_path.exists():
                continue
            fixture_count += 1
            diff = parse_unified_diff(diff_path.read_text(encoding="utf-8"))
            compare(BaseReviewer().review(diff), diff, f"{root_name}/{fixture_dir.name}")
    return {"total": total, "fixtures": fixture_count, "moves": moves, "accepted_equal": accepted_equal}


def main() -> int:
    u1 = universe1()
    u2 = universe2()
    u3 = universe3()
    vp_total = len(u1["vp"])
    falsos_total = len(u1["falsos"]) + len(u2["falsos"])
    equivalencia = u1["accepted_equal"] and u2["accepted_equal"] and u3["accepted_equal"]
    adoptada = vp_total >= 1 and falsos_total == 0 and equivalencia and u1["sanity_ok"]
    out = {
        "universo1": u1,
        "universo2": u2,
        "universo3": u3,
        "vp_recuperados": vp_total,
        "falsos_nuevos": falsos_total,
        "equivalencia_aceptados": equivalencia,
        "sanidad_u1": u1["sanity_ok"],
        "veredicto": "ADOPTADA" if adoptada else "NO ADOPTADA",
    }
    if "--json" in sys.argv:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(f"Universo 1: {sum(r['candidates'] for r in u1['runs'].values())} candidatos asentados; "
              f"VP recuperados={vp_total} {u1['vp']}; falsos U1={len(u1['falsos'])} {u1['falsos']}; "
              f"sanidad 1.3.0={'OK' if u1['sanity_ok'] else 'FALLA'}")
        print(f"Universo 2: {u2['total']} ataques; movimientos={u2['moves']}")
        print(f"Universo 3: {u3['total']} candidatos ({u3['fixtures']} fixtures + pares heredados); "
              f"movimientos={u3['moves']}")
        print(f"Equivalencia de aceptados en los tres universos: {equivalencia}")
        print(f"VEREDICTO §6: {out['veredicto']} (VP={vp_total}, falsos={falsos_total})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
