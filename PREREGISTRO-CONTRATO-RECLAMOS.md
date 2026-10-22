# Pre-registro — Contrato de reclamos: la forma en que un hallazgo debe nacer para ser verificable

**Fecha:** 2026-10-22 · **Autorización:** Alejandro, 22/10/2026
(toque en widget + «Dale, diseñá el contrato de reclamos
(US$0)»). **Costo: US$0** — solo archivos locales; sin llamadas
a modelos, sin portal, sin publicación. **Orden obligatorio de
este papel: este documento se escribe ANTES que el código**
(`agent/claim_contract.py`), y la vara de la §5 queda declarada
antes de construir.

## 1. El antecedente medido (por qué existe este papel)

La puerta 1.5.0 (`PREREGISTRO-PUERTA-150.md`) definió la regla
de verificación que la 1.4.1 no tenía para la vía general, y su
replay (`RESULTADO-REPLAY-150-20261022.md`) dio **NO PASA**:
emite por primera vez (32 emisiones, 19 TP, precisión 59,4 %),
pero la sala de espera se llevó 133/166 (80,1 %) contra una
vara de < 50 %. Los dos blockers dominantes de esa sala son
propiedades de **cómo nacen los reclamos**, no de la puerta:

- `sin_patron_concreto_en_el_reclamo` — **71**: el mensaje no
  afirma ningún token de código contrastable con su cita.
- `tokens_afirmados_ausentes_en_la_evidencia` — **62**: el
  reclamo afirma tokens que sus propias líneas citadas no
  contienen.

La puerta juzga reclamos ya nacidos; ningún rediseño de la
puerta cambia cómo se escriben. Este papel ataca el otro
extremo del tubo: **el contrato que un hallazgo debe cumplir
al nacer** para que una puerta determinista pueda verificarlo,
más un **normalizador determinista** que lleva un reclamo
nacido sin contrato a la forma de contrato **cuando eso es
posible sin inventar evidencia** — y declara no-conforme al
que no puede, sin taparlo. La no-conformidad es señal sobre el
revisor, no un defecto a esconder.

## 2. El contrato (diseño)

Un hallazgo está **en forma de contrato** cuando cumple las
cinco condiciones siguientes. Las condiciones C1–C3 son las
que la puerta 1.5.0 ya sabe contrastar (su regla (G4)/(G1)/
(G2)); el contrato las declara del lado del productor, antes
de que el reclamo exista como salida.

- **C1 — Patrón concreto declarado.** El mensaje afirma un
  patrón concreto: un conjunto no vacío de tokens de código
  citados entre backticks en el propio mensaje (la forma
  exacta que la regla (G4) de la 1.5.0 lee). Un token de
  código es el de la normalización ya declarada en el papel
  150: sin punto inicial, sin `()` final vacío, sin espacios
  internos, longitud ≥ 2.
- **C2 — Todo token afirmado está en la evidencia citada.**
  Cada token del patrón aparece (búsqueda de subcadena) en
  las líneas de evidencia que el propio reclamo cita
  (`evidence_text`, el extracto del head para el rango
  citado). Un reclamo que afirma lo que su cita no contiene
  nació roto: no es verificable ni por su propio autor.
- **C3 — Cita resoluble.** El rango citado cubre exactamente
  las líneas de evidencia almacenadas y se resuelve contra
  el archivo head y/o los hunks del diff (lo que la 1.5.0
  contrasta en (G1)/(G2)). La cita no se ensancha ni se
  recorta para «ayudar»: es la que el reclamo trae al nacer.
- **C4 — Tipo declarado.** El reclamo es de una de las 19
  clases (su contrato es el dialecto de clase de la 1.4.1,
  sin cambios) **o** de una categoría general **con** patrón
  concreto (C1). Una categoría general sin patrón no es
  forma de contrato: es prosa sobre código.
- **C5 — La no-conformidad nunca es rechazo por formato.**
  Un reclamo no conforme no se rechaza en firme en la etapa
  de contrato: queda en `needs_validation` con su código de
  razón específico (§3). El rechazo firme sigue reservado a
  lo afirmativamente falso, y eso lo decide la puerta, no
  el contrato.

**La sección del productor (diseño, NO construcción).** En
una versión futura, el revisor emitiría reclamos nativos del
contrato con tres cambios de formato/prompt, declarados acá a
nivel de diseño y **no implementados en esta tarea**:

1. **El patrón se declara al nacer, copiado de la cita.** El
   prompt/formato de salida exige que cada hallazgo cite
   entre backticks los tokens del patrón que afirma, y que
   esos tokens se copien de las líneas que el propio
   hallazgo cita (nunca de memoria del modelo): la plantilla
   de emisión lleva el campo «patrón» junto al campo
   «evidencia», y un hallazgo sin patrón no se emite como
   verificado — nace ya marcado como no verificable.
2. **La cita es el rango mínimo que contiene el patrón.** El
   revisor cita el rango cuyas líneas contienen los tokens
   que afirma (hoy cita rangos de función, mediana 4 líneas,
   máximo 17 — medido en la autopsia); el contrato pide que
   el rango y el patrón se elijan juntos.
3. **Lo que no se puede citar, no se afirma.** Si ningún
   patrón concreto puede copiarse de las líneas citadas, el
   hallazgo futuro nace con la declaración de no-conformidad
   puesta por su propio productor (la sala de espera deja de
   ser un destino descubierto por la puerta y pasa a ser un
   estado declarado en origen).

## 3. El normalizador determinista (diseño)

Módulo nuevo `agent/claim_contract.py`. Toma un candidato tal
como nació y produce **(a)** el candidato en forma de
contrato, o **(b)** la declaración de no-conformidad con su
código de razón específico. Determinista, sin modelos, y con
una única fuente de verdad para «token»: la tokenización de
la propia puerta 1.5.0 (mismo extractor de backticks, misma
normalización), importada sin modificarla.

- **Caso A — el reclamo ya declara patrón (≥ 1 token entre
  backticks).** Si **todos** sus tokens afirmados están en su
  evidencia citada → **conforme tal como nació** (el
  normalizador es la identidad: no agrega ni quita una
  letra). Si **alguno** está ausente → **NO conforme**,
  código `tokens_afirmados_ausentes_en_la_evidencia`, con la
  lista de ausentes. **El normalizador no recorta el patrón
  para rescatarlo**: un reclamo que afirma lo que su cita no
  contiene es exactamente la señal que la vara (5) protege;
  recortarlo la taparía. Tampoco lo rescata minando la prosa:
  el patrón declarado por el reclamo es su afirmación, y
  sustituirla por otra sería reescribir el reclamo.
- **Caso B — el reclamo no declara ningún token (la
  población `sin_patron_concreto`).** El normalizador mina
  la prosa del mensaje — solo el texto **fuera** de los
  spans entre backticks — buscando tokens con **forma de
  código** de esta lista cerrada: (i) cadena con `_` entre
  alfanuméricos (`snake_case`, dunders); (ii) cadena con
  `.` entre partes identificador (ruta punteada); (iii)
  `camelCase`/`PascalCase` (transición minúscula→mayúscula);
  (iv) forma de llamada: identificador seguido inmediatamente
  de `(` en la prosa; (v) sigla en mayúsculas de longitud
  ≥ 3; (vi) literal entre comillas simples o dobles cuyo
  contenido no tenga espacios. Un token minado se afirma
  solo si cumple **las tres**: tiene forma de código en la
  prosa del propio reclamo, **no está gobernado por una
  marca de ausencia** (la lista cerrada de la regla (G3)
  de la 1.5.0; un tipo de token que aparece gobernado por
  ausencia en cualquier ocurrencia se salta entero — el
  normalizador no afirma como presente lo que el reclamo
  declara ausente), y **aparece verbatim (subcadena) en las
  líneas de evidencia citadas**. La forma normalizada del
  mensaje = el mensaje original con cada ocurrencia no
  gobernada de cada token minado envuelta en backticks (y,
  para literales entre comillas, las comillas de prosa
  reemplazadas por los backticks): **no se agrega, quita ni
  reordena una sola palabra**; archivo, rango, tipo y
  evidencia quedan byte-idénticos a los nacidos. Con ≥ 1
  token minado → **conforme por minado**, con el patrón =
  los tokens minados en orden de primera aparición. Con 0 →
  **NO conforme**, código `sin_patron_concreto_en_el_reclamo`.
- **Caso C — reclamos de las 19 clases.** Pasan intactos:
  su contrato es el dialecto de clase de la 1.4.1 y el
  normalizador no los reescribe (conformidad por
  construcción del etiquetado; el corpus A no contiene
  ninguno — declarado en la autopsia — y el camino de clase
  se mide por la delegación de la puerta, no acá).

**Integridad (la cláusula que manda sobre todo lo demás):**
la normalización solo extrae y reformatea lo que el reclamo
y sus líneas citadas ya contienen. Ningún token se afirma si
no ocurre en el texto del reclamo **y** en su evidencia;
ninguna línea de evidencia se agrega, quita o altera;
ninguna cita se mueve. Todo reclamo cuyos tokens afirmados
no existan en su evidencia queda NO conforme y contado como
tal: esa no-conformidad es señal sobre el revisor, no un
defecto a tapar.

## 4. Semántica del pipeline compuesto (declarada)

La medición corre el pipeline **normalizador → puerta 1.5.0
sin modificar**, sobre el corpus A, con el replay idéntico a
los anteriores (misma reconstrucción de candidatos con la
fórmula del revisor, mismos diffs regenerados, ledger
prendido):

- Solo los candidatos **conformes** (tal como nacieron o por
  minado) entran a la puerta, por PR y en su orden original.
- Los **no conformes** no entran a la puerta disfrazados: se
  quedan en la etapa de contrato con su código de razón, y
  cuentan dentro de la fracción `needs_validation` del
  pipeline (la sala de espera compuesta = retenidos del
  contrato + retenidos de la puerta).
- Los rechazos firmes solo pueden venir de la puerta. La
  etapa de contrato nunca rechaza (C5).
- «Emitido» = aceptado por la puerta entre los conformes
  (emisión estricta, la misma lectura de los papeles
  anteriores).

## 5. La vara (declarada antes de construir, sin cambios)

Corpus A = los 166 hallazgos de la base nº 298 con
`adjwork298/decisions.json`; pipeline = normalizador →
puerta 1.5.0 SIN MODIFICAR, replay idéntico a los anteriores:

1. **Conformidad:** cuántos de los 166 quedan conformes al
   contrato tras la normalización determinista, y cuántos de
   los 133 que la 1.5.0 dejó en espera salen de la espera por
   esa vía (reportar ambos conteos crudos y por blocker
   original).
2. **Fracción en `needs_validation` del pipeline compuesto
   < 50 %** de los candidatos (la vara que la 1.5.0 sola no
   pasó: 80,1 %).
3. **Precisión entre emitidos del pipeline ≥ 53,6 %** y
   **TP emitidos > 19** (el número de la 1.5.0 sola), con
   recall de TP gold distintos reportado.
4. **Discriminación reportada:** tasa de muerte de los 8 FP
   gold-confirmados vs la de los 89 TP, sin umbral inventado.
5. **Integridad: cero evidencia inventada** — la
   normalización solo extrae y reformatea lo que el reclamo
   y sus líneas citadas ya contienen; todo reclamo cuyos
   tokens afirmados no existan en su evidencia queda NO
   conforme y contado como tal.

Definiciones operativas (declaradas con la vara): «salen de
la espera» en (1) = retenidos por la 1.5.0 sola **y** emitidos
por el pipeline compuesto; «tasa de muerte» en (4) = fracción
no emitida dentro de cada conjunto gold; los componentes (2)
y (3) son los umbrales de la vara, (1) y (4) se reportan sin
umbral, y (5) es condición de validez de la medición misma
(si se violara, la medición no vale, no un componente más).
**Si el pipeline no pasa la vara, NO PASA y se asienta así:
prohibido ajustar la vara, el contrato o el normalizador
después de ver el número y remediar en esta misma tarea;
cualquier ajuste es una iteración posterior declarada.**

## 6. Qué NO cambia

- Las puertas 1.0.0–1.4.1 quedan **byte-idénticas**
  (congeladas) y la **1.5.0 no se modifica**: el pipeline la
  consume tal cual; al cierre se verifican y reportan los
  hashes de archivo de las siete.
- El revisor **no se reconstruye**: la sección del productor
  de la §2 es diseño en papel; ningún prompt ni formato de
  emisión cambia en esta tarea.
- Ningún montaje, ninguna corrida, ninguna adopción se
  decide acá: el contrato y su normalizador se miden en seco
  contra la §5 y el resultado se asienta tal cual salga.
- La medición vale para el corpus A (producción del revisor
  2.3.1 en la práctica nº 298) y no afirma nada sobre otra
  corrida ni otro examen.

— Pre-registro del contrato de reclamos, 2026-10-22. Insumos:
`REPLAY-PUERTA-141-20261022.md`, `PREREGISTRO-PUERTA-150.md`,
`RESULTADO-REPLAY-150-20261022.md`. Gasto: **US$0**.
