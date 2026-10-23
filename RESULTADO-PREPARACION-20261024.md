# RESULTADO — Preparación de la validación del 24/10/2026

**Encargo:** dejar el paquete de la corrida A/B del 24/10/2026
completo y verificado — aprobada por Alejandro el 23/10
(«No va a ser en enero va a ser mañana la corrida», sí sobre
el total de la línea ~US$131) — para que mañana solo falte
(a) su carga de saldo en OpenAI y (b) lanzar. **Gasto US$0:**
sin prácticas, sin cargas, sin llamadas a modelos; toda la
verificación corre con transportes guionados. Papel de la
corrida: `PREREGISTRO-VALIDACION-20261024.md` (10.145 B),
escrito ANTES de tocar código.

## 1. Estado por pieza

| Pieza | Estado |
|---|---|
| Pre-registro de la corrida | ✓ escrito, con vara, economía y procedimiento |
| Montaje de brazos (v24/v25/v26 + puerta v150) | ✓ hecho y probado en seco (ver §2–§3) |
| Registro de sesión en la ruta de corrida | ✓ `main.py` lleva `run_ledger` prendido por defecto; el extremo a extremo lo ejercita |
| Contextos dentro de la imagen (Dockerfile) | ✓ delta de una línea, probado por layout |
| Suite completa | ✓ **388/388 OK** (378 de apertura + 10 nuevas) |
| Congelados byte-idénticos | ✓ foto sha256 antes/después: 22/22 |
| Imágenes publicadas con sha256 | ✗ **BLOQUEADAS** en la compuerta del pipeline (ver §5) — todo lo demás listo |

## 2. El hallazgo de la preparación: los brazos no estaban montados

Los tres brazos estaban **diseñados** (papeles cerrados) pero
ninguno podía correr: `agent/main.py` seleccionaba revisores
solo hasta `v23` y puertas solo hasta `v141` en sus tres
lugares (`_select_gate`, `_selected_gate_identity` y, por
delegación, el resolver del v2.4 terminaba en `v141`), de modo
que `gate=v150` era rechazado en todas partes y cada brazo
habría muerto fail-closed antes de llamar a un modelo — la
muerte de la nº 310 por la vía de la selección. Segundo
bloqueo, en la imagen: los revisores v2.5/v2.6 resuelven su
contexto en `Path(__file__).parent.parent / "CONTEXTO-*.md"`
(en la imagen, `/app/CONTEXTO-*.md`) y el `Dockerfile` solo
copiaba `agent/` — ambos brazos habrían rehusado al
construirse dentro del contenedor. Los dos bloqueos se
cazaron en seco, a US$0, que es exactamente para lo que era
esta preparación.

## 3. El montaje (declarado en el pre-registro §3 y §4, antes)

- **`agent/llm_reviewer_v24.py`** (`ae378c2e…` → `f9d3578e…`):
  función nueva `_resolve_gate_v24` — la rama `v150` devuelve la
  familia especialista de la 1.5.0 (las 19 clases de la
  1.3.0, verificado por programa:
  `KNOWN_CLAIM_TYPES_V150` == las 19 de V13 ordenadas), la
  guía de clases de la 1.3.0 y la etiqueta
  `alma-evidence-gate/1.5.0`; todo otro valor delega en
  `_resolve_gate_v23` sin tocarlo. `from_env` del V24 (que
  V25/V26 heredan) la adopta. Los `REVIEWER_VERSION`
  (2.4.0/2.5.0/2.6.0) no cambian: son la identidad del revisor,
  no de sus bytes — declarado con su razón en el papel.
- **`agent/main.py`** (`5469ff6d…` → `228e5de5…`): imports de
  la puerta 1.5.0 y de los tres revisores; rama `v150` en
  `_select_gate` y en `_selected_gate_identity`; ramas
  `v24`/`v25`/`v26` en la selección de revisor, espejo de la
  de `v23`. Ninguna otra línea de comportamiento cambia; el
  registro de sesión (default prendido) ya vivía en este
  archivo y es lo que la imagen lleva.
- **`Dockerfile`**: una línea —
  `COPY CONTEXTO-LECCIONES.md CONTEXTO-AUSENCIAS.md /app/` —
  para que los contextos existan donde los revisores los
  buscan dentro del contenedor.
- **Re-fijado declarado:** las tablas de congelados de
  `tests/test_llm_reviewer_v25.py` y `test_llm_reviewer_v26.py`
  fijaban el hash del v2.4; el papel (§3) re-fija ese único
  valor en ambas al nuevo `f9d3578e…`. Sus `RESULTADO` quedan
  como el registro histórico de los bytes de su construcción.

## 4. Verificación (todo en seco)

`tests/test_montaje_validacion.py`, **10/10**: admisión de la
puerta (`_select_gate` → `AlmaGateV150` con el policy sha
congelado `16befdd1…`; identidad `v150`; puertas previas
intactas); el resolver (rama v150 con 19 clases y guía V13;
delegación idéntica a `_resolve_gate_v23` en v1–v141;
desconocida rehusada); construcción `from_env` de los tres
revisores con `gate=v150`; **extremo a extremo por
`run_agent`** — modo alma, revisor v2.6, puerta 1.5.0,
transporte guionado, registro de sesión activo: 1 candidato
citable, 1 finding emitido, ledger con
`validator_version = alma-evidence-gate/1.5.0`,
`verify_chain` OK y `audit_completeness` completo (la regla
de adjudicación del §6 del papel, ejercitada en seco); y
**layout de imagen**: los tres revisores se construyen desde
un árbol copiado con el layout exacto del contenedor
(`agent/` + los dos contextos en la raíz), en subproceso.
Suite completa **388/388 OK**; congelados 22/22 byte-idénticos
(puertas 1.0.0–1.5.0, contrato, formador, revisores
v2.3/v2.5/v2.6, compiladores, contextos, `net_score.py`,
`run_ledger.py`).

## 5. Las imágenes: el bloqueo exacto

El pipeline asentado de la línea es: sincronizar el paquete a
`almaoficial/alma-reviewbench` (main) → disparar el workflow
`reviewbench-image` por `workflow_dispatch` → el digest queda
en el run y en el package `reviewbench-agent`. **Los dos
primeros pasos son la compuerta humana del diseño**: el
disparo se hace en la UI de GitHub con la sesión de Alejandro
(así se publicaron la v2.3.1, workflow nº 7, y la v2.3.2), y
este entorno no tiene credenciales de GitHub (`gh` sin login)
ni el mecanismo de sincronización de snapshots, que corre por
el sistema del agente principal. No se improvisó otra vía.
**Lo que el sync debe llevar** (delta computado contra la
cabeza remota verificada `7bb8c493…`): difieren
`agent/main.py` y `agent/llm_reviewer_v24.py`; faltan en el
remoto `agent/run_ledger.py`, `agent/net_score.py`,
`agent/llm_reviewer_v26.py`, `agent/absence_compiler.py`,
`agent/executability_census.py` — más los papeles y tests de
la tanda local posterior al push del 22/10, el `Dockerfile`
corregido y los dos contextos con su provenance. Todo el
resto de `agent/` ya es byte-idéntico al remoto. Con el sync
hecho, el disparo es un clic y la verificación del digest en
dos fuentes (runs + packages) la hace el paso ejecutor antes
de lanzar, como manda el procedimiento del pre-registro §5.

## 6. Mañana — lo que queda en cada mano

**De Alejandro:** (1) cargar el saldo de OpenAI — el saldo
conocido es US$5,31 (22/10) menos US$0,1290 del juez; la
compuerta del papel es saldo verificado ≥ US$25 antes de
cada brazo, ~US$61 para los tres; (2) el sync + disparo de la
imagen por su sesión (o su sí para que el agente principal lo
sincronice por su mecanismo). **Del paso ejecutor:** verificar
el digest publicado en dos fuentes y asentarlo en
`RB_IMAGE_SHA256`; `RB_RUN_ID` único por intento; correr los
tres brazos en el orden del papel, mismo «Test run» de 25 PR,
Submit jamás, freno US$6,50/PR intocable; recolectar
`run-ledger.jsonl` de cada brazo como salida requerida;
**auditar cadena + completitud antes de adjudicar** (sin
auditoría completa no se adjudica, se diagnostica); adjudicar
contra el gold congelado con la vara del §2 del papel (P/R
grounded + neto, con la regla del neto ≤ 0); reconciliar el
`spend` estimado del registro contra el saldo real al cierre.

## 7. Qué NO afirma este resultado

El montaje no mide efecto alguno de los brazos: lo verificado
es que **pueden correr** (selección, puerta, contextos,
registro) y que la vara, el examen y la regla de adjudicación
quedaron escritos antes. La medición es la corrida de mañana,
y su resultado — el que sea — se asienta con el mismo tamaño
que este papel.
