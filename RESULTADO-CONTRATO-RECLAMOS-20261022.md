# Resultado — Contrato de reclamos: normalizador + pipeline compuesto sobre el corpus A (2026-10-22)

**Encargo:** diseñar el contrato que un hallazgo debe cumplir
al nacer para ser verificable por una puerta determinista
(`PREREGISTRO-CONTRATO-RECLAMOS.md`, escrito ANTES que el
código, con la vara de su §5 declarada), construir el
normalizador determinista (`agent/claim_contract.py`) y medir
el pipeline compuesto **normalizador → puerta 1.5.0 sin
modificar** sobre el corpus A. **Costo: US$0** — sin llamadas
a modelos, sin portal, sin publicación. Autorización:
Alejandro, 22/10/2026 («Dale, diseñá el contrato de reclamos
(US$0)»).

## 0. Veredicto — la vara de la §5: **NO PASA**

| Componente | Vara | Medido | Estado |
|---|---|---|---|
| (1) Conformidad (reporte) | reportar conteos | **49/166** conformes; de los 133 en espera, **17 salen** | reportado (§2) |
| (2) `needs_validation` del pipeline | < 50 % | **70,5 %** (117/166) | **NO PASA** |
| (3) Precisión entre emitidos / TP emitidos | ≥ 53,6 % y > 19 | **53,1 %** (26/49); **TP 26**; recall distintos **5,11 %** | **NO PASA** (la precisión; el conteo de TP pasa) |
| (4) Discriminación (reporte) | reportar los dos números | muerte FP **75,0 %** (6/8) vs muerte TP **70,8 %** (63/89) | reportado (§4) |
| (5) Integridad (validez) | cero evidencia inventada | **0 violaciones / 166 auditados** | **PASA** |

**El relato en una línea:** el normalizador rescató sin
inventar nada todo lo rescatable del corpus — 17 reclamos que
la 1.5.0 dejaba en la sala por no declarar patrón salen y se
emiten — pero el pipeline compuesto sigue dejando el 70,5 %
en espera (la vara pedía < 50 %) y la precisión entre
emitidos cae a 53,1 %, medio punto bajo la vara, porque los
rescatados son más sucios que los nacidos conformes. Ningún
ajuste de vara, contrato o normalizador se hizo después de
ver el número; cualquier ajuste es una iteración posterior
declarada (§5 del pre-registro).

## 1. El arnés (idéntico a los anteriores)

Mismo corpus A (los 166 hallazgos de la base nº 298 de
`adjwork298/run298/prs/*/findings.json`, con sus veredictos
de `adjwork298/decisions.json`), misma reconstrucción de
candidatos con la fórmula del revisor (evidencia desde el
head sobre los clones, diffs regenerados de la autopsia):
**166/166 reconstruidos sin errores**. Controles de sanidad
del propio arnés: la corrida base (la 1.5.0 sola sobre los
candidatos nacidos) **reproduce exactamente los estados del
replay de la 1.5.0** (32/133/1 y sus blockers); el pipeline
compuesto es **invariante** entre las dos asignaciones
extremas de categoría general (todas `correctness`; rotación
por las nueve), como en los replay anteriores. Disposiciones
por PR asentadas en `/tmp/replay_contrato/ledgers/`.

## 2. Conformidad (componente 1) — por blocker original

**Conformes tras la normalización: 49/166 (29,5 %)** — 32
tal como nacieron (origen `born`: su patrón declarado ya
estaba entero en su evidencia) y **17 por minado** (origen
`mined`). No conformes: **117** — 63 por
`tokens_afirmados_ausentes_en_la_evidencia` y 54 por
`sin_patron_concreto_en_el_reclamo`, ahora como códigos de la
etapa de contrato.

**De los 133 que la 1.5.0 sola dejó en espera: 17 quedan
conformes y los 17 se emiten** — salen de la espera por la
vía del minado, todos del blocker `sin_patron`:

| Blocker primario (1.5.0 sola) | n | Conformes | Emitidos por el pipeline | Siguen en espera | Rechazados |
|---|---:|---:|---:|---:|---:|
| `sin_patron_concreto_en_el_reclamo` | 71 | **17** | **17** | 54 | 0 |
| `tokens_afirmados_ausentes_en_la_evidencia` | 62 | 0 | 0 | 62 | 0 |

Los 62 de tokens ausentes son **no normalizables por
diseño**: el reclamo afirma lo que su propia cita no
contiene, y rescatarlo exigiría recortar su patrón o
inventar su evidencia — las dos cosas que la cláusula de
integridad prohíbe. Su no-conformidad es la medición: el
37,3 % del corpus nace afirmando fuera de su cita. Los 54
restantes de `sin_patron` no cargan en su prosa ningún token
con forma de código que esté en su evidencia (o el único
candidato está gobernado por una marca de ausencia): tampoco
hay nada que extraer sin inventar.

Nota de composición: los no conformes por tokens son 63, no
62 — el reclamo extra es el TP de Mcp-Docker que la 1.5.0
sola rechazaba en firme por contradicción afirmativa (G3):
también afirma un token ausente de su evidencia, así que en
el pipeline compuesto queda retenido en la etapa de contrato
y nunca llega a la puerta. **El pipeline no rechaza a nadie
en firme: 0 rechazos** (la 1.5.0 sola: 1).

## 3. El pipeline compuesto contra la 1.5.0 sola

| Destino | 1.5.0 sola | Pipeline compuesto |
|---|---:|---:|
| Emitido | 32 (19,3 %) | **49 (29,5 %)** |
| En espera | 133 (80,1 %) | **117 (70,5 %)** — contrato 117, puerta 0 |
| Rechazado firme | 1 (0,6 %) | **0** |

| Gold | Emitido | En espera | Total |
|---|---:|---:|---:|
| TP (verdadero) | **26** | 63 | 89 |
| FPG (falso confirmado) | 2 | 6 | 8 |
| GREY (zona gris) | 3 | 14 | 17 |
| NOVEL (sin veredicto) | 18 | 34 | 52 |

Dato estructural del pipeline: de los 49 conformes que
entraron a la puerta, la 1.5.0 emitió **49/49** (0 retenidos,
0 rechazados en la etapa de puerta sobre este corpus). Con
el reclamo en forma de contrato, la regla de grounding de
la 1.5.0 no retiene a nadie: **el cuello completo del
pipeline compuesto quedó en el nacimiento** — 117/166
reclamos nacen fuera del contrato y no son normalizables
sin inventar.

**El intercambio medido de los 17 rescatados:** precisión
entre emitidos 59,4 % (19/32, solo nacidos conformes) →
53,1 % (26/49): los minados emiten a 41,2 % de precisión
(7 TP / 17), más sucios que los nacidos conformes, y su
entrada baja el promedio medio punto bajo la vara del
53,6 % — al mismo tiempo que sube los TP emitidos de 19 a
26 y el recall de TP gold distintos de 3,12 % (11/352) a
**5,11 % (18/352)**. Las dos lecturas son ciertas a la vez y
quedan asentadas juntas: el rescate compra cobertura real a
costa de la pureza que la vara fijó.

## 4. Discriminación e integridad (componentes 4 y 5)

**Discriminación (sin umbral, los dos números):**

- Tasa de muerte de los FP gold-confirmados: **6/8 = 75,0 %**
  (6 retenidos en contrato, 0 rechazados, 2 emitidos).
- Tasa de muerte de los TP: **63/89 = 70,8 %** (63 retenidos
  en contrato, 0 rechazados, 26 emitidos).

Por primera vez en la línea la tasa de muerte de los
verdaderos queda **por debajo** de la de los falsos
confirmados (la 1.5.0 sola: FP 75,0 % vs TP 78,7 %; la
1.4.1: 100 % para ambos en la vía general). La brecha es de
4,2 puntos sobre conjuntos chicos (8 FP) y se reporta tal
cual, sin umbral: el contrato no separa verdadero de falso —
nada determinista sobre esta evidencia lo hace — pero su
conformidad ya no es ciega al gold: conformar es levemente
más probable para un reclamo verdadero (26/89 = 29,2 %) que
para uno falso confirmado (2/8 = 25,0 %).

**Integridad (componente 5 — condición de validez):**
auditoría programática sobre los 166 candidatos del
pipeline: evidencia alterada **0**, cita alterada (archivo,
rango o tipo) **0**, token afirmado por el pipeline que no
ocurra en el mensaje nacido **0**, token afirmado que no
ocurra en la evidencia citada **0**. Cero evidencia
inventada: la medición vale bajo su propia cláusula. Los 63
no conformes por tokens ausentes son la contraparte
positiva de esta auditoría: la señal quedó contada, no
tapada.

## 5. Verificación de la construcción

- **Suite completa: 272/272 OK** (262 previas + 10 nuevas de
  `tests/test_claim_contract.py`: nacido conforme es
  identidad, tokens ausentes no conformes y no recortados,
  sin patrón no conforme, minado conforme y aceptado por la
  1.5.0 sin modificar, token gobernado por ausencia jamás
  minado, literal entre comillas minable, clases intactas,
  hashes congelados). La batería semáforo 16/16 corre dentro
  de la suite, sin regresiones.
- **Puertas congeladas byte-idénticas** (sha256 de archivo,
  antes = después): 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`,
  1.2.0 `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0 `b16c5a79…`,
  1.4.1 `08d813e9…`.
- **La 1.5.0, sin modificar:** `agent/alma_gate_v150.py`,
  sha256 de archivo `71b1996b…` antes = después (la aserta
  también un test nuevo); POLICY_SHA256
  `16befdd1c71d84ad83b54b857fc3ed2260c6c881a32f7498b70437b3f861654c`.
- **El normalizador:** `agent/claim_contract.py`, sha256
  `7df8abc77ec1cec46222bd276b739b0d23be4671882e2d96323d11818268f0f8`,
  versión `alma-claim-contract/1.0`. Consume la tokenización
  de la 1.5.0 por importación, sin tocarla.

## 6. Lo que este resultado NO decide

- **Ninguna adopción:** el pipeline compuesto no pasa la
  vara de la §5 y queda asentado así; el contrato como
  especificación de nacimiento (pre-registro §2, incluida la
  sección del productor) queda como diseño medido en su
  forma normalizable, no como formato adoptado del revisor.
- **El revisor no se reconstruyó:** cuántos reclamos nativos
  del contrato rendiría un revisor futuro es una pregunta
  que este corpus no puede responder — acá se midió cuánto
  del corpus YA nacido entra en el contrato sin inventar
  (49/166), y dónde se concentra lo que no entra (63
  afirmando fuera de su cita, 54 sin patrón extraíble).
- La pregunta abierta de la salida de `needs_validation` en
  producción (papel 150 §5) sigue abierta y es de
  Alejandro; este resultado le pone el número compuesto:
  con contrato, la sala sería 117/166 sobre este corpus, y
  su composición ya no es un blocker genérico sino dos
  poblaciones con nombre propio.
- Como todo replay de esta línea: vale para el corpus A
  (revisor 2.3.1, práctica nº 298) y no afirma nada sobre
  otra corrida ni otro examen.

— Resultado del contrato de reclamos, 2026-10-22. Insumos:
`PREREGISTRO-CONTRATO-RECLAMOS.md`,
`RESULTADO-REPLAY-150-20261022.md`, arnés y ledgers en
`/tmp/replay_contrato/`. Gasto: **US$0**.
