# Pre-registro — Revisor con reclamos nativos del contrato: la capa de formación al nacer

**Fecha:** 2026-10-22 · **Autorización:** Alejandro, 22/10/2026
(«Lo hagamos») tras el cierre de la cadena gratis (autopsia de
la 1.4.1 → puerta 1.5.0 → contrato de reclamos). **Costo de
este papel y de la construcción que pre-registra: US$0** —
diseño y construcción en seco, replay local; sin llamadas a
modelos, sin portal, sin publicación. **Orden obligatorio de
este papel: este documento se escribe ANTES que el código**
(`agent/birth_shaper.py`), y la vara de la §4 queda declarada
antes de construir.

## 1. El antecedente medido (por qué existe este papel)

La cadena gratis cerró con una conclusión medida en tres
pasos:

- La **autopsia de la 1.4.1** (`REPLAY-PUERTA-141-20261022.md`):
  sobre los 166 hallazgos de la base nº 298, la puerta congelada
  aceptó 0, retuvo 149 (blocker único
  `sin_regla_de_verificacion_en_puerta`) y rechazó 17 por ancla
  entre artefactos. La causa dominante no era el dialecto: la
  1.4.1 no define regla para las categorías generales.
- La **puerta 1.5.0** (`RESULTADO-REPLAY-150-20261022.md`)
  definió esa regla y emitió por primera vez (32 emisiones,
  19 TP, precisión 59,4 %), pero su vara **NO PASA**: la sala
  de espera se llevó 133/166 (80,1 %) con dos blockers que son
  propiedades de **cómo nacen los reclamos** — 71
  `sin_patron_concreto_en_el_reclamo` y 62
  `tokens_afirmados_ausentes_en_la_evidencia`.
- El **contrato de reclamos** (`PREREGISTRO-CONTRATO-RECLAMOS.md`,
  `RESULTADO-CONTRATO-RECLAMOS-20261022.md`) especificó la forma
  en que un hallazgo debe nacer para ser verificable (C1–C5) y
  midió cuánto del corpus ya nacido entra en esa forma **a
  posteriori, sin inventar evidencia**: **49/166** (32 nacidos
  conformes + 17 minados de la prosa). Los 63 no conformes por
  tokens ausentes son **no normalizables por diseño**: el
  reclamo afirma lo que su propia cita no contiene, y el
  normalizador se negó a recortar el patrón para rescatarlo —
  recortarlo taparía la señal. Dato estructural de ese
  pipeline: de los 49 conformes que entraron a la 1.5.0, la
  puerta emitió **49/49** — en forma de contrato, la puerta no
  retiene a nadie en este corpus; **el cuello completo quedó
  en el nacimiento**.

Este papel construye el lado que faltaba: **la capa de
formación al nacer** que la sección del productor del papel
del contrato dejó a nivel de diseño. La diferencia con el
normalizador a posteriori es de posición, no de truco: el
formador actúa **dentro del revisor, sobre cada candidato
antes de la puerta y con el diff completo a la vista**, en el
punto en que el reclamo todavía es emisión del productor y
puede reformular **su propia afirmación** — afirmar solo lo
que su cita contiene — en vez de ser juzgado después por una
afirmación que nació rota. Lo que el normalizador no podía
hacer sin tapar la señal (recortar el patrón afirmado), el
formador sí puede hacerlo en origen, **asentando cada recorte
en el ledger**: la señal no se tapa, se traslada del veredicto
de la puerta a la declaración de nacimiento.

## 2. El diseño de la capa de formación al nacer

**Identidad:** `SHAPER_VERSION = alma-birth-shaper/1.0`,
módulo nuevo `agent/birth_shaper.py`. Determinista, sin
llamadas a modelos. Interfaz: `shape_claim(candidate, diff)`
→ `ShapingOutcome`, y su forma de lote `shape_candidates`.
La tokenización tiene una única fuente de verdad — la de la
puerta 1.5.0, importada sin modificarla (la misma que consume
`claim_contract.py`) — y el minado de prosa reutiliza el del
normalizador, importado sin modificarlo: el formador no
redefine qué es un token ni qué formas de prosa son minables.

El formador recibe el `DiffIndex` completo (en producción
trabaja junto al diff, dentro del revisor) y lo usa para
asentar en el resultado un dato informativo: si el rango
formado contiene al menos una línea `added` (el mismo dato
que las puertas registran como `no_added_line`). Las reglas
de formación operan sobre el mensaje y la cita nacidos del
candidato, que es el extracto del head ya verificado por el
propio revisor:

- **Caso C — las 19 clases: pasan intactas.** Su contrato es
  el dialecto de clase de la 1.4.1 (decisión del pipeline, no
  del formador; misma regla que el Caso C del normalizador).
  El corpus A no contiene ninguno — declarado en la autopsia —
  y este caso no se ejercita en la medición.
- **Caso A — el reclamo ya declara patrón (≥ 1 token entre
  backticks):**
  - **(b) Recorte en origen.** El patrón que sobrevive =
    los tokens afirmados que **están presentes en las líneas
    citadas** (subcadena sobre el extracto citado). Los
    tokens afirmados ausentes se **des-declaran**: el
    formador quita los backticks de cada span cuyo token
    normalizado fue recortado, de modo que el token queda
    como palabra de prosa y el reclamo deja de afirmarlo.
    **Jamás se agrega un token** que el reclamo no haya
    afirmado. Cada token recortado queda asentado en el
    resultado (`trimmed_tokens`), con su razón.
  - Si **ningún** token afirmado está en la cita, el reclamo
    **no puede nacer en contrato**: queda **declarado no
    verificable en origen** (§2(d)).
  - Un token afirmado que **sí** está en la cita **nunca**
    se des-declara, aunque esté gobernado por una marca de
    ausencia: la contradicción afirmativa (G3) es familia de
    rechazo de la puerta, no materia que el formador lave.
- **Caso B — el reclamo no declara ningún token:** el patrón
  se **declara al nacer copiándolo de la cita del propio
  reclamo** mediante el minado cerrado del normalizador
  (formas de código en la prosa fuera de backticks, veto a
  tokens gobernados por ausencia, presencia verbatim en la
  evidencia citada). Con ≥ 1 token minado, el mensaje formado
  es el nacido con esos tokens envueltos en backticks — ni
  una palabra agregada, quitada o reordenada. Con 0, el
  reclamo queda **declarado no verificable en origen**
  (§2(d)).
- **(c) La cita formada es el rango mínimo que contiene el
  patrón.** Para todo reclamo formado con patrón no vacío
  (Casos A y B): el rango [primera línea citada que contiene
  algún token del patrón, última línea citada que lo
  contiene]. La evidencia formada es el **trozo contiguo
  correspondiente del extracto nacido** (las mismas líneas,
  sin releer ni alterar ninguna); archivo, tipo, `rule_id`,
  severidad, categoría y productor quedan como nacieron. Si
  el rango mínimo coincide con el nacido, la cita no cambia.
  El rango formado nunca sale del rango nacido: el formador
  elige la cita **dentro** de lo que el reclamo citó (en
  producción, productor y formador eligen cita y patrón
  juntos desde el diff; en este proxy seco la cita nacida es
  el universo — §3).
- **(d) Lo que no puede nacer en contrato queda DECLARADO no
  verificable en origen**, con su código de razón asentado en
  el resultado (y, en la medición, en el ledger por PR):
  `tokens_afirmados_ausentes_en_la_evidencia` (Caso A sin
  ningún token citable) o `sin_patron_concreto_en_el_reclamo`
  (Caso B sin nada minable) — los mismos códigos de la línea.
  La declaración en origen **no es un rechazo**: el reclamo
  cuenta como retenido (sala de espera compuesta) en la
  contabilidad del pipeline, con la diferencia de que su
  estado lo declara su productor al nacer y no lo descubre
  la puerta después. El formador nunca rechaza en firme:
  el rechazo sigue reservado a la puerta (contrato C5).

**Integridad (la cláusula que manda):** el formador afirma
solo tokens que el reclamo nacido afirmó (Caso A) o que su
prosa y su cita contienen a la vez (Caso B); la evidencia
formada es un trozo contiguo de la evidencia nacida, línea
por línea idéntica; la cita formada está contenida en la
cita nacida; ningún token se afirma si no ocurre en el texto
nacido **y** en la evidencia formada. La auditoría
programática de la §4(5) verifica exactamente esto sobre los
166.

**Semántica del pipeline compuesto (declarada):** formador →
chequeo de contrato (`claim_contract.normalize_claim`, SIN
MODIFICAR) → puerta 1.5.0 (SIN MODIFICAR), sobre el corpus A,
con el replay idéntico a los anteriores (misma reconstrucción
de candidatos con la fórmula del revisor, mismos diffs
regenerados, ledger prendido):

- Los reclamos **formados** (o intactos, Caso C) entran al
  chequeo de contrato en su orden original, por PR. Por
  construcción, un formado cumple C1–C4 contra su cita
  formada y el chequeo lo confirma como nacido conforme; si
  el chequeo declarara no conforme a un formado, eso es un
  dato de la medición (se reporta tal cual), no un error a
  corregir en esta tarea.
- Los **declarados no verificables en origen** no entran ni
  al chequeo ni a la puerta disfrazados: se quedan en la
  etapa de formación con su código, y cuentan dentro de la
  fracción `needs_validation` del pipeline compuesto (sala
  compuesta = declarados en origen + retenidos del contrato
  + retenidos de la puerta).
- «Emitido» = aceptado por la puerta entre los que llegaron
  a ella (emisión estricta, la misma lectura de los papeles
  anteriores).

## 3. La salvedad honesta del proxy seco (declarada, no escondida)

La medición alimenta el formador con los **hallazgos finales
de la base nº 298** (los `findings.json` por PR, reconstruidos
como candidatos con la fórmula del revisor y los diffs
regenerados, exactamente como en la autopsia y los dos replay
anteriores) — no con candidatos vivos dentro de una corrida.
Las diferencias con la producción, declaradas:

- En producción la capa actúa sobre los **candidatos
  pre-puerta** del revisor en la misma corrida; acá actúa
  sobre los hallazgos finales de la corrida nº 298
  reconstruidos. La identidad es la mejor disponible y la de
  toda la línea: en el brazo base esos candidatos SON los
  hallazgos (el revisor verifica el ancla contra el head
  antes de la puerta y descarta lo que no coincide, en ambas
  ramas), y en el brazo ALMA los mismos objetos son los que
  la puerta juzga (las ramas difieren solo en la config de la
  puerta, papel v2.3 §3d). La deduplicación entre pasadas ya
  ocurrió en la corrida: el formador de producción vería
  también los duplicados que el revisor descartó acá, y su
  ledger los asentaría como tales; esta medición no los ve
  y no afirma nada sobre ellos.
- El formador de producción elige el rango de cita **desde
  el diff completo** al emitir; acá el rango formado se
  elige **dentro de la cita nacida** (el extracto del head
  que el hallazgo trae). Un reclamo cuyo patrón vive fuera
  de su cita nacida es, en este proxy, no verificable en
  origen; en producción, productor y formador juntos
  podrían haber citado ese rango al nacer. La salvedad
  corre en contra del formador (su conformidad medida acá
  es un piso, no un techo) y queda declarada con la vara.
- La medición vale para el corpus A (producción del revisor
  2.3.1 en la práctica nº 298) y no afirma nada sobre otra
  corrida ni otro examen — la misma cláusula de alcance de
  toda la línea.

## 4. La vara (declarada antes de construir, sin cambios)

Pipeline = formador al nacer → chequeo de contrato
(`claim_contract.py` sin modificar) → puerta 1.5.0 (sin
modificar), sobre el corpus A (los 166 de la base nº 298 con
`decisions.json`, diffs regenerados como en los replays
anteriores):

1. **Conformidad al nacer > 49/166** (el techo del
   normalizador a posteriori) — reportar el conteo crudo y
   por razón de no-conformidad residual.
2. **Fracción en `needs_validation` del pipeline compuesto
   < 50 %.**
3. **Precisión entre emitidos ≥ 53,6 %** y **TP emitidos
   > 26** (el número del pipeline con normalizador), recall
   de TP gold distintos reportado.
4. **Discriminación reportada:** tasa de muerte de los 8 FP
   gold-confirmados vs la de los 89 TP, sin umbral inventado.
5. **Integridad: cero evidencia inventada** (auditoría
   programática como la del contrato: evidencia/cita/tokens
   verificados contra el origen).
6. **La prueba paga futura queda FUERA de este papel:** se
   anota como decisión pendiente de Alejandro (papel de
   corrida nuevo, con tope de línea fijado por él) para
   cuando haya ingresos.

Definiciones operativas (declaradas con la vara):
«conformidad al nacer» en (1) = reclamos que el formador
entrega en forma de contrato (formados Casos A/B o intactos
Caso C) sobre 166; «no-conformidad residual» = los declarados
no verificables en origen, por código. «Tasa de muerte» en
(4) = fracción no emitida dentro de cada conjunto gold. Los
componentes (2) y (3) son umbrales; (1) es umbral sobre el
techo a posteriori con su desglose reportado; (4) se reporta
sin umbral; (5) es condición de validez de la medición misma
(si se violara, la medición no vale, no un componente más).
**Si el pipeline no pasa la vara, NO PASA y se asienta así:
prohibido ajustar la vara, el diseño o el formador después
de ver el número y remediar en esta misma tarea; cualquier
ajuste es una iteración posterior declarada.**

## 5. Qué NO cambia

- Las puertas 1.0.0–1.4.1 quedan **byte-idénticas**
  (congeladas), la **1.5.0 no se modifica** y
  **`claim_contract.py` no se modifica**: el pipeline los
  consume tal cual; al cierre se verifican y reportan los
  hashes de archivo de los ocho.
- El revisor **no se reconstruye en producción**: ningún
  prompt, formato de emisión ni montaje cambia en esta
  tarea; el formador es un módulo nuevo medido en seco
  contra la §4. Integrarlo al revisor (y cualquier corrida)
  exige su propio papel — §4(6).
- Ninguna adopción se decide acá: el formador se mide
  contra la vara y el resultado se asienta tal cual salga.

— Pre-registro del revisor con reclamos nativos del contrato,
2026-10-22. Insumos: `PREREGISTRO-CONTRATO-RECLAMOS.md`,
`RESULTADO-CONTRATO-RECLAMOS-20261022.md`,
`PREREGISTRO-PUERTA-150.md`, `REPLAY-PUERTA-141-20261022.md`,
`RESULTADO-REPLAY-150-20261022.md`. Gasto: **US$0**.
