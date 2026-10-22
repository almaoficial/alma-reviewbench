# Resultado — Replay de la puerta 1.5.0 sobre el corpus A (2026-10-22)

**Encargo:** construir la puerta 1.5.0 pre-registrada en
`PREREGISTRO-PUERTA-150.md` (la vara de su §4 declarada ANTES del
código) y medirla con el replay local idéntico al de la autopsia
de la 1.4.1. **Costo: US$0** — sin llamadas a modelos, sin
portal, sin publicación. Autorización: Alejandro, 22/10/2026
(«Bueno lo hagamos»), Paso 2 del plan de mejora de ALMA.

## 0. Veredicto — la vara de la §4: **NO PASA**

| Componente | Vara | Medido | Estado |
|---|---|---|---|
| (1) Emisiones y TP emitidos | > 0 y > 0 | **32 emisiones, 19 TP** | **PASA** |
| (2) Precisión entre emitidos / recall de TP distintos | ≥ 53,6 % y > 0 (excelencia ≥ 58,6 %) | **59,4 %** (19/32); **3,12 %** (11/352) | **PASA** (en banda de excelencia) |
| (3) Fracción en `needs_validation` | < 50 % | **80,1 %** (133/166) | **NO PASA** |
| (4) Candidatos perdidos sin razón registrada | 0 | **0** (166/166 con disposición y razón) | **PASA** |
| (5) Discriminación (reporte, sin umbral) | reportar los dos números | muerte FP **75,0 %** (6/8) vs muerte TP **78,7 %** (70/89) | reportado (§4) |

**El relato en una línea:** la regla nueva repara lo que la
autopsia midió — la puerta emite por primera vez sobre la vía
general (32 emisiones, 19 verdaderas, precisión sobre la base y
en la banda de excelencia declarada) y el ancla head/diff
elimina las 17 muertes por artefacto — pero la sala de espera
sigue llevándose el 80,1 % de los candidatos, por encima del
50 % que la vara fijó: con un componente caído, **la 1.5.0 no es
adoptable bajo este papel** (§7 del pre-registro). Ningún ajuste
de vara ni de diseño se hizo después de ver el número; cualquier
ajuste es una versión o un papel posterior.

## 1. El arnés (idéntico al de la autopsia)

Mismo corpus A (los 166 hallazgos de la base nº 298 de
`adjwork298/run298/prs/*/findings.json`), misma reconstrucción
de candidatos con la fórmula del revisor (evidencia desde
`git show <head>:<archivo>` sobre los clones; diffs regenerados
de la autopsia, 8/8 byte-idénticos a la tabla de la sonda):
**166/166 reconstruidos sin errores**. La categoría general
individual no es atribuible desde los outputs (supuesto de la
autopsia); el replay corrió con dos asignaciones extremas
(todas `correctness`; rotación por las 9 categorías) y los
vectores de veredicto y de blockers salieron **idénticos** —
invarianza probada también para la 1.5.0, por construcción (la
regla es uniforme entre categorías). Ledger prendido: una
disposición por candidato, asentada por PR (`/tmp/replay150/
ledgers/`), con razones o blockers en los 166 casos.

**Sanidad de la delegación de clases:** el único candidato de
clase identificable de la nº 311 (`tarfile_unsafe_extract`,
DisciplinedSoftware) el replay de la 1.5.0 lo **acepta**, con la
misma razón de soporte que la 1.4.1 — el arnés reproduce la
única emisión real de la corrida y la delegación no altera el
camino de clase.

## 2. Tabla por destino y por razón (corpus A, n = 166)

| Veredicto de la 1.5.0 | n | % |
|---|---:|---:|
| Aceptado (emitido) | **32** | 19,3 % |
| `needs_validation` (retenido) | **133** | 80,1 % |
| Rechazado firme | **1** | 0,6 % |

**Retenidos por blocker primario** (cada retenido tiene un
blocker primario; `no_added_line` aparece solo como blocker
adicional, en 15):

| Blocker | n |
|---|---:|
| `tokens_afirmados_ausentes_en_la_evidencia` | 62 |
| `sin_patron_concreto_en_el_reclamo` | 71 |
| `no_added_line` (adicional, nunca primario) | 15 |

Es decir: de los 133 retenidos, 71 son reclamos cuyo mensaje no
afirma ningún token de código contrastable, y 62 afirman tokens
que sus propias líneas citadas no contienen. Son propiedades
medidas de cómo el revisor escribe sus mensajes frente a lo que
una puerta determinista puede contrastar sin un modelo — se
asientan como composición del resultado, no como ajuste.

**El único rechazo firme del corpus:** Mcp-Docker #29, emisión
1, `services/copilot-review-mcp/internal/auth/handler.go:130-133`
— un **TP** muerto por contradicción afirmativa sobre el token
`code`: el reclamo lo declara ausente (gobernado por marca de
ausencia) y la evidencia contiene la subcadena `code`, como
contiene casi todo archivo fuente. La familia de contradicción
funciona mecánicamente como se diseñó, y su primer muerto real
es un verdadero por un token demasiado genérico: debilidad del
diseño asentada con su recibo, sin corrección en esta tarea
(una corrección sería una versión posterior).

## 3. Cruce con el gold y con la 1.4.1

**Veredicto de la puerta × veredicto gold** (adjudicación de la
298: 89 TP, 8 FP gold, 17 zona gris, 52 novedosos):

| Gold | Aceptado | Retenido | Rechazado | Total |
|---|---:|---:|---:|---:|
| TP (verdadero) | 19 | 69 | 1 | 89 |
| FPG (falso confirmado) | 2 | 6 | 0 | 8 |
| GREY (zona gris) | 2 | 15 | 0 | 17 |
| NOVEL (sin veredicto) | 9 | 43 | 0 | 52 |

Precisión entre emitidos = 19 TP / 32 = **59,4 %** (la base sin
puerta: 53,6 %; la vara pedía ≥ 53,6 % y declaraba excelencia
en ≥ 58,6 %). Recall de TP gold distintos = 11/352 = **3,12 %**
(la base: 66/352 = 18,75 %): pasa el «> 0» de la vara y queda
muy por debajo de la base, porque 69 TP siguen retenidos. El
intercambio medido de la 1.5.0 es: **algo más de pureza en lo
emitido, a costa de la mayor parte de la cobertura** — la
contracara exacta de la 1.4.1, que no emitía nada.

**Destino bajo la 1.4.1 × destino bajo la 1.5.0:**

| 1.4.1 ↓ / 1.5.0 → | Aceptado | Retenido | Rechazado |
|---|---:|---:|---:|
| Retenido (149) | 31 | 117 | 1 |
| Rechazado por ancla (17) | 1 | 16 | 0 |

Las 17 muertes por ancla desaparecen como causa: ninguno de
los 17 vuelve a morir por ancla (1 se emite, 16 quedan en la
sala por las razones nuevas, específicas). De los 149 que la
1.4.1 retenía con el blocker genérico, 31 se emiten y 117
siguen retenidos — ahora cada uno con su código de razón
propio (§2), que es lo que el componente (4) y el diseño
pedían.

## 4. Discriminación (componente 5, sin umbral)

- **Tasa de muerte de los FP gold-confirmados: 6/8 = 75,0 %**
  (6 retenidos, 0 rechazados firmes, 2 emitidos).
- **Tasa de muerte de los TP: 70/89 = 78,7 %** (69 retenidos,
  1 rechazado firme).

Los dos números, tal cual: en tasa de muerte la puerta nueva
**prácticamente no discrimina** (mata verdaderos a una tasa
levemente MAYOR que falsos confirmados). La pureza del subconjunto
emitido (59,4 % contra el 53,6 % del flujo crudo) coexiste con
esa paridad: la ganancia de precisión viene de qué reclamos son
verificables contra su cita, no de una separación verdadero/falso
— exactamente el límite que el diseño declaró (grounding
determinista, no juicio de verdad).

## 5. Verificación de la construcción

- **Suite completa: 262/262 OK** (249 previas + 13 nuevas de
  `tests/test_gate_v150.py`: regla general acepta/rechaza/retiene
  con sus códigos, la reparación del ancla contrastada contra la
  1.4.1 sobre el mismo candidato, equivalencia de veredictos de
  clase por delegación, registro sin severidad, duplicados,
  hashes congelados). La batería semáforo 16/16 corre dentro de
  la suite, sin regresiones.
- **Puertas congeladas byte-idénticas** (sha256 de archivo,
  antes = después): 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`,
  1.2.0 `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0 `b16c5a79…`,
  1.4.1 `08d813e9…`. POLICY de la 1.4.1 recomputada:
  `73a403d8…`, intacta.
- **La 1.5.0:** `agent/alma_gate_v150.py`, POLICY_VERSION
  `alma-evidence-gate/1.5.0`, POLICY_SHA256
  `16befdd1c71d84ad83b54b857fc3ed2260c6c881a32f7498b70437b3f861654c`.
  Las 19 clases se validan por delegación a `AlmaGateV141`
  intacta (verificado por test de equivalencia y por la
  sanidad del tarfile de la 311, §1).

## 6. Lo que este resultado NO decide

- **La salida de `needs_validation` en producción** sigue
  abierta (pre-registro §5: emisión marcada, validación
  posterior o descarte declarado, con sus costos): es decisión
  de Alejandro. Con el 80,1 % medido, la opción (b) cargaría
  ~133 reclamos por corrida de este tamaño y la (a) convertiría
  la sala en la emisión mayoritaria: los costos escritos en el
  pre-registro ahora tienen el número puesto.
- **Ningún montaje:** la 1.5.0 no está en ninguna imagen ni
  config; la persistencia del ledger en el portal quedó
  diseñada (pre-registro §6), no construida. Cualquier corrida
  futura exige su propio pre-registro, su compuerta y su «sí».
- El NO PASA es de ESTA vara sobre ESTE corpus: no afirma que
  la regla de grounding sea inútil — de hecho es la primera
  puerta de la línea que emite sobre la vía general con
  precisión sobre la base —; afirma que, con la vara que se
  declaró antes de construir, no alcanza para adoptarla.

— Resultado del replay de la puerta 1.5.0, 2026-10-22. Insumos:
`PREREGISTRO-PUERTA-150.md`, `REPLAY-PUERTA-141-20261022.md`,
`ADJUDICACION-COMPLETA-311-20261022.md`, arnés y ledgers en
`/tmp/replay150/`. Gasto: **US$0**.
