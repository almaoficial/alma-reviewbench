# Pre-registro — Puerta 1.4.0: el tercer estado `needs_validation`

**Fecha:** 2026-10-21 · **Aprobación:** Alejandro, 21/10/2026 17:43 EDT
(«Ok» a la recomendación de escribir este papel ahora).
**Estado:** CONGELADO al escribirse. **Este documento es SOLO PAPEL: no
existe código de la 1.4.0, y escribirlo no autoriza implementarla.**
Toda corrección posterior es una adenda fechada, nunca una edición
silenciosa.
**Antecede:** `PREREGISTRO-REVIEWBENCH-V2.md` (congelado 2026-10-19,
Adendas 1–6), `PREREGISTRO-REVIEWBENCH-V21.md` (congelado 2026-10-21),
`RESULTADO-SEMAFORO-20261021.md` (semáforo v2: VERDE),
`RESULTADO-SEMAFORO-V21-20261021.md` (semáforo v2.1: VERDE) y el
`informe-003-cloudflare-security-audit.md` de El Probador (2026-10-21),
de donde sale la pieza que este papel importa.

## 1. El antecedente medido (por qué existe este papel)

- La puerta 1.3.0 es **binaria**: acepta o rechaza, y lo rechazado
  desaparece. Su costo ya está medido dos veces, sobre la misma batería
  congelada y con dos revisores distintos:
  - Semáforo v2 (revisor v2): base 8/8 plantados, ALMA 6/8. Uno de los
    dos misses de ALMA es la puerta: en **sem_01** el revisor propuso
    el sql_injection verdadero y la 1.3.0 lo rechazó — «a SQL skeleton
    and an unsafe construction marker must co-occur on the same cited
    line»: esqueleto y construcción existían en el código, pero no
    reunidos en la misma línea citada.
  - Semáforo v2.1 (revisor v2.1): base 7/8, ALMA 7/8 — y el único miss
    de ALMA es **sem_01 otra vez, con la misma razón textual**. En el
    brazo base, sin puerta, el mismo caso se emitió y detectó en ambas
    corridas.
  Es decir: hay ≥1 verdadero positivo medido, repetido, que el sistema
  *ve* y la binariedad de la puerta *pierde* — no por falso, sino por
  evidencia citada incompleta.
- El Probador 003 (2026-10-21) encontró la pieza que falta en un
  sistema publicado por Cloudflare (`security-audit`): un **tercer
  estado**, `needs_validation`, para el candidato no verificable — el
  schema lo impone por construcción: ese estado **no puede llevar
  `severity`** y debe declarar **`blockers`** (el hecho exacto sin
  resolver) y un **`validation_plan`**. Lo confirmado, en cambio,
  exige traza y evidencia. La puerta de ALMA caza claims sin evidencia
  en la *forma*; hoy su única respuesta a la forma incompleta es el
  rechazo seco.
- **Declaración de timing:** este papel se escribe **antes** de que la
  práctica v2.1 tenga veredicto, a propósito. El diseño del tercer
  estado no puede quedar contaminado por esa nota: si se escribiera
  después, cualquier frontera del estado podría sospecharse ajustada
  al resultado.

## 2. Hipótesis (falsables)

1. **Recuperación:** sobre la batería congelada del semáforo, ≥1
   verdadero positivo que la 1.3.0 rechaza *solo* por evidencia
   incompleta cae en `needs_validation` bajo la 1.4.0 en vez de
   perderse (el caso sem_01 es el candidato conocido; la hipótesis no
   depende de que sea él).
2. **Cero falsos:** ningún candidato que no sea un defecto real (la
   batería roja de la 1.3.0, los adversarios de la suite, los
   candidatos no plantados del semáforo) cambia de rechazado a
   `needs_validation` o aceptado. El tercer estado no es una sala de
   espera para ataques.
3. **Equivalencia de emisión:** con los mismos candidatos, el conjunto
   aceptado de la 1.4.0 es idéntico al de la 1.3.0 en toda batería. El
   tercer estado no emite: la puntuación en el portal no se entera
   (ver §5).

## 3. Diseño del tercer estado

**Veredictos de la 1.4.0:** `accepted` / `needs_validation` /
`rejected`. La 1.4.0 heredará las 19 clases y los chequeos de la 1.3.0
por delegación, como la 1.3.0 heredó los de la 1.2.0, en un módulo
nuevo (`agent/alma_gate_v14.py`, selección futura `RB_CONFIG_GATE=v14`;
el default del paquete no cambia). `POLICY_VERSION`:
`alma-evidence-gate/1.4.0`; su POLICY_SHA256 se asienta en la adenda de
construcción, si alguna vez se construye.

**La frontera (debe ser mecánica, como todo lo de la puerta):** un
candidato que la 1.3.0 rechaza pasa a `needs_validation` **si y solo
si** cumple las cinco condiciones siguientes, todas verificables sin
opinar:

1. La clase es una de las 19 conocidas. (Clase desconocida →
   `rejected`, como hoy.)
2. El candidato está bien formado. (Malformado → `rejected`.)
3. La cita **ancla**: el texto citado coincide con el archivo head,
   byte a byte a nivel de línea, igual que exige hoy la verificación
   de anclaje. (Cita falsa o no anclada → `rejected`: fabricar
   evidencia no es «evidencia insuficiente», es evidencia falsa.)
4. **Nada refuta el claim** en la evidencia ni en el bloque: ningún
   antídoto presente (la forma segura de la clase: SafeLoader,
   defusedxml, `with`/`.close()`, `raise`, etc.). Si el antídoto está,
   la evidencia *desmiente* el claim → `rejected`, como hoy.
5. La **marca primaria de la clase está presente** en la evidencia
   citada, y los únicos chequeos que fallan son de **completitud de
   evidencia**: (a) co-ocurrencia — marca y construcción presentes en
   la cita pero no reunidas como la regla exige (el caso sem_01:
   esqueleto SQL y construcción insegura en líneas citadas distintas);
   (b) construcción fuera del span citado — la marca está y la
   construcción no entra en el rango citado; (c) la cita no contiene
   una línea agregada por el cambio (regla de la Adenda 2(f) del papel
   v2). Si ni la marca está, no hay nada que validar → `rejected`.

Todo candidato que no cumpla las cinco queda exactamente donde la
1.3.0 lo dejaba. Los conjuntos resultan así: aceptados(1.4.0) =
aceptados(1.3.0); rechazados(1.4.0) ⊆ rechazados(1.3.0); la diferencia
es, por definición, el conjunto `needs_validation`.

**El registro `needs_validation`** (espejo del schema de Cloudflare,
impuesto por construcción, no por convención):

- El tipo de registro **no define el campo `severity`**: no es que se
  deje vacío — no existe. Un `needs_validation` con severidad es un
  error de schema, no un hallazgo tibio.
- Lleva: `claim_type`, archivo y líneas citadas, la evidencia tal como
  fue citada, el id del productor del candidato (el revisor) y el
  POLICY id de la puerta que lo juzgó.
- Lleva los **blockers**: la lista exacta de los chequeos de
  completitud que fallaron, con las razones textuales de la propia
  puerta (ej.: la frase de co-ocurrencia de sem_01).
- Lleva el **requisito de confirmación** por blocker: qué evidencia lo
  cerraría, en términos mecánicos («una cita donde esqueleto y
  construcción co-ocurran según la regla de la clase»; «el bloque
  completo del archivo, para verificar ausencia de antídoto y línea
  agregada»).
- Los registros viven en una **sección separada del ledger**, jamás en
  el archivo de hallazgos emitidos — el equivalente al
  `NEEDS-VALIDATION.md` de Cloudflare: que nunca se lea como hallazgo
  algo que la propia puerta declaró no verificado.
- Determinismo: mismo candidato + mismo head → mismo veredicto, bit a
  bit, como en todas las puertas de la línea.

## 4. Qué NO cambia

- **Las puertas 1.0.0–1.3.0, byte a byte, para siempre** (POLICY_SHA256
  asentados en el papel v2.1 §3; la 1.3.0:
  `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`).
  La 1.4.0, si nace, nace al lado — nunca encima.
- **Las 19 clases** y cada regla de evidencia de la 1.3.0, heredadas
  sin retoques. Ninguna clase nueva entra por este papel.
- **La disciplina de cita y la verificación de anclaje**, idénticas.
- **El productor de candidatos:** el revisor v2.1 (una pasada, 19
  clases en secciones), mismo modelo (gpt-5.6-sol) y effort (medium).
  Ningún ajuste de prompts se autoriza desde este papel.
- **Los frenos y topes:** `RB_MAX_SPEND_USD` 6,50 por PR (Adenda 4),
  tope de la práctica US$30, tope del semáforo US$20. La puerta es
  determinista y local: juzgar con ella cuesta US$0.
- **La regla de avance y la prueba de la linterna** del papel v2,
  para cualquier uso futuro en el portal.
- **Las prohibiciones anti-pesca:** nada de afinar la frontera del §3
  contra el detalle por PR de ninguna práctica, ni contra el set
  dorado (privado, nunca visto).

## 5. Regla de puntuación en ReviewBench (ninguna ventaja no medida)

- **`needs_validation` NO cuenta como hallazgo emitido.** No entra al
  numerador de recall ni al denominador de precisión. Dado el §3
  (aceptados idénticos), correr la práctica o la final con la 1.4.0
  produce **exactamente el mismo puntaje** que con la 1.3.0, candidato
  a candidato. El portal no puede distinguirlas; esa es la garantía,
  no una promesa.
- **La pasada de validación (definida aquí, inactiva hasta medirse):**
  el único camino por el que un `needs_validation` puede llegar a
  emitido es una pasada posterior que complete la evidencia que falta
  y vuelva a someter el candidato a **todos** los chequeos de la
  puerta. Como queda definida en este papel, esa pasada es
  **determinista y sin llamadas a modelo**: para cada blocker, reúne
  mecánicamente la evidencia requerida desde el archivo head (la cita
  ampliada al bloque que contiene las líneas citadas, buscando la
  co-ocurrencia y la línea agregada, y verificando antídoto sobre el
  bloque completo). Tres salidas posibles: la evidencia completada
  pasa todos los chequeos → `accepted` (recién ahí emite); la
  evidencia completada refuta (antídoto) → `rejected`; sigue
  incompleta → permanece `needs_validation` y no cuenta.
- **La pasada no puntúa hasta medirse aparte:** aunque se implemente,
  su efecto sobre precisión/recall queda **apagado** en cualquier
  corrida del portal hasta que exista una medición comparativa propia,
  pre-registrada por adenda a este papel, que demuestre sobre las
  baterías del §6 que sus aceptados son verdaderos (criterio: 0 falsos
  aceptados por la pasada; cualquier falso la deja apagada). Una
  validación con modelo (un agente que re-lea y opine) **no** está
  definida ni autorizada por este papel: sería papel nuevo.

## 6. La medición futura (pre-registrada aquí)

**Pregunta:** ¿cuántos verdaderos positivos recupera el tercer estado
sin dejar pasar ningún falso?

**Universos** (todos congelados o ya corridos; juzgar con la puerta es
local y cuesta US$0):

1. **La batería del semáforo** (`fixtures_semaforo`, manifiesto del
   2026-10-20, 32/32 hashes): los candidatos ya producidos por el
   revisor v2.1 en la corrida asentada (salidas en
   `runs/semaforo-v21-20261021/`), re-juzgados offline por la 1.4.0
   contra los de la 1.3.0. La verdad de terreno es el manifiesto de la
   batería (los defectos plantados). Muestra secundaria, mismo
   procedimiento: los candidatos de la corrida v2
   (`runs/semaforo-intento3/`).
2. **La batería roja de la 1.3.0** (69 ataques del equipo rojo
   extendido, asentados en la Adenda 3 del papel v2): todo ataque debe
   quedar donde la 1.3.0 lo dejó — incluidos los residuales
   declarados C3 y X2 (aceptados con límite declarado: la equivalencia
   de la hipótesis 3 los mantiene ahí).
3. **La suite completa vigente** (149/149 al escribirse este papel):
   equivalencia de veredictos aceptado/rechazado sobre todos los
   fixtures legítimos y adversarios.

**Definiciones de conteo (cerradas ahora):**

- **VP recuperado:** un candidato cuyo defecto es real según la
  verdad de terreno del universo 1, que la 1.3.0 rechazó y la 1.4.0
  ubica en `needs_validation` cumpliendo la frontera del §3.
- **Falso nuevo:** cualquier candidato que NO es un defecto real y que
  la 1.4.0 ubica en `needs_validation` o `accepted` habiendo sido
  rechazado por la 1.3.0 (en el universo 2: cualquier ataque que se
  mueva de estado; en el 3: cualquier adversario que se mueva).
- **Equivalencia:** aceptados(1.4.0) = aceptados(1.3.0), exacto, en
  los tres universos.

**Criterio de adopción (escrito antes de medir):** la 1.4.0 se adopta
**si y solo si** VP recuperados ≥ 1 **y** falsos nuevos = 0 **y**
equivalencia exacta en los tres universos **y** la suite previa sigue
verde con los tests nuevos del tercer estado en verde. Si VP
recuperados = 0, no se adopta: un tercer estado que no recupera nada
es decoración. Si falsos nuevos ≥ 1, no se adopta: la sala de espera
filtra. No hay adopción parcial ni re-afinación de la frontera contra
estas baterías después de ver el resultado — cualquier cambio de
frontera es papel nuevo y medición nueva.

**Costo de la medición:** US$0 en su forma offline. Si hiciera falta
un semáforo comparativo fresco con modelos reales (mismos 8 códigos,
mismo revisor, puerta v13 contra v14), hereda el tope duro de US$20 y
requiere el «sí» de Alejandro en ese momento, como todo gasto. Este
papel no autoriza ningún gasto.

## 7. Orden de ejecución futuro (compuertas, en orden)

1. **Este papel** — escrito antes del veredicto de la práctica v2.1, a
   propósito (ver §1).
2. **El veredicto de la práctica v2.1 aterriza.** Nada de lo que sigue
   empieza antes: la 1.4.0 no compite por atención con la medición en
   curso ni se contamina de ella.
3. **Implementación:** módulo nuevo, puertas anteriores intactas,
   adenda de construcción a este papel con el POLICY_SHA256, suite
   previa verde + tests nuevos por categoría de la frontera (aceptación
   equivalente; rechazo firme por clase desconocida, malformado,
   anclaje falso, antídoto o marca ausente; `needs_validation` por
   cada chequeo de completitud).
4. **Semáforo comparativo 1.3.0 vs 1.4.0** según el §6.
5. **Decisión de adopción** según el criterio del §6. Recién ahí, uso
   en el portal — y aun adoptada, su puntuación es la de la 1.3.0
   hasta que la pasada de validación se mida (§5).

## 8. Falsadores (qué mata a la 1.4.0)

- La frontera del §3 no se puede implementar sin una sola decisión de
  juicio (algo «parece» construcción, algo «probablemente» es
  antídoto) → muere en el papel: la puerta no opina.
- VP recuperados = 0 en la medición del §6 → no se adopta.
- Falsos nuevos ≥ 1 → no se adopta.
- Aceptados(1.4.0) ≠ aceptados(1.3.0) en cualquier universo → no se
  adopta: la neutralidad de puntaje era la garantía central.
- Que alguien proponga puntuar un `needs_validation` en el portal
  antes de que la pasada de validación esté medida según el §5 →
  fuera de papel; si ocurriera, se asienta como desvío, no como
  interpretación.
