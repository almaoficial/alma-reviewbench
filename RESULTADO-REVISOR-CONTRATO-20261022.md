# Resultado — Revisor con reclamos nativos del contrato: la formación al nacer medida en seco

**Fecha:** 2026-10-22 · **Papel:** `PREREGISTRO-REVISOR-CONTRATO.md`
(la vara de su §4 fue declarada ANTES de construir el formador).
**Costo: US$0** — replay local sobre archivos y clones públicos;
sin llamadas a modelos, sin portal, sin publicación.

## Veredicto en una línea

**El pipeline compuesto NO PASA la vara** — y es el mejor
resultado de la línea hasta hoy: la conformidad al nacer salta
del techo a posteriori de 49 a **80/166**, la precisión entre
emitidos es **55,7 %** (44 TP emitidos, contra 26 del pipeline
anterior), y la puerta emite **79** reclamos — pero la sala de
espera compuesta queda en **86/166 = 51,8 %**, a 3 reclamos del
< 50 % que la vara pedía. El cuello ya no es la forma de los
reclamos que nacen con patrón: es que **86 reclamos nacen sin
nada citable que afirmar** (54 sin patrón en la prosa, 32
afirmando solo tokens que su cita no contiene) y el formador,
por su cláusula de integridad, los declara no verificables en
origen en vez de inventarles evidencia. Ningún ajuste de vara,
diseño o formador se hizo después de ver el número; cualquier
ajuste es una iteración posterior declarada (§6).

## 1. El arnés (idéntico a los anteriores)

Mismo corpus A (los 166 hallazgos de la base nº 298 de
`adjwork298/run298/prs/*/findings.json`, veredictos de
`adjwork298/decisions.json`), misma reconstrucción con la
fórmula del revisor (evidencia desde `git show <head>:<archivo>`
sobre clones — parciales `--filter=blob:none`, que entregan el
mismo contenido —, diffs regenerados `git diff base...head`):
**166/166 reconstruidos sin errores**. Controles de sanidad,
ambos exactos: la 1.5.0 sola reproduce el replay de la 1.5.0
(**32/133/1**, blockers primarios 71 `sin_patron` + 62
`tokens_afirmados_ausentes`); el pipeline del contrato
reproduce su medición (**49 emitidos / 117 en espera**, 32
nacidos + 17 minados). El pipeline nuevo es **invariante**
entre las dos asignaciones extremas de categoría general (P1
todas `correctness`; P2 rotación por las nueve): vectores de
estado y etapa idénticos. Disposiciones por PR asentadas en
`/tmp/replay_revisor/ledgers/`; emparejamiento entre etapas
por índice de candidato (la cita formada puede achicarse; las
claves por ubicación mentirían).

**La capa medida:** `agent/birth_shaper.py`
(`alma-birth-shaper/1.0`), determinista, sin modelos, con la
tokenización de la 1.5.0 y el minado del normalizador
importados sin modificar. Pipeline: formador →
`claim_contract.normalize_claim` (sin modificar) → puerta
1.5.0 (sin modificar), ledger prendido.

## 2. Conformidad al nacer (componente 1) — PASA

**Conformes al nacer: 80/166 (48,2 %)** — vara: > 49. De los
80: **63 declarados** (el reclamo ya traía patrón entre
backticks; el formador recortó en origen los tokens afirmados
ausentes de la cita y achicó la cita al rango mínimo del
patrón) y **17 minados al nacer** (patrón declarado desde la
cita con el minado cerrado del normalizador — los mismos 17
que el pipeline anterior rescataba a posteriori, reclamo por
reclamo). Ninguna clase entre los 166 (el corpus no las
contiene; el Caso C no se ejercita, como en toda la línea).

**Recortes asentados:** de los 63 declarados, **32 no
llevaron recorte** — son, reclamo por reclamo, los 32 que el
normalizador ya hallaba nacidos conformes — y **31
recortaron 48 tokens** en total (cada token recortado quedó
registrado en el outcome y en el ledger por PR). Los 32
declarados no verificables por tokens llevan asentados sus
42 tokens nacidos: la afirmación completa que no sobrevivió
a su propia cita. **48 citas** se achicaron a su rango
mínimo de patrón (33 declaradas, 15 minadas).

**No-conformidad residual: 86**, declarados no verificables
en origen por el propio productor, por razón:

| Razón de origen | n | Lectura |
|---|---:|---|
| `sin_patron_concreto_en_el_reclamo` | 54 | La prosa no declara ni deja minar ningún token presente en su cita. |
| `tokens_afirmados_ausentes_en_la_evidencia` | 32 | Todo lo que el reclamo afirma entre backticks está ausente de sus líneas citadas: no hay patrón citable que sobrevivir. |

Cruzado con el pipeline anterior: de los 63 no conformes por
tokens del normalizador, 31 llevaban al menos un token
citable y nacen conformes acá (recorte en origen); los 32
restantes no tenían nada que sobrevivir. De los 54 sin
patrón, 0: el minado al nacer encuentra exactamente lo mismo
que el minado a posteriori (17/71 reclamos sin patrón
declarado), porque la materia prima — prosa y cita — es la
misma.

**Chequeo de contrato sobre los formados: 80/80 conformes**
(origen `born` para el chequeador: una vez declarado el
patrón al nacer, el reclamo formado es indistinguible de uno
que nació declarando — esa indistinguibilidad ES el punto de
formar al nacer). La etapa de contrato retuvo **0**.

## 3. El pipeline compuesto (componentes 2 y 3)

| Etapa | Aceptados | En espera | Rechazados |
|---|---:|---:|---:|
| Formador (declarados en origen) | — | 86 | — |
| Chequeo de contrato | — | 0 | — |
| Puerta 1.5.0 (sobre 80) | **79** | 0 | 1 |
| **Compuesto (sobre 166)** | **79** | **86** | **1** |

- **Componente 2 — NO PASA:** fracción en `needs_validation`
  del compuesto = 86/166 = **51,8 %** (vara: < 50 %; hacían
  falta ≤ 82 en espera — faltaron 3 reclamos). Toda la espera
  quedó en la etapa de formación: es la declaración del
  productor, no el descubrimiento de la puerta.
- **Componente 3 — PASA:** precisión entre emitidos =
  **44/79 = 55,7 %** (vara: ≥ 53,6 %) y **TP emitidos = 44**
  (vara: > 26). Recall de TP gold distintos: **17/352 =
  4,83 %** (reportado sin umbral) — con una salvedad honesta:
  los TP emitidos suben de 26 a 44 pero los distintos bajan
  de 18 a 17 contra el pipeline del contrato: las emisiones
  nuevas se concentran en ítems de gold ya cubiertos por
  otras emisiones.
- **El único rechazo firme** es el reclamo de Mcp-Docker
  (`handler.go`, TP gold 33) que toda la línea conoce: el
  formador recortó su token ausente
  (`error=access_denied&state=...`) pero conservó `code` —
  presente en la evidencia y gobernado por una marca de
  ausencia — porque el formador **no lava contradicciones**
  por diseño; la puerta lo rechazó por (G3), la misma causa
  del replay de la 1.5.0 sola. Consistencia entre arneses,
  no regresión.

## 4. Discriminación (componente 4, reportada sin umbral)

| Conjunto gold | n | Murieron (no emitidos) | Tasa de muerte |
|---|---:|---:|---:|
| FP gold-confirmados | 8 | 4 (0 rechazados, 4 en origen) | **50,0 %** |
| TP gold | 89 | 45 (1 rechazado, 44 en origen) | **50,6 %** |

Paridad casi exacta (0,6 pp): el pipeline compuesto, como
todos los de la línea, **no discrimina** verdaderos de
falsos — decide por verificabilidad de nacimiento, y los
reclamos verdaderos nacen tan mal citados como los falsos
(44 de los 89 TP quedaron declarados no verificables en
origen). Lo que la formación al nacer cambia no es la
discriminación: es **cuánto de lo verificable llega a
emitirse** (79 emisiones contra 32 de la puerta sola y 49
del pipeline a posteriori) y **dónde se asienta la espera**
(en origen, con razón declarada por el productor).

Por origen, sobre los emitidos: declarados 62 emitidos con
37 TP (59,7 % de precisión); minados al nacer 17 emitidos
con 7 TP (41,2 %) — los minados emiten más sucio que los
declarados, la misma señal del pipeline anterior.

## 5. Integridad (componente 5) — PASA (condición de validez)

Auditoría programática sobre los 166, como la del contrato,
ampliada a las operaciones del formador:

- **Evidencia inventada o alterada: 0.** La evidencia de los
  80 formados es, línea por línea, el trozo contiguo exacto
  del extracto nacido que corresponde a su rango formado.
- **Cita fuera del rango nacido: 0.** Las 80 citas formadas
  están contenidas en la cita nacida (archivo, tipo y
  `rule_id` idénticos).
- **Token afirmado que el reclamo no escribió: 0.** Todo
  token afirmado por un formado ocurre en el mensaje nacido
  **y** en la evidencia formada.
- **Recorte exacto: 0 desvíos.** En los 63 declarados, los
  tokens recortados son exactamente los afirmados ausentes
  de la evidencia nacida, y el patrón sobreviviente es
  exactamente los presentes — el formador no recortó de más
  ni de menos en ningún reclamo.
- **Declaración sin razón: 0.** Los 86 no verificables en
  origen llevan su código asentado.

## 6. Qué sigue (fuera de este papel)

El veredicto es el del pre-registro: **NO PASA**, por el
componente 2, y se asienta sin remediar en esta tarea. La
lectura que el número deja, para la iteración que Alejandro
decida: el 51,8 % en espera ya no es un problema de FORMA
(el formador llevó la conformidad a 80 y la etapa de
contrato a 0 retenciones) sino de MATERIA — 86 reclamos cuyo
contenido no cita nada verificable. Mover ese número ya no
es trabajo de la capa de formación: es trabajo del revisor
mismo (que emita reclamos con su patrón y su cita elegidos
juntos al producir, o que no emita lo que no puede citar), y
es exactamente el punto donde esta línea deja de ser
medible en seco: validarlo exige producción real.

**La prueba paga queda FUERA de este papel** (§4(6) del
pre-registro): decisión pendiente de Alejandro — papel de
corrida nuevo, con el tope de línea fijado por él, para
cuando haya ingresos. Ninguna adopción se decide acá: el
formador queda construido y medido, no adoptado.

## 7. Verificación de cierre

- Suite completa: **280/280** tests en verde (272 previos +
  8 nuevos de `tests/test_birth_shaper.py`: reclamo que nace
  conforme con el diff a la vista, token ausente recortado y
  asentado, sin patrón declarado no verificable en origen,
  todos los tokens ausentes declarado no verificable, minado
  al nacer con rango mínimo, clase intacta, identidad y
  hashes congelados).
- Batería semáforo: **16/16** sin regresiones
  (`test_battery_16_of_16_without_refusals` en verde dentro
  de la suite).
- Archivos intocados (sha256 de archivo, verificados al
  cierre): puertas 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`,
  1.2.0 `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0 `b16c5a79…`,
  1.4.1 `08d813e9…`, 1.5.0 `71b1996b…` y `claim_contract.py`
  `7df8abc7…` — byte-idénticos a los asentados en los
  papeles anteriores.
- Nuevos: `agent/birth_shaper.py` y
  `tests/test_birth_shaper.py` (hashes en el asiento del
  REGISTRO).

— Resultado del revisor con reclamos nativos del contrato,
2026-10-22. Gasto: **US$0**.
