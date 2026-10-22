# Diagnóstico en seco — Práctica v2.2 (base nº 295): ¿en qué paso se perdió cada defecto?

**Fecha:** 2026-10-21 · **Costo:** US$0 (sin llamadas a OpenAI, sin corridas nuevas)
**Pregunta:** clasificar los misses de la base nº 295 en (a) el triage no marcó la
clase, (b) la profunda no lo encontró, (c) se emitió pero el corrector no lo contó,
(d) degradación por el freno.

## 0. Material y una ausencia que acota el diagnóstico

- **El gold es público** (repo `review-bench/ReviewBench`, `golden/*.json` +
  `corpus/test/findings.json`, que es el filtro `tp_fp == "tp"` de ese gold,
  verificado archivo por archivo): el set de práctica tiene **352 hallazgos
  golden TP y 213 FP** en 25 PRs. La metodología de puntuación es la pública
  (`review-bench.ai/methodology` §6–7): matching semántico por archivo entre
  lo emitido y el gold; grounded usa solo etiquetas del gold; augmented suma
  los emitidos sin match que el clasificador juzga TP («novel»).
- **Los outputs crudos de la nº 295 NO están en disco** (la vigilancia asentó
  en `RESULTADO-PRACTICA-V22-20261021.md` que no se descargaron; en
  `~/workspace/browser_downloads/` solo existen los zips de las corridas
  251/282/287). Sin el `agent.log` por PR de la 295 no se puede separar
  (a) de (b) defecto por defecto: esa separación vive en los campos
  `selection_selected`, `passes`, `raw_findings`, `malformed_findings`,
  `unanchored_findings` y `degradation` que el revisor v22 escribe por PR
  (verificado en `agent/llm_reviewer_v22.py` y `agent/main.py`).
- Lo que sigue separa **lo demostrable sin ese zip** (que resulta ser la
  mayor parte de la respuesta, porque el gold y los puntajes alcanzan para
  acotar casi todo) de **lo pendiente**, con el procedimiento exacto para
  cerrarlo cuando el zip se descargue del portal.

## 1. El techo estructural: el gold no vive en el universo de las 19 clases

Adjudiqué los 352 golden TP, mensaje por mensaje, contra las 19 clases de la
puerta 1.3.0 (`KNOWN_CLAIM_TYPES_V13`). Distribución del gold por categoría
del benchmark: correctness 133 · reliability 58 · maintainability 44 ·
testing 35 · security 27 · documentation 21 · api-architecture 12 ·
performance 12 · accessibility 10.

Resultado de la adjudicación:

| Grupo | Cantidad | % de 352 |
|---|---|---|
| Fuera del universo de clases (ninguna de las 19 describe el defecto) | **343** | 97,4 % |
| Análogos fronterizos (la forma se parece a una clase; un matcher generoso podría discutirlo) | **8** | 2,3 % |
| Instancia clara de una clase | **1** | 0,3 % |

- **La única instancia clara:** `renedierking/LANdalf#88`,
  `src/API/Services/DeviceMonitoringService.cs:184` — *«OperationCanceledException
  is swallowed by the generic catch (Exception ex) block… Cancellation is not
  propagated»* = `swallowed_exception` de manual. El propio gold lo marca
  severity medium, **difficulty easy, context_required diff-only**,
  scope introduced-by-pr: es el defecto que un triage + pasada profunda
  deberían poder cazar en principio.
- **Los 8 fronterizos:** pika#200 `ContentView.swift:151` (Swift `try?`
  descarta errores en silencio — análogo silenced/swallowed); chronicle#14
  `retention.rs:150` (error de borrado logueado, sigue y reporta éxito) y
  `media.rs:296` (walk que traga errores por diseño); apilix#12
  `storageDriver.ts:179` (catch que cae en silencio ante error de lectura);
  Mcp-Docker#29 `session.go:44` (goroutine sin parada — análogo resource_leak);
  konturio#1230 `GenericRenderer.ts:229` (sin guarda ante switches
  concurrentes), jadx#3 `Plugin.kt:550` (lecturas de estado compartido en
  hilo de fondo) y CrabTrap#15 `api.go:325` (conteo y consulta no
  transaccionales) — análogos race_condition.
- **Ni siquiera la categoría «security» del benchmark intersecta:** sus 27 TP
  son traversal de paths (×5), CSRF, PKCE/OAuth (×11), CORS/endpoints sin
  autenticación, plaintext storage de credenciales de usuario, root en
  Dockerfile, permisos de directorio — **cero** instancias de sql_injection,
  hardcoded_secret, tls_verification_disabled, unsafe_deserialization, etc.
  Las 19 clases son patrones de código (mayoría nacidos de Python: tarfile,
  tempfile, mutable default, bare except); el corpus es revisión general
  políglota (TS/JS, Go, Rust, Kotlin, C#, Ruby, Swift…).
- **Techo de recall grounded para CUALQUIER revisor que solo emita las 19
  clases: 0,3 % estricto (1/352) a 2,6 % generoso (9/352).** La linterna de
  la práctica exige superar 0,7 %: solo es alcanzable cubriendo ~1–2 de los
  ≤9 TP alcanzables, y en PRs chicos (con promediado macro del portal,
  cubrir el de LANdalf solo ya da (1/6)/25 ≈ 0,67 %).

## 2. La nº 295, defecto por defecto — lo que el gold + el portal demuestran

Hechos del portal (asentados en el RESULTADO v2.2): SUCCEEDED, 25/25 PRs;
**grounded P 0,0 % · R 0,0 % · F1 0,0 %**; augmented P 15,0 % · R 0,4 % ·
F1 0,8 %; **11 findings, 3 novel**; duración promedio 7 s.

De grounded R = 0,0 % se sigue sin ambigüedad (con promediado macro, una
sola cobertura en cualquier PR mostraría ≥0,1 %): **la 295 cubrió 0 de los
352 golden TP**. La descomposición de esos 352 misses:

| Categoría | Conteo | Base |
|---|---|---|
| **(a0) Fuera del universo de emisión** — ninguna marca de triage ni pasada profunda puede producirlos; la pérdida es anterior al pipeline | **343** | §1 de este diagnóstico |
| **(a/b/c) Alcanzables pero no cubiertos** — 1 claro + 8 fronterizos; el paso exacto exige el `agent.log` de la 295 | **9** | §1; split pendiente (§5) |
| **(d) Degradación por el freno** | **no verificado** | La vigilancia lo asentó «no gatillado con la evidencia disponible»; sin outputs por PR no se puede contar. Señales indirectas en contra de una degradación masiva: la corrida completó 25/25, y en seco el plan del PR ancla cerraba en US$4,93 < freno 6,50 con 0 degradaciones en 16/16 llamadas de prueba |

Del lado de las emisiones (los 11 findings de la 295):

| Destino de lo emitido | Conteo | Base |
|---|---|---|
| Cubrió un golden TP (categoría «acierto») | **0** | grounded R = 0 |
| Sin match, juzgado TP por el clasificador («novel», solo suma en augmented) | **3** | portal: «3 novel» |
| Sin match o match a gold FP, juzgado FP — **(c) en sentido amplio: se emitió y el corrector no lo contó** | **8** | 11 − 3; el split match-FP vs novel-FP exige el `findings.json` de la 295 |

O sea: en la 295, la categoría (c) a nivel puntaje es **11 de 11 emisiones**
(ninguna contó como cobertura), y la categoría dominante de los misses no
es (a), (b) ni (d): es la **(a0) estructural, 343 de 352 (97,4 %)**.

## 3. La comparación obligada: ¿las otras arquitecturas perdían en el mismo paso?

### 3.1. v1 (nº 251) — descomposición completa, verificada contra el gold

La 251 es la única corrida con outputs completos en disco
(`browser-download-…-run-251-output.zip`: `findings.json` + `agent.log` por
PR). Portal: grounded F1 1,4 % · P 42,9 % · R 0,7 %; augmented F1 4,4 % ·
P 53,3 % · R 2,3 %; 14 findings, 5 novel. Mi adjudicación independiente de
sus 14 emisiones contra el gold **reproduce los tres números grounded del
portal** (P = 3/7 = 42,9 %; R macro = (1/9 + 1/36 + 1/22)/25 = 0,74 % ≈
0,7 %; F1 = 1,4 %), así que la descomposición es firme:

- **Cubrió 3 golden TP:** jadx#3 `Plugin.kt:44` (emisión «cada activación
  lanza un hilo sin sincronizar; Pull/Push concurrentes se pisan» ↔ gold
  correctness «prometía un executor de un solo hilo y sigue usando
  `kotlin.concurrent.thread`»); apilix#12 `store.tsx:648` (emisión sobre el
  cleanup del debounce que cancela la escritura pendiente al cambiar de
  workspace ↔ gold correctness en las mismas líneas 648–668);
  Mcp-Docker#29 `session.go:83` (emisión «CompleteCallback permite completar
  la misma sesión varias veces» ↔ gold security :77 «la sesión queda en el
  store y el state puede repetirse contra /callback»).
- **(c) puro — emitió el defecto y el corpus ya lo tenía… como FP (4):**
  PROTRIDER#10 `pipeline.py:63` — la v1 emitió el `torch.load(weights_only=
  False)` = unsafe_deserialization de manual; el gold contiene ese mismo
  issue en `:62` (regla trailofbits de pickle) **etiqueta FP** (el
  clasificador/humanos lo juzgaron no-TP para este PR). TechDebtMCP#135
  `handlers.ts:441` — la v1 emitió un TOCTOU check-then-read; el gold tiene
  un TOCTOU en `:438` **etiqueta FP**, y el TP de esas líneas es el path
  traversal (clase inexistente entre las 19). chronicle#14 `media.rs:78` y
  `:94` — dos TOCTOU de la v1 contra gold FPs de race en `:46`/`:107` del
  mismo archivo.
- **Novel (sin match, juzgados TP): 5** según el portal — entre ellos el
  `rescue nil` de fastimage `jpeg.rb:50` (silenced_bare_except de manual
  en Ruby: el gold de ese archivo no contiene ese defecto como TP) y las
  dos carreras de primer-usuario-admin de emdash#2.
- **El único TP de clase clara (LANdalf, swallowed_exception): la v1 emitió
  0 findings en ese PR** (3 s de corrida, silencio) — perdido en emisión,
  el análogo (b) de una arquitectura sin triage.

### 3.2. v2.1 (nº 290) — no resoluble desde el registro, con cotas

La 290 dio P 37,5 % · R 0,4 %, 8 findings, 3 novel (RESULTADO-PRACTICA-V21).
El registro **no asentó si ese par era grounded o augmented**, y su zip de
outputs nunca se descargó. Cotas: si 37,5 % = 3/8 fuera augmented micro,
su cobertura grounded fue 0; si fuera grounded, cubrió ~3 TP como la v1.
La v2.1 no tiene triage (pasada única, 19 clases, contexto completo): sus
pérdidas alcanzables solo pueden ser (b)-análogas o (c), y sus 343
pérdidas estructurales son idénticas por construcción. **El zip de la 290
decide; con el registro actual, cualquier split sería inventado.**

### 3.3. Respuesta a la pregunta de fondo

**Sí pierden en el mismo paso — y el paso es anterior a todos los que la
arquitectura controla.** Las tres arquitecturas (v1: una pasada, 8 tipos de
reclamo; v2.1: una pasada, 19 clases; v2.2: triage + profundas, 19 clases)
comparten el mismo universo de emisión, y 343/352 del gold vive fuera de
él. Dentro del universo, la evidencia también converge: la v1 cubrió 3 TP
y **ninguno fue la instancia clara de clase** (sus hits fueron una
concurrencia y dos issues generales que el matcher emparentó); sus dos
emisiones de clase más nítidas (pickle de PROTRIDER, `rescue nil` de
fastimage) chocaron contra un gold que las tenía como FP o no las tenía.
La dilución de la v2.1 y el triage de la v2.2 operan sobre un subconjunto
que el benchmark casi no puntúa: por eso dos arquitecturas opuestas dan el
mismo recall (0,4 %) y la v1, con una pasada general más ancha dentro de
su prompt, dio apenas 0,7 %.

## 4. Ejemplos concretos nombrados (síntesis)

1. **LANdalf#88, `DeviceMonitoringService.cs:184`, `swallowed_exception`
   (gold TP, fácil, diff-only):** el único defecto del set que la 295
   podía cazar por diseño. Grounded R = 0 % prueba que no lo cubrió; si
   fue (a) triage, (b) profunda o (c) anclaje/matcher, lo dice su
   `agent.log`. La v1 lo perdió por emisión directa (0 findings en el PR).
2. **PROTRIDER#10, `pipeline.py:63`, `unsafe_deserialization`:** la v1 lo
   emitió con el patrón exacto de la clase; el gold lo contiene en `:62`
   como **FP**. Categoría (c) en su forma más pura: el corrector no lo
   contó porque el corpus ya había juzgado ese issue como no-TP.
3. **TechDebtMCP#135, `handlers.ts:438–455`:** la v1 emitió TOCTOU; el
   corpus tiene ese TOCTOU como FP y el TP de las mismas líneas es un
   path traversal — clase que **no existe** entre las 19. Aun acertando
   el archivo y las líneas, la clase pedida no era la del defecto.
4. **pika#200, `ContentView.swift:151` (try? que descarta errores) y
   chronicle#14, `retention.rs:150` (error logueado, sigue, reporta
   éxito):** los dos análogos `swallowed_exception` más cercanos del set;
   junto con LANdalf forman el subconjunto que una v2.3 debería usar como
   vara interna si se quiere medir la clase sin ruido del corpus general.

## 5. Qué falta para cerrar (a)/(b)/(c)/(d) por defecto en la 295

Descargar del portal (review-bench.ai → alma-reviewer → run 295) el zip de
outputs, igual que se hizo con las corridas 251/282/287, y por cada PR:

1. `agent.log` → línea `llm_run` (JSON del run info v22): leer
   `selection_selected` (¿marcó la clase del TP alcanzable de ese PR? →
   si no, **(a)**), `selection_overflow` y `degradation` (→ **(d)** con
   conteo directo de PRs afectados; el falsador del papel v22 es >1/4).
2. Si marcó y la pasada corrió (`passes`), mirar `raw_findings` vs
   `malformed_findings` + `unanchored_findings`: crudos 0 → **(b)** silencio
   de la profunda; crudos >0 pero todos caídos por anclaje/formato →
   **(c) interno** (la disciplina de cita exacta contra el head descartó
   el candidato antes de salir).
3. Cruzar el `findings.json` de cada PR contra el gold por archivo
   (matching semántico, §6.2 de la metodología) → **(c) de corrector** y
   aciertos, como se hizo aquí con la 251.
4. PRs prioritarios para esa lectura: LANdalf#88 (el TP claro),
   pika#200 y chronicle#14 (los análogos swallowed), Mcp-Docker#29,
   apilix#12, konturio#1230, jadx#3, CrabTrap#15 (los fronterizos).

## 6. Conclusión falsable

**El paso que concentra la pérdida no es el triage (a), ni la profunda
(b), ni el freno (d): es el universo de emisión.** 343 de 352 golden TP
(97,4 %) no son instancias de ninguna de las 19 clases, así que ningún
reordenamiento de pasadas puede mover el recall grounded más allá del
techo de 0,3–2,6 %; los tres diseños medidos (0,7 % / 0,4 % / 0,0 %
grounded) ya viven pegados a ese techo, y la diferencia entre ellos es
ruido alrededor de ≤9 defectos alcanzables.

**Qué la falsaría:** que el `agent.log` de la 295 muestre, para LANdalf,
al triage marcando `swallowed_exception`, la profunda corriendo y un
candidato anclado emitido que el portal igual no contó — eso movería el
cuello a (c) y esta conclusión caería. (La predicción de este diagnóstico
es la contraria: en LANdalf el triage no marcó la clase o la profunda
devolvió silencio, como le pasó a la v1 por emisión.)

**El cambio puntual que ataca el cuello medido** (nombrado, no
construido): no es una cuarta arquitectura de pasadas sobre las mismas 19
clases — es **ensanchar el universo de emisión del brazo base** (una
pasada de revisión general cuyos hallazgos salgan sin restricción de
clase, el rasgo que le dio a la v1 sus únicos 3 aciertos) o, si el
experimento quiere seguir midiendo la puerta, **redefinir la vara de la
práctica al subconjunto alcanzable** (recall sobre los ≤9 TP de
clase/análogos, con LANdalf como caso testigo). Seguir ajustando
triage/profundas contra el recall total es optimizar contra un denominador
que el diseño no puede tocar.

---
*Fuentes: gold y metodología públicos de ReviewBench (repo clonado y
verificado el 21/10); outputs de la corrida 251 en
`~/workspace/browser_downloads/sess-3687829514/`; `REGISTRO-REVIEWBENCH.md`;
`RESULTADO-PRACTICA-V21-20261021.md`; `RESULTADO-PRACTICA-V22-20261021.md`;
`agent/llm_reviewer_v22.py`; `agent/alma_gate_v13.py`. Sin gasto, sin
corridas nuevas, sin tocar puertas ni registros ajenos a este archivo.*
