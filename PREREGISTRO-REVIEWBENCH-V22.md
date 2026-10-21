# Pre-registro — ReviewBench v2.2: triage + pasadas profundas (diseño C2)

**Fecha:** 2026-10-21 · **Autor del «corre»:** Alejandro («Construir
C2», 21/10 18:30 EDT), sobre el veredicto de linterna de la práctica
v2.1 y el diseño C2 de la **Adenda 6** de
`PREREGISTRO-REVIEWBENCH-V2.md`.
**Estado:** CONGELADO al escribirse. Toda corrección posterior es una
adenda fechada, nunca una edición silenciosa.
**Antecede:** `PREREGISTRO-REVIEWBENCH-V2.md` (con Adendas 1–6),
`PREREGISTRO-REVIEWBENCH-V21.md`, `RESULTADO-PRACTICA-V21-20261021.md`.

## 1. El antecedente medido (por qué existe la v2.2)

Los dos diseños anteriores fallaron en extremos opuestos, ambos
medidos:

- **La v2 (20 pasadas) veía pero no podía pagar su vista.** Semáforo:
  base 8/8, ALMA 6/8. En PRs reales su guardia estimó US$8,37–97,21 por
  PR y se negó a correr (corridas #282/#287, «refused before calling»):
  20 pasadas con contexto completo no caben en la economía de la
  práctica (tope US$30) ni de la final.
- **La v2.1 (1 pasada, diseño C1) pagaba pero no veía.** Semáforo
  VERDE (7/8 y 7/8, US$0,5038), y la práctica completó — la corrida
  base nº 290 fue la primera post-v1 en puntuar — pero con **recall
  0,4 %** (precisión 37,5 %, F1 ≈0,8 %, 8 hallazgos): la **prueba de
  la linterna NO PASÓ** (0,4 % ≤ 0,7 % de la v1), el brazo ALMA no se
  lanzó y la práctica quedó **sin veredicto válido**. La causa
  declarada: **dilución C1** — 19 clases compitiendo por una sola
  salida acotada sobre contextos de decenas de miles de tokens. Es el
  riesgo que la Adenda 6 declaró para C1 y el falsador que la §6 del
  papel v2.1 fijó («linterna sin superar 0,7 %» → la salida es C2,
  con su propio papel: este).

**C2 es el punto medio que la Adenda 6 definió:** «una pasada barata
solo sobre el diff marca clases candidatas (≤5); las pasadas profundas
corren solo para esas, con el archivo. Riesgo: el triage puede no
marcar una clase presente (pérdida de recall medible)». La v2.2 pone
ese riesgo en el centro de la medición: cada marca del triage queda
registrada, y un defecto plantado cuya clase no fue marcada es una
pérdida atribuible al triage, no al azar.

## 2. Hipótesis de la v2.2 (falsable)

1. **Economía:** selección (diff solo) + hasta 5 pasadas profundas
   (contexto completo) tienen un peor caso del orden de **US$2–6**
   sobre el PR ancla de 41.160 tokens (§4) — una fracción de los
   US$36,80 que la guardia de la v2 estimó para ese PR — y la
   práctica cabe en el tope congelado de US$30. Cuando ni así cabe,
   la regla de degradación (§3c) reduce pasadas **declarando** la
   truncación: ningún PR se niega en silencio ni se corta a mitad.
2. **Detección:** las pasadas profundas son las pasadas de la v2,
   byte a byte (misma plantilla, misma guidance con las adendas de
   cita de la Adenda 3, mismo contexto completo, misma verificación
   de anclaje). La detección por clase marcada debería comportarse
   como la de la v2 (semáforo: 8/8 base, 6/8 ALMA). El único canal de
   pérdida nuevo es que el triage no marque una clase presente —
   medible caso por caso en el semáforo (§5).
3. **Linterna:** con pasadas profundas de formato v2 sobre las clases
   que el diff sugiere, el recall del brazo base en PRs reales
   debería superar el 0,7 % de la v1. Si tampoco pasa, la hipótesis
   falsada ya no es la estructura de pasadas — es la de contexto
   (ver falsadores, §6).

## 3. Diseño C2 (qué cambia)

**Cambia el revisor** (`agent/llm_reviewer_v22.py`, selección
`RB_CONFIG_REVIEWER=v22`; el default del paquete sigue siendo `v1`).
El revisor hace, por PR, tres etapas:

### (a) Pasada de selección (triage) — solo el diff

- **Una llamada** cuyo contenido de usuario es **el diff únicamente**
  (sin archivos head, sin contexto completo). El prompt de sistema
  lista las clases de la puerta activa (las 19 de la 1.3.0 bajo
  `RB_CONFIG_GATE=v13`) con la guidance de la v2 por clase,
  **byte-idéntica** (incluidas las adendas de disciplina de cita de la
  palanca 1 de la Adenda 3 bajo v13), y pide una salida JSON única:
  `{"candidates": [{"claim_type": "...", "reason": "..."}]}` con las
  clases que el diff sugiere, **en orden de prioridad** (la más
  probable primero).
- El revisor filtra la respuesta: descarta clases que no sean de la
  puerta activa (contadas), deduplica conservando el primer orden, y
  aplica el **tope duro de 5 clases** (`MAX_DEEP_PASSES`). Las marcas
  válidas que excedan el tope quedan registradas como
  `selection_overflow` en la información de corrida — nunca se corren
  «porque el modelo las mencionó dos veces» ni se descartan en
  silencio.
- La salida de esta pasada está acotada aparte
  (`max_completion_tokens` propio, default 1.024; env
  `RB_LLM_V22_TRIAGE_MAX_OUTPUT_TOKENS`): marcar clases no necesita
  la salida de una revisión.
- La selección **no produce hallazgos**: solo decide qué clases
  reciben pasada profunda. Sus marcas quedan asentadas en la
  información de corrida (`selection_candidates`,
  `selection_selected`, `selection_overflow`).

### (b) Pasadas profundas — el formato exacto de la v2

- Por cada clase seleccionada, en el orden de prioridad del triage,
  **una pasada profunda idéntica a la de la v2**: la misma plantilla
  de prompt de la v2 (importada, no copiada: `_SYSTEM_PROMPT_TEMPLATE`
  de `llm_reviewer_v2.py`), la misma guidance por clase (bajo v13,
  con las adendas de cita **textuales**), el mismo contenido de
  usuario (diff + contenidos head completos de los archivos tocados,
  mismo presupuesto de contexto por PR, default 60.000 tokens
  estimados, misma declaración de incluidos/saltados/ausentes) y la
  misma verificación de anclaje y conversión a `Candidate` de la v2
  (un hallazgo cuya clase no coincide con su pasada es malformed).
- Los hallazgos llegan a la puerta en el **mismo formato `Candidate`**
  de siempre; la procedencia se estampa `alma-llm-reviewer-v22`.
- **Sin pasada general en ningún brazo** (paridad A/B, heredada de la
  declaración de la v2.1 §3): ambos brazos hacen la misma selección y
  las mismas profundas; el único campo distinto entre brazos sigue
  siendo `governance`. En el base los candidatos se emiten sin puerta;
  en el ALMA los juzga la 1.3.0.

### (c) Guardia en dos etapas y REGLA DE DEGRADACIÓN (pre-registrada)

La guardia de la v2 sumaba el peor caso de TODAS las pasadas posibles
y se negaba. La de C2 planifica sobre lo que va a correr:

1. **Pre-vuelo 1 (antes de cualquier llamada):** si el peor caso de la
   pasada de selección sola supera `RB_MAX_SPEND_USD`, el revisor se
   niega antes de llamar (falla cerrada, como siempre). Nada más se
   exige ex ante: el plan completo depende del triage.
2. **Pre-vuelo 2 (después de la selección, antes de las profundas):**
   con el costo real ya reportado de la selección, se admiten pasadas
   profundas en orden de prioridad mientras
   `costo_selección + Σ peor_caso(profundas admitidas) ≤ freno`.
   Las marcadas que no caben **no corren** y quedan asentadas en la
   información de corrida como degradación:
   `degradation = {reason: "spend_cap", deep_passes_planned,
   deep_passes_run, deep_passes_dropped: [...]}`. La truncación es un
   dato de la corrida, jamás un silencio.
3. **Caso degenerado — ni una profunda cabe:** el revisor emite **solo
   lo de la selección**: una única pasada mixta restringida a las
   clases marcadas (las secciones de la v2.1, solo esas clases), si
   su peor caso cabe en el freno restante; la corrida lo declara
   (`degradation.fallback_single_pass = true`). Si ni eso cabe, emite
   cero hallazgos **con la declaración asentada**
   (`degradation.reason = "no_deep_pass_affordable"`) — nunca una
   negativa muda ni un cero disfrazado de «no encontró nada».

   **Adenda 1 (2026-10-21, antes de cualquier corrida de la v2.2):**
   precisión de implementación de este punto — la pasada mixta del
   caso degenerado corre **sobre el diff únicamente**, como la propia
   selección (sin contenidos head). Es lo que la hace alcanzable
   cuando ninguna profunda con contexto completo cabe en el freno;
   con el mismo contexto que una profunda, su peor caso sería ≥ el
   de una profunda y la rama sería inalcanzable. La verificación de
   anclaje contra el head se aplica igual: un hallazgo del fallback
   cuya cita no coincida byte a byte con el archivo head se descarta
   como no anclado, como en toda pasada.
4. **Control acumulativo posterior** (heredado de v1/v2/v2.1): tras
   cada llamada, si el costo real acumulado supera el freno, se falla
   cerrado sin emitir hallazgos.

## 4. Cuenta económica esperada (con su base de cálculo)

Precios de planificación del paquete: US$15/M tokens de entrada,
US$75/M de salida; peor caso = entrada estimada por caracteres (÷3,5,
la fórmula de la guardia) + salida acotada. Anclas medidas:

- **Pasada profunda (formato v2):** sobre el PR ancla (41.160 tokens
  de prompt medidos en la v1 para cmik_apilix_12) el peor caso de una
  pasada con contexto completo es ≈ **US$0,95** (la cuenta de la §4
  del papel v2.1: entrada estimada 42.746 → US$0,64 + salida máxima
  4.096 → US$0,31). Con el contexto saturado al presupuesto (60.000):
  ≈ **US$1,31**.
- **Pasada de selección (solo diff):** el diff del ancla es una
  fracción del prompt total; con un diff de ~12.000 tokens estimados,
  peor caso ≈ 12.000×US$15/M + 1.024×US$75/M ≈ **US$0,26**. La Adenda
  6 la estimaba en US$0,10–0,30 reales: consistente.
- **PR ancla, plan completo:** selección (US$0,26) + 5 profundas
  (5 × US$0,95) ≈ **US$5,01** — dentro del freno firmado de US$6,50
  (Adenda 4) y del orden US$2–6 para PRs típicos (la mayoría marca
  menos de 5 clases y/o trae menos contexto). Contra los US$36,80 que
  la guardia de la v2 estimó para el mismo PR: ~7× menos, porque 14
  pasadas profundas nunca se pagan.
- **Peor caso con contexto saturado:** selección + 5 × US$1,31 ≈
  US$6,8 — *por encima* del freno: es exactamente el territorio de la
  regla de degradación (§3c): corren 4 profundas (≈US$5,5) y la quinta
  queda declarada como caída por freno. La degradación es el
  comportamiento diseñado para PRs gigantes, no una falla.
- **Práctica v2.2 (50 códigos):** costo real esperado ≈ US$10–25
  (reales, no peor caso: las pasadas reales de la v2 costaron ~US$0,17
  por código en la batería; un PR real grande pagó US$0,86 en la v1).
  **Tope duro heredado: US$30**; por construcción ningún PR puede
  superar el freno por PR (planificación por peor caso + control
  acumulativo).
- **Semáforo v2.2 (16 códigos):** la batería es miniatura (la
  selección y las profundas trabajan sobre diffs de cientos de
  bytes); por analogía con las corridas v2 (US$2,75) y v2.1
  (US$0,50), esperado ≈ **US$1–3**. Tope duro del semáforo: **US$20**
  (Adenda 3), sin cambios.

## 5. Qué NO cambia

- **Las puertas 1.0.0–1.3.0, byte a byte.** POLICY_SHA256 asentados:
  1.0.0 `3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35` ·
  1.1.0 `6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9` ·
  1.2.0 `a768afa46136ba1bf542da65006a946d11cb39e8db73fbd484c3f021b7994211` ·
  1.3.0 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`.
  La práctica v2.2 corre con la **1.3.0** (`RB_CONFIG_GATE=v13` en
  ambas configuraciones, como la v2.1).
- El modelo (gpt-5.6-sol), el effort (medium), la plataforma, el
  contrato de salida y el pipeline.
- La **regla de avance** de la v2, intacta: F1 ALMA ≥ F1 base,
  precisión ALMA ≥ precisión base + 0,05, recall ALMA no cae más de
  0,03 (mismo set privado de 25 PRs, 1 corrida por brazo, la primera
  que complete es la válida).
- La **prueba de la linterna**, intacta: recall del brazo base debe
  superar el 0,7 % de la v1.
- La **batería del semáforo**, intacta y congelada
  (`fixtures_semaforo`, manifiesto del 2026-10-20, 32/32 hashes).
- Las prohibiciones anti-pesca de la v2: nada de ajustar prompts
  contra el detalle por PR de la práctica; nada de repetir corridas
  «hasta que salga»; nada de tocar la puerta para mejorar el A/B; el
  set dorado es privado y nunca fue visto.

## 6. Semáforo v2.2 — criterio de veredicto (fijado antes de correr)

Misma batería congelada, mismos dos brazos (`reviewer=v22`,
`gate=v13`, modelo gpt-5.6-sol, effort medium; único campo distinto =
gobernanza), una corrida por brazo, sin ajustar NADA del sistema a
partir del resultado.

- **ROJO:** si algún brazo emite CERO hallazgos sobre los códigos con
  defectos plantados; si la guardia se niega en algún código; **o si
  la regla de degradación se dispara en algún código de la batería**
  (la batería es miniatura: si el freno muerde ahí, la cuenta de la
  §4 es falsa).
- **VERDE:** ambos brazos emiten, sin negativas ni degradación → se
  procede a la práctica v2.2 con el «sí» de Alejandro al lanzar.
- **Mediciones C2 declaradas (no alteran el veredicto salvo ROJO):**
  por caso y brazo — si el triage marcó la clase plantada
  (`triage_hit`), cuántas clases marcó, cuántas profundas corrieron.
  Un caso cuyo defecto plantado no puede detectarse porque su clase
  no fue marcada se asienta como **triage miss**: la pérdida de
  recall de C2 queda atribuida y contada, no escondida en el ruido.
- **Comparación declarada:** contra v2 (base 16 emitidos / 8/8;
  ALMA 6 / 6/8) y v2.1 (base 7 / 7/8; ALMA 7 / 7/8). Si un brazo
  detecta MENOS plantados que su par v2.1, se registra como señal
  (de triage o de dilución residual) sin «corregir» contra el
  semáforo.

## 7. Secuencia y falsadores

1. Construir `llm_reviewer_v22.py` con mock (US$0): suite previa
   verde (149/149) + tests nuevos (la selección marca ≤5 y solo esas
   reciben profunda; la guardia suma selección + profundas — orden
   US$2–6 en el ancla, no 36 —; la degradación se dispara con un
   freno chico y queda registrada; el formato alimenta la 1.3.0 sin
   cambios) + corrida en seco con LLM mock sobre los 8 códigos de la
   batería × 2 brazos (16/16 sin negativas con freno US$6,50).
2. Semáforo v2.2 real — gasto: requiere el «sí» de Alejandro y una
   clave viva por la vía sancionada. Veredicto según §6.
3. Práctica v2.2 — imagen y manifiesto nuevos (mismo procedimiento
   que la v2/v2.1), «sí» al lanzar, regla de avance y linterna de
   la §5.

**Falsadores (qué nos haría detenernos):**

- El triage no marca la clase plantada en ≥4 de 8 casos por brazo en
  el semáforo → el triage es el cuello: registrar el nulo de C2 y
  detener (la salida NO es afinar el triage contra la batería).
- Semáforo v2.2 con un brazo en ≤3/8 plantados detectados → la
  estructura selección+profundas no conserva la detección de la v2:
  registrar y detener.
- Práctica: la linterna vuelve a no superar 0,7 % con pasadas de
  formato v2 → la hipótesis falsada es la de contexto, no la de
  estructura de pasadas: registrar y detener la línea de revisores.
- Degradación declarada en más de 1/4 de los PRs de la práctica → la
  economía de C2 tampoco cierra sobre PRs reales: registrar.
