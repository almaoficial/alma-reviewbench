# Pre-registro — ReviewBench v2.3: el revisor general (camino A)

**Fecha:** 2026-10-21 · **Autor del «corre»:** Alejandro, que eligió el
**camino A — ensanchar la base** — el 21/10/2026 a las 21:01 EDT
(«A» a la recomendación fundada en el diagnóstico y su adenda).
**Estado:** CONGELADO al escribirse. Toda corrección posterior es una
adenda fechada, nunca una edición silenciosa. **Este papel no
autoriza construir nada: la construcción espera el «sí» de Alejandro
a ESTE papel (§11, paso 1).**
**Antecede:** `PREREGISTRO-REVIEWBENCH-V2.md` (con Adendas 1–6),
`PREREGISTRO-REVIEWBENCH-V21.md`, `PREREGISTRO-REVIEWBENCH-V22.md`,
`RESULTADO-PRACTICA-V22-20261021.md`,
`DIAGNOSTICO-PRACTICA-V22-20261021.md`,
`ADENDA-DIAGNOSTICO-PRACTICA-V22-20261021.md` y
`PREREGISTRO-PUERTA-140.md`.

## 1. El antecedente medido (por qué existe la v2.3)

- **La práctica v2.2 cerró sin veredicto válido.** Base nº 295:
  SUCCEEDED, 25/25 PRs, pero **grounded P 0,0 % · R 0,0 % · F1 0,0 %**
  (augmented P 15,0 % · R 0,4 % · F1 0,8 %; 11 findings, 3 novel). La
  linterna no pasó (0,0 % ≤ 0,7 %), el brazo ALMA no se lanzó, y con
  esta son **cuatro prácticas (v1, v2, v2.1, v2.2) sin un solo puntaje
  válido del brazo ALMA**: la comparación que el sistema existe para
  medir nunca se midió en el examen real.
- **El gold de la práctica es público y fue adjudicado completo**
  (diagnóstico del 21/10, verificado archivo por archivo): el set
  tiene **352 hallazgos golden TP** (y 213 FP). Distribución por la
  propia taxonomía del benchmark: correctness 133 · reliability 58 ·
  maintainability 44 · testing 35 · security 27 · documentation 21 ·
  api-architecture 12 · performance 12 · accessibility 10.
- **343 de los 352 TP (97,4 %) están fuera del universo de las 19
  clases** de la puerta 1.3.0: ninguna de las 19 los describe. Quedan
  8 análogos fronterizos (2,3 %) y **una sola instancia clara** de
  clase (0,3 %): LANdalf#88, `swallowed_exception`. Ni siquiera la
  categoría «security» del benchmark intersecta: sus 27 TP son
  traversal, CSRF, PKCE/OAuth, CORS, credenciales en claro, root en
  Dockerfile — cero instancias de las 19 clases.
- **Techo estructural:** para cualquier revisor que solo emita las 19
  clases, el recall grounded máximo sobre este set es **0,3 %
  estricto (1/352) a 2,6 % generoso (9/352)**. Las tres arquitecturas
  medidas ya viven pegadas a ese techo; sus diferencias son ruido
  alrededor de ≤9 defectos alcanzables.
- **La única base que puntuó en grounded es la v1** (nº 251: P 42,9 %
  · R 0,7 % · F1 1,4 %), y sus 3 TP cubiertos vinieron de su **pasada
  general sin restricción de clase**: jadx#3 concurrencia
  (`Plugin.kt:44`), apilix#12 pérdida por debounce (`store.tsx:648`),
  Mcp-Docker#29 replay de sesión (`session.go:83`) — ninguno es una
  instancia de las 19 clases. Sus dos emisiones de clase más nítidas
  chocaron contra el gold (el pickle de PROTRIDER estaba etiquetado
  FP; el `rescue nil` de fastimage salió como novel, no como TP).
- **v2.1 (nº 290) y v2.2 (nº 295) empatan en grounded 0,0 %.** El
  «P 37,5 % · R 0,4 %» de la 290 era **augmented** (3 novel / 8
  emitidos; adjudicación de la adenda): su cobertura grounded fue
  0/352. La comparación «37,5 % → 15,0 %» entre prácticas mezcla
  augmented con augmented; en la métrica dura, ambas son cero.
- **El cierre con outputs de la 295 acota el margen alcanzable:**
  los 9 TP alcanzables se perdieron **todos en la etapa que decide
  qué mirar — (a) = 9/9** (la selección no marcó la clase del TP).
  En 5 PRs la selección no marcó *nada*; en LANdalf marcó
  `race_condition` con `DeviceMonitoringService.cs` en contexto y
  `swallowed_exception` jamás apareció (la predicción falsable del
  diagnóstico sobre LANdalf quedó **confirmada** por su primer
  disyunto). (b) = 0, (c) interno = 0 (`malformed = 0`,
  `unanchored = 0` en los 25 PRs) y **(d) = 0: degradación en 0/25
  PRs — el falsador de economía de C2 NO se gatilló**. Las profundas,
  cuando se las convoca con la clase justa, producen y emiten sin
  pérdida de formato; el defecto muere antes, en la selección.
- **La 290 muestra el mismo evento un paso antes:** sin triage, su
  pasada única devolvió silencio (`raw = 0`) en los 8 PRs alcanzables
  — (b)-análoga = 9/9. Conclusión de la adenda: la (a) de C2 y la
  (b)-análoga de C1 son el mismo evento en distinta posición del
  pipeline: **el modelo, mirando el diff real bajo el encuadre de las
  19 clases, no levanta el defecto**.
- **El semáforo ya no predice la selección en diffs reales.** El
  triage de C2 marcó 16/16 en la batería miniatura y 0/9 en los
  alcanzables reales. Consecuencia pre-registrada en la §9: el
  semáforo v2.3 solo podrá afirmar mecánica, economía y emisión —
  **la detección se juzga únicamente en la práctica**.
- **Los caminos B y C quedaron descartados por Alejandro** al elegir
  A: **B** (redefinir la vara al subconjunto alcanzable de ≤9 TP) es
  n = 9 — frágil para cualquier regla de avance y se lee como mover
  el arco; **C** (cambiar de examen por uno de seguridad pura) tira
  la comparabilidad v1→v2.2 y el historial acumulado en el portal.
  Este papel no los reabre.

## 2. Hipótesis de la v2.3 (falsables)

1. **El encuadre (hipótesis central):** lo que ciega la etapa de
   selección no es la estructura de pasadas — dos estructuras opuestas
   (C1 y C2) perdieron en el mismo evento — sino el **encuadre de
   19 clases de seguridad** sobre diffs de revisión general. Un
   revisor cuya selección trabaja sobre las categorías generales del
   propio benchmark, con las 19 clases como especialidad, recupera
   detección grounded sobre el universo completo de 352 TP. Deriva de
   la evidencia: el único diseño que cubrió TP grounded (la v1) lo
   hizo con su componente general, débil y sin pasadas dedicadas, y
   aun así alcanzó R 0,7 %; ningún diseño de solo-clases cubrió uno.
2. **Economía (heredada de C2, ya medida):** conservar la disciplina
   de la v2.2 — selección barata + ≤5 pasadas profundas con
   degradación declarada — mantiene la práctica dentro del tope
   congelado de US$30 y el peor caso por PR bajo el freno de
   US$6,50. El falsador de degradación de la v2.2 no se gatilló en la
   práctica real (0/25): la cuenta cerró dos veces.
3. **La puerta (brazo ALMA):** con el tercer estado
   `needs_validation` (§4), la gobernanza deja de ser invisible en
   las métricas: ALMA retiene todo lo que no puede verificar y
   comercia recall por precisión **por diseño declarado**, de modo
   que su efecto se mide en las métricas globales en vez de perderse
   en el ruido de ≤9 defectos.

## 3. Diseño v2.3 (brazo base)

**Cambia el revisor** (`agent/llm_reviewer_v23.py`, selección
`RB_CONFIG_REVIEWER=v23`; el default del paquete sigue siendo `v1`).
La estructura es la de C2 — selección, profundas, degradación — con
el universo de la selección ensanchado. Por PR, tres etapas:

### (a) Pasada de selección generalizada — solo el diff

- **Una llamada** con el diff únicamente (sin archivos head), como la
  selección de la v2.2. El prompt de sistema lista **dos familias de
  marcas**:
  1. **Categorías generales:** las nueve etiquetas con que el propio
     benchmark clasifica sus hallazgos — correctness, reliability,
     maintainability, testing, security, documentation,
     api-architecture, performance, accessibility — cada una con una
     guidance breve derivada de su nombre público.
  2. **Clases de especialidad:** las 19 de la puerta activa, con la
     guidance de la v2 por clase, **byte-idéntica** (incluidas las
     adendas de disciplina de cita bajo v13), como en la v2.2.
- **Declaración de temario (anti-pesca, vinculante):** la taxonomía
  de categorías sale de la **documentación pública del benchmark** —
  es el temario público del examen, no sus respuestas. Ningún prompt,
  guidance ni regla del revisor v2.3 puede derivarse del **detalle
  por PR** del gold (público o no): el diagnóstico lo usó para contar
  en agregado (343/8/1) y clasificar pérdidas *post-hoc*, y eso es
  todo lo que este diseño hereda de él. Los casos nombrados en el
  diagnóstico (LANdalf incluido) **no reciben ningún tratamiento
  especial** en prompts ni en tests dirigidos: diseñar «para que
  marque LANdalf» sería pesca con otro nombre.
- La salida es un JSON único con las marcas en **orden de prioridad
  global** (la más probable primero, mezclando familias). El revisor
  filtra: descarta marcas fuera de la taxonomía o de las 19 clases
  (contadas), deduplica conservando el primer orden, y aplica el
  **tope duro de 5 marcas totales** (`MAX_DEEP_PASSES`, compartido
  entre familias — la disciplina de peor caso de la v2.2 no se
  relaja). Las marcas válidas excedentes quedan como
  `selection_overflow`. Salida de la selección acotada aparte
  (default 1.024 tokens, env propio como en la v2.2).
- La selección **no produce hallazgos**. Sus marcas quedan asentadas
  por familia en la información de corrida (`selection_general`,
  `selection_specialty`, `selection_overflow`), para que una pérdida
  por no-marcar quede atribuida a la familia correcta.

### (b) Pasadas profundas — una por marca, en orden de prioridad

- **Marca de especialidad → pasada de clase estilo v2:** la misma
  plantilla importada de `llm_reviewer_v2.py`, la misma guidance por
  clase bajo v13 (adendas de cita textuales), el mismo contenido de
  usuario (diff + contenidos head completos, presupuesto de contexto
  de 60.000 tokens estimados, declaración de incluidos/saltados/
  ausentes) y la misma verificación de anclaje de la v2/v2.2.
- **Marca general → pasada general de esa categoría:** la misma
  plantilla y el mismo contexto completo; la guidance es la
  descripción pública de la categoría más la instrucción de reportar
  **solo** defectos de esa categoría, con la **misma disciplina de
  cita exacta y la misma verificación de anclaje**. Nada de pasada
  «libre»: cada profunda responde a exactamente una marca.
- Todo hallazgo llega en el **mismo formato `Candidate`** de siempre,
  con procedencia `alma-llm-reviewer-v23`. El `claim_type` de un
  hallazgo de especialidad es su clase; el de un hallazgo general es
  **su etiqueta de categoría**. Un hallazgo cuya clase/categoría no
  coincide con la marca de su pasada es `malformed`, como en la v2.
- En el brazo base, todos los candidatos verificados por anclaje se
  **emiten** (la puerta se omite al validar, como en v2/v2.1/v2.2).

### (c) Guardia en dos etapas y regla de degradación — la de C2, intacta

Se hereda **sin cambios** la §3(c) del papel v2.2: pre-vuelo 1 sobre
la selección sola (negativa cerrada si su peor caso supera el
freno); pre-vuelo 2 que admite profundas por prioridad mientras
`costo_selección + Σ peor_caso(profundas) ≤ freno`, asentando las
caídas como `degradation` declarado; caso degenerado con pasada mixta
solo-diff restringida a las marcas (con la Adenda 1 de la v2.2: sobre
el diff únicamente, anclaje igual) y, si ni eso cabe, cero hallazgos
**con la declaración asentada** — jamás una negativa muda; y control
acumulativo posterior a cada llamada. Ningún PR se niega entero.

### (d) Paridad de brazos

Ambos brazos corren el **mismo** revisor v2.3 (misma selección,
mismas profundas). La diferencia entre brazos es la gobernanza, y en
la v2.3 incluye la puerta: la config base usa `RB_CONFIG_GATE=v13`
(la 1.3.0 define el universo de clases de la selección; al validar se
omite, como siempre) y la config ALMA usa `RB_CONFIG_GATE=v14` (la
1.4.0 del §4). Es la primera versión donde las configs difieren en
`gate` además de en `governance`, y se declara aquí para que nadie
lo lea como deriva: **la puerta ES la diferencia de gobernanza**.

## 4. Decisión de diseño (brazo ALMA): qué hace la puerta con los hallazgos generales

Bajo el camino A, la mayor parte de la emisión del revisor será
general — y la puerta 1.3.0 solo sabe juzgar sus 19 clases. Qué pasa
con un hallazgo general en el brazo ALMA es por tanto *la* decisión
de diseño de la v2.3. Se trabajaron dos variantes; se pre-registra
**una** y la otra queda asentada como rechazada, con su razón.

### Variante (i) — pasan tal cual: **RECHAZADA**

Los hallazgos generales se emiten en ALMA igual que en base; la
puerta juzga solo la especialidad. Razón del rechazo: **el efecto de
la puerta queda estructuralmente invisible en las métricas
globales**, el mismo pecado de diseño que la linterna original pero
en espejo. La linterna exigía recall a un revisor cuyo universo de
emisión no podía producirlo; la variante (i) exigiría una diferencia
de precisión (la regla heredada pide +0,05) a una puerta que juzga
una fracción del puntaje con ≤9 defectos alcanzables de 352: el ΔP
entre brazos sería ≈0 por construcción o ruido sobre ese puñado, y
la regla de avance se volvería **infalsable en la práctica** —
pasaría o fallaría por azar, no por la gobernanza. Además, (i) deja
sin gobernar exactamente la emisión que el camino A convierte en
mayoría: un brazo «ALMA» que emite sin juicio casi todo lo que dice
no mide la capa de gobernanza, mide al revisor dos veces.

### Variante (ii) — tercer estado `needs_validation`: **PRE-REGISTRADA**

En el brazo ALMA, un hallazgo general **no se emite como hallazgo**:
entra en el tercer estado `needs_validation` de la puerta 1.4.0 y
queda como candidato en el ledger, con blockers. La puerta no tiene
regla de verificación para categorías generales — ese es el blocker,
declarado mecánicamente: `sin_regla_de_verificacion_en_puerta` más el
requisito de confirmación (una pasada de validación medida aparte;
este papel no la define ni la autoriza). Simétricamente, un hallazgo
de especialidad lo juzga la 1.4.0 con la frontera de su propio papel
(aceptado / `needs_validation` por completitud de evidencia /
rechazado).

Fundamentación:

- **El experimento queda honesto:** misma vista (el mismo revisor
  v2.3), distinta gobernanza. ALMA retiene todo lo que no puede
  verificar — la especialidad por sus reglas heredadas, lo general
  por construcción — y **comercia recall por precisión por diseño**,
  declarado antes de correr (§6 deriva la regla de avance de este
  trueque, no a pesar de él).
- **El efecto de la puerta se vuelve medible:** la fracción retenida
  ya no es un puñado de casos sino la mayoría de la emisión, así que
  ΔP y la retención tienen señal en las métricas globales del portal
  en vez de ruido sobre ≤9 defectos.
- **Nada se pierde en silencio:** `needs_validation` no emite ni
  cuenta (regla de puntuación del papel de la 1.4.0, §5), pero vive
  en una sección separada del ledger con sus blockers — auditable
  candidato por candidato, que es lo que permite la contabilidad de
  la §6 (pérdida explicada vs. inexplicada).
- **La extensión se declara como extensión:** el papel de la 1.4.0
  definió el tercer estado para candidatos *de clase* rechazados
  solo por completitud de evidencia. Aplicarlo a hallazgos generales
  es una decisión de **este** papel; no altera la frontera de la
  1.4.0 para candidatos de clase, que se hereda sin retoques.

### Dependencia con la puerta 1.4.0 (declarada, con su compuerta)

La variante (ii) exige la 1.4.0 construida. Su papel fijó el orden:
papel → veredicto de la práctica v2.1 → implementación → semáforo
comparativo → adopción por su criterio. El veredicto de la v2.1 ya
aterrizó (y también el de la v2.2), así que **este papel habilita
explícitamente la implementación de la 1.4.0 para el brazo ALMA de
la v2.3**, en los términos de su propio pre-registro y **sin tocar
las puertas congeladas 1.0.0–1.3.0**. La compuerta es la de su §6,
sin rebajas: la 1.4.0 se usa en la práctica v2.3 **si y solo si** su
medición de adopción da VP recuperados ≥ 1, falsos nuevos = 0,
equivalencia exacta de aceptados con la 1.3.0 en los tres universos
y suite verde. **Si la 1.4.0 no se adopta bajo su propio criterio,
el brazo ALMA de la v2.3 no corre** y este diseño vuelve a papel
(adenda): no hay sustitución silenciosa por la 1.3.0, porque con la
1.3.0 la variante (ii) no existe — la binariedad es exactamente lo
que este diseño deja atrás para lo no verificable.

## 5. Qué NO cambia

- **Las puertas 1.0.0–1.3.0, byte a byte.** POLICY_SHA256 asentados:
  1.0.0 `3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35` ·
  1.1.0 `6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9` ·
  1.2.0 `a768afa46136ba1bf542da65006a946d11cb39e8db73fbd484c3f021b7994211` ·
  1.3.0 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`.
  La 1.4.0, si nace, nace al lado — nunca encima (su papel, §4).
- El modelo (gpt-5.6-sol), el effort (medium), la plataforma, el
  contrato de salida `Candidate` y el pipeline.
- Los frenos: `RB_MAX_SPEND_USD` **US$6,50 por PR** (Adenda 4),
  tope de la práctica **US$30**, tope del semáforo **US$20**.
- La **batería del semáforo**, intacta y congelada
  (`fixtures_semaforo`, manifiesto del 2026-10-20, 32/32 hashes).
- La contabilidad grounded como métrica primaria (la lección de la
  290: un par augmented asentado sin declarar costó una comparación
  entera; todo puntaje que este papel o sus resultados citen declara
  si es grounded o augmented).
- Las prohibiciones anti-pesca, reforzadas por la §3(a): nada de
  ajustar prompts contra el detalle por PR de la práctica **ni del
  gold público**; nada de repetir corridas «hasta que salga»; nada
  de tocar ninguna puerta para mejorar el A/B.

## 6. Regla de avance y linterna — re-derivadas bajo el nuevo diseño

La regla heredada (v2 → v2.1 → v2.2): F1 ALMA ≥ F1 base ·
precisión ALMA ≥ precisión base + 0,05 · caída de recall ≤ 0,03 ·
linterna R_base > 0,7 %. Bajo el camino A con la variante (ii), dos
de sus componentes quedan **inalcanzables por construcción** y
exigirlos sería repetir el pecado de la variante (i) en espejo:

- **F1 ALMA ≥ F1 base:** con R en el orden de 1–3 %, F1 ≈
  2·R·P/(P+R) está dominado por R. ALMA sacrifica recall *por
  diseño* (retiene lo general); para que su F1 igualara al de base,
  la precisión tendría que compensar multiplicando — con R reducido
  a la fracción verificada, eso no depende de la calidad de la
  puerta sino del tamaño del sacrificio declarado. La compuerta
  mediría el diseño, no la gobernanza.
- **Caída de recall ≤ 0,03 (global):** si la base cubre TP sobre
  todo con hallazgos generales (la evidencia de la v1: sus 3 TP
  fueron generales) y ALMA los retiene todos, la caída es el recall
  entero de base — puede exceder 0,03 sin que la puerta haya
  juzgado mal *nada*. La compuerta castigaría el trueque declarado,
  no un error.

**Regla de avance v2.3** (sustituye a la heredada para esta línea;
mismo set privado de 25 PRs, 1 corrida por brazo, la primera que
complete es la válida; métricas del portal, grounded):

1. **Linterna, SIN CAMBIOS:** R_base grounded > **0,7 %**. Ahora sí
   es una prueba del encuadre y no del techo: el universo alcanzable
   es 352 TP, y la v1 ya marcó 0,7 % con una pasada general débil.
2. **Precisión:** P_ALMA ≥ P_base + **0,05** (grounded, portal). Se
   mantiene el componente heredado: es el que la variante (ii) está
   construida para mover. Declaración de techo: si P_base grounded
   resultara ≥ 0,90, este componente se asienta como **no falsable
   por techo** en el resultado — no se ajusta *post-hoc*.
3. **Pureza de la retención** (contabilidad propia desde los outputs
   de ambas corridas contra el gold público, con la metodología del
   diagnóstico, que reprodujo los números del portal de la v1 al
   decimal): de los hallazgos que la base emitió y ALMA retuvo
   (`needs_validation`) o rechazó, **a lo sumo 1 de cada 3 era un TP
   grounded** — la puerta sacrifica ≥2 FP por cada TP que retiene.
4. **Pérdida inexplicada = 0:** todo TP grounded que la base cubrió
   y ALMA no, aparece en el ledger de ALMA como retenido o rechazado
   con su razón. Una pérdida muda — un TP que ALMA no emitió y no
   registró — falsifica la compuerta aunque los demás componentes
   pasen: la gobernanza que no puede explicar sus pérdidas no
   gobierna.
5. **F1 se asienta y se reporta** en ambos brazos, sin ser compuerta,
   por la razón aritmética de arriba.

«ALMA mejora» en la v2.3 significa entonces, declarado de antemano:
la base por fin detecta (linterna) **y** la puerta limpia sin
esconder (precisión +0,05, retención pura, cero pérdidas mudas).

## 7. Cuenta económica esperada (con su base de cálculo)

Precios de planificación del paquete: US$15/M tokens de entrada,
US$75/M de salida; peor caso = entrada estimada por caracteres
(÷3,5) + salida acotada — la fórmula de la guardia, como en v2.2.

- **Pasada profunda (general o de clase):** idéntica cuenta que la
  v2.2 — peor caso ≈ **US$0,95** sobre el PR ancla (41.160 tokens) y
  ≈ **US$1,31** con el contexto saturado a 60.000. La profunda
  general comparte plantilla, contexto y topes de salida con la de
  clase: su peor caso es el mismo por construcción.
- **Pasada de selección generalizada:** la de la v2.2 (≈ US$0,26 de
  peor caso en el ancla) con un prompt de sistema mayor — suma la
  guidance breve de 9 categorías a la de las 19 clases que ya
  estaba. Estimación declarada (a verificar en la construcción en
  seco, no medida): peor caso ≈ **US$0,30–0,35** en el ancla.
- **PR ancla, plan completo:** selección (≈0,35) + 5 profundas
  (5 × 0,95) ≈ **US$5,10** — dentro del freno de US$6,50. Con
  contexto saturado: ≈ US$6,90 → territorio de degradación (corren
  4 profundas, la quinta se declara), igual que en la v2.2.
- **Práctica v2.3 (50 códigos, dos brazos):** costo real esperado
  ≈ **US$10–25**; **tope duro US$30**. Advertencia honesta: las
  pasadas generales pueden producir salidas más pobladas que las de
  clase; la salida acotada (4.096 tokens por llamada) mantiene el
  peor caso, y el costo real se mide en el semáforo y se asienta.
- **Semáforo v2.3 (16 códigos):** esperado ≈ **US$1–3** por analogía
  con v2 (US$2,75) y v2.2 (US$0,62); tope duro **US$20**.
- **Puerta 1.4.0 y su medición de adopción:** determinista y local —
  **US$0** (su papel, §6). Juzgar nunca cuesta.

## 8. Predicción registrada y falsadores

**Predicción (antes de construir, derivada de la evidencia):** la
v1 alcanzó R grounded 0,7 % (3 TP) con una pasada general débil —
sin selección dedicada, sin profundas por categoría, con el grueso
de su prompt ocupado por 8 tipos de reclamo. La v2.3 dedica la
selección y hasta 5 profundas con contexto completo a ese mismo
universo, sobre el mismo modelo. Se predice para la **base v2.3 en
la práctica: R grounded entre 1 % y 3 %** (≈4–10 TP en términos
macro-equivalentes), **P grounded entre 10 % y 40 %** (la emisión
general amplia emite más FP que las 7 emisiones contadas de la v1;
el rango es ancho porque el n es chico y se declara así), F1
grounded ≈ 2–5 %.

**Falsadores (qué nos haría detenernos):**

- **Principal — el encuadre:** R_base grounded ≤ 0,7 % en la
  práctica v2.3 → **muere la hipótesis del encuadre**. Con el
  universo ensanchado y profundas dedicadas, si el recall no supera
  lo que la v1 hizo con una pasada débil, el cuello ya no es qué se
  le pide mirar al modelo: es su **capacidad sobre diffs reales**
  (o el matching del corrector). Se registra el nulo de la línea de
  revisores tal como está planteada; no hay v2.4 de encuadre.
- **Economía (heredado):** degradación declarada en más de 1/4 de
  los PRs de la práctica → la economía tampoco cierra con revisor
  general: registrar y detener.
- **Selección generalizada ciega:** en la práctica, PRs con **cero
  marcas** (ni generales ni de especialidad) en más de 1/4 del set
  → la selección no opera sobre diffs reales ni generalizada: es el
  análogo del (a) masivo de la 295 y se asienta como tal.
- **Puerta:** la 1.4.0 no se adopta según su §6 → el brazo ALMA no
  corre (§4); el resultado de la práctica queda «base sola» y la
  línea vuelve a papel.
- **Semáforo:** cualquier condición ROJA de la §9 → no hay práctica.

## 9. Semáforo v2.3 — qué puede y qué NO puede afirmar

Misma batería congelada, dos brazos (`reviewer=v23`; base
`gate=v13`, ALMA `gate=v14` según §3(d); modelo gpt-5.6-sol, effort
medium), una corrida por brazo, sin ajustar NADA a partir del
resultado. La batería es de defectos plantados **de clase** — y eso
acota su alcance, declarado de antemano:

- **SÍ puede afirmar:** mecánica (selección → profundas → emisión
  sin negativas en los 16 códigos), economía (costo por código,
  ausencia de degradación en miniatura) y **que la vía de
  especialidad sobrevivió al ensanche**: las marcas de clase siguen
  llegando y detectando los plantados, con comparación declarada
  contra v2 (base 8/8 · ALMA 6/8), v2.1 (7/8 · 7/8) y v2.2
  (7/8 · 6/8), incluida la medición de marcas por familia.
- **NO puede afirmar detección general:** la batería no contiene TP
  de categorías generales; un VERDE no predice recall en la
  práctica. La lección está medida dos veces (triage 16/16 en
  miniatura → 0/9 en diffs reales): **la detección de la v2.3 se
  juzga únicamente en la práctica**.
- **ROJO:** algún brazo emite CERO hallazgos sobre los códigos con
  plantados; la guardia se niega en algún código; o la degradación
  se dispara en algún código de la batería (si el freno muerde en
  miniatura, la cuenta de la §7 es falsa).
- **VERDE:** ambos brazos emiten, sin negativas ni degradación → se
  procede a la práctica con el «sí» de Alejandro al lanzar.

## 10. Sonda previa OPCIONAL (separada del semáforo, no lo toca)

Si el corpus público del benchmark ofrece PRs **fuera del set de
práctica de 25**, se puede correr — solo con el «sí» de Alejandro y
clave viva — la **pasada de selección** del revisor v2.3 ya
construido sobre ~10 de esos PRs públicos. Mini-regla registrada:
costo estimado ≈ US$0,30 por PR → **≈ US$3, tope duro US$5**; si la
selección generalizada marca ≥1 categoría en ≥8 de 10 PRs cuyos
defectos públicos conocidos caen en categorías marcadas, la etapa
opera sobre diffs reales y se sigue a la §11; si marca ~0 como la
selección de la 295, **detener antes del semáforo** y registrar —
la sonda falsaría barato lo que la práctica falsaría caro. La sonda
no usa ni modifica la batería congelada, no es un semáforo, y de su
resultado no se ajusta ningún prompt: solo decide seguir o parar.
Si no existe tal conjunto público ajeno al set, esta sección queda
sin efecto y se asienta.

## 11. Secuencia y frenos (en orden, sin saltos)

1. **Este papel → «sí» de Alejandro a ESTE papel.** Nada se
   construye antes de ese sí. (El «A» del 21/10 eligió el camino;
   este papel es el diseño concreto que ese camino exige.)
2. **Construcción en seco (US$0):** `llm_reviewer_v23.py` con mock —
   suite previa verde (163/163) + tests nuevos (la selección marca
   ≤5 totales entre familias y solo esas reciben profunda; marcas
   fuera de taxonomía descartadas y contadas; la guardia suma
   selección + profundas en el orden de la §7; la degradación se
   dispara con freno chico y queda registrada; los `Candidate`
   generales llevan su categoría por `claim_type`; el peor caso de
   la selección generalizada medido en seco contra la estimación de
   la §7) + corrida en seco 16/16 sin negativas con freno US$6,50.
3. **Puerta 1.4.0 (US$0):** implementación según su papel y su
   medición de adopción (§6 de ese papel). Si no se adopta, alto:
   la secuencia vuelve a papel por adenda (§4, §8).
4. **Sonda opcional (§10)** — «sí» + clave; tope US$5.
5. **Semáforo v2.3** — «sí» + clave viva por la vía sancionada;
   esperado US$1–3, tope US$20; veredicto según §9.
6. **Publicación v2.3:** imagen y manifiesto nuevos (procedimiento
   de la v2.2, digest verificado contra GHCR) y configs del portal
   (`reviewer=v23`; base `gate=v13`, ALMA `gate=v14`; el freno del
   portal no se toca).
7. **Práctica v2.3:** «sí» al lanzar; base primero, **linterna**;
   ALMA solo si la linterna pasa; veredicto contra la **regla de
   avance de la §6**. Frenos: US$6,50 por PR, US$30 el total de la
   práctica. Nada de «Submit» (la final) desde este papel.

---

## ADENDA 1 — Reemplazo de la puerta del brazo ALMA: 1.4.0 → 1.4.1 (`gate=v141`)

**Fecha:** 2026-10-21 · **Firma:** Alejandro, el 21/10/2026 a las
21:56 EDT, por el chat («Firmar la adenda (gate=v141)»). Esta adenda
se agrega al final del papel, fechada, **sin alterar ni una línea
del cuerpo original** — las 11 secciones quedan tal como se
congelaron — según el formato de la casa (el papel v2 acumuló 6
adendas así). Es la adenda que la §6 del
`PREREGISTRO-PUERTA-141.md` exigía **antes de cualquier corrida
ALMA**: sin ella, la 1.4.1 — aun adoptada — no se usa en el brazo
ALMA. **Esta adenda no autoriza ninguna corrida**: declara el
reemplazo de puerta y nada más.

### 1. La 1.4.0: construida, medida, NO adoptada

La puerta 1.4.0 (`alma-evidence-gate/1.4.0`) fue construida según su
papel e implementó la variante (ii) pre-registrada en la §4 de este
papel. Su medición de adopción (recibo:
`RESULTADO-MEDICION-PUERTA-140.md`) dio **NO ADOPTADA**: VP
recuperados = 4 (≥ 1 ✓), equivalencia exacta de aceptados con la
1.3.0 en los tres universos (✓), suite 208/208 verde (✓), pero
**falsos nuevos = 1 (≠ 0 ✗)**: en la batería roja, el ataque **S3**
— una inyección SQL real pero preexistente, citada solo en líneas
de contexto, que el PR no introduce — pasó de rechazado a
`needs_validation` por la vía (c) de completitud (su único chequeo
fallido era el (f) «sin línea agregada»). El criterio de su §6 es
conjuntivo y un solo falso bastó. En consecuencia, y tal como este
papel declaró en su §4, **el brazo ALMA de la v2.3 no podía correr
con la 1.4.0**, y no hubo sustitución silenciosa por la 1.3.0. La
1.4.0 queda intacta como artefacto construido y medido; su NO
adopción no se corrigió encima de ella.

### 2. La 1.4.1: pre-registrada, construida en seco, ADOPTADA

La reparación de esa frontera fue papel nuevo, como mandaba el
resultado anterior: `PREREGISTRO-PUERTA-141.md` (cambio único: el
chequeo (f) sale de los chequeos de completitud — un candidato de
clase cuya evidencia citada no contiene ninguna línea agregada por
el cambio es **rechazo firme** en la frontera, dominante sobre
(a)/(b)). Construida en seco con el «sí» de Alejandro del
21/10/2026 21:49 EDT y medida con el instrumento
`medir_adopcion_v141.py` (recibo:
`RESULTADO-MEDICION-PUERTA-141.md`), la 1.4.1 quedó **ADOPTADA**
cumpliendo el criterio conjuntivo entero de su §4: VP recuperados =
**los mismos 4** de la medición de la 1.4.0, identidad por
identidad; **falsos nuevos = 0** en los tres universos, con **S3
rechazado firme como causal (f), sin movimiento**; equivalencia
exacta de aceptados con la 1.3.0 en los tres universos (mapa de
estados idéntico en U2 y U3); **suite 236/236 verde**.

### 3. El reemplazo declarado (anterior a cualquier corrida ALMA)

Conforme a la §6 del papel de la 1.4.1, esta adenda declara
expresamente, antes de cualquier corrida del brazo ALMA:

- La puerta del brazo ALMA de la v2.3 es la
  **`alma-evidence-gate/1.4.1`** (módulo `agent/alma_gate_v141.py`,
  `POLICY_SHA256: 73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46`,
  selector `RB_CONFIG_GATE=v141`).
- La etiqueta de config del brazo ALMA en el portal es
  **`gate=v141`**. Las menciones a `gate=v14` para el brazo ALMA en
  el cuerpo de este papel (§3(d), §9 y §11 paso 6) quedan
  sustituidas por esta declaración. La etiqueta `v14` queda atada
  para siempre al artefacto 1.4.0 tal como fue construido y
  medido: dos puertas distintas no comparten etiqueta.
- La config ALMA llevará entonces `reviewer=v23` (sin cambio) y
  `gate=v141` (en vez de `gate=v14`).

### 4. Todo lo demás del papel queda intacto

Este reemplazo de puerta es el único cambio. Quedan sin tocar: la
**variante (ii)** `needs_validation` de la §4 (ALMA retiene lo
general con sus blockers y la especialidad la juzga la puerta — hoy
la 1.4.1 — con su frontera); la **regla de avance re-derivada de la
§6** (linterna R_base grounded > 0,7 % primero; P_ALMA ≥ P_base +
0,05 con su declaración de techo; pureza de la retención ≤ 1 de
cada 3; **pérdida inexplicada = 0**; F1 reportado, no compuerta);
el **orden base → linterna → ALMA** de la §11; los falsadores de la
§8; y los frenos y topes (US$6,50 por PR, US$30 la práctica, US$20
el semáforo). El semáforo v2.3 ya corrido (VERDE, solo brazo base)
no se reabre ni se reinterpreta por esta adenda.

### 5. Secuencia declarada (qué falta para que el brazo ALMA corra)

Adoptada y declarada no es corriendo. El código v141 **todavía no
está en la imagen publicada**: la imagen v2.3 en curso de
publicación contiene la 1.4.0, no la 1.4.1. Para que el brazo ALMA
corra harán falta, en orden y cada uno con su verificación:

1. **Publicar el código v141 en una imagen verificada** (mismo
   procedimiento de la línea: digest cotejado contra GHCR,
   manifiesto que lo declare).
2. **Editar la config ALMA del portal** con esa imagen y
   `gate=v141` (guardar y releer, como siempre; el freno del portal
   no se toca).
3. Que la **práctica base supere la linterna** (R_base grounded >
   0,7 %, §6 componente 1): solo entonces el brazo ALMA es
   pertinente y se lanza, con el «sí» de Alejandro al lanzar como
   manda la §11.

Si la base no supera la linterna, los pasos 1 y 2 no se ejecutan:
no se publica ni se configura para un brazo que no va a correr.

---

## ADENDA 2 — Reparación del techo de completion de la selección + observabilidad (v2.3.1)

**Fecha:** 2026-10-21 · **Firma:** Alejandro, el 21/10/2026 a las
23:20 EDT, por el chat («Bueno lo hagamos») — aprobación de la
secuencia completa que esta adenda pre-registra: arreglar el techo,
probar el arreglo sobre los casos que murieron, y relanzar la
práctica. Se agrega al final del papel, fechada, **sin alterar ni
una línea del cuerpo original ni de la Adenda 1**, según el formato
de la casa. **Recibos:** `DIAGNOSTICO-PRACTICA-V23-20261021.md`
(causa (d), clasificada y con su falsador) y
`ADJUDICACION-PARCIAL-296-20261021.md` (la señal de detección que
justifica reparar la línea en vez de archivarla).

### 1. El hecho: la nº 296 murió en casa, en la etapa (a)

La práctica base nº 296 (lanzada el 2026-10-21 22:26:40 EDT) cerró
**FAILED «at run-agent (3, 4)»**, sin puntajes: 15 de 25 PRs
completaron (106 findings nunca puntuados) y **20 de 35 intentos
murieron con `error:2`** y el mismo texto terminal: *«selection pass
did not return parseable JSON; failing closed»*. El diagnóstico
clasificó la causa como **(d) — defecto del diseño v2.3 en casos
reales**: la selección generalizada de la §3(a) — la única pieza que
cambió contra la v2.2 — heredó sin cambios el techo de completion
de **1.024 tokens** (`DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS`, idéntico en
v2, v2.1, v2.2 y v2.3); en esta clase de modelo ese techo descuenta
los tokens de razonamiento **y** los de la respuesta visible, así
que en diffs reales el razonamiento lo agota y el contenido vuelve
vacío o truncado a mitad del JSON; `_extract_selection` hace
`json.loads`, falla, y el revisor **cierra en falso por diseño**
(`RealLLMRefused`, exit 2). El paso fino — que el razonamiento agota
el presupuesto — quedó declarado como **inferencia** en el
diagnóstico, porque el código no asienta el cuerpo de la respuesta
ni su `finish_reason` cuando una pasada falla. Descartados con
evidencia: plataforma/infraestructura (éxitos y muertes intercalados
en el mismo contenedor; ningún shard cerca del timeout de 1.800 s,
máximo 1.202 s), fondos (la corrida murió con **US$3,02** positivos;
facturó **US$13,50**) y timeout por volumen (ningún corte es por
timeout). La excepción de relanzamiento de la casa (cortes de
infraestructura declarados) **no aplica** a una causa (d):
relanzar exige arreglo declarado — esta adenda.

La justificación de reparar, y no archivar: la adjudicación parcial
de los 106 findings contra el gold público midió sobre los 15 PRs
completados **precisión grounded 51,9 %** (55/106) y **recall del
subconjunto 22,1 %** (43/195 TP; piso contado sobre el set completo:
43/352 = **12,2 %**), con los **43 TP cubiertos todos por la vía
general** — el diseño detecta en diffs reales muy por encima de la
predicción de la §8 (1–3 %). Declarado en su propio informe y
repetido aquí: esa medición es **parcial**, sobre un subconjunto
auto-seleccionado por supervivencia al defecto, y **no es un
puntaje** ni evalúa la linterna.

### 2. El cambio exacto (dos piezas, nada más)

**(i) Techo de completion de la selección: 1.024 → 4.096 tokens.**
Se mueve el default de la pasada de selección (vía ya existente:
`RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS`). **Solo la selección:** las
pasadas profundas ya operan con su salida acotada a 4.096 (la cuenta
de la §7) y **no se tocan** — ni su techo, ni su plantilla, ni su
contexto, ni su disciplina de cita.

**(ii) Observabilidad de la falla de parseo.** Cuando una respuesta
de la selección no parsee, el revisor asienta en la información de
corrida (`llm_run`) el **`finish_reason`** y un **extracto acotado
del contenido crudo** recibido, antes de cerrar en falso. Sin cambio
de comportamiento: el parseo sigue siendo `json.loads` total, la
falla sigue siendo `RealLLMRefused` (exit 2), y el parseo permisivo
sigue descartado (arreglo (v) del diagnóstico). Lo que cambia es
que ninguna muerte futura de esta etapa se diagnostica por
inferencia: el cuerpo queda a la vista.

La construcción corregida se nombra **v2.3.1** (revisor
`llm-reviewer/2.3.1`). La etiqueta `reviewer` del portal **se
mantiene en `v23`** — lo que cambia es la imagen; la versión 2.3.1
se declara en su manifiesto (§6, paso 4).

**Todo lo demás queda idéntico:** la selección generalizada y su
prompt (28 marcas en una lista de prioridad, tope duro de 5, orden),
las pasadas profundas de la §3(b), la guardia en dos etapas y la
degradación de la §3(c), la puerta base `gate=v13`, el brazo ALMA
con la variante (ii) y la puerta 1.4.1 (`gate=v141`, Adenda 1), la
regla de avance y la linterna de la §6, la batería congelada del
semáforo, el modelo (gpt-5.6-sol) y el effort (medium), y las
prohibiciones anti-pesca de la §5. Ningún prompt se ajusta: el
arreglo nace de la causa medida en agregado, no del detalle por PR
del gold.

### 3. Contabilidad de peor caso re-derivada (precios de planificación de la §7)

El único término que se mueve es la salida acotada de la selección:
1.024 → 4.096 tokens × US$75/Mtok = de US$0,0768 a **US$0,3072** por
llamada — **+US$0,2304 ≈ +US$0,23 por PR**, el delta que el
diagnóstico calculó en su §6.

| Plan | Papel (§7) | Con el techo nuevo | Régimen |
|---|---|---|---|
| Selección sola (PR ancla) | ≈US$0,30–0,35 | ≈US$0,53–0,58 | pre-vuelo 1 holgado contra el freno |
| PR ancla completo (selección + 5 profundas) | ≈US$5,10 | **≈US$5,33** | **entra entero** bajo el freno de US$6,50 |
| PR con contexto saturado (60.000) | ≈US$6,90 | ≈US$7,13 | **la degradación heredada absorbe la diferencia**: corren selección + 4 profundas (≈US$5,82 ≤ US$6,50) y la 5ª se declara |

Declaración: el plan ancla sigue entrando completo y el saturado
entra por la misma regla de degradación de la §3(c) que el papel ya
pre-registró — el +US$0,23 no cambia *qué* plan degrada, solo el
monto. El freno por PR (`RB_MAX_SPEND_USD` = US$6,50) **no se
toca**, ni en el portal ni en el código. Y la salvedad medida por
el diagnóstico (§4): la banda de planificación sobreestima la
factura real en ≥2,4× (caché y/o precios de lista menores) — estas
cuentas son unidades de guardia; la sonda y la práctica se miden
por saldo, como siempre.

### 4. La prueba del arreglo: sonda dirigida sobre los casos que murieron (tope US$8)

Antes de cualquier práctica, y solo tras la construcción en seco
(§6, paso 2), se corre **únicamente la pasada de selección
arreglada** — sin pasadas profundas, sin puerta, sin emisión — en
local, con la credencial por la vía sancionada
(`custom.openai-rbench`), sobre los diffs de los PRs que la nº 296
no pudo leer:

- **Los 5 que murieron 3/3 (obligatorios, en este orden):**
  `simnaut_emdash_2`, `scotthamilton77_agents-config_1`,
  `wirechat_wirechat_183`, `mheuss_chronicle_14`,
  `sdsykes_fastimage_165`.
- **Si el presupuesto lo permite, los 3 intermitentes** (completaron
  tras 1–2 intentos muertos): `PierreJanineh_TechDebtMCP_135`,
  `brianc_node-postgres_3650`, `cmik_apilix_12`.

**Éxito pre-registrado: JSON parseable en TODOS los casos
corridos.** La sonda corre con contabilidad acumulada y **tope
duro de US$8**; si el tope impidiera correr los 5 obligatorios, la
sonda se declara **no ejecutada** (no hay éxito parcial). **Si un
solo caso corrido vuelve no parseable, NO hay práctica:** se vuelve
a diagnóstico en seco — esta vez con el cuerpo y el `finish_reason`
asentados por la pieza (ii), sin inferencia.

**Alcance honesto de la sonda:** prueba que los casos que morían
determinísticamente (3/3 con el techo viejo) ahora parsean; **no
mide una tasa de muertes** — una llamada por caso no la mide. La
tasa se juzga en la práctica relanzada, contra el falsador del §7 de
esta adenda (que adopta el del diagnóstico). De su resultado no se
ajusta ningún prompt, como en la sonda de la §10: decide seguir o
parar. Esta adenda **no autoriza un semáforo nuevo**: el de la §9
ya corrió VERDE para la mecánica de la v2.3, y la sonda es el
chequeo dirigido de la única etapa que cambia.

### 5. Presupuesto de la etapa y compuerta de saldo

Esta adenda **supersede la banda y el tope de la práctica del
cuerpo (§7 y §11: esperado US$10–25, tope duro US$30) solo para
esta etapa de reparación** — del tope viejo ya se consumieron
US$13,50 en la nº 296, y fingir que sigue vigente sería
contabilidad falsa. El presupuesto declarado de la etapa es:

- **Sonda dirigida (§4): ≤ US$8.**
- **Práctica base relanzada: US$15–25.**
- **Brazo ALMA: US$15–25, solo si la linterna pasa** (sin linterna
  no hay ALMA: §6 del papel y Adenda 1).

**Compuerta de saldo (vinculante):** el saldo actual es **US$3,02**
(lectura del billing de la cuenta Personal, 2026-10-21 22:52 EDT).
**Ningún paso con gasto corre sin carga previa de Alejandro y sin
saldo verificado ≥ el costo esperado del paso** (sonda: ≥ US$8;
práctica: ≥ US$25; ALMA: ≥ US$25 y linterna pasada). El freno por
PR (US$6,50) y el tope del semáforo (US$20) quedan como están.

### 6. Secuencia (en orden, sin saltos)

1. **Esta adenda** — firmada por Alejandro («Bueno lo hagamos»,
   2026-10-21).
2. **Construcción en seco v2.3.1 (US$0):** las dos piezas del §2 y
   nada más. Suite completa verde (la heredada de 236 + tests
   nuevos que fijen: el techo de la selección en 4.096, el techo de
   las profundas intacto, y el asentamiento de `finish_reason` +
   extracto ante un parseo fallido) y peor caso de la selección
   re-medido en seco contra la cuenta de la §3.
3. **Sonda dirigida (§4)** — compuerta de saldo cumplida; tope
   US$8; éxito = JSON parseable en todos los casos corridos. Si
   falla: alto, y diagnóstico en seco con el cuerpo a la vista.
4. **Publicación v2.3.1:** imagen corregida por el procedimiento
   de la línea (build desde la UI de GitHub Actions, **digest
   verificado contra GHCR**, manifiesto nuevo que declara la
   v2.3.1 y esta adenda). El commit de la publicación incluye
   además los **documentos locales pendientes**: el paquete 1.4.1
   completo (`agent/alma_gate_v141.py`, `tests/test_gate_v141.py`,
   `medir_adopcion_v141.py`, `RESULTADO-MEDICION-PUERTA-141.md`),
   este papel con la Adenda 2, `DIAGNOSTICO-PRACTICA-V23-20261021.md`,
   `ADJUDICACION-PARCIAL-296-20261021.md` y
   `RESULTADO-PRACTICA-V23-20261021.md`.
5. **Config base del portal a la imagen nueva** — guardar y
   releer, como siempre (`reviewer=v23` se mantiene, `gate=v13`;
   el freno no se toca; la config ALMA no se toca en este paso).
6. **Práctica base relanzada** — compuerta de saldo cumplida. Es
   **una corrida nueva**: no re-califica a la nº 296, que queda
   FAILED. Su puntaje se lee contra la §6.
7. **Linterna** (R_base grounded > 0,7 %, §6 componente 1) sobre
   la corrida relanzada.
8. **Si la linterna pasa:** config ALMA con **la misma imagen
   corregida** y `gate=v141` (cumpliendo la secuencia de la
   Adenda 1, §5) y corrida del brazo ALMA, con el «sí» de
   Alejandro al lanzar; veredicto contra la regla de avance de la
   §6. Si no pasa, se lee el falsador principal de la §8 tal como
   está escrito.

### 7. Falsadores de esta adenda y honestidad

- **La nº 296 queda FAILED para siempre.** Esta adenda no la
  re-califica, no le inventa un puntaje y no pasa su linterna
  retroactivamente: la adjudicación parcial es evidencia para
  decidir la reparación, no un puntaje — la linterna solo se
  evalúa sobre una corrida completa puntuada por la plataforma.
- **La hipótesis del techo, a prueba:** si la práctica relanzada
  muere con la **misma firma** (JSON no parseable en la selección),
  la hipótesis del techo queda **refutada** y la línea **se
  detiene sin tercer intento automático**. Ningún arreglo (iii)
  reintento interno ni (iv) rediseño de la selección corre por
  inercia: cualquier nuevo intento es papel nuevo y decisión nueva
  de Alejandro. Es el falsador que el diagnóstico dejó escrito en
  su §7, adoptado por esta adenda.
- **Si el cuerpo asentado mostrara truncación aun con 4.096**, el
  mecanismo se confirma pero el techo no alcanza: también se
  detiene a papel — no se sube el techo otra vez por inercia.
- **Lo que esta adenda no promete:** que la práctica relanzada
  complete (la sonda acota el riesgo sobre los casos peores
  conocidos; no lo elimina), ni que la linterna pase. La predicción
  de la §8 sigue siendo la del papel; la adjudicación parcial, con
  su sesgo declarado, sugiere que era pesimista. La corrida manda.


---

## ADENDA 3 — Lectura de la colisión linterna/§8: la economía cierra la línea del revisor, no la medición de la puerta

**Fecha:** 2026-10-22 · **Firma:** Alejandro, el 22/10/2026, por el
chat («Adenda de lectura y que corra ALMA»), tras recibir la
adjudicación completa de la nº 298 que él mismo encargó «antes de
decidir». Se agrega al final del papel, fechada, **sin alterar ni
una línea del cuerpo original ni de las Adendas 1–2**, según el
formato de la casa. **Recibos:**
`RESULTADO-PRACTICA-V231-20261022.md` (cierre formal de la nº 298:
SUCCEEDED; costo real US$20,41; falsador de economía registrado
gatillado), `ADENDA-RESULTADO-PRACTICA-V231-20261022.md` (linterna
acreditada por cota inferior) y
`ADJUDICACION-COMPLETA-298-20261022.md` (el par grounded exacto de
la base v2.3.1). **Esta adenda no lanza nada:** resuelve una
colisión entre dos textos pre-registrados de este mismo papel y
declara, antes de cualquier lanzamiento, la corrida que queda
habilitada y cómo se la mide. La corrida ALMA sigue sujeta a su
compuerta de saldo y al «sí» de Alejandro al lanzar, como manda la
§11.

### 1. Los dos hechos, sin maquillaje

**(i) La linterna PASÓ — por conteo completo, no por cota.** La
regla (§6, componente 1, heredada sin cambios por la Adenda 1):
R_base grounded > 0,7 % sobre 352 TP gold, es decir ≥ 3 TP
distintos cubiertos. La nº 298 (base v2.3.1, SUCCEEDED, 25/25 PRs,
166 emisiones) fue adjudicada completa contra el gold público, con
el método de la casa: **66 TP gold distintos cubiertos — recall
grounded 18,75 %**, precisión grounded **53,6 %** (89/166), F1
**27,8 %**. La predicción de la §8 (R 1–3 %, P 10–40 %) quedó por
debajo del resultado en ambas bandas, y el **falsador principal
del §8 — el encuadre — NO se gatilló**. El 100 % del recall vino de
la vía general: la especialidad de 19 clases aportó **0 emisiones
y 0 TP** en la práctica completa (la selección marcó clases en
3/25 PRs; dos las perdieron por degradación y la única pasada de
especialidad ejecutada, `sql_injection` en CrabTrap, no produjo
una sola emisión de su clase).

**(ii) El falsador de economía del §8 quedó GATILLADO en los
hechos, y así queda registrado para siempre.** Su texto:
«degradación declarada en más de 1/4 de los PRs de la práctica →
la economía tampoco cierra con revisor general: registrar y
detener». La nº 298 declaró degradación en **10 de 25 PRs
(40 % > 1/4)**: 9 por `spend_cap` y el caso extremo de **emdash**
por `no_deep_pass_affordable` — las 5 pasadas profundas fuera del
freno, 0 hallazgos emitidos sobre 6 TP gold, un fallo de economía
y no de detección. El cierre formal lo registró gatillado y esta
adenda **no lo des-asienta, no lo borra ni lo reinterpreta
retroactivamente**: el hecho medido (40 %) es el hecho medido,
con su nombre y su texto, para cualquier lector futuro del papel.

### 2. La lectura (por qué los dos hechos no se contradicen)

La colisión es aparente solo si el falsador de economía se lee
como una prohibición genérica de seguir corriendo. Leído con su
propio texto, el falsador tiene **una afirmación y una
consecuencia**, y ambas nombran su objeto:

- **La afirmación:** «la economía **tampoco cierra con revisor
  general**». Es una afirmación sobre la **viabilidad económica
  de la línea del revisor general** — la misma línea cuya
  hipótesis de encuadre juzga el falsador principal, y cuya
  economía la hipótesis 2 de este papel pre-registró («conservar
  la disciplina de la v2.2 mantiene la práctica dentro del tope»).
- **La consecuencia:** «registrar y detener» obliga sobre la
  pretensión que la afirmación nombra: **detener la línea del
  revisor general como empresa viable** — su continuación:
  nuevas iteraciones de base, una v2.4 de encuadre, escalarla.

La evidencia de la nº 298 habla a esa afirmación **en los dos
sentidos, y esta adenda lo declara entero**:

- **A favor del gatillo:** la degradación del 40 % es real y su
  caso extremo es severo — en emdash el freno se comió el plan
  entero y el revisor no emitió nada. Un revisor general que en
  2 de cada 5 PRs no puede ejecutar su propio plan bajo su freno
  no tiene, con estos precios y este freno, una economía que
  «cierre» como línea: cada mejora de cobertura pediría más
  pasadas contra el mismo tope. La afirmación del falsador, sobre
  la continuación de la línea, queda **firme**.
- **En contra de extender el gatillo a todo lo demás:** la
  corrida **completó** 25/25 y su costo real, **US$20,41**, cayó
  **dentro de la banda pre-registrada de la etapa** (US$15–25,
  Adenda 2 §5), con el tope de etapa y el freno por PR intactos —
  la economía de *esta medición* cerró. La degradación no fue una
  falla de operación ni un silencio: es **el mecanismo de
  declaración del propio diseño** (§3(c)) — la 5ª pasada se
  declara caída en el ledger, jamás se esconde — y aun operando
  en el 40 % del set, la corrida produjo **la medición más fuerte
  de la línea** (R 18,75 % contra una predicción de 1–3 %). La
  degradación mide el precio de la cobertura bajo el freno; no
  midió que la corrida no pudiera hacerse ni pagarse.

**FALLO de la lectura:** el falsador de economía del §8 queda
**firme contra la continuación de la línea del revisor**: la base
v2.3.1 queda **CONGELADA como medida** — sin v2.4, sin nuevas
iteraciones de base, sin re-corridas de base bajo este papel — y
**no prohíbe la medición del brazo ALMA**, porque esa medición
responde a **otra pregunta pre-registrada y distinta**: el efecto
de la puerta (la variante (ii) de la §4, la puerta 1.4.1 de la
Adenda 1, la regla de avance de la §6), cuya cadena de
habilitación — Adenda 1 §5 y Adenda 2 §6, paso 8 — estaba
condicionada a una sola cosa: **que la linterna pasara. Pasó.**
La corrida ALMA no continúa la línea del revisor: la usa, una
última vez y tal como está congelada, como instrumento de la
comparación para la que todo este papel existe («cuatro prácticas
sin un solo puntaje válido del brazo ALMA: la comparación que el
sistema existe para medir nunca se midió en el examen real», §1).

**Límite de esta lectura, declarado:** si alguien la leyera como
«el §8 no importa» o «los falsadores se negocian cuando el
resultado gusta», sería **falsa**. El §8 importa exactamente acá:
es el §8 el que cierra la línea del revisor con esta misma
corrida como su último acto de base (§5 de esta adenda), y es el
§8 el que deja asentado, sin rebaja, que su economía no cerró.
Lo que esta lectura niega es solo la extensión del falsador a
una pregunta que su texto no nombra.

### 3. La corrida ALMA que queda habilitada (declaración previa a cualquier lanzamiento)

- **Imagen:** la v2.3.1 ya publicada y verificada —
  `ghcr.io/almaoficial/alma-reviewbench@sha256:144756cea49ee33e8b16ddb0204556adb0f1c2430ea885ec6a206bbaa6964544`
  — la misma de la base nº 298. La imagen ya contiene el revisor
  2.3.1, la puerta 1.4.1 y el selector `gate=v141` (Adenda 1):
  no hay publicación nueva.
- **Config ALMA del portal:** cambian **solo** el campo de
  imagen (a la de arriba) y las etiquetas **`reviewer=v23`** y
  **`gate=v141`**. El resto de la fila queda como ya está —
  `backend=llm · governance=alma · model=gpt-5.6-sol ·
  effort=medium` — y se **verifica campo por campo al editar**
  (guardar y releer, como siempre). **`RB_MAX_SPEND_USD` jamás
  se abre ni se toca**, en esta corrida como en todas.
- **Compuerta de saldo (vinculante, heredada de la Adenda 2
  §5):** saldo verificado en el portal **≥ US$25** antes de
  lanzar. El saldo actual es **US$7,58** (tras la nº 298):
  la corrida **no corre** hasta la carga de Alejandro y su
  verificación en el acto.
- **Economía heredada, declarada de antemano:** costo esperado
  **US$15–25** (la banda de la Adenda 2 §5 para el brazo ALMA) y
  **degradación esperada ≈ 40 %**, asentada aquí como **hecho
  conocido y aceptado antes de correr**, no como sorpresa: el
  brazo ALMA corre el mismo revisor bajo el mismo freno, y su
  degradación esperada es la de la base. Si la corrida ALMA
  excede su banda de costo o muere por causa propia, **se
  registra igual**, con la misma disciplina de cierre que la
  nº 298 — ningún resultado de esta corrida se esconde ni se
  re-corre «hasta que salga».
- **Un solo lanzamiento:** la primera corrida ALMA que complete
  es la válida (§6 del papel). Nada de «Submit» (la final) desde
  esta adenda.

### 4. Cómo se mide el efecto de la puerta (declarado ahora)

El cuerpo de este papel (§6) re-derivó la regla de avance sobre
«métricas del portal, grounded». La nº 298 demostró, con recibos,
que **ese grounded del portal no es acreditable**: el titular de
lista va sin etiqueta Grounded/Augmented, el desglose no aparece
en ninguna vista accesible, y el cotejo aritmético muestra que el
titular es indescomponible como grounded micro (adenda al
resultado de la nº 298, §2–§3). La vara grounded exacta de la base
— la que la regla compara — salió de la **adjudicación local
completa** contra el gold público, no del portal. Para que la
comparación de brazos sea homogénea, esta adenda declara **antes
de correr** el instrumento de medición del brazo ALMA:

1. **La corrida de práctica del portal se corre y se reporta
   entera**, incluido su titular de lista — asentado **como
   augmented**, con la misma salvedad de etiqueta que la nº 298,
   sin acreditarlo como grounded.
2. **Adjudicación local completa (US$0)** de las emisiones del
   brazo ALMA contra el gold público, con **el mismo método** de
   las adjudicaciones de la 296 (parcial) y la 298 (completa):
   mismo archivo + mismo defecto/mecanismo, un TP primario por
   emisión, conteo micro sobre los mismos denominadores (352 TP
   / 213 FP gold; emisiones = las del zip de outputs).
3. **La regla de avance de la §6, variante (ii) según la Adenda
   1, se evalúa sobre los números adjudicados de ambos brazos:**
   - **Precisión:** P_ALMA ≥ P_base + **0,05**, con P_base
     grounded adjudicada = **53,6 %** → **vara: P_ALMA ≥ 58,6 %**.
     (La declaración de techo de la §6 no se dispara: 53,6 % <
     90 %.)
   - **Pureza de la retención:** de los hallazgos que la base
     emitió y ALMA retuvo (`needs_validation`) o rechazó, **a lo
     sumo 1 de cada 3 era un TP grounded** adjudicado.
   - **Pérdida inexplicada = 0:** todo TP grounded que la base
     cubrió y ALMA no, aparece en el ledger de ALMA como retenido
     o rechazado con su razón; una sola pérdida muda falsifica la
     compuerta aunque los demás componentes pasen.
   - **F1 se reporta en ambos brazos; no es compuerta** (la
     razón aritmética de la §6 sigue vigente).
4. **Los conteos de la puerta salen de los run-info de la propia
   corrida ALMA:** aceptados / `needs_validation` / rechazados,
   **por familia** (general vs especialidad), junto con la
   degradación declarada de la corrida y su costo real por
   diferencia de saldo — la contabilidad completa de la retención
   que la §6, componente 3, exige.

Si la adjudicación del brazo ALMA no pudiera ejecutarse por
cualquier causa, el efecto de la puerta queda **sin medir** y así
se asienta: no se sustituye por el titular del portal.

### 5. Cierre de la línea

La corrida ALMA habilitada por esta adenda es **el último acto
del papel v2.3**. Con su resultado — pase o no pase la regla de
avance — **la línea de revisores de este papel se cierra**: la
base v2.3.1 queda como artefacto medido y congelado (P grounded
53,6 % · R 18,75 % · F1 27,8 % adjudicados), el falsador de
economía del §8 queda firme sobre su continuación, y la pregunta
de la puerta queda respondida con el instrumento de la §4 de esta
adenda o asentada como sin medir. **Cualquier continuación —
otra base, otra puerta, otro examen — es un papel nuevo**, con su
pre-registro y su «sí» propios. Nada de este papel se estira por
inercia más allá de esta corrida.

— Adenda 3, 2026-10-22. Textos que la sostienen: §6 (regla de
avance y linterna), §8 (falsadores) y §11 (secuencia) del cuerpo;
Adenda 1 (puerta 1.4.1, variante (ii), secuencia §5); Adenda 2
(§5 presupuesto y compuerta, §6 secuencia paso 8). Recibos:
`RESULTADO-PRACTICA-V231-20261022.md`,
`ADENDA-RESULTADO-PRACTICA-V231-20261022.md`,
`ADJUDICACION-COMPLETA-298-20261022.md`. Gasto de esta adenda:
**US$0** — sin código, sin portal, sin corridas, sin publicar.

## ADENDA 4 — Reparación de la admisión de `gate=v141` en el revisor (v2.3.2) y relanzamiento del brazo ALMA

### 1. Hechos: la nº 310 no midió nada

La práctica del brazo ALMA habilitada por la Adenda 3 se lanzó el
2026-10-22 07:15:27 EDT como corrida nº 310 (config «llm · alma ·
gpt-5.6-sol · medium · v23 · v141», imagen v2.3.1
`sha256:144756cea4…`) y cerró **FAILED «at run-agent (4, 4)»**.
Recibos: **costo real US$0,00** — saldo OpenAI (org Personal)
US$25,58 antes (07:13 EDT) y US$25,58 después (~07:29–07:33 EDT);
**cero llamadas al modelo y cero emisiones** (`findings = null` en
los 4 shards alcanzados, 21 PRs nunca alcanzados; puntajes del
portal «P — · R —», sin titular).

La causa quedó diagnosticada con recibos en
`DIAGNOSTICO-PRACTICA-ALMA-310-20261022.md`: la imagen trae **dos
resolvedores de `RB_CONFIG_GATE` que no se espejan**. El selector
de `agent/main.py` admite `v141` desde la Adenda 1 y de hecho cargó
la puerta 1.4.1 (la cabecera de la corrida declara
`validator=alma-evidence-gate/1.4.1`,
`policy_sha256=73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46`),
pero el resolvedor interno del revisor —
`agent/llm_reviewer_v23.py::_resolve_gate_v23` (líneas 235–259) —
tiene su propia lista de admisión, escrita cuando la puerta más
nueva era la 1.4.0, que termina en `v14` y rechazó `v141`
fail-closed antes de cualquier llamada al modelo, con el error
verbatim: «unknown gate version 'v141'; expected 'v1', 'v11',
'v12', 'v13' or 'v14'». La base nº 298 pasó con la misma imagen
porque corrió con `gate=v13`, valor presente en ambos resolvedores;
la nº 310 es la primera corrida que le presenta `v141` al
resolvedor del revisor.

**Clasificación: falla de admisión/cableado (infraestructura), NO
una medición.** En consecuencia: (i) la regla de avance variante
(ii) de la Adenda 3 §4 quedó **SIN MEDIR, no caída** — no hay
emisiones que adjudicar y la vara no se evalúa ni se sustituye por
titular alguno; (ii) la nº 310 **no cuenta como el acto ALMA del
papel**: el «último acto» de la Adenda 3 §5 sigue pendiente de una
corrida que efectivamente mida.

### 2. Decisión

Alejandro, 2026-10-22 07:37 EDT, sobre el informe de la falla de
la nº 310 (costo US$0,00, causa diagnosticada, decisión pedida):
**«Lo hagamos»**. La decisión autoriza exactamente dos cosas: el
arreglo mínimo declarado en la §3 de esta adenda y **UN
relanzamiento** del brazo ALMA con la imagen reparada. No autoriza
ninguna otra cosa: ni otra base, ni cambios en la puerta, ni un
tercer intento (ver el falsador de la §4).

### 3. El arreglo, declarado antes de correr

Un solo archivo cambia: **`agent/llm_reviewer_v23.py`**.

1. Importación de la identidad de la puerta 1.4.1 junto a las
   existentes (líneas ~116–120), siguiendo su patrón exacto:
   `from .alma_gate_v141 import POLICY_VERSION as GATE_V141_VERSION`.
2. Rama espejo en `_resolve_gate_v23`, después de la de `v14`:
   `if gate_version == "v141": return KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V141_VERSION`.
   Las 19 clases y la guía son las mismas que devuelve `v14`: la
   1.4.1 hereda el conjunto de clases de la 1.3.0 a través de la
   1.4.0; su único cambio es el ruteo interno de la puerta.
3. El mensaje de error de ese resolvedor pasa a listar `'v141'`
   entre los valores esperados (y su docstring se actualiza en el
   mismo sentido).
4. `REVIEWER_VERSION` pasa a `llm-reviewer/2.3.2` (la constante
   vive en ese mismo archivo).
5. Un test nuevo fija la resolución: `_resolve_gate_v23` con
   `v141` devuelve la tupla con `GATE_V141_VERSION`, y `v13`/`v14`
   siguen resolviendo como antes — la combinación revisor-v2.3 ×
   gate-v141 que ninguna prueba cubría.

Lo que NO cambia, declarado: **`agent/alma_gate_v141.py` queda
BYTE-IDÉNTICA** (puerta congelada; su POLICY sigue
`73a403d8…`) y **`agent/main.py` no se toca** (su selector ya era
correcto). Mismos prompts, mismas clases, mismo techo de 4.096: es
completar la tabla de admisión del revisor, no un cambio de
comportamiento de la puerta ni del revisor.

La reparación implica **imagen nueva (digest nuevo)**: el revisor
viaja dentro de la imagen, y del lado del portal no hay nada que
arreglar (inyectó la config pedida y relayó el error fielmente).
En el portal se actualiza **SOLO el campo de imagen** de la config
ALMA; las etiquetas `reviewer=v23` y `gate=v141` ya son las
correctas y no se tocan, y `RB_MAX_SPEND_USD` jamás se toca.

### 4. Compuerta y falsador de la reparación

**Compuerta vinculante:** ningún relanzamiento sin saldo OpenAI
verificado **≥ US$25** en el acto (saldo al 2026-10-22 07:33 EDT:
US$25,58 — la nº 310 no gastó nada).

**FALSADOR de la reparación:** si la corrida relanzada muere con
la misma firma de admisión («unknown gate version 'v141'»), la
reparación queda **refutada** y la línea se detiene **sin tercer
intento**: el efecto de la puerta se asienta como sin medir por
falla de integración y el papel v2.3 se cierra con ese resultado.

### 5. Medición de la relanzada: rige la Adenda 3 §4, entera

Todo lo demás de la Adenda 3 §4 sigue vigente para la relanzada,
sin mover una coma: vara variante (ii) — **P_ALMA grounded ≥
58,6 %**, pureza de retención **≤ 1 de cada 3** retenidos/rechazados
era TP grounded, **pérdida inexplicada = 0** — evaluada sobre
**adjudicación local completa (US$0)** contra el gold con el
método de las adjudicaciones 296/298; el titular del portal se
reporta como **augmented** con su salvedad; conteos de la puerta
(aceptados / `needs_validation` / rechazados, por familia) desde
los run-info; economía heredada declarada (costo esperado
US$15–25, degradación esperada ≈ 40 % como hecho conocido). Y
rige también la §5 de la Adenda 3: **la corrida relanzada ES el
último acto del papel v2.3** — pase o no pase la regla de avance,
la línea se cierra con su resultado y cualquier continuación es
un papel nuevo.

— Adenda 4, 2026-10-22. Textos que la sostienen: Adenda 1 (puerta
1.4.1 y selector `v141`), Adenda 3 (§4 medición y vara, §5 cierre
de la línea) de este papel. Recibos:
`RESULTADO-PRACTICA-ALMA-V231-20261022.md` (la nº 310),
`DIAGNOSTICO-PRACTICA-ALMA-310-20261022.md` (la causa).
Decisión: Alejandro, 2026-10-22 07:37 EDT («Lo hagamos»). Gasto de
esta adenda: **US$0** — sin corridas; el arreglo en seco y la
publicación se asientan en `RESULTADO-ARREGLO-V232-20261022.md` y
en el REGISTRO.
