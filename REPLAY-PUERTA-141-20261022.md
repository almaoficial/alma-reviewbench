# Replay offline de la puerta 1.4.1 — por qué pasó 1 de ≤165 en la nº 311 (2026-10-22)

**Encargo:** responder con recibos por qué la puerta 1.4.1 dejó pasar
1 de ≤165 candidatos en la práctica ALMA nº 311, y falsar o confirmar
la hipótesis del dialecto: «los reclamos reales del revisor no citan
la evidencia en el dialecto que los chequeos causales de la puerta
exigen, y por eso casi todo rebota en el control de evidencia».
**Costo: US$0** — solo archivos locales y clones públicos; sin
llamadas a modelos, sin portal, sin publicación. La puerta
(`agent/alma_gate_v141.py`, POLICY `73a403d8…`) se leyó y se ejecutó;
no se modificó (congelada).

## 1. Arnés y supuestos declarados

**Corpus A (el que responde):** los 166 hallazgos finales de la base
nº 298 (`adjwork298/run298/prs/*/findings.json`). En el brazo base la
puerta se saltea y los hallazgos SON los candidatos del revisor
(identidad 1:1 asentada en la adjudicación de la 298). Es el corpus
perfecto para la pregunta: los mismos reclamos que sin puerta
rindieron P 53,6 % / R 18,75 %, alimentados a la 1.4.1 en local.

**Reconstrucción de candidatos (fidelidad verificada):** el revisor
v2.3 construye cada `Candidate` mecánicamente
(`agent/llm_reviewer_v23.py`, `_to_candidate_v23`):
`rule_id = llm_v23_<claim_type>`, `evidence_text` = las líneas del
archivo en el **head** citadas, ancladas contra el archivo completo.
El arnés reconstruyó cada candidato con esa misma fórmula:
evidencia desde `git show <head>:<archivo>` sobre los clones, y los
diffs regenerados con el procedimiento de la sonda
(`git diff base...head`, SHAs de `corpus/test/test.json`).

- Diffs: 25/25 regenerados; **8/8 coinciden byte a byte** con los
  asentados en `RESULTADO-SONDA-V231-20261021.md` (la primera pasada
  corrompió CRLF por captura en modo texto; se regeneró en binario y
  la tabla cerró exacta).
- Reconstrucción: **166/166 candidatos sin un solo error** — toda la
  evidencia citada se recuperó del head y coincide con la que el
  revisor almacenó (condición que el propio revisor verificó al
  construirlos: 0 sin ancla en la corrida).
- **Supuesto de traducción 1 — la categoría general individual no
  es atribuible** desde los outputs (los `findings.json` no guardan
  `claim_type`; la adjudicación de la 298 atribuyó las 166 emisiones
  a la vía general por ruta y contenido: especialidad ejecutó 1
  pasada en 25 PRs con 0 emisiones). **Invarianza probada:** el
  replay se corrió dos veces con asignaciones extremas de categoría
  (las 166 como `correctness`; las 166 rotando por las 9 categorías
  generales) y los vectores de veredicto y de causa de muerte
  salieron **idénticos** — por construcción de la puerta, que trata
  a las 9 categorías con la misma regla (ninguna). La atribución no
  mueve ningún número de este informe.
- **Supuesto de traducción 2 — sensibilidad CrabTrap:** las 4
  emisiones de CrabTrap son las únicas que podrían haber nacido de
  la pasada de especialidad ejecutada (`sql_injection`). Re-juzgadas
  como candidatos de clase `sql_injection`, **mueren igual**: 2 por
  ancla fuera del diff y 2 por soporte (sin co-ocurrencia esqueleto
  SQL + construcción insegura en la línea citada). La ambigüedad de
  atribución no cambia ningún veredicto del corpus.
- El ledger local quedó activado en el arnés: cada decisión se
  asentó por PR con su estado, sus razones y sus blockers (el
  artefacto que el montaje del portal no persistió en la 311).

## 2. Corpus A — qué les habría hecho la puerta a los 166 de la base

| Veredicto de la 1.4.1 | n | % |
|---|---:|---:|
| Aceptado (emitido) | **0** | 0,0 % |
| `needs_validation` (retenido) | **149** | 89,8 % |
| Rechazado firme | **17** | 10,2 % |

**Los 149 retenidos** comparten un único blocker:
`sin_regla_de_verificacion_en_puerta` (149/149) — la puerta no
define regla de verificación para las categorías generales, y por
diseño un reclamo general bien formado y anclado se retiene, nunca
se emite. Solo 2 de los 149 cargan además el blocker
`no_added_line`. Es decir: 147 reclamos con cita anclada, evidencia
exacta y al menos una línea agregada por el cambio **tampoco pueden
pasar**: su techo en esta puerta es la sala de espera.

**Los 17 rechazados firmes** mueren todos por la misma causa
primaria: **ancla fuera del diff** — al menos una línea citada no
está presente en los hunks del diff (17/17; la razón concurrente
«la evidencia no coincide exactamente» aparece en los 17 como
consecuencia aritmética de la línea ausente). Ningún otro chequeo
mató a nadie en el corpus de producción:

| Chequeo causal | Muertes (causa primaria) |
|---|---:|
| (f) sin línea agregada por el cambio | 0 |
| Soporte de clase (marca/construcción/antídoto) | 0 |
| Duplicado de un aceptado | 0 |
| Rango inválido / clase desconocida | 0 |

El detalle de los 17 (PR, emisión, gold, líneas fuera del diff):
AY2526S2 #7 TP ×1, #8 NOVEL ×1, #9 TP ×1, #10 NOVEL ×1 (todos
`docs/UserGuide.md`, 1 línea); NCATSTranslator #10 NOVEL (7 líneas),
#11 TP (3); TechDebtMCP #1 GREY (1); gimmes #1 NOVEL (3); CrabTrap
#0 TP (2), #1 TP (4); node-postgres #0 TP (1); LANdalf #0 TP (1),
#1 TP (1); agents-config #0 NOVEL (1), #1 NOVEL (1), #4 TP (5);
wirechat #8 NOVEL (3). Ancho de cita del corpus: mediana 4 líneas,
máximo 17 — el revisor cita rangos de función; la puerta exige que
**cada** línea citada viva dentro de un hunk del diff. El revisor
ancla contra el archivo head completo (y su evidencia coincide con
el archivo, 166/166); la puerta ancla contra el diff. Son dos
anclas distintas, no dos calidades de cita.

Por PR, el patrón es uniforme: aceptados 0 en los 25 PRs (emdash,
el caso extremo del §8, ya emitía 0 sin puerta). Los PR con más
rechazos por ancla: AY2526S2 (4/12), agents-config (3/7), LANdalf
(2/3), CrabTrap (2/4), NCATSTranslator (2/19).

## 3. Cruce con el gold — a quién mata la puerta (corpus A)

Veredictos de la adjudicación completa de la 298 (`decisions.json`:
89 TP, 8 sobre FP gold, 17 zona gris, 52 novedosos) cruzados con el
veredicto de la puerta:

| Gold | Aceptado | Retenido | Rechazado | Total |
|---|---:|---:|---:|---:|
| TP (verdadero) | 0 | 80 | 9 | 89 |
| FPG (falso confirmado) | 0 | 8 | 0 | 8 |
| GREY (zona gris) | 0 | 16 | 1 | 17 |
| NOVEL (sin veredicto) | 0 | 45 | 7 | 52 |

- **TP-kill rate: 89/89 emisiones verdaderas no emitidas (100 %)** —
  80 retenidas por falta de regla y 9 rechazadas por ancla. La
  cobertura tras la puerta es **0 de los 66 TP gold distintos** que
  la base cubrió: el recall grounded pasa de 18,75 % a **0,00 %**, y
  con 0 emisiones la precisión queda sin definir (0/0). Es, número
  por número, la misma foto que la nº 311 mostró en vivo.
- **De los 66 TP gold distintos:** los retenidos cubren 59; los 7
  restantes solo los cubrían emisiones que la puerta rechaza por
  ancla. Ni siquiera la sala de espera conserva la cobertura
  completa.
- **FP-kill: los 8 falsos confirmados tampoco se emiten (8/8)** —
  pero la puerta no rechaza afirmativamente a **ninguno**: los 8
  quedan retenidos por la misma falta de regla que retiene a los 80
  TP. En la vía general la puerta no discrimina: no tiene
  instrumento para declarar falso un reclamo general, solo para
  declararlo no verificable por ella. Verdaderos y falsos comparten
  destino y razón.

## 4. Corpus B (nº 311) — no replayable con identidad; la estructura

Los candidatos pre-puerta de la 311 **no son recuperables con
identidad** desde los archivos: el zip del portal (58 archivos)
trae, por PR, solo el run-info agregado y los hallazgos finales; el
ledger de la puerta no se persistió en el montaje (defecto de
observabilidad asentado en la adjudicación de la 311). Sin archivo,
línea ni mensaje por candidato no hay replay fiel posible, y no se
inventó. Lo que el registro sí permite afirmar:

- 169 crudos, 0 malformados, 4 sin ancla → **165 candidatos** ante
  la puerta (idéntico al ≤165 de la adjudicación).
- Pasadas de especialidad **ejecutadas en solo 2 de 25 PRs**:
  `tarfile_unsafe_extract` (DisciplinedSoftware) y `sql_injection`
  (chronicle). En los otros 23 PRs **solo corrieron pasadas
  generales**: por la construcción medida en el corpus A, todo
  candidato de pasada general tiene por techo `needs_validation`.
- **Sanidad del arnés:** el único candidato de clase identificable
  de la 311 — el hallazgo emitido, `tarfile_unsafe_extract` en
  `fortran_to_rust/fetcher.py:85`, reconstruido con el mismo
  procedimiento — el replay lo **acepta**, con la misma razón de
  soporte asentada («tar extraction via .extractall( without
  filter=»). El arnés reproduce la única emisión real de la corrida.

## 5. Contrafactual declarado — «no verificable en el formato» a `needs_validation`

Definición operativa (declarada antes de mirar el resultado):
pasan a `needs_validation` los rechazos cuya causa primaria es
**evidencia no verificable contra el artefacto diff** — ancla fuera
del diff y evidencia que no coincide exactamente. Quedan firmes los
rechazos **afirmativamente falsos** (antídoto presente, placeholder,
forma segura, marca ausente con refutación — el territorio del
chequeo de soporte) y el causal (f). En el corpus A no hay ningún
rechazo de soporte ni por (f), así que la definición se aplica sobre
lo que hay:

- Rechazados que convierten: **17/17**. Rechazos firmes restantes:
  **0**.
- **Lectura (i) — emisión estricta (solo aceptados emiten): no
  cambia nada.** `needs_validation` no emite por diseño, así que el
  par tras la puerta queda idéntico: 0 emisiones, precisión sin
  definir, **R = 0/352 = 0,00 %**. El contrafactual de ruteo, solo,
  no rescata recall: mueve el cadáver de carpeta.
- **Lectura (ii) — salida útil del pipeline (aceptados + retenidos +
  convertidos, es decir lo que un validador humano recibiría):**
  166 reclamos, con **P = 89/166 = 53,6 %** y **R = 66/352 =
  18,75 %** — **exactamente el par de la base sin puerta**. Y los 8
  falsos confirmados también están en la salida útil (8/8): bajo
  cualquiera de los dos ruteos, **la puerta aporta discriminación
  cero sobre la vía general** — ni con el ruteo vigente ni con el
  contrafactual separa un solo verdadero de un solo falso.

## 6. Veredicto sobre la hipótesis del dialecto

**REFUTADA como causa dominante.** La descomposición de la muerte
de los 166 reclamos de producción es:

1. **Causa dominante — estructural, no de dialecto (149/166 =
   89,8 %):** la puerta 1.4.1 no define regla de verificación para
   las categorías generales del revisor v2.3; todo reclamo general,
   cite como cite — incluso con ancla perfecta, evidencia exacta y
   línea agregada — tiene por techo `needs_validation`. La puerta
   solo puede emitir reclamos de sus 19 clases; la producción del
   revisor v2.3 (camino A del papel) es de vía general. Las dos
   mitades nunca fueron compatibles: la ruta que produce los
   verdaderos es exactamente la ruta que la puerta no puede emitir.
2. **Causa secundaria — sí es formato, pero entre artefactos
   (17/166 = 10,2 %):** el revisor ancla las citas al archivo head
   completo y la puerta al diff (solo líneas dentro de hunks). La
   evidencia de esos 17 coincide exactamente con el archivo — no es
   que citen mal; citan contra otro artefacto. Es un desajuste de
   dialecto de anclaje, no del dialecto evidencial de clase.
3. **El dialecto evidencial de clase — el de la hipótesis — mató
   a cero reclamos medibles:** el corpus de producción no contiene
   un solo candidato de clase (0/166), los 4 de la sensibilidad
   CrabTrap mueren por ancla o por no ser reclamos SQL en absoluto,
   y el único candidato de clase genuino recuperable (el tarfile de
   la 311, n=1) **pasó** su chequeo de evidencia. La puerta se
   calibró en el semáforo con reclamos de clase escritos en su
   propio formato; ese universo no es el que el revisor produce.

**Respuesta a la pregunta del encargo, en una línea:** la puerta
dejó pasar 1 de ≤165 no porque los reclamos reales citen la
evidencia en el dialecto equivocado, sino porque solo puede emitir
reclamos de 19 clases con evidencia mecánica completa, y el revisor
v2.3 casi no produce esos reclamos — produce reclamos generales,
para los que la puerta no tiene regla y cuyo destino máximo es la
sala de espera.

**Qué NO afirma este replay:** no mide el split interno de la 311
(impersistido por el montaje; el corpus A es producción del revisor
2.3.1 y la 311 corrió el 2.3.2, cuya delta — techo de selección y
admisión de la puerta — no altera la producción de candidatos en
clase); no juzga si una puerta CON regla para la vía general
filtraría bien (esa puerta no existe en los papeles vigentes); y no
reabre la línea v2.3, cerrada por la Adenda 3 §5: es una medición
sobre el artefacto congelado, a US$0.
