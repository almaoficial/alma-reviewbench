# Resultado — Práctica v2.3 de ReviewBench (2026-10-21)

## Brazo base — corrida nº 296

- Lanzada: 2026-10-21 22:26:40 EDT, por autorización expresa de
  Alejandro («Corre»). Saldo OpenAI previo (portal de billing, org
  Personal, 22:25 EDT): **US$16,52**.
- Configuración (verbatim de los `agent.log` de los outputs):
  `backend=llm · governance=base · model=gpt-5.6-sol · effort=medium ·
  reviewer=v23 · gate=v13`; validador declarado
  `alma-evidence-gate/1.3.0` (omitido al validar en el brazo base).
- Imagen: `ghcr.io/almaoficial/alma-reviewbench@sha256:932ac3ffa1944d92cb4defd5b96b7b1146eb37bdd3b4245676039e7844b40e27`.
- Estado terminal: **FAILED «at run-agent (3, 4)»** — la corrida NO
  completó el set y el portal **no publicó puntajes** (Grounded y
  Augmented: sin valores; los 106 hallazgos emitidos quedaron **nunca
  puntuados**).

## Qué pasó, según los outputs (fuente primaria, leídos completos)

Zip descargado del portal («agent output») y verificado en disco:
`~/workspace/browser_downloads/sess-2601685563/browser-download-20261022T025314.409251136Z-0-alma-reviewer-run-296-output.zip`
(44.799 B) y copia en `runs/run-296-output.zip` (44.799 B, idéntica).

- `summary.txt`: «The run ended with errors» — **20 PRs alcanzados de
  25: 15 succeeded, 5 did not**; 5 PRs nunca fueron alcanzados (el
  shard 2 se detuvo en su primer PR por la regla de preflight).
- Los 5 PRs en `error:2` (3 intentos cada uno) cierran todos con el
  mismo error textual del agente: **«selection pass did not return
  parseable JSON; failing closed»** — mheuss/chronicle#14,
  simnaut/emdash#2, scotthamilton77/agents-config#1,
  wirechat/wirechat#183, sdsykes/fastimage#165.
- Hallazgos emitidos (findings.json de los 15 PRs completados):
  **106 en total** (`malformed = 0`, `unanchored = 0` en todos los
  `llm_run` asentados). Nunca puntuados por la plataforma.
- Marcas de selección en los PRs completados: la vía general operó
  (categorías del benchmark en las 15 pasadas); la especialidad
  apareció una sola vez (CrabTrap: `sql_injection`). Ningún PR
  completado quedó con cero marcas.
- **Degradación declarada (`spend_cap`) en 3 PRs:** figlet (5
  planeadas → 3 corridas), pika (5 → 4) y TechDebtMCP (5 → 4).
- LANdalf#88 (el único TP de clase clara del set, `swallowed_exception`):
  el revisor emitió 3 hallazgos sobre
  `DeviceMonitoringService.cs:184-186` describiendo exactamente la
  excepción de cancelación tragada por el catch amplio — sin puntaje
  oficial que lo confirme como TP (la adjudicación contra el gold es
  trabajo posterior, en curso por otra vía, US$0).

## Costo real (por diferencia de saldo)

- Saldo previo: US$16,52 (22:25 EDT, antes de lanzar).
- Saldo final: **US$3,02** (org Personal, tras el cierre de la corrida).
- **Costo real de la corrida nº 296: US$16,52 − US$3,02 = US$13,50.**
- Lecturas intermedias de esta vigilancia (22:41 EDT, corrida aún en
  curso): US$5,33 → US$4,73 → US$4,17, cayendo — consistentes con el
  total. Dentro del tope duro de la práctica (US$30).
- Contraste declarado: la suma de `estimated_cost_usd` de los
  `llm_run` del intento final registrado en los 15 PRs completados es
  US$32,47 a tarifas de planificación (US$15/M entrada · US$75/M
  salida, las de la guardia). Es una estimación conservadora del
  propio agente, NO lo facturado: lo facturado es la diferencia de
  saldo de arriba. Los intentos fallidos (3 por PR en error, y
  reintentos en 3 PRs que completaron) también facturaron llamadas
  parciales que la diferencia de saldo sí captura.

## Prueba de la linterna (papel v2.3, §6 componente 1)

- Regla: recall base grounded > 0,7 % sobre 352 TP → PASA.
- Recall base grounded: **no existe** — la corrida FAILED y el portal
  no puntuó. **Veredicto: NO PASA** (por ausencia de medición, no por
  un recall medido bajo el umbral).
- **Consecuencia pre-registrada: el brazo ALMA NO se lanza.** Sin
  linterna no hay comparación: la práctica v2.3 queda **SIN VEREDICTO
  VÁLIDO** sobre «ALMA mejora», igual que la v2.1 y la v2.2 pero por
  una causa distinta (falla del diseño, no recall medido en cero).
  Los pasos de publicación de la imagen con `gate=v141` y de edición
  de la config ALMA tampoco se ejecutan (Adenda 1, §5: solo son
  pertinentes si la base supera la linterna).

## Lectura del falsador (papel v2.3, §8)

- **Principal — el encuadre: NO juzgado.** La hipótesis del encuadre
  no quedó falsada ni confirmada: la corrida murió antes de que la
  detección pudiera medirse, en la pasada de selección. Con la
  evidencia de los outputs, la causa es la **(d) = defecto del
  diseño**: la pasada de selección generalizada heredó el techo de
  completion de 1.024 tokens de la v2.2 y en diffs reales el
  razonamiento lo agota antes de emitir el JSON (inferencia declarada
  como tal: el error asentado es «did not return parseable JSON» y el
  código no registra `finish_reason`; la atribución al techo es la
  lectura del diagnóstico, no un log directo). 5 PRs muertos así +
  5 no alcanzados = 10 de 25 PRs sin revisión posible.
- **Economía: NO gatillado.** Degradación en 3/15 PRs completados
  (20 %) y 3/20 alcanzados (15 %), ambas lecturas bajo el umbral de
  1/4; costo total US$13,50 bajo el tope de US$30.
- **Selección generalizada ciega: NO gatillado en su forma** (cero
  PRs completados con cero marcas), pero con un modo de falla nuevo
  y peor asentado: la selección no devolvió JSON parseable en 5 PRs
  reales — la etapa de selección no solo puede no marcar: puede no
  responder.
- **Puerta / semáforo:** sin aplicación (el brazo ALMA nunca fue
  pertinente; el semáforo v2.3 VERDE no se reabre).

## Nota de integridad de esta vigilancia

Una pasada intermedia del navegador reportó la corrida como
«SUCCEEDED» con puntajes (Grounded P 11,1 % · R 0,3 % · F1 0,5 %;
findings 36). Ese reporte quedó **DESCARTADO** por contradecir dos
fuentes primarias independientes: el zip de outputs de la propia
corrida (summary: «ended with errors», 15/20 PRs, 106 hallazgos sin
puntuar) y el registro del cierre asentado por el agente principal
(FAILED at run-agent (3,4), costo US$13,50, saldo final US$3,02).
Ningún puntaje de ese reporte se usa en este resultado.

## Cierre

- No se tocó «Submit» (final de 219 PRs), ni la config ALMA, ni
  `RB_MAX_SPEND_USD`. Sin relanzamientos: la práctica no se reintenta
  en esta vigilancia (prohibido por la consigna y por la disciplina
  anti-pesca). Cualquier decisión sobre la línea de revisores es de
  Alejandro con este resultado en la mano.
- La vigilancia `vigilar-practica-v23-reviewbench` se elimina en esta
  misma pasada, como manda su protocolo ante estado terminal.
