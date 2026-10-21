# Pre-registro — ReviewBench v2.1: el revisor de UNA pasada (diseño C1)

**Fecha:** 2026-10-21 · **Autor del «corre»:** Alejandro («necesito comprobar
que ALMA funcione o cómo hacerla funcionar», 21/10), sobre el diagnóstico y
las opciones de la **Adenda 6** de `PREREGISTRO-REVIEWBENCH-V2.md`.
**Estado:** CONGELADO al escribirse. Toda corrección posterior es una adenda
fechada, nunca una edición silenciosa.
**Antecede:** `PREREGISTRO-REVIEWBENCH-V2.md` (congelado 2026-10-19, con
Adendas 1–6) y `RESULTADO-SEMAFORO-20261021.md` (semáforo v2: VERDE).

## 1. El antecedente medido (por qué existe la v2.1)

- El revisor v2 funciona en miniatura: el semáforo del 21/10 (batería
  sintética congelada de 8 códigos) dio **VERDE** — brazo base: 16 hallazgos
  emitidos, **8/8** defectos plantados detectados; brazo ALMA (puerta 1.3.0):
  6 emitidos, **6/8**. Costo real total US$2,7457.
- El mismo revisor es **inviable en costo sobre PRs reales**: su guardia de
  pre-vuelo estimó el peor caso por PR entre US$8,37 y US$97,21 (20 pasadas:
  19 clases + general, contexto completo en cada una) contra un freno de
  US$5,00–6,50, y se negó a correr en las dos corridas de práctica lanzadas
  (#282 y #287; detalle y corrección del diagnóstico en la Adenda 6). La
  plataforma ejecutó bien; el freno es el mensajero, no el problema: el
  diseño de 20 pasadas con contexto completo no cabe en la economía de esta
  práctica (tope US$30) ni de la final.
- El dato económico ancla: el PR cmik_apilix_12 costó en la v1 **US$0,86
  reales en UNA pasada** (41.160 tokens de prompt, 3.271 de completion,
  precios de planificación US$15/M entrada y US$75/M salida). El mismo PR,
  estimado por la guardia de la v2 a 20 pasadas: US$36,80.

## 2. Hipótesis de la v2.1 (falsable)

1. **Economía:** con UNA sola pasada por PR, el peor caso estimado por la
   guardia vuelve al orden de **US$1 por PR** (ver §5) y la práctica cabe en
   el tope congelado de US$30: el veredicto «ALMA mejora» se vuelve
   alcanzable.
2. **Detección:** una sola llamada que pide las 19 clases **en secciones**,
   con la misma disciplina de cita exacta de la v2, conserva la detección
   medida en el semáforo (base 8/8, ALMA 6/8) en vez de diluirla — el riesgo
   declarado de C1 en la Adenda 6. El semáforo v2.1 (§6) es donde esta
   hipótesis se contrasta primero, sin ajustar nada a partir de él.

## 3. Diseño C1 (qué cambia)

**Cambia el revisor** (`agent/llm_reviewer_v21.py`, selección
`RB_CONFIG_REVIEWER=v21`; el default del paquete sigue siendo `v1`):

- **Una sola llamada por PR.** Un único prompt que recorre las **19 clases
  de la puerta 1.3.0 en secciones** — una sección por clase con su guidance
  (la misma de la v2 bajo `RB_CONFIG_GATE=v13`, incluidas las adendas de
  disciplina de cita de la palanca 1 de la Adenda 3, **conservadas
  textuales**) — y pide una salida JSON única: un array `findings` donde
  cada hallazgo declara su `claim_type` y cita su evidencia.
- **Mismo contexto que la v2:** el diff más el contenido head completo de
  cada archivo tocado, leído de `/work/repo` con el mismo presupuesto de
  contexto por PR (default 60.000 tokens estimados) y la misma declaración
  de incluidos/saltados/ausentes.
- **Misma disciplina de cita exacta:** cada hallazgo debe reproducir el
  texto exacto de las líneas citadas del archivo head; la verificación de
  anclaje del revisor (la cita existe en el head y coincide byte a byte a
  nivel de línea) se aplica igual que en la v2, y `evidence_text` se llena
  desde el archivo head, nunca desde las palabras del modelo. Lo que no
  ancla se descarta en el revisor, contado como no anclado.
- **Misma guardia de gasto, sobre UNA pasada:** la estimación de peor caso
  previa a la llamada cubre la única llamada (prompt completo + salida
  acotada por `max_completion_tokens`); si supera `RB_MAX_SPEND_USD`, se
  niega antes de llamar, igual que la v2. El control acumulativo posterior
  a la llamada también queda.
- **Sin pasada general en el brazo base.** Diferencia declarada respecto
  del diseño v2 (donde el papel permitía al base una pasada general
  adicional): con una sola llamada no existe «pasada extra» sin romper la
  paridad del A/B. Ambos brazos hacen LA MISMA llamada única; el único
  campo distinto entre brazos vuelve a ser `governance`, sin excepciones.
  En ambos brazos la llamada pide solo clases verificables: en el base los
  candidatos se emiten sin puerta; en el ALMA los juzga la 1.3.0.

**Qué NO cambia:**

- **Las puertas 1.0.0–1.3.0, byte a byte.** POLICY_SHA256 asentados:
  1.0.0 `3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35` ·
  1.1.0 `6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9` ·
  1.2.0 `a768afa46136ba1bf542da65006a946d11cb39e8db73fbd484c3f021b7994211` ·
  1.3.0 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`.
  La práctica v2.1 corre con la **1.3.0** (`RB_CONFIG_GATE=v13` en ambas
  configuraciones: define el universo de 19 clases; en el brazo base la
  puerta se omite al validar, como en la v2).
- El modelo (gpt-5.6-sol), el effort (medium), la plataforma, el contrato
  de salida y el pipeline: los hallazgos llegan a la puerta en el **mismo
  formato** `Candidate` que hoy.
- La **regla de avance** de la v2, intacta: F1 ALMA ≥ F1 base, precisión
  ALMA ≥ precisión base + 0,05, recall ALMA no cae más de 0,03 (métrica
  primaria grounded F1, co-primaria grounded precision, mismo set privado
  de 25 PRs, 1 corrida por brazo, la primera que complete es la válida).
- La **prueba de la linterna**, intacta: si el recall del brazo base no
  supera el 0,7% de la v1, la hipótesis de contexto queda falsada aunque
  el A/B «gane» por precisión.
- La **batería del semáforo**, intacta y congelada (`fixtures_semaforo`,
  manifiesto del 2026-10-20, 32/32 hashes).
- Las prohibiciones anti-pesca de la v2: nada de ajustar prompts contra el
  detalle por PR de la práctica; nada de repetir corridas «hasta que
  salga»; nada de tocar la puerta para mejorar el A/B; el set dorado es
  privado y nunca fue visto.

## 4. Cuenta económica esperada (con su base de cálculo)

Precios de planificación del paquete (los de la v1 y la v2): US$15/M tokens
de entrada, US$75/M de salida; salida acotada por `max_completion_tokens`
(default 4.096 → US$0,3072 de salida máxima por llamada). La estimación de
peor caso usa la fórmula de la propia guardia: tokens estimados por
caracteres (÷3,5, conservadora) sobre el prompt completo, más la salida
máxima.

- **Ancla medida (v1):** PR cmik_apilix_12 — 41.160 tokens de prompt y
  3.271 de completion reportados por la API → US$0,8627 reales en una
  pasada (la fórmula reproduce el número: 41.160×15/M + 3.271×75/M =
  US$0,8627).
- **Peor caso v2.1 sobre ese mismo PR:** prompt de sistema con las 19
  secciones ≈ 1.586 tokens estimados (5.550 caracteres, medido al componer
  el prompt) + 41.160 de tamaño de PR → entrada estimada 42.746 →
  **US$0,9484**. Orden **US$1**, contra los US$36,80 que la guardia de la
  v2 estimó para el mismo PR (39× menos).
- **Peor caso con el contexto al tope:** el presupuesto de contexto
  (60.000 tokens estimados) acota el prompt; con diff y sistema, entrada
  estimada ≈ 66.586 → **US$1,31**. El freno firmado de US$6,50 por PR
  (Adenda 4) queda con ~5× de margen: la guardia de la v2.1 no debería
  negarse sobre ningún PR que quepa en el presupuesto de contexto.
- **Práctica v2.1 (50 códigos):** costo real esperado ≈ US$10–25 (base:
  media real de la v1 US$0,14/PR con salida chica; PRs grandes tipo el
  ancla, ~US$0,9). **Tope duro heredado: US$30**, sin cambios; si se
  alcanza, la práctica se detiene y se registra, como mandaba el papel v2.
- **Semáforo v2.1 (16 códigos):** costo real esperado ≈ **US$1** (rango
  US$0,5–2). Base: en la corrida v2 de hoy cada código costó ~US$0,16–0,18
  reales con ~20 llamadas de contexto diminuto; la v2.1 hace UNA llamada
  por código con ese mismo contexto y un prompt de sistema mayor
  (~US$0,024 de entrada estimada) y una salida única. Tope duro del
  semáforo: **US$20** (Adenda 3), sin cambios.

## 5. Semáforo v2.1 — criterio de veredicto (fijado antes de correr)

Misma batería congelada, mismos dos brazos (`reviewer=v21`, `gate=v13`,
modelo gpt-5.6-sol, effort medium; único campo distinto = gobernanza),
una corrida por brazo, sin ajustar NADA del sistema a partir del
resultado (su función es detectar catástrofes, no afinar).

- **ROJO** (criterio de la Adenda 3, heredado): si algún brazo emite CERO
  hallazgos sobre los códigos con defectos plantados → no se lanza la
  práctica; se frena, se diagnostica y el diagnóstico se asienta antes de
  cualquier nuevo intento.
- **VERDE:** ambos brazos emiten → se procede a la práctica v2.1 con el
  «sí» de Alejandro al momento de lanzar.
- **Comparación declarada (no altera el veredicto):** contra la corrida
  v2 de hoy — base 16 emitidos / 8/8 plantados detectados; ALMA 6 emitidos
  / 6/8. Se asientan, por brazo, emitidos y plantados detectados de la
  v2.1 al lado de esos números. Si un brazo detecta MENOS plantados que
  su par de la v2, eso se registra como **señal de dilución C1** (el
  riesgo declarado en la Adenda 6) y se declara en el manifiesto de la
  práctica; no se «corrige» el revisor contra el semáforo.
- **La guardia también se mide:** ninguna negativa de pre-vuelo es
  aceptable sobre la batería (los 16 códigos deben completar llamada);
  si la guardia se niega en algún código, el semáforo es ROJO por
  economía, sea cual sea la emisión.

## 6. Secuencia y falsadores

1. Construir `llm_reviewer_v21.py` con mock (US$0): suite previa verde
   (137/137) + tests nuevos del revisor (una sola llamada por PR; la
   guardia estima 1 pasada — con el tamaño del ancla, orden US$1 —; la
   salida alimenta la puerta 1.3.0 sin cambios de formato) + corrida en
   seco con LLM mock sobre los 8 códigos de la batería × 2 brazos.
2. Semáforo v2.1 real — gasto: requiere el «sí» de Alejandro y una clave
   viva por la vía sancionada, como hoy. Veredicto según §5.
3. Práctica v2.1 — imagen y manifiesto nuevos (mismo procedimiento que
   la v2), «sí» al lanzar, regla de avance y linterna de la §3.

**Falsadores (qué nos haría detenernos):**

- La guardia de la v2.1 se niega sobre PRs reales que caben en el
  presupuesto de contexto → la cuenta de la §4 era falsa: registrar y
  detener.
- Semáforo v2.1 con ALMA en 0 emitidos, o detección de plantados muy por
  debajo de la v2 (≤3/8) → la pasada única diluye la detección: registrar
  el nulo de C1 y detener (la salida sería C2 de la Adenda 6, con su
  propio papel — no un ajuste en caliente de la v2.1).
- Práctica: los falsadores heredados de la v2 (linterna sin superar
  0,7%; ALMA emitiendo ≈0–1 con el revisor nuevo; costo >3× lo estimado
  sin mejora de recall).
