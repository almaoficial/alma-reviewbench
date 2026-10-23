# Pre-registro — Registro de sesión del runner (session log propio)

**Fecha:** 2026-10-23 · **Aprobación:** Alejandro, 23/10/2026 («Lo
hagamos») · **Costo: US$0** — construcción en seco sobre archivos
locales; sin llamadas a modelos, sin portal, sin publicación.

## 1. El defecto que esta pieza cierra

La práctica ALMA nº 311 (22/10/2026) quedó parcialmente
inconmensurable por un defecto de observabilidad asentado en el
REGISTRO (entrada de la adjudicación completa de la nº 311): el
ledger de decisiones de la puerta solo se escribe si el entorno
trae `ALMA_LEDGER_PATH` o `RB_ALMA_LEDGER=1` (`agent/main.py`), y
el paquete de salidas del portal no lo incluyó. Consecuencia
medida: de los ≤165 candidatos que la puerta vio, solo quedó
identificado el único emitido; el split aceptados / rechazados /
`needs_validation` y el desglose por familia **no existen en el
registro**, la pureza de retención quedó **SIN MEDIR** y la
pérdida inexplicada se falsó en 66 por ausencia de ledger, no por
evidencia sobre la puerta.

El cierre de esa línea declaró la precondición dura para
cualquier corrida futura: **ningún lanzamiento sin un registro
persistido del lado propio**. Este papel construye esa
precondición. La diferencia con el ledger existente no es de
contenido sino de régimen: el ledger de la puerta es un artefacto
opcional que un flag externo tiene que recordar pedir; el
registro de sesión es parte del runner, se escribe siempre, por
cada PR, en un formato que hace **detectable** cualquier pérdida
posterior.

## 2. Diseño

### 2.1 Módulo y formato

- Módulo nuevo: `agent/run_ledger.py`, formato declarado
  `alma-run-ledger/1.0`. Ningún módulo existente se modifica
  salvo la integración de observabilidad en `agent/main.py`
  (§2.4).
- Archivo: **JSONL append-only**, una línea por evento. Cada
  línea es un objeto JSON con los campos:
  `seq` (entero, desde 0, sin huecos), `ts` (ISO-8601 UTC),
  `run_id` (string o null), `event` (string), `data` (objeto),
  `prev` (hex-64) y `hash` (hex-64).
- **Encadenamiento por hash:** `prev` es el `hash` de la línea
  anterior (la génesis usa 64 ceros) y `hash` es el sha256 del
  JSON canónico (claves ordenadas, separadores compactos, UTF-8)
  del objeto completo sin el campo `hash`. Toda truncación
  intermedia, inserción, borrado o alteración de una línea rompe
  la cadena en un `seq` localizable; la truncación de cola deja
  la cadena válida pero la **auditoría de completitud** (§2.5)
  detecta las sesiones abiertas sin cierre y las decisiones
  ausentes. Los dos controles son deliberadamente distintos:
  integridad de lo que hay, y completitud de lo que debería haber.
- **Durabilidad por evento:** cada append es una sola escritura
  de la línea completa seguida de `flush` + `os.fsync`. Un
  proceso muerto a mitad de corrida pierde, como máximo, el
  evento en vuelo.
- **Recuperación al abrir:** si el archivo termina en una línea
  rasgada (sin `\n` final o no parseable), el lector la descarta,
  trunca el archivo al final de la última línea íntegra y expone
  el conteo en `recovered_torn_tail`. Si la corrupción está en
  cualquier línea que no sea la última, abrir **falla cerrado**
  con `RunLedgerError`: un registro corrupto en el medio no se
  «repara» en silencio.
- **Deduplicación al retomar:** los eventos `candidate`,
  `gate_decision`, `spend` y `session_close` llevan
  `data.dedupe_key` derivada de `(run_id, pr_number[, candidate_id])`.
  Al abrir, el módulo indexa las claves existentes; re-emitir un
  evento con clave ya asentada es un no-op que devuelve el `seq`
  original. Matar el proceso a mitad y retomar el mismo PR no
  pierde ni duplica decisiones ya asentadas. Las decisiones son
  deterministas dados los mismos insumos; si un PR se re-corre
  con insumos distintos bajo el mismo `run_id`, la clave colisiona
  y el evento nuevo NO se asienta dos veces: el papel de corrida
  debe usar un `run_id` por intento (declarado, no escondido).

### 2.2 Eventos asentados

Por cada PR (cada invocación del runner procesa un PR):

1. `session_open` — `run_id`, `segment` (id de esta invocación),
   `agent`, `mode`, `backend`, snapshot ordenado de la config
   `RB_CONFIG_*`, puerta seleccionada (`version`,
   `policy_sha256`), `image_sha256` (de `RB_IMAGE_SHA256` o
   `RB_CONFIG_IMAGE_SHA256`; null declarado si la imagen no lo
   expone — el runner no puede inventar el digest de su propia
   imagen), `max_spend_usd` (de `RB_MAX_SPEND_USD`, null si no
   aplica) y el PR (`repo`, `pr_number`, `base`, `head`).
2. `candidate` — uno por candidato producido, con
   `candidate_id` = primeros 16 hex del sha256 del JSON canónico
   de `{rule_id, claim_type, file, start_line, end_line, message}`,
   más esos mismos campos y `producer`. El id es función del
   contenido: el mismo reclamo tiene el mismo id en cualquier
   corrida, que es lo que permite emparejar decisiones contra
   candidatos y contra el gold.
3. `gate_decision` — uno por candidato, sin excepción:
   `candidate_id`, `status` (`accepted` | `rejected` |
   `needs_validation`; en el brazo base, `accepted` con la razón
   de bypass asentada en el ledger de la puerta), `reasons`
   (las razones del ledger para aceptados/rechazados; para
   `needs_validation`, los códigos de bloqueo extraídos de cada
   blocker — primer valor presente entre `code`, `blocker`,
   `kind`, `reason` — **más los blockers crudos** bajo
   `blockers`, para que ningún código se pierda por extracción),
   `validator_version` y `policy_sha256` de la decisión.
4. `spend` — `estimated_cost_usd` (del run-info del revisor;
   0.0 en el backend mock), `max_spend_usd` y `cost_source:
   "runner_estimate"`. Declaración honesta: el runner solo ve su
   estimación; la facturación real la conoce el portal y la
   reconcilia el papel de corrida contra el saldo, como hasta
   ahora. El registro asienta la estimación y el freno contra el
   que se comparó, que es lo que la nº 311 tampoco conservó por PR.
5. `session_close` — conteos del PR (`candidates`, `accepted`,
   `rejected`, `needs_validation`, `findings_emitted`),
   `spend_estimated_usd`, `resumed` (true si ya existía una
   sesión abierta sin cierre para ese `(run_id, pr_number)`) y
   el `segment`.
6. `session_error` — tipo y mensaje de la excepción, asentado
   best-effort desde el camino de error de `main()` antes de
   devolver el código de fallo: las corridas que explotan también
   quedan en el registro.

### 2.3 Dónde vive el archivo

Resolución de ruta en `main()`, en este orden:
`ALMA_RUN_LEDGER_PATH` (entorno) → `RB_CONFIG_RUN_LEDGER`
(config; el valor `off` lo apaga, y es el único apagado) →
**default: `run-ledger.jsonl` junto al `--out`** (el directorio
que el propio runner ya escribe). Régimen: **prendido por
defecto**, no opt-in — esa es la corrección exacta del defecto
de la nº 311. La ruta vive del lado del runner (su imagen, su
filesystem de salida), no en un montaje opcional del portal; el
papel de la corrida paga (§5) declara `run-ledger.jsonl` como
salida requerida a recolectar, al mismo nivel que `findings.json`.

Segundo canal deliberado: al cerrar, `main()` imprime por stdout
una línea `alma-reviewbench run_ledger events=<n> head=<hash>`
que los logs del portal sí capturan siempre: aunque el archivo
se perdiera entero, queda asentado en el log cuántos eventos y
con qué hash de cabeza debió volver.

### 2.4 Integración en el runner (solo observabilidad)

`agent/main.py` es el único archivo existente que se toca, así:

- import del módulo nuevo y de sus funciones de emisión;
- `run_agent(...)` gana dos kwargs opcionales
  (`run_ledger=None`, `run_id=None`): con `None` (todo llamador
  existente) el comportamiento es byte-idéntico al actual. Con
  registro, emite `candidate` tras la producción,
  `gate_decision` tras la puerta (o el bypass del brazo base) y
  `spend` al final. Ninguna salida existente cambia: ni
  `findings`, ni el ledger de la puerta, ni el run-info, ni los
  códigos de retorno;
- `main()` resuelve la ruta (§2.3), abre el registro tras cargar
  el PR, emite `session_open`, pasa el registro a `run_agent`,
  emite `session_close` tras escribir las salidas, imprime la
  línea de stdout y asienta `session_error` en el camino de
  excepción;
- **fail-soft declarado:** si el registro no se puede abrir o un
  append falla, el runner lo anuncia por stderr
  (`run-ledger disabled: …`) y la corrida sigue produciendo sus
  salidas normales. La observabilidad jamás rompe la producción;
  y a diferencia de la nº 311, su ausencia nunca es silenciosa:
  queda en stderr, en el log y en la auditoría de completitud
  del papel de corrida. La verificación del registro, en cambio,
  es fail-closed (§2.5).

### 2.5 Verificación (API del módulo)

- `verify_chain(path)` → `{ok, lines, head_hash, errors[]}`:
  recomputa `seq`/`prev`/`hash` línea por línea; detecta
  alteración, inserción, borrado intermedio y línea rasgada.
- `audit_completeness(path)` → por `(run_id, pr_number)`:
  sesiones abiertas vs cerradas, candidatos asentados,
  decisiones asentadas, `decisions_missing` (ids de candidato
  sin decisión), `decisions_extra`, eventos de gasto. Es la
  auditoría que, corrida sobre la nº 311, habría dicho en el
  acto «165 candidatos, 1 decisión» en vez de descubrirse en la
  adjudicación.

## 3. Pruebas declaradas (tests/test_run_ledger.py)

- **(a) Corrida simulada completa:** varios PRs a través de
  instancias separadas del registro (el patrón real: un proceso
  por PR) sobre el backend mock con la puerta v141 y un PR de
  brazo base, vía `run_agent`: la cadena verifica, la auditoría
  cierra completa y decisiones = candidatos por PR.
- **(b) Matar y retomar:** eventos parciales de un PR, cola
  rasgada escrita a mano (crash a mitad de append), reapertura
  con recuperación, re-emisión de los mismos eventos: sin
  pérdidas y sin duplicados (conteo por `dedupe_key` = 1),
  cadena válida.
- **(c) Truncación detectable:** (i) cortar las últimas líneas
  → la cadena de lo que queda verifica, pero la auditoría
  reporta la sesión sin cierre y las decisiones ausentes;
  (ii) cortar a mitad de una línea intermedia → `verify_chain`
  falla en ese `seq`. Más: alterar un byte en el medio →
  `verify_chain` falla en ese `seq`.
- **(d) El escenario nº 311 no se repite:** `run_agent` en modo
  ALMA con la puerta v141 sobre un diff fixture con varios
  candidatos: **cada** candidato tiene exactamente una
  `gate_decision` asentada (aceptados + rechazados +
  retenidos), aunque los `findings` emitidos sean menos — el
  ledger de la puerta de una corrida tipo 311 habría quedado
  completo, no solo el emitido.
- **(e) Montaje del portal en solo lectura (simulado):** la
  ruta del registro apunta a un directorio sin permiso de
  escritura → `main()` completa la corrida, escribe sus salidas,
  devuelve 0 y anuncia la falla del registro por stderr (nada
  se pierde en silencio); y con la ruta en un directorio propio
  escribible, dos invocaciones CLI separadas del mismo `run_id`
  encadenan en un solo archivo continuo que verifica.

## 4. Qué NO hace esta pieza

- No monta ningún revisor nuevo en `main.py` (v2.4/v2.5 siguen
  sin montar ni adoptar), no toca ninguna puerta, contrato,
  formador, compilador ni contexto: los hashes congelados deben
  salir byte-idénticos y se verifican al cierre.
- No llama modelos ni al portal; no publica ni pushea nada.
- No mide efecto alguno sobre la producción: es infraestructura
  de observabilidad. Su propia vara es la de §3: las cinco
  pruebas, la suite completa en verde y el semáforo dry 16/16.

## 5. Qué queda para la corrida paga estacionada

Declarado aquí para que el papel de esa corrida lo herede sin
rediseñar: (i) `RB_RUN_ID` por intento y `RB_IMAGE_SHA256` con
el digest publicado de la imagen, seteados en la config del
portal; (ii) `run-ledger.jsonl` como salida requerida en la
recolección, con `verify_chain` + `audit_completeness` corridos
**antes** de adjudicar — una corrida cuyo registro no audita
completo no se adjudica, se diagnostica; (iii) la reconciliación
del gasto: `spend` del registro (estimación) contra el saldo del
portal (real), con ambas cifras asentadas.
