# Pre-registro — Puerta 1.5.0: regla de verificación para la vía general

**Fecha:** 2026-10-22 · **Autorización:** Alejandro, 22/10/2026
(«Bueno lo hagamos»), como Paso 2 del plan de mejora de ALMA tras
la autopsia de la puerta 1.4.1. **Costo de este papel y de la
construcción que pre-registra: US$0** — diseño y construcción en
seco, replay local; sin llamadas a modelos, sin portal, sin
publicación. **Orden obligatorio de este papel: este documento se
escribe ANTES que el código** (`agent/alma_gate_v150.py`), y la
vara de la §4 queda declarada antes de construir.

## 1. El antecedente medido (por qué existe este papel)

La adjudicación completa de la práctica ALMA nº 311
(`ADJUDICACION-COMPLETA-311-20261022.md`) midió el efecto de la
puerta 1.4.1 integrada al revisor v2.3: de ≤165 candidatos dejó
pasar **1** (0,6 %), y ese único emitido no acreditó contra el
gold (zona gris): precisión grounded 0,0 %, recall 0,00 %, regla
de avance variante (ii) **NO PASA**. La autopsia por replay
(`REPLAY-PUERTA-141-20261022.md`, US$0, sobre los 166 hallazgos
de la base nº 298, que sin puerta rindieron P 53,6 % / R 18,75 %)
descompuso la muerte y **refutó la hipótesis del dialecto** como
causa dominante:

- **Causa dominante — estructural (149/166 = 89,8 %):** la
  puerta 1.4.1 no define regla de verificación para las
  categorías GENERALES del revisor v2.3 (las nueve etiquetas
  públicas del papel v2.3 §3(a)). Todo reclamo general bien
  formado y anclado queda retenido en `needs_validation` con el
  blocker único `sin_regla_de_verificacion_en_puerta`: la sala
  de espera es su techo y la sala de espera no emite. TP-kill
  89/89; los 8 FP gold-confirmados comparten destino y razón
  con los verdaderos: **discriminación cero en la vía general**.
- **Causa secundaria — ancla entre artefactos (17/166 =
  10,2 %):** el revisor construye la evidencia contra el
  archivo **head** completo (y verifica esa coincidencia antes
  de la puerta: `_to_candidate_v23`); la puerta ancla solo
  contra los **hunks del diff**. La evidencia de esos 17
  coincide exactamente con el archivo: citan contra otro
  artefacto, no citan mal. Los 17 mueren por «ancla fuera del
  diff», incluidos 9 TP.
- **El dialecto evidencial de clase mató 0 reclamos medibles:**
  el corpus de producción no contiene candidatos de clase
  (0/166) y el único candidato de clase genuino recuperable de
  la 311 (tarfile) pasó su chequeo.

La 1.5.0 ataca exactamente estas dos causas medidas y ninguna
otra: **define la regla que falta para la vía general** y
**resuelve el ancla contra el head O el diff**. No reabre la
línea v2.3 (cerrada por la Adenda 3 §5): es un artefacto nuevo
con su papel propio, medido en seco contra la vara de la §4.

## 2. El diseño de la 1.5.0

**Identidad:** `POLICY_VERSION = alma-evidence-gate/1.5.0`,
módulo nuevo `agent/alma_gate_v150.py`. Determinista, sin
llamadas a modelos, con la misma interfaz de la línea:
`validate(candidates, diff, agent_name)` → hallazgos, ledger y
sección `needs_validation`.

**Reclamos de las 19 clases: sin cambio de comportamiento.** Se
validan por delegación a `AlmaGateV141` intacta (que a su vez
delega en la 1.3.0 y aplica la frontera de la 1.4.1): mismos
veredictos, mismas razones, misma equivalencia de aceptación.
La 1.5.0 no reimplementa ni retoca una sola regla de clase.

**Reclamos generales (las nueve categorías): la regla nueva.**
La evidencia almacenada del candidato ES el extracto del head
para el rango citado — es la garantía de construcción del
pipeline (el revisor la verifica contra el head antes de la
puerta y descarta lo que no coincide; en el brazo base esos
mismos candidatos son los hallazgos). La puerta verifica:

- **(G0) Forma:** `start_line ≥ 1` y `end_line ≥ start_line`;
  si no, rechazo firme («invalid line range», como toda la
  línea).
- **(G1) Existencia contra el head:** la cantidad de líneas de
  evidencia almacenada debe ser exactamente
  `end_line − start_line + 1`. Si no, la cita refiere líneas
  que no existen tal como están citadas: rechazo firme
  (cita de línea inexistente, §2(iii) del encargo).
- **(G2) Ancla — head O diff:** por cada línea citada que el
  `DiffIndex` SÍ contiene para ese archivo, el texto del diff
  debe coincidir exactamente con la evidencia almacenada; una
  contradicción entre artefactos es rechazo firme (la cita no
  es ni el head ni el diff: fabricación o cita de otro
  archivo). Las líneas que el diff no contiene se resuelven
  contra el extracto del head. Un archivo ausente del diff se
  resuelve entero contra el head. **Esto repara los 17.**
- **(G3) Contradicción afirmativa — rechazo firme, única
  familia además de G0–G2:** el reclamo declara ausente una
  guarda que su propia evidencia muestra presente. Mecánica:
  se extraen los tokens de código entre backticks del mensaje;
  si un token está gobernado en su oración por una marca de
  ausencia de la lista cerrada (`without`, `no`, `missing`,
  `lacks`, `does not use`, `doesn't use`, `never uses`,
  `not using`, con artículo opcional interpuesto) y el token
  normalizado aparece en la evidencia citada, el reclamo se
  contradice con su cita: rechazo firme con la razón asentada.
- **(G4) Grounding afirmativo — lo que la puerta SÍ puede
  emitir:** el patrón concreto que el reclamo afirma = el
  conjunto de tokens de código entre backticks del mensaje
  (normalización declarada: sin punto inicial, sin `()` final
  vacío; token «de código» = sin espacios internos y longitud
  ≥ 2). Si **todos** los tokens afirmados aparecen en las
  líneas de evidencia citadas (búsqueda de subcadena sobre el
  extracto), el reclamo está grounded: **aceptado y emitido**.
- **(G5) Duplicado:** un reclamo verificado cuyo (archivo,
  rango, mensaje normalizado) ya fue aceptado — de clase o
  general — se rechaza firme como duplicado de un aceptado,
  con la disciplina de toda la línea.

**Lo no verificable ni contradicho → `needs_validation`, con
código de razón específico** (nunca más un motivo genérico que
lo tape todo):

- `sin_patron_concreto_en_el_reclamo` — el mensaje no afirma
  ningún token de código contrastable con su cita.
- `tokens_afirmados_ausentes_en_la_evidencia` — algunos tokens
  afirmados no aparecen en las líneas citadas (la razón los
  lista): la puerta no puede verificar el reclamo contra su
  propia cita, y tampoco puede contradecirlo.

Los retenidos generales cargan además el blocker informativo
`no_added_line` cuando ninguna línea citada es `added` en el
diff (continuidad con la vía general de la 1.4.1; alimenta la
pregunta abierta de la §5). Cada candidato deja asentados su
destino y sus razones en el ledger del replay: la vara (4)
exige que ninguno se pierda sin razón registrada.

**Limitaciones declaradas del diseño:** la verificación de
tokens es por subcadena sobre las líneas citadas, sin AST ni
distinción comentario/string/código; la familia de contradicción
es una lista cerrada de marcas de ausencia en inglés (el idioma
de los mensajes del revisor); la puerta confía en
`evidence_text` como extracto del head según el contrato de
construcción del pipeline, y lo contrasta contra el diff en
cada línea que el diff contiene.

## 3. Qué NO cambia

- Las puertas 1.0.0, 1.1.0, 1.2.0, 1.3.0, 1.4.0 y 1.4.1 quedan
  **byte-idénticas** (congeladas): la 1.5.0 es un módulo nuevo
  que las importa; al cierre se verifican y reportan los seis
  hashes de archivo.
- El rulebook de las 19 clases es el de la 1.4.1 por delegación,
  sin cambios de comportamiento (§2).
- El registro `needs_validation` sigue **sin campo de
  severidad** (por construcción del tipo, como en la 1.4.x) y
  vive fuera de los hallazgos y del ledger de aceptados/
  rechazados.
- El montaje (portal, `main.py`, resolvedor del revisor) **no
  se construye en esta tarea**: la §6 deja el diseño de la
  persistencia del ledger; ningún cambio de montaje entra en
  este papel.
- Ninguna adopción se decide acá: la 1.5.0 se mide en seco
  contra la §4 y el resultado se asienta tal cual salga.

## 4. La vara del replay (declarada antes de construir)

Corpus A = los 166 hallazgos de la base nº 298 con sus
veredictos de `adjwork298/decisions.json`, replay local
idéntico al de la autopsia (misma reconstrucción de candidatos
con la fórmula del revisor, mismos diffs regenerados, ledger
prendido):

1. Emisiones > 0 y TP emitidos > 0 (la 1.4.1 dio 0 y 0).
2. Precisión entre emitidos (TP / total emitidos) ≥ 53,6 %
   (al menos igualar a la base sin puerta) Y recall de TP
   gold distintos > 0; tramo de excelencia declarado:
   precisión ≥ 58,6 %.
3. Fracción en `needs_validation` < 50 % de los candidatos
   (la 1.4.1 dejó 89,8 %).
4. Cero candidatos perdidos sin razón registrada (ledger
   completo del replay).
5. Discriminación reportada por separado: tasa de muerte de
   los 8 FP gold-confirmados vs tasa de muerte de los 89 TP
   (sin umbral inventado: se reportan los dos números).

Definiciones operativas (declaradas con la vara): «emitidos»
= aceptados por la puerta bajo lectura de emisión estricta
(solo los aceptados emiten; la salida de `needs_validation`
en producción es la pregunta abierta de la §5 y no entra en
esta medición); «TP emitidos» = emisiones cuyo veredicto en
`decisions.json` es TP; «recall de TP gold distintos» = TP
gold distintos cubiertos por emisiones TP / 352; «tasa de
muerte» = fracción no emitida (rechazada o retenida) dentro
de cada conjunto gold. **Si la 1.5.0 no pasa la vara, NO PASA
y se asienta así: prohibido ajustar la vara o el diseño
después de ver el número y volver a medir en esta misma
tarea; cualquier ajuste es una versión o un papel
posterior.**

## 5. Pregunta abierta — la salida de `needs_validation` en producción

Esta pregunta **NO la resuelve este papel**: queda como
decisión de Alejandro, con las opciones y sus costos escritos.
La medición de la §4 corre con emisión estricta (los
retenidos no emiten) bajo cualquiera de las respuestas.

- **(a) Emisión marcada:** los retenidos salen en los
  hallazgos con una marca visible de «no verificado». Costos:
  el contrato de salida del benchmark espera hallazgos con la
  forma del contrato — una marca exige un campo que el juez
  augmented puntuaría como hallazgo más, con lo que la sala
  de espera se convierte en emisión con una precisión propia
  jamás medida; y se rompe la propiedad que protege la vara
  (retenido ≠ emitido) sin un papel que mida el efecto.
- **(b) Validación posterior:** una segunda etapa (humana o
  un validador aparte) revisa la sala y emite los
  sobrevivientes. Costos: una etapa entera nueva, con su
  propio papel y su propia medición si el validador es otro
  modelo; en volumen de producción el costo humano por
  corrida es el cuello (la 1.4.1 retenía 149/166: sin
  sub-selección previa, nadie valida 149 reclamos por PR de
  práctica); y la pregunta de quién valida al validador
  queda abierta por diseño.
- **(c) Descarte declarado:** los retenidos no emiten nunca;
  el ledger viaja con la corrida y la retención se reporta
  como número del run (cuántos, con qué razones). Costos: el
  recall del brazo queda con techo en los aceptados — la
  sala aporta auditabilidad, no cobertura — y su valor
  depende por entero de que alguien lea los ledgers.

## 6. Diseño (no construcción) — la persistencia del ledger en el montaje

**El defecto medido:** en la nº 311 el ledger de la puerta no
llegó a ningún archivo entregado. El código ya sabe escribirlo
(`agent/main.py`: solo si `ALMA_LEDGER_PATH` está fijado o
`RB_ALMA_LEDGER=1`, en cuyo caso cae junto al archivo de
salida), pero el zip del portal (58 archivos: `prs/*/findings
.json`, `agent.log` por PR, `summary.txt`, logs de shards) no
lo trajo. Sin ledger no hay pureza de retención medible ni
pérdida explicable: la Adenda 3 §4 quedó sin instrumento.

**El diseño (para un papel de montaje futuro; acá no se
construye):**

1. **La ruta del ledger cae dentro del directorio que el
   portal ya devuelve:** el montaje fija `ALMA_LEDGER_PATH`
   por PR apuntando al mismo directorio por-PR del que sale
   `prs/<pr>/findings.json` (p. ej.
   `prs/<pr>/alma-ledger.json`), no junto a una salida raíz
   que el zip no recoge. Requiere que el montaje pase al
   agente la ruta de salida por-PR (cambio en `main.py` /
   lanzador: diseñado, no construido).
2. **Redundancia por stdout:** el agente imprime además la
   tabla de disposición por candidato (destino + razones) en
   el log del agente, que el zip sí trae (`agent.log` por
   PR): aunque la recolección de archivos cambie, la
   disposición queda asentada en un artefacto que viaja.
3. **Verificación previa obligatoria:** cualquier papel
   futuro que mida una puerta en este examen corre primero
   UNA pasada seca de un solo PR por el portal y controla
   que el zip contenga el ledger antes de pagar la corrida
   completa. Nunca más medir a ciegas (lección de la 311,
   asentada en su adjudicación §7).
4. El resolvedor del revisor deberá admitir la etiqueta de
   la puerta nueva (`gate=v150`) como admitió `v141` en la
   v2.3.2 — cambio de montaje del mismo papel futuro, no de
   este.

## 7. Falsadores y alcance honesto

- Si el replay de la §4 no alcanza cualquier componente de
  la vara, la 1.5.0 queda **no adoptable** con este papel, y
  el resultado se asienta con sus números (como se asentó el
  de la 1.4.1).
- La vara mide SOLO el corpus A (producción del revisor
  2.3.1 sobre la práctica nº 298): un pase no afirma nada
  sobre otra corrida, otro examen ni producción real; y la
  discriminación del componente (5) se reporta sin umbral —
  si la puerta nueva tampoco separa TP de FP, eso queda
  dicho con los dos números a la vista.
- Este papel no pone la 1.5.0 en ningún montaje ni corrida:
  cualquier corrida futura exige su propio pre-registro, su
  compuerta de saldo y su «sí».

— Pre-registro de la puerta 1.5.0, 2026-10-22. Insumos:
`REPLAY-PUERTA-141-20261022.md`,
`ADJUDICACION-COMPLETA-311-20261022.md`,
`PREREGISTRO-PUERTA-141.md`. Gasto: **US$0**.
