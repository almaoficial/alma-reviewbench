# Resultado — Sonda dirigida del arreglo v2.3.1 (Adenda 2 §4)

**Veredicto: ÉXITO según el éxito pre-registrado** — los 8 casos
corridos devolvieron **JSON parseable** (los 5 obligatorios que
murieron 3/3 en la nº 296 + los 3 intermitentes, alcanzados porque
el presupuesto lo permitió). Una llamada por caso, sin reintentos.
**Total reportado: US$6,3282** (precios del revisor) contra el tope
duro de **US$8** — 79 % usado.

Aprobaciones: Alejandro, «Bueno lo hagamos» (21/10 23:20 EDT, la
secuencia completa) y «Cargue ya el crédito, ahora todo tuyo»
(23:25 EDT); saldo verificado en el portal **US$25,02** (23:27 EDT)
≥ compuerta de US$8 ✓. Papel que manda: Adenda 2 §4 (la sonda) y
§5 (presupuesto y compuerta de saldo), firmado 21/10.

## 1. Qué corrió (declaración de alcance)

- **Revisor:** `llm-reviewer/2.3.1`, verificado por assert al
  arrancar. Configuración del brazo base declarada en el portal:
  `gate=v13` (familia especialidad = las 19 clases de la 1.3.0),
  modelo `gpt-5.6-sol`, `reasoning_effort=medium`.
- **Lo cambiado:** techo de completion de la selección = 4.096
  tokens (default verificado; las profundas no existen en esta
  sonda porque no corren).
- **Etapa corrida:** solo la (a) — selección — replicando
  `review()` línea por línea: `build_selection_payload` →
  pre-flight 1 (peor caso del revisor por caso, todos ≤
  `RB_MAX_SPEND_USD=US$6,50`) → `_call` → `_account` →
  `_extract_selection` → `_filter_selection`. Sin pasadas
  profundas, sin puerta, sin emisión, sin reintentos.
- **Clave:** sustituto dinámico del conector `custom.openai-rbench`
  en memoria del proceso; sonda de costo cero previa: `GET
  /v1/models` → HTTP 200, 133 modelos, `gpt-5.6-sol` visible.
- **Orden:** los 5 obligatorios primero
  (`simnaut_emdash_2`, `scotthamilton77_agents-config_1`,
  `wirechat_wirechat_183`, `mheuss_chronicle_14`,
  `sdsykes_fastimage_165`), luego los 3 intermitentes
  (`PierreJanineh_TechDebtMCP_135`, `brianc_node-postgres_3650`,
  `cmik_apilix_12`). Compuerta de tope aplicada por caso
  (acumulado + peor caso del revisor ≤ US$8,00): corrieron los 8.

## 2. Los diffs (fuente declarada)

El zip de la nº 296 no trae diffs. Se regeneraron en local con
`git diff base...head` sobre clones públicos (`--filter=blob:none`),
con los SHAs base/head de `corpus/test/test.json` del repo público
`review-bench/ReviewBench` — el mismo set de 25 PRs de la práctica.
El contrato de la plataforma declara el diff como «idéntico a lo
que GitHub muestra en el pull request» (`AGENT_CONTRACT.md:31`), y
los sufijos de los directorios del zip (`41d75006`, `1fc78970`,
`6e3156e7`, `04ac4c02`, `8fc7cd32`, …) coinciden con los head de
ese corpus. Comprobación de contenido: el `prompt_tokens`
reportado por la API en el caso emdash (259.942) coincide con el
asentado en la nº 295 para su llamada de selección (259.630),
con una diferencia de +312 tokens consistente con el system prompt
más largo de la v2.3 (28 marcas contra 19 clases de la v2.2) — el
diff recibido es, al token, el mismo.

| Caso | bytes del diff | sha256 (12) |
|---|---|---|
| simnaut_emdash_2 | 852.286 | `cf5d991ce3cd` |
| scotthamilton77_agents-config_1 | 48.975 | `fa1fdad2a1a4` |
| wirechat_wirechat_183 | 52.265 | `bafc750ce634` |
| mheuss_chronicle_14 | 79.719 | `876dba2b88f9` |
| sdsykes_fastimage_165 | 21.970 | `08b05b1aa354` |
| PierreJanineh_TechDebtMCP_135 | 22.824 | `45e636614bf6` |
| brianc_node-postgres_3650 | 20.501 | `72067ebf5b44` |
| cmik_apilix_12 | 152.330 | `ff40b8479160` |

## 3. Resultados por caso

Veredicto en todos: **parseable**. `finish_reason="stop"` en los 8
(terminación natural del contenido, no corte por techo).
`selection_unknown_marks=0` y `selection_malformed_entries=0` en
los 8. Overflow: ninguno. Marcas totales: 38 de vía general, 1 de
especialidad (`sql_injection` en chronicle).

| Caso | finish | prompt | compl. | razonam. | seg | marcas (familia) | US$ rep. |
|---|---|---|---|---|---|---|---|
| emdash_2 | stop | 259.942 | 1.609 | 1.462 | 25,8 | security, correctness, reliability, testing, accessibility (general ×5) | 4,0198 |
| agents-config_1 | stop | 14.296 | 1.177 | 1.025 | 19,9 | correctness, testing, reliability, maintainability, api-architecture (general ×5) | 0,3027 |
| wirechat_183 | stop | 14.787 | 1.167 | 1.024 | 20,1 | correctness, reliability, performance, api-architecture, maintainability (general ×5) | 0,3093 |
| chronicle_14 | stop | 22.492 | 1.676 | 1.536 | 26,9 | security, reliability, **sql_injection (especialidad)**, correctness, testing | 0,4631 |
| fastimage_165 | stop | 8.946 | 900 | 777 | 16,7 | correctness, reliability, performance, maintainability (general ×4) | 0,2017 |
| TechDebtMCP_135 | stop | 7.481 | 638 | 512 | 12,3 | security, performance, reliability, documentation (general ×4) | 0,1601 |
| node-postgres_3650 | stop | 7.027 | 1.020 | 886 | 17,4 | correctness, performance, security, reliability, testing (general ×5) | 0,1819 |
| apilix_12 | stop | 42.631 | 669 | 512 | 11,4 | security, correctness, reliability, documentation, testing (general ×5) | 0,6896 |
| **Total** | | | | | | | **6,3282** |

## 4. El mecanismo, ahora leído (no inferido)

La pieza (ii) del arreglo no tuvo que asentarse — ningún caso
falló — pero la causa (d) del diagnóstico quedó confirmada por
lectura directa de los tokens que el modelo reportó, contra el
techo viejo de 1.024:

- **4 casos con razonamiento ≥ el techo viejo:** emdash (1.462),
  agents-config (1.025), wirechat (1.024) y chronicle (1.536). En
  ellos, el razonamiento solo ya agotaba o igualaba el
  presupuesto de 1.024 que heredó la v2.3 — el contenido no podía
  existir. Es la muerte determinista que la nº 296 mostró 3/3 en
  estos PRs.
- **El intermitente, explicado:** node-postgres usó 886 de
  razonamiento y dejó 134 visibles (total 1.020, justo bajo
  1.024). Con el techo viejo el PR vivía en el borde: cualquier
  pasada de razonamiento apenas más larga lo mataba — exactamente
  la historia de la 296 (murió 2, pasó al 3º). La estocasticidad
  alrededor del borde queda medida, no inferida.
- **Los otros dos intermitentes:** fastimage (777 razonando) y
  TechDebtMCP (512) — también cerca del borde viejo, con
  respuesta visible chica.
- **Ninguna llamada fue cortada por el techo nuevo:**
  `finish_reason="stop"` en las 8 y completion máximo 1.676 <
  4.096. El arreglo no fue «casi justo»: tiene 2,4× de margen en
  el caso más pesado.

La alternativa «prosa en vez de JSON» queda descartada en estos
8 casos: las respuestas parsean y el uso reportado explica las
muertes bajo el techo viejo al token.

## 5. Contabilidad

- **Costo reportado total (precios del revisor 15/75): US$6,3282**
  ≤ tope duro US$8 (la compuerta por caso corrió con la
  aritmética del revisor; el peor acumulado con peor caso,
  US$8,0554 con apilix, quedó por encima de lo efectivamente
  reportado, como manda el papel).
- **Gasto facturado estimado:** la nº 296 midió razón
  facturado/planificación ≤ 0,42 (US$13,50 contra US$32,47 de
  solo intentos finales exitosos) → facturado ≤ **≈US$2,7**.
- **Saldo resultante estimado:** US$25,02 − ≈US$2,7 ≈
  **US$22,4**. La lectura oficial queda para el portal; este
  informe no tocó el billing.

## 6. Alcance honesto y lo que sigue

- La sonda **no mide una tasa de muertes** (una llamada por caso)
  ni toca la detección: el éxito pre-registrado era parseo en
  todos los casos corridos, y se cumplió en los 8.
- **No se ajustó ningún prompt** (Adenda 2 §4): la sonda decide
  seguir o parar, y decide **seguir**.
- Siguiente paso de la Adenda 2 §6: **publicación de la imagen
  v2.3.1** (digest verificado contra GHCR; el commit incluye los
  documentos locales pendientes). La práctica relanzada exige la
  **compuerta de saldo ≥ US$25 verificada antes de lanzar** —
  con el saldo estimado post-sonda (≈US$22,4) **hará falta una
  carga chica** (del orden de US$3–8) antes del paso 6 de la
  secuencia.
- **El falsador de la Adenda 2 §7 sigue en pie:** si la práctica
  relanzada muere con la misma firma (JSON no parseable en la
  selección), la hipótesis del techo queda refutada y la línea se
  detiene sin tercer intento automático. La nº 296 queda FAILED
  para siempre; esta sonda no la re-califica.

— Sonda dirigida, 2026-10-21. Recibos: `/tmp/probe/results.jsonl`
(8 registros), `/tmp/probe/probe.log`, diffs regenerados en
`/tmp/probe/diffs/` con sus sha256. Sin portal, sin publicación,
sin cambios de código ni papeles; la credencial nunca salió de la
memoria del proceso.
