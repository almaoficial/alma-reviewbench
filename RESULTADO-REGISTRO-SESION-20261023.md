# Resultado — Registro de sesión del runner: la precondición de la nº 311, construida

**Fecha:** 2026-10-23 · **Papel:** `PREREGISTRO-REGISTRO-SESION.md`
(diseño declarado ANTES de construir, §2).
**Costo: US$0** — construcción en seco sobre archivos locales;
sin llamadas a modelos, sin portal, sin publicación.

## Veredicto en una línea

La precondición dura que el cierre de la nº 311 declaró —
ninguna corrida futura sin un registro persistido del lado
propio — **existe y está probada**: el runner ahora asienta
siempre, por cada PR y por cada candidato, qué se produjo, qué
decidió la puerta y con qué razón, y cuánto gasto se estimó
contra el freno, en un JSONL append-only con encadenamiento
por hash (`alma-run-ledger/1.0`) que hace detectable
cualquier pérdida posterior — la integridad por cadena y la
completitud por auditoría. En la nº 311 ese registro no
existió y la retención quedó SIN MEDIR; con esta pieza, una
corrida tipo 311 deja las decisiones de **todos** los
candidatos asentadas, no solo la del único emitido (prueba d).

## 1. Qué se construyó

**`agent/run_ledger.py`** (el módulo; formato
`alma-run-ledger/1.0`):

- **Línea-evento** con `seq` sin huecos, `ts`, `run_id`,
  `event`, `data`, `prev` y `hash` (sha256 del JSON canónico
  del objeto sin `hash`; génesis = 64 ceros). Cada append es
  una escritura de línea completa + `flush` + `fsync`.
- **Eventos:** `session_open` (brazo/config snapshot, puerta
  y `policy_sha256`, `image_sha256` — null declarado si la
  imagen no lo expone —, freno `RB_MAX_SPEND_USD`, PR),
  `candidate` (uno por candidato, con `candidate_id` =
  dirección por contenido: sha256 canónico de
  `{rule_id, claim_type, file, start_line, end_line, message}`
  truncado a 16 hex — el mismo reclamo tiene el mismo id en
  cualquier corrida), `gate_decision` (uno por candidato:
  `accepted` / `rejected` con sus razones del ledger;
  `needs_validation` con los códigos de bloqueo extraídos
  **más los blockers crudos**; en el brazo base, `accepted`
  con la razón de bypass), `spend` (estimación del runner
  contra el freno, `cost_source: "runner_estimate"` — la
  facturación real la reconcilia el papel de corrida contra
  el portal, declarado en el pre-registro), `session_close`
  (conteos del PR y marca `resumed`) y `session_error`
  (best-effort desde el camino de error).
- **Recuperación al abrir:** cola rasgada (crash a mitad de
  append, incluido un carácter UTF-8 partido) se descarta y
  se trunca al final de la última línea íntegra, con el
  descarte expuesto en `recovered_torn_tail`; corrupción en
  el medio **falla cerrado** (`RunLedgerError`): no se
  «repara» en silencio.
- **Deduplicación al retomar:** `candidate`,
  `gate_decision`, `spend` y `session_close` llevan
  `dedupe_key` por `(run_id, pr_number[, candidate_id])`;
  re-emitir tras un kill no duplica decisiones ya asentadas.
  Declarado en el papel: un `run_id` por intento — si un PR
  se re-corre con insumos distintos bajo el mismo `run_id`,
  la clave colisiona y el evento nuevo no se asienta dos
  veces.
- **Verificación (API pública):** `verify_chain(path)`
  (integridad: recomputa seq/prev/hash; localiza el `seq`
  roto) y `audit_completeness(path)` (completitud: por PR,
  sesiones abiertas/cerradas, candidatos vs decisiones,
  `decisions_missing`/`decisions_extra`, eventos de gasto).
  Son dos controles deliberadamente distintos: la cadena
  certifica lo que volvió; la auditoría dice lo que falta.

## 2. Integración en `agent/main.py` (solo observabilidad)

`main.py` es el único archivo existente tocado — sha256
`9ac76b6f…` → `5469ff6d…` — y solo en estos puntos:

1. imports de `uuid` y de las funciones de emisión de
   `run_ledger`;
2. `run_agent(...)` gana el kwarg opcional `run_ledger=None`
   (con `None` — todo llamador existente — el comportamiento
   es el de siempre) y tres emisiones envueltas en fail-soft
   anunciado por stderr: `candidate` tras la producción,
   `gate_decision` tras la puerta o el bypass, `spend` al
   final. Ninguna salida existente cambia: ni `findings`,
   ni el ledger de la puerta, ni el run-info, ni códigos de
   retorno;
3. helper `_selected_gate_identity(config)` extraído de
   `_print_applied_config` (la salida impresa es la misma) y
   helper `_resolve_run_ledger_path(...)`: `ALMA_RUN_LEDGER_PATH`
   → `RB_CONFIG_RUN_LEDGER` (`off` es el único apagado) →
   **default `run-ledger.jsonl` junto al `--out`, prendido
   siempre** — la corrección exacta del defecto de la
   nº 311, donde escribir el ledger era opt-in por flag;
4. `main()` abre el registro tras identificar el PR (si no
   puede, lo anuncia por stderr — `run-ledger disabled: …` —
   y la corrida sigue: la ausencia nunca más es silenciosa),
   emite `session_open`, pasa el registro a `run_agent`, y
   tras escribir las salidas emite `session_close`, imprime
   por stdout la línea `run_ledger events=<n> head=<hash>`
   (segundo canal: los logs del portal siempre vuelven, y
   dicen cuántos eventos y con qué cabeza debieron volver)
   y asienta `session_error` en el camino de excepción.

## 3. Pruebas de persistencia (las cinco del pre-registro, §3)

`tests/test_run_ledger.py` — **11/11 OK**:

- **(a) Corrida simulada completa:** 3 PRs por instancias
  separadas del registro (el patrón real, un proceso por
  PR), puerta 1.4.1 y un PR de brazo base: la cadena
  verifica y la auditoría cierra completa, decisiones =
  candidatos (2/2) por PR.
- **(b) Matar y retomar:** sesión sin cerrar + cola rasgada
  escrita a mano → reapertura recupera (`recovered_torn_tail
  = 1`), la sesión se ve sin cerrar, y re-emitir el mismo PR
  bajo el mismo `run_id` no duplica **ningún** evento
  (conteo por `dedupe_key` = 1; total de eventos intacto).
- **(c) Truncación detectable, dos veces:** cortar la cola
  deja la cadena de lo que queda válida pero la auditoría
  reporta la incompletitud; cortar a mitad de línea y
  alterar un byte en el medio rompen `verify_chain` en el
  `seq` exacto. Abrir un archivo corrupto en el medio
  rehúsa (`RunLedgerError`).
- **(d) El escenario nº 311 no se repite:** modo ALMA +
  puerta 1.4.1 sobre el fixture 01 (2 candidatos, 1 solo
  finding emitido): quedan asentadas **2 decisiones** —
  aceptado y rechazado, con razones — y la auditoría no
  reporta ninguna ausente. La retención es el registro, no
  el emitido. Más: una decisión `needs_validation`
  sintética conserva su código de bloqueo
  (`sin_regla_de_verificacion_en_puerta`) y sus blockers
  crudos en el evento.
- **(e) Montaje en solo lectura, simulado:** con la ruta
  del registro bajo un padre que no es directorio (la
  apertura debe fallar), el CLI completa la corrida,
  escribe los findings, devuelve 0 y anuncia
  `run-ledger disabled` por stderr — nada se pierde en
  silencio. Y dos invocaciones CLI separadas del mismo
  `run_id` encadenan en **un solo archivo** que verifica y
  audita completo (2 PRs, sesiones 1/1 abiertas/cerradas).

## 4. Verificación de cierre

- **Suite completa: 362/362 OK.** Desglose honesto del
  número: 337 a la apertura de esta tarea + 14 de la pieza
  hermana del puntaje neto (`tests/test_net_score.py`,
  cerrada en paralelo) + **11 nuevas de
  `tests/test_run_ledger.py`**.
- **Semáforo dry 16/16:** la batería
  `test_battery_16_of_16_without_refusals` pasa dentro de la
  suite en sus cuatro portadores (v22–v25: 61 tests OK en la
  corrida dirigida de esos módulos).
- **Congelados byte-idénticos** (sha256 antes = después,
  foto completa al abrir y al cerrar): puertas 1.0.0
  `4223cb05…`, 1.1.0 `fdd974f1…`, 1.2.0 `c5c32bfc…`, 1.3.0
  `d3b993d4…`, 1.4.0 `b16c5a79…`, 1.4.1 `08d813e9…`, 1.5.0
  `71b1996b…`, `claim_contract.py` `7df8abc7…`,
  `birth_shaper.py` `2b127b23…`, revisores v2.3 `a78bdd6d…`,
  v2.4 `ae378c2e…`, v2.5 `7546d7d9…`, compiladores de
  lecciones/ausencias/censo y ambos contextos con su
  provenance. Las únicas diferencias contra la foto:
  `agent/main.py` (esta integración, declarada arriba),
  `agent/run_ledger.py` (nuevo) y `agent/net_score.py`
  (nuevo, de la pieza hermana — no de esta tarea).

## 5. Qué queda para el montaje real (corrida paga estacionada)

Heredado del pre-registro §5, sin rediseñar: (i) setear
`RB_RUN_ID` por intento y `RB_IMAGE_SHA256` con el digest
publicado en la config del portal; (ii) recolectar
`run-ledger.jsonl` como salida requerida y correr
`verify_chain` + `audit_completeness` **antes** de adjudicar
— una corrida cuyo registro no audita completo no se
adjudica, se diagnostica; (iii) reconciliar el `spend` del
registro (estimación) contra el saldo del portal (real) en
el papel de la corrida. Nada de esto se ejecuta acá: la
validación paga sigue **estacionada** a la espera del tope
de línea de Alejandro, y ningún revisor nuevo quedó montado
por esta pieza (v2.4/v2.5 siguen sin montar ni adoptar).

— Resultado del registro de sesión del runner, 2026-10-23.
Gasto: **US$0**.
