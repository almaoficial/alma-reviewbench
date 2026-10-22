# Resultado — Práctica v2.3.1 de ReviewBench (2026-10-22)

## Brazo base — corrida nº 298

- Lanzada: 2026-10-22 00:32:41 EDT, por autorización expresa de
  Alejandro (secuencia de la Adenda 2 al papel v2.3). Saldo OpenAI
  previo (portal de billing, org Personal, 00:31–00:32 EDT):
  **US$27,99**.
- Configuración (verbatim del portal y de los `agent.log` de los
  outputs): `backend=llm · governance=base · model=gpt-5.6-sol ·
  effort=medium · reviewer=v23 · gate=v13`; versión del revisor
  `llm-reviewer/2.3.1`; validador declarado
  `alma-evidence-gate/1.3.0` (omitido al validar en el brazo base).
- Imagen: `ghcr.io/almaoficial/alma-reviewbench@sha256:144756cea49ee33e8b16ddb0204556adb0f1c2430ea885ec6a206bbaa6964544`.
- Estado terminal: **SUCCEEDED** — la corrida completó el set y el
  portal publicó puntaje (ver la salvedad de etiqueta de abajo).

## Puntajes tal como los muestra el portal (verbatim)

- Lista de corridas de `alma-reviewer` (Register → Test runs):
  «#298 · llm · base · gpt-5.6-sol · medium · v23 · v13»,
  estado «succeeded», **«P 89.4%» · «R 34.5%» ·
  «166 findings · 88 novel»**.
- **Salvedad de etiqueta (buscada exhaustivamente, dos pasadas):**
  el portal **no etiqueta** ese P/R como Grounded ni como
  Augmented — solo lleva las descripciones genéricas «Precision»
  y «Recall». El desglose **Grounded P/R/F1, Augmented P/R/F1,
  cualquier F1 y la duración media NO aparecen en ninguna vista
  accesible** del portal para esta corrida: ni en la lista, ni en
  el detalle por PR expandido, ni en el detalle de un PR, ni en
  «Best run», ni en el bloque de la configuración base, ni en
  «Final runs» («None yet.»), ni en el paso Leaderboard del flujo
  de envío («Nothing submitted yet.»), ni en el leaderboard
  público (13 agentes publicados; `alma-reviewer` no está).
  Ningún valor de esos se inventó ni se derivó en este resultado.
- **Comparación de integridad:** el mismo portal, hoy, muestra la
  corrida nº 295 (práctica v2.2) solo como «P 15% · R 0.4%», que
  en su resultado asentado (`RESULTADO-PRACTICA-V22-20261021.md`)
  corresponde a sus valores **Augmented** (su Grounded fue
  0,0 % / 0,0 %). Declarado como inferencia de dos fuentes: el
  P/R de lista no se puede acreditar como **grounded** — y por
  tanto el 34,5 % no acredita por sí solo la linterna (ver abajo).

## Qué pasó, según los outputs (fuente primaria, leídos completos)

Zip descargado del portal («agent output» de la nº 298) y
verificado en disco:
`~/workspace/browser_downloads/sess-661379183/browser-download-20261022T045601.390490338Z-0-alma-reviewer-run-298-output.zip`
(69.389 B, md5 `9a224fb4edab1ced09bfd7cf7497bb60`) y copia idéntica
en `runs/run-298-output.zip` (mismo tamaño y md5).

- `summary.txt`: «25 pull requests: 25 succeeded, 0 did not» —
  los 4 shards dejaron output; 24 PRs en 1 intento y ForgeMap en 2.
- Hallazgos en los `findings.json`: **166 en total**, idéntico al
  número del portal. `malformed = 0` en los 25 PRs;
  `unanchored = 2` (TechDebtMCP y apilix: 168 crudos → 166 emitidos).
- **La firma que mató a la nº 296 está ausente:** cero errores
  «selection pass did not return parseable JSON» y
  `parse_failures = []` en los 25 `llm_run` — con
  `triage_max_output_tokens = 4096` asentado en los 25.
- **Selección:** cero PRs con cero marcas (los 25 seleccionaron
  entre 3 y 5 pasadas; marcas de especialidad en 3 PRs:
  `tarfile_unsafe_extract` + `swallowed_exception` en
  Codebase-Conversion, `sql_injection` en CrabTrap y chronicle).
  El único PR con 0 hallazgos emitidos es emdash (ver degradación).
- **Degradación declarada en 10/25 PRs:** 9 por `spend_cap`
  (Codebase-Conversion 5→2, figlet 4→3, TechDebtMCP 5→4, CrabTrap
  5→4, apilix 5→2, PROTRIDER 5→1, chronicle 5→2, nebula 4→1,
  wirechat 5→3) y emdash por `no_deep_pass_affordable` (5→0, sin
  pasada de respaldo: emitió 0).
- Duración por PR según `run-status.jsonl` de los outputs (no es
  la «duración media» del portal, que no se mostró): media
  102,5 s, mínimo 20 s, máximo 220 s.
- Suma de `estimated_cost_usd` de los 25 `llm_run` (104 llamadas):
  **US$63,6736** a tarifas de planificación (US$15/M entrada ·
  US$75/M salida) — estimación de la guardia, **no** lo facturado
  (ver costo real abajo; la razón estimación/facturado es 3,12×,
  en línea con la sobreestimación ≥2,4× medida en la nº 296).

## Costo real (por diferencia de saldo)

- Saldo previo: US$27,99 (00:31–00:32 EDT, antes de la corrida).
- Saldo final: **US$7,58** (org Personal, portal de billing de
  OpenAI: Settings → Organization → Billing → Overview, «API
  credit balance»; el mismo saldo en la portada, «Credit balance»).
- **Costo real de la corrida nº 298: US$27,99 − US$7,58 =
  US$20,41.** Dentro de la banda pre-registrada de la Adenda 2 §5
  para la práctica base relanzada (US$15–25).

## Prueba de la linterna (papel v2.3, §6 componente 1)

- Regla: recall base grounded > 0,7 % sobre 352 TP → PASA.
- Recall base grounded: **no acreditado en esta pasada** — el
  portal no lo muestra: el único recall publicado (34,5 %) va sin
  etiqueta Grounded/Augmented y, por la comparación con la nº 295
  asentada arriba, no se lo puede tomar por grounded.
- **Veredicto: NO PASA — por ausencia de medición grounded
  acreditada, no por un recall medido bajo el umbral** (el mismo
  tipo de cierre que la nº 296, con causa distinta: allá la
  corrida FAILED sin puntaje; acá SUCCEEDED con puntaje sin
  etiqueta grounded).
- **Consecuencia pre-registrada según la consigna de esta
  vigilancia: el brazo ALMA NO se lanza en esta pasada** (además
  está prohibido por la propia consigna), no se edita la config
  ALMA y no se ejecuta ningún paso de `gate=v141`.
- **El paso que puede dirimirla** (trabajo posterior, US$0, no
  hecho acá): la adjudicación grounded de los 166 hallazgos del
  zip descargado contra el gold público, con la metodología de
  `ADJUDICACION-PARCIAL-296-20261021.md` (la que reprodujo los
  números del portal de la v1). El zip quedó descargado y copiado
  exactamente para eso. Hasta esa adjudicación, ninguna lectura
  de «ALMA mejora» tiene vara grounded: la práctica v2.3.1 queda
  **SIN VEREDICTO VÁLIDO** sobre la comparación, con la base por
  fin completa y puntuada en el portal.

## Lectura del falsador

- **Adenda 2 §7 — firma de la nº 296: NO se disparó.** La
  práctica relanzada **no** murió con «selection pass did not
  return parseable JSON»: completó 25/25 con `parse_failures`
  vacío en todos los PRs. La hipótesis del techo **no queda
  refutada**; el arreglo (1.024 → 4.096) es consistente con la
  sonda 8/8. No hay tercer intento automático ni hace falta:
  esta corrida es la relanzada y completó.
- **Principal — el encuadre (papel v2.3, §8): NO juzgado.** Sin
  recall grounded acreditado no se puede declarar muerta ni
  viva la hipótesis del encuadre, y la predicción del papel
  (R grounded 1–3 %, P grounded 10–40 %) no se evalúa contra
  números sin etiqueta.
- **Economía (§8): GATILLADO en la evidencia de los outputs.**
  Degradación declarada en 10/25 PRs = 40 %, más de 1/4 del set.
  El texto del falsador: «la economía tampoco cierra con revisor
  general: registrar y detener». Queda registrado tal cual; su
  aplicación a la secuencia (si detiene la línea aun si la
  adjudicación grounded posterior pasara la linterna) es lectura
  del papel a decidir por Alejandro con este resultado en la
  mano — esta vigilancia la registra, no la reinterpreta. El
  costo real (US$20,41) sí quedó dentro de la banda de la etapa.
- **Selección generalizada ciega (§8): NO gatillado** — 0/25 PRs
  con cero marcas.
- **Puerta / semáforo:** sin aplicación en esta pasada (el brazo
  ALMA nunca fue lanzado; el semáforo v2.3.1 no existe como etapa:
  la secuencia fue sonda → publicación → práctica).

## Cierre

- No se tocó «Submit» (final de 219 PRs), ni la config ALMA, ni
  `RB_MAX_SPEND_USD`. Sin lanzamientos ni relanzamientos en esta
  vigilancia: el único gasto fue el de la propia corrida nº 298,
  ya cerrada, medido por diferencia de saldo.
- La vigilancia `vigilar-practica-v231-reviewbench` se elimina en
  esta misma pasada, como manda su protocolo ante estado
  terminal.
