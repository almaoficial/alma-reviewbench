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
