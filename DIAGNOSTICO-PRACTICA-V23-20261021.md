# Diagnóstico en seco — Práctica v2.3 (base nº 296): por qué murió «at run-agent (3, 4)»

Corrida nº 296 (brazo base · reviewer=v23 · gate=v13 · gpt-5.6-sol ·
medium), lanzada el 2026-10-21 22:26:40 EDT. El portal la cerró
FAILED «at run-agent (3, 4)» sin puntajes. Este diagnóstico responde
por qué, con los outputs reales. US$0: sin corridas, sin llamadas,
sin portal.

## 0. Material y una ausencia que acota el diagnóstico

Material: el zip de outputs de la corrida
(`alma-reviewer-run-296-output.zip`, 44.779 B): `summary.txt`,
`logs/run-status.jsonl`, `logs/run-shard-1..4.log`,
`logs/preflight.txt`, `logs/egress-proxy.log` (vacío) y, por PR,
`prs/<pr>/agent.log` y — solo cuando el PR terminó — `findings.json`.
Saldos asentados fuera del zip: US$16,52 antes (22:25 EDT) →
US$3,02 después (22:52 EDT).

La ausencia: el agente **no asienta el cuerpo de la respuesta del
modelo ni su `finish_reason`** cuando una pasada falla. De cada
intento muerto sobrevive solo la línea de error que el proceso
imprimió antes de salir. Por eso la §5 distingue lo probado por los
logs de lo inferido: el mecanismo fino (qué contenía exactamente la
respuesta no parseable) es inferencia acotada y declarada como tal,
no lectura directa. El zip tampoco trae `logs/labels.txt` (el README
lo anuncia); no se pierde nada: los labels quedaron asentados en el
encabezado de cada `run-shard-*.log` (`reviewer=v23`, `gate=v13`,
`model=gpt-5.6-sol`, `effort=medium`, `governance=base`,
`backend=llm` — la config declarada, sin desvío).

## 1. Qué corrió y qué no: el mapa por shard

El set son 25 PRs repartidos en 4 shards (7/6/6/6). Se intentaron
20; **5 nunca se intentaron**. Completaron 15, murieron 5.

| Shard | Asignados | Resultado |
|---|---|---|
| 1 | 7 | **7/7 success.** `done. success=7 failed=0` — el único shard limpio |
| 2 | 6 | **Cortado por preflight en su primer PR** (ver abajo): 1 intentado, 5 jamás intentados |
| 3 | 6 | Completó la lista: 4 success, 2 muertos |
| 4 | 6 | Completó la lista: 4 success, 2 muertos |

**Shard 2 — el único corte de shard.** Su primer PR,
`simnaut_emdash_2`, murió en sus 3 intentos (248 s). La plataforma
aplica una regla de preflight: si el primer PR del shard falla, el
shard se detiene. Los 5 PRs restantes del shard nunca corrieron y
ni siquiera aparecen en `summary.txt`: `DisciplinedSoftware_
Codebase-Conversion_1`, `gagneurlab_PROTRIDER_10`, `k1LoW_gh-
copilot-review_9`, `scottlz0310_Mcp-Docker_29`, `vanyastaff_
nebula_224` (identificados por diferencia contra el set de 25 de
la corrida nº 295, que es el mismo set).

**Shards 3 y 4 no fueron cortados**: recorrieron su lista entera
y cerraron con `done. success=4 failed=2`. Muertos del shard 3:
`scotthamilton77_agents-config_1` (235 s, 3 intentos) y
`wirechat_wirechat_183` (236 s, 3 intentos). Muertos del shard 4:
`mheuss_chronicle_14` (233 s, 3 intentos) y
`sdsykes_fastimage_165` (236 s, 3 intentos). Nota de lectura: el
«(3, 4)» del veredicto del portal no coincide con la numeración
de los logs del zip, donde los shards con errores son el 2, el 3
y el 4; lo que el zip prueba es lo de esta tabla.

**Lo que los shards que corrieron dejaron**: 15 `findings.json`
con **106 findings** en total (los conteos por PR de
`summary.txt`: de 2 en `AA-Factory_aafactory-prototype_17` a 23
en `PaulStSmith_figlet-comment-generator_32`). Esos 106 findings
**nunca fueron puntuados**: la corrida murió en la etapa
run-agent, antes del scoring. No hay veredicto de detección de
esta práctica, ni parcial: la linterna del papel v2.3 (R_base
grounded > 0,7 %) no es evaluable sobre una corrida sin puntajes.

**Timeouts: ninguno.** Duración total por shard (suma de
`duration_seconds`): 579 s (1), 248 s (2), 978 s (3), 1.202 s
(4) — todos muy por debajo del timeout de contenedor de
1.800 s por shard del contrato. El PR individual más largo,
`cmik_apilix_12` con 493 s, es la suma de sus 3 intentos, no un
intento al borde del corte.

## 2. El error terminal, textual

Los cinco PRs muertos conservan un `agent.log` de 420 B,
**byte-idénticos entre sí** (mismo md5): el encabezado de config
y una sola línea de error:

> `alma-reviewbench error: selection pass did not return parseable JSON; failing closed`

El mismo texto quedó citado por la plataforma en
`logs/preflight.txt` y en la línea `::error::` de
`logs/run-shard-2.log`. La ruta en el código es exacta
(`agent/llm_reviewer_v23.py`, etapa (a) de `review()`): la llamada
de selección vuelve con HTTP 200 y contenido, `_extract_selection`
intenta `json.loads` sobre el texto completo (tras quitar cercos
de markdown) y, ante `ValueError`, levanta `RealLLMRefused` con
ese mensaje; `agent/main.py` captura la excepción, imprime
`alma-reviewbench error: …` y sale con código **2** — el
`error:2` del driver, que reintenta el PR hasta 3 veces.

Qué errores **no** son, por contraste de mensajes (todos
distintos y todos ausentes de los logs):

- **Error HTTP de OpenAI**: el camino `status != 200` de `_call`
  levanta «model endpoint returned HTTP …; failing closed
  without emitting findings» — ausente. El sobre de respuesta
  inválido («model response is not valid chat-completions
  JSON») — ausente. Las llamadas volvían 200 con contenido.
- **Negativa de la guardia de pre-vuelo** (pre-flight 1: el peor
  caso de la selección supera el tope): su mensaje es «refused
  before calling: worst-case estimate … no model call was
  made» — ausente. Esta es, además, la corrección histórica de
  la Adenda 6 del papel v2: la guardia que en la v2 se negó
  antes de llamar aquí **no se negó nunca**.
- **Guardia de gasto acumulado** (post-llamada): «cumulative
  reported cost … exceeds RB_MAX_SPEND_USD» — ausente.
- **La puerta** (gate=v13): ni interviene; la muerte es anterior,
  en la primera llamada del revisor, antes de todo hallazgo.

## 3. La firma estadística: intermitente, no determinista

- Intentos totales: **35** (20 PRs × sus reintentos). Muertes
  con `error:2`: **20 de 35**. De los 15 PRs que completaron, 3
  llegaron tras intentos muertos: `PierreJanineh_TechDebtMCP_135`
  (1 muerto, éxito al 2º), `brianc_node-postgres_3650` (2
  muertos, éxito al 3º) y `cmik_apilix_12` (2 muertos, éxito al
  3º). El mismo PR, el mismo diff, la misma config: un intento
  muere en la selección y el siguiente la pasa. (El `agent.log`
  conservado es el del último intento; que los intentos muertos
  previos de estos 3 PRs murieron por la misma causa es
  inferencia desde el exit code compartido y el mensaje de
  preflight — el driver solo asienta `error:2`, sin texto.)
- Duración por intento muerto en los 5 PRs terminales: **77,7–
  82,7 s** (233–248 s ÷ 3), una banda estrecha. La llamada de
  selección no volvía rápido con basura: corría ~78 s y devolvía
  algo no parseable.
- **El contraste con la nº 295 (v2.2) es la pieza dura.** Mismo
  set de 25 PRs, mismo modelo (`gpt-5.6-sol`, effort medium),
  mismo techo de completion de la selección (1.024 tokens,
  heredado sin cambios): la 295 completó **25/25 al primer
  intento, con cero `error:2`**. Los cinco PRs que hoy murieron
  3/3 habían completado en la 295 en **3–17 s**, con totales de
  completion (selección + profundas) de 67–732 tokens:
  `agents-config_1` 3 s / 1 llamada / 67 tokens; `wirechat_183`
  4 s / 1 / 130; `fastimage_165` 15 s / 2 / 797; `emdash_2`
  17 s / 1 / 529; `chronicle_14` 17 s / 2 / 732. La variable que
  cambió entre las dos corridas es el diseño de la selección
  (docstring del módulo v2.3: «ONLY this changes against
  v2.2: generalized selection») — 28 marcas (9 categorías
  generales + 19 clases) en una única lista de prioridad, con
  una razón corta por marca, contra las 19 clases de la v2.2.

## 4. Reconciliación de gasto: US$13,50 facturados, cero itemizables de los intentos muertos

**Facturado (fuente: saldo)**: US$16,52 − US$3,02 = **US$13,50**
por 35 intentos. La corrida **murió con saldo positivo**: los
fondos no son la causa (ver §5-b).

**Lo que los ledgers del zip pueden y no pueden decir.** Cada
PR completado asienta en su `agent.log` una línea `llm_run` con
el costo **estimado a precios de planificación** de su intento
exitoso (banda de la guardia: US$15/Mtok de entrada, US$75/Mtok
de salida — `RB_PRICE_*_PER_MTOK_USD`, defaults del código, no
precios facturados). Los intentos muertos **no dejan ledger**:
el proceso muere en `_extract_selection`, antes de imprimir la
línea `llm_run`; su gasto existe (la llamada de selección se
hizo y se pagó) pero no es itemizable desde el zip.

| PR (intento exitoso) | US$ planif. | Llamadas | Degradación |
|---|---|---|---|
| cmik_apilix_12 | 4,1297 | 3 | **spend_cap** (5 planeadas → 2 corridas) |
| superhighfives_pika_200 | 3,6302 | 5 | **spend_cap** |
| PierreJanineh_TechDebtMCP_135 | 3,6229 | 5 | **spend_cap** |
| PaulStSmith_figlet-comment-generator_32 | 3,5225 | 4 | **spend_cap** |
| brexhq_CrabTrap_15 | 3,4872 | 5 | — |
| AY2526S2-CS2103T-W14-3_tp_152 | 3,3351 | 5 | — |
| brianc_node-postgres_3650 | 2,3513 | 6 | — |
| NCATSTranslator_translator-ingests_336 | 2,2006 | 4 | — |
| allan-mobley-jr_gimmes_468 | 1,9167 | 3 | — |
| ardevd_jadx-collaboration_3 | 1,3187 | 5 | — |
| Marvell-Consulting_statswales-frontend_626 | 0,9708 | 4 | — |
| superyyrrzz_ForgeMap_106 | 0,8466 | 4 | — |
| konturio_disaster-ninja-fe_1230 | 0,6667 | 4 | — |
| renedierking_LANdalf_88 | 0,3525 | 4 | — |
| AA-Factory_aafactory-prototype_17 | 0,1145 | 2 | — |
| **Suma, 15 intentos finales exitosos** | **32,4659** | | |

La suma a precios de planificación de **solo los intentos
finales exitosos (US$32,47) ya es 2,4× todo lo facturado por
los 35 intentos (US$13,50)**. Conclusión de la reconciliación:
la banda de planificación sobreestima el costo facturado en
≥2,4× (la razón facturado/planificación es ≤0,42 aun sin
contar los 20 intentos muertos). El zip no permite distinguir
el mecanismo (caché de prompt entre llamadas con el mismo
prefijo — selección y profundas comparten diff y contexto, y
los reintentos repiten la llamada — y/o precios de lista del
modelo por debajo de la banda). Queda asentado como hallazgo
de economía: la guardia opera con precios deliberadamente
conservadores; sus «US$» son unidades de freno, no de factura.

**¿Algún PR individual disparó el costo?** A precios de
planificación, el más caro es `apilix` (US$4,13, con
degradación declarada: el contexto saturó el presupuesto de
60.000 tokens — 59.971 — y la guardia corrió 2 de 5 profundas).
La degradación `spend_cap` se declaró en **4 de los 15 PRs
completados** (apilix, pika, PierreJanineh, PaulStSmith). El
falsador de economía del papel v2.3 («degradación declarada
en más de 1/4 de los PRs de la práctica») lee 4/25 = 16 %
sobre el set — no gatillado — o 4/15 = 26,7 % sobre los
completados; la práctica murió antes de que el falsador tenga
un denominador válido, y su falsador principal (la linterna)
no es evaluable sin puntajes. Ningún PR explotó el gasto
facturado por sí solo: **el desperdicio estructural son los
20 intentos muertos**, cada uno pagó su llamada de selección
completa (~78 s de modelo) y produjo nada. Dato de escala de
esa llamada: la selección recibe el **diff completo sin
presupuesto de tokens** (el tope de 60.000 aplica solo al
contexto de las profundas); en la nº 295 la selección de
`emdash_2` asentó 259.630 tokens de prompt en una sola
llamada — a precio de planificación, ≈US$3,93 por intento.

## 5. Veredicto causal clasificado: (d) — defecto del diseño v2.3 en casos reales

**(d). El mecanismo, etapa por etapa:**

1. La etapa (a) de la v2.3 — la selección generalizada — le
   pide al modelo, con `reasoning_effort=medium`, una tarea de
   razonamiento más pesada que la de la v2.2: sopesar **28
   marcas** de dos familias sobre el diff completo, ordenarlas
   en una única lista de prioridad y justificar cada una con
   una frase, devolviendo un único objeto JSON.
2. Esa llamada heredó **sin cambios** el techo de completion
   de la v2.2: `max_completion_tokens = 1024`
   (`DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS`, idéntico en v2, v2.1,
   v2.2 y v2.3). En esta clase de modelo el techo descuenta
   los tokens de razonamiento **y** los de la respuesta
   visible: el JSON tiene que caber en lo que sobre tras
   razonar.
3. En diffs reales, el razonamiento de la nueva selección
   agota con frecuencia ese presupuesto: el contenido vuelve
   vacío o truncado a mitad del JSON. `_extract_selection`
   hace `json.loads` sobre el texto completo — falla — y el
   revisor **cierra en falso por diseño** (`RealLLMRefused`,
   exit 2). Sin selección no hay revisión: el PR muere antes
   de su primera profunda.
4. El driver reintenta el PR 3 veces; la longitud del
   razonamiento es estocástica, así que el mismo PR a veces
   pasa al 2º o 3er intento (3 casos) y a veces no pasa nunca
   (5 casos). Si el PR que muere 3/3 es el primero del shard,
   la regla de preflight de la plataforma corta el shard
   entero (shard 2: 5 PRs perdidos sin intento).

**Estado epistémico**: el paso 3 es inferencia, la más fuerte
que el material sostiene, no observación directa — el zip no
guarda el cuerpo de las respuestas fallidas ni el
`finish_reason` (§0). Lo que sí está probado por los logs: la
muerte es en el parseo de la selección, con HTTP 200 y
contenido; es intermitente sobre el mismo PR; tarda ~78 s por
intento (compatible con generar hasta un techo, no con
devolver prosa breve); y ocurre **solo** en la arquitectura
cuya selección cambió, contra una 295 limpia en 25/25 con el
mismo modelo y el mismo techo. La alternativa «el modelo
devolvió prosa en vez de JSON» es improbable con
`response_format: json_object` activo y no explica ni la
duración ni el contraste con la 295. La alternativa «techo
de completion alcanzado» sí explica las tres observaciones.

**Descartados con evidencia:**

- **(a) Infraestructura/plataforma**: la plataforma bajó la
  imagen, cargó credenciales y corrió los 4 shards; éxitos y
  muertes se intercalan dentro del mismo shard y del mismo
  contenedor (shard 3: konturio OK → brianc muere 2 y pasa →
  agents-config muere 3 → NCATS OK). Ningún shard se acercó
  al timeout de 1.800 s (máx. 1.202 s). `egress-proxy.log`
  vacío, sin rechazos asentados.
- **(b) Fondos**: murió con US$3,02 positivos; la guardia de
  gasto nunca levantó su mensaje; 15 PRs completaron
  gastando en los mismos shards donde otros morían.
- **(c) Timeout por volumen**: ningún corte es por timeout
  (ver §1). El volumen sí es **efecto secundario medido**:
  35 intentos y 3.007 s de agente para 20 PRs intentados, y
  US$13,50 facturados por una práctica que no produjo ni un
  puntaje — el diseño paga la selección completa hasta 3
  veces por PR antes de rendirse.

## 6. Arreglos candidatos — qué implicaría cada uno (sin ejecutar ninguno)

Diagnóstico solamente: ningún arreglo está ejecutado ni
recomendado por este documento, y la excepción de
relanzamiento de la casa (cortes de infraestructura
declarados) **no aplica** — la causa clasificada es (d).
Cualquier relanzamiento exigiría arreglo + papel o adenda
que lo declare; es decisión de Alejandro.

| # | Arreglo | Qué toca | Costo en seco estimado | Qué NO arregla |
|---|---|---|---|---|
| i | **Subir el techo de completion de la selección** (1024 → p. ej. 4096; ya existe la vía `RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS`) | Config/default del revisor v2.3 + tests que fijan el valor | Bajo: cambio de una constante, suite de selección, re-declaración en papel/adenda. El peor caso de la guardia sube ≈US$0,23/PR (4096−1024 tokens × US$75/Mtok): el pre-flight 1 sigue holgado contra US$6,50 | Si el contenido volviera no-parseable por otra vía (prosa), no rescata nada; y no reduce los ~78 s por llamada — los aumenta cuando el modelo use el techo nuevo |
| ii | **Asentar el contenido fallido y el `finish_reason`** (extracto acotado) antes de cerrar en falso | `_call`/`_extract_selection` + tests | Bajo: observabilidad pura, sin cambio de comportamiento medido | No salva ningún PR: convierte la próxima muerte de inferencia en prueba. Es prerequisito honesto de cualquier diagnóstico futuro de esta etapa |
| iii | **Reintento interno de la selección** (1 re-llamada ante parseo fallido, antes de `RealLLMRefused`) | Etapa (a) de `review()` + tests | Bajo-medio: con la tasa observada (20/35 muertes por intento), un reintento bajaría la pérdida de PRs de ~57 % de intentos a una fracción menor por PR; cuesta una llamada de selección extra por falla (a precio de planificación, US$0,2–3,9 según el diff). **Cambia el diseño medido**: exige declaración previa en papel | No ataca la causa raíz: si la propensión por PR es alta (diffs que siempre razonan largo), el PR sigue muriendo, solo que más tarde y más caro |
| iv | **Aliviar la tarea de selección**: dos llamadas (familias por separado), o sin razones por marca, o sin orden de prioridad | Etapa (a) + prompt + tests + semáforo nuevo | Medio-alto: es rediseño de la etapa que define a la v2.3; el papel v2.3 ya no lo cubriría — papel nuevo | No garantiza nada sin (ii): seguiríamos sin ver el cuerpo de las respuestas que fallen |
| v | **Parseo permisivo** (extraer el primer objeto JSON del texto en vez de `json.loads` total) | `_extract_selection` + tests | Bajo | Si la causa es truncación/vacío (la inferencia fuerte), **no rescata un solo caso**: no hay objeto completo que extraer. Además debilita la filosofía fail-closed que la casa sostuvo en todas las versiones |

## 7. Conclusión falsable

La nº 296 no murió por la plataforma, ni por fondos, ni por
timeout: murió porque la selección generalizada de la v2.3 —
la única pieza que cambió contra la v2.2 — no cabe, en diffs
reales, en el techo de completion de 1.024 tokens que heredó
sin cambios, y el revisor cierra en falso ante el primer
JSON no parseable. 20 de 35 intentos murieron en esa línea;
un shard entero cayó por la regla de preflight.

Falsador del mecanismo: en cualquier corrida futura con el
techo de la selección subido (arreglo i) y el contenido
fallido asentado (arreglo ii), la tasa de muertes por
`error:2` en la selección debería caer a ~0 y los cuerpos
asentados deberían mostrar el JSON completo que antes no
cabía. Si las muertes persistieran con contenido asentado
**no truncado** (prosa, o JSON completo pero de otra forma),
este mecanismo cae y la causa pasa a ser la obediencia de
formato del modelo bajo la nueva consigna — otro diagnóstico,
con el cuerpo a la vista.

— Diagnóstico en seco, US$0. Fuentes: zip de outputs de la
nº 296 (44.779 B), zip de outputs de la nº 295 como contraste,
`agent/llm_reviewer_v23.py` (líneas de `_extract_selection`,
`_payload`, `review()` etapa (a)), `agent/main.py` (salida 2),
`PREREGISTRO-REVIEWBENCH-V23.md` (falsadores), saldos
US$16,52 → US$3,02 asentados por el portal de billing.
