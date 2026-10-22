# Adjudicación completa de la práctica ALMA nº 311 (v2.3.2, puerta 1.4.1) — el efecto de la puerta y el veredicto de la regla de avance

**Fecha:** 2026-10-22 · **Costo de esta adjudicación: US$0** (sin portal,
sin corridas, sin llamadas a modelos; cotejo local contra el gold
público). **Objeto:** la corrida nº 311 (brazo ALMA, SUCCEEDED, 25/25
PRs, imagen v2.3.2, puerta 1.4.1, costo real US$20,27) contra el gold
público del benchmark (`review-bench/ReviewBench`: `golden/*.json` +
`corpus/test/findings.json`; 352 TP / 213 FP). **Instrumento:**
Adenda 3 §4 del pre-registro v2.3, conservada entera por la Adenda 4:
la regla de avance variante (ii) se evalúa sobre esta adjudicación.

## 0. Veredicto — regla de avance variante (ii): **NO PASA**

| Componente | Vara | Medido | Estado |
|---|---|---|---|
| Precisión grounded de ALMA | ≥ 58,6 % | **0/1 = 0,0 %** (n=1) | **NO PASA** |
| Pureza de la retención | ≤ 1 de cada 3 retenidos/rechazados era TP grounded | **no computable** — los retenidos no están identificados en los outputs (§4) | **SIN MEDIR (no acreditable)** |
| Pérdida inexplicada | = 0 | **66** TP gold que la base cubrió y ALMA no, sin asiento en ningún ledger entregado (§5) | **NO PASA (falsada)** |
| F1 grounded (reporte, no compuerta) | — | **0,0 %** (base: 27,8 %) | — |

**El relato en una línea:** el revisor de la 311 produjo 169 hallazgos
crudos (≤165 candidatos ante la puerta tras el anclaje); la puerta
1.4.1 dejó pasar **1** (0,6 %), y ese único sobreviviente **no es un
TP grounded** (zona gris, §2). El recall grounded de ALMA es
**0/352 = 0,00 %** contra el 18,75 % de la base. La puerta no filtró
ruido de una señal: sobre esta corrida suprimió el flujo de
candidatos casi entero, y el instrumento de medición que el papel
pre-registró (el ledger de la puerta) **no viajó en los outputs**,
así que la retención ni siquiera es auditable hallazgo por hallazgo
(§1 y §4). Sin maquillaje: con estos números la variante (ii) no se
sostiene por ningún componente.

## 1. Método, denominadores y el límite del instrumento

El método de la casa, idéntico al de las adjudicaciones de la 296 y
la 298: match grounded = mismo archivo + región que cubre la línea
del defecto + **el mismo defecto/mecanismo**; una emisión, un TP
primario como máximo; TP gold gemelos se acreditan una vez; FPG =
mismo archivo y mismo reclamo que un FP gold; **zona gris** = mismo
archivo y territorio, mecanismo distinto, dudoso o no cerrable con
el estándar; **novedoso** = sin contraparte en el gold (esta
adjudicación no lo juzga). Precisión sobre emisiones; recall sobre
TP gold distintos cubiertos; todo micro.

**Contabilidad de candidatos (desde los run-info de la propia
corrida, `prs/*/agent.log`):** el revisor v2.3 cuenta
`raw_findings` al extraer, descarta malformados (forma) y sin ancla
(evidencia que no coincide con el head) **antes** de la puerta, y
deduplica entre pasadas con una clave (archivo, líneas, tipo de
reclamo, mensaje) **sin contar los descartes por duplicado**. Por
eso los candidatos que efectivamente llegaron a la puerta son
**≤ 165** (= 169 crudos − 0 malformados − 4 sin ancla, menos los
duplicados entre pasadas que el run-info no cuenta; en la base
nº 298 la identidad cerró exacta: 168 − 2 = 166 emitidos, duplicados
= 0). Las cotas de este informe usan 165 como techo declarado.

**El límite del instrumento (hallazgo de esta adjudicación):** el
ledger de la puerta — la decisión por candidato (aceptado /
`needs_validation` / rechazado, con su razón) — existe en el código
(`agent/main.py`: `gate.validate()` produce `ledger` y la sección
`needs_validation`), pero **solo se escribe a disco si
`ALMA_LEDGER_PATH` está fijado o `RB_ALMA_LEDGER=1`** (main.py,
líneas 466–479), y **no forma parte de los outputs que el portal
entrega**: el zip de la 311 trae 58 archivos — `findings.json` y
`agent.log` por PR, `summary.txt` y logs de shards — y ningún
`alma-ledger.json`. Consecuencia, declarada antes de los números:
el destino individual de cada candidato no emitido es
**irrecuperable desde el registro entregado**; solo existen su
conteo agregado (§3) y las emisiones finales. La §4.4 de la Adenda 3
pedía «aceptados / needs_validation / rechazados, por familia,
desde los run-info»: los run-info **no traen ese desglose** — ni el
split needs_validation/rechazado, ni candidatos por familia de vía
(solo las marcas de selección y las pasadas corridas, §3). Lo que
no está, se declara; no se reconstruye.

## 2. El único hallazgo emitido y su adjudicación

La corrida emitió exactamente **1 hallazgo final** (los otros 24 PRs,
0). Viene de `DisciplinedSoftware/Codebase-Conversion #1`:

- **Archivo/línea:** `fortran_to_rust/fetcher.py`, línea 85.
- **Clase (por el mecanismo del mensaje):** `tarfile_unsafe_extract`
  — vía de **especialidad** (la corrida de ese PR corrió las pasadas
  `correctness` y `tarfile_unsafe_extract`; el `findings.json` no
  trae `claim_type` ni productor por hallazgo, así que la clase se
  infiere del mensaje y de la disciplina de pasadas: en una pasada
  profunda el reclamo debe llevar el nombre de su marca).
- **Texto:** «The tar archive is extracted with extractall() without
  a filter= argument. The manual member-name check does not provide
  tarfile's full extraction protections, including handling of links
  and special files; use an appropriate extraction filter in this
  call.»

**Adjudicación por capas, contra el gold de ese PR (31 TP / 23 FP):**

1. **Capa exacta (archivo + línea + mecanismo): sin match.** El
   único TP gold que cubre la línea 85 es el de `fetcher.py:85-92`,
   pero su mecanismo es otro: tras extraer, `rglob('*.f')` recursa
   dentro del propio directorio caché y `shutil.copy2` sobre un
   archivo consigo mismo levanta `SameFileError`. No es la ausencia
   de `filter=` ni el manejo de links: **no es ese defecto**.
2. **Contra el FP gold del mismo territorio:** el gold juzgó FP un
   reclamo de extracción en `fetcher.py:94-99` (path traversal /
   Zip Slip): lo refutó porque el código llama `.resolve()` sobre
   la ruta del miembro y sobre `output_dir` antes de chequear, con
   lo que el bypass por `..` no existe. La emisión de la 311 **no
   repite ese reclamo**: concede que hay un chequeo manual de
   nombres y objeta otra cosa — que ese chequeo no cubre miembros
   link ni archivos especiales, que es exactamente lo que agrega
   `filter=` de tarfile. Reclamo distinto del FP juzgado: **no es
   FPG** con el estándar de la casa (mismo archivo + *mismo
   reclamo*).
3. **Veredicto: ZONA GRIS.** Mismo archivo, misma función
   (`_try_download_tarball`) y mismo territorio (seguridad de la
   extracción) que un reclamo ya juzgado, con un mecanismo que el
   gold **ni confirma ni refuta**: la justificación del FP solo
   establece que el chequeo por nombres resueltos derrota el
   traversal por `..`; no dice nada sobre miembros link. El reclamo
   no es cerrable con el estándar desde el gold. (La alternativa
   «novedoso» se descarta porque sí hay contraparte gold en el
   territorio; en cualquier caso, gris o novedoso, **no es TP** y el
   efecto sobre el veredicto es el mismo.)

**El par grounded de ALMA, con su n declarado a la vista:**

| Métrica grounded | Valor |
|---|---|
| Emisiones | **1** |
| Emisiones grounded en TP gold | **0 / 1** |
| TP gold distintos cubiertos | **0 / 352** |
| **Precisión grounded** | **0,0 %** (n=1: un par sobre una sola emisión es un número frágil — si esa emisión hubiera sido TP, la precisión sería 100 % con la misma fragilidad; lo que no es frágil es el denominador de recall) |
| **Recall grounded** | **0,00 %** |
| **F1 grounded** | **0,0 %** |
| Emisiones sobre FP gold / zona gris / novedosas | 0 / **1** / 0 |

Contra la vara: **0,0 % < 58,6 %** — el componente de precisión
**no pasa**, y no por el margen: el único hallazgo que la puerta
dejó salir del examen no acredita contra el gold.

## 3. La tabla de la puerta — conteos desde los run-info

Por PR: crudos del revisor (`raw_findings`), descartes previos a la
puerta (malformados / sin ancla), candidatos ante la puerta (cota
superior: crudos − descartes, antes de la deduplicación entre
pasadas que el run-info no cuenta), emitidos finales
(`findings.json`) y **no emitidos** (candidatos − emitidos: quedaron
del lado de la puerta, como `needs_validation` o rechazados — **el
split entre esos dos destinos no está registrado en los outputs**).

| PR | Crudos | Malf. | Sin ancla | Candidatos ≤ | Emitidos | No emitidos ≤ |
|---|---|---|---|---|---|---|
| AA-Factory aafactory-prototype #17 | 2 | 0 | 0 | 2 | 0 | 2 |
| AY2526S2-CS2103T-W14-3 tp #152 | 9 | 0 | 0 | 9 | 0 | 9 |
| DisciplinedSoftware Codebase-Conversion #1 | 7 | 0 | 0 | 7 | **1** | 6 |
| Marvell-Consulting statswales-frontend #626 | 2 | 0 | 0 | 2 | 0 | 2 |
| NCATSTranslator translator-ingests #336 | 19 | 0 | 0 | 19 | 0 | 19 |
| PaulStSmith figlet-comment-generator #32 | 18 | 0 | 1 | 17 | 0 | 17 |
| PierreJanineh TechDebtMCP #135 | 7 | 0 | 0 | 7 | 0 | 7 |
| allan-mobley-jr gimmes #468 | 4 | 0 | 0 | 4 | 0 | 4 |
| ardevd jadx-collaboration #3 | 4 | 0 | 0 | 4 | 0 | 4 |
| brexhq CrabTrap #15 | 7 | 0 | 0 | 7 | 0 | 7 |
| brianc node-postgres #3650 | 10 | 0 | 0 | 10 | 0 | 10 |
| cmik apilix #12 | 7 | 0 | 3 | 4 | 0 | 4 |
| gagneurlab PROTRIDER #10 | 5 | 0 | 0 | 5 | 0 | 5 |
| k1LoW gh-copilot-review #9 | 6 | 0 | 0 | 6 | 0 | 6 |
| konturio disaster-ninja-fe #1230 | 4 | 0 | 0 | 4 | 0 | 4 |
| mheuss chronicle #14 | 5 | 0 | 0 | 5 | 0 | 5 |
| renedierking LANdalf #88 | 3 | 0 | 0 | 3 | 0 | 3 |
| scotthamilton77 agents-config #1 | 6 | 0 | 0 | 6 | 0 | 6 |
| scottlz0310 Mcp-Docker #29 | 9 | 0 | 0 | 9 | 0 | 9 |
| sdsykes fastimage #165 | 8 | 0 | 0 | 8 | 0 | 8 |
| simnaut emdash #2 | 0 | 0 | 0 | 0 | 0 | 0 |
| superhighfives pika #200 | 13 | 0 | 0 | 13 | 0 | 13 |
| superyyrrzz ForgeMap #106 | 7 | 0 | 0 | 7 | 0 | 7 |
| vanyastaff nebula #224 | 2 | 0 | 0 | 2 | 0 | 2 |
| wirechat wirechat #183 | 5 | 0 | 0 | 5 | 0 | 5 |
| **Total** | **169** | **0** | **4** | **≤165** | **1** | **≤164** |

**Tasa de paso de la puerta: 1/≤165 = 0,6 %.** El volumen de
candidatos del revisor fue el de siempre (169 crudos vs 168 de la
base nº 298; tokens 3.536.690/137.857 vs 3.487.004/151.581): el
revisor trabajó y produjo como en la base — **el colapso está en
la puerta, no en el revisor**.

**Por familia de vía:** el desglose de candidatos por vía **no es
recuperable** de los run-info (no hay conteo por pasada; §1). Lo
único asentado por los registros: la selección marcó especialidad
en **3/25 PRs** (DisciplinedSoftware: `tarfile_unsafe_extract` +
`swallowed_exception`; chronicle: `sql_injection`; emdash:
`race_condition`) y pasadas profundas de especialidad corrieron en
**2/25** (la de tarfile en DisciplinedSoftware — de donde sale la
única emisión — y la de `sql_injection` en chronicle, cuya pasada
corrió y no dejó emisión alguna que pasara la puerta; la de emdash
quedó descartada por degradación). Todo lo demás que produjo
candidatos fue vía general. El desglose aceptados/needs_validation/
rechazados por familia que pedía la Adenda 3 §4.4 **no existe en el
registro** y se declara sin medir, no estimado.

**Costo (contexto):** costo real por diferencia de saldo
**US$20,27** (asentado en el cierre formal); el estimado interno
del revisor suma US$63,39 — sobreestima como en la base (US$63,67
estimados vs US$20,41 reales en la 298): la misma corrida de
revisor, el mismo gasto, con la puerta como único cambio de
gobernanza entre los dos brazos.

## 4. Pureza de la retención — **sin medir (no acreditable)**

La vara: de los hallazgos que la puerta no dejó pasar, a lo sumo
1 de cada 3 era un TP grounded. Para computarla hay que adjudicar
los retenidos contra el gold — y los retenidos **no están
identificados en ninguna parte de los outputs**: ni su archivo,
línea o reclamo, ni su destino (`needs_validation` vs rechazado),
ni su razón. El ledger que los contiene se generó dentro del
contenedor y no se persistió en los archivos que el portal entrega
(§1). Sin identidad no hay emparejamiento posible contra los 352:
**la fracción de pureza no es computable con este registro, y se
asienta SIN MEDIR — no estimada.**

Dos precisiones que no cambian el estado pero sí el relato:

- La definición operativa adoptada es la de esta adjudicación:
  retenidos = candidatos ante la puerta no emitidos (≤164, §3).
  Sobre ese conjunto solo se conoce el conteo. Ni siquiera el
  split entre `needs_validation` (retenidos para validación) y
  rechazados (descartados) existe en el registro.
- La corrida 311 es una corrida **nueva** del revisor: sus
  candidatos pre-puerta **no son** las 166 emisiones de la base
  nº 298 (varianza de corrida, selección y degradación propias).
  Ningún número de la 298 se importa como identidad de un retenido
  de la 311; la comparación entre brazos se hace solo donde la
  Adenda la define sobre cobertura del gold (§5), no sobre
  hallazgos individuales.

Para la regla — que es conjuntiva: los tres componentes deben
pasar — un componente no acreditable **no certifica un pase**. La
pureza queda como el segundo componente que no sostiene la regla,
detrás de dos que directamente caen (§2 y §5).

## 5. Pérdida inexplicada — **falsada: 66 ≠ 0**

La vara (Adenda 3 §4.3): todo TP grounded que la base cubrió y
ALMA no, aparece en el ledger de ALMA como retenido o rechazado
con su razón; **una sola pérdida muda falsifica el componente**.

- La base nº 298 cubrió **66 TP gold distintos** (adjudicación
  completa de la 298, sobre el gold).
- ALMA nº 311 cubrió **0** (su única emisión es zona gris, §2).
- Los **66** TP cubiertos por la base están ausentes de la salida
  de ALMA, y **ninguno** aparece en un ledger de ALMA como retenido
  o rechazado con su razón, porque **ningún ledger de ALMA forma
  parte del registro entregado** (§1).

**Pérdida inexplicada = 66** sobre el registro — el componente no
pasa por el máximo margen posible. La precisión del cargo importa:
no se afirma que la puerta «haya rechazado esos 66 hallazgos» en
la corrida 311 — sus candidatos son otros (§4) y su destino
individual es irrecuperable. Se afirma lo que el registro sostiene:
en el único registro que existe, 66 verdaderos que el brazo sin
puerta encontró **desaparecen del brazo con puerta sin una sola
razón asentada**. La definición del componente se escribió
exactamente para esto — que ninguna pérdida de cobertura quede
muda — y sobre esta corrida todas quedan mudas. (La misma lectura
aplica, en agregado, a los ≤164 candidatos propios de la 311 no
emitidos: ninguno tiene disposición ni razón en los outputs.)

## 6. Degradación — 36 % (9/25), y no explica el colapso

Degradación declarada en los run-info (`spend_cap`, salvo emdash):

| | Base nº 298 | ALMA nº 311 |
|---|---|---|
| PRs con degradación | 10/25 = **40 %** | 9/25 = **36 %** |
| Caso extremo | emdash 0 emisiones (`no_deep_pass_affordable`) | emdash 0 crudos (`no_deep_pass_affordable`) |

La degradación de la 311 es levemente menor que la de la base y
**no es la causa del resultado**: los 16 PRs **sin** degradación
suman 113 candidatos ante la puerta y emitieron **0** (p. ej.
NCATSTranslator: 19 candidatos, sin degradación, 0 emisiones;
pika: 13, 0; node-postgres: 10, 0). Y la única emisión de la
corrida salió de un PR **degradado** (DisciplinedSoftware, 2 de 5
pasadas profundas corridas). El cuello de botella medido es la
puerta 1.4.1 en modo ALMA sobre este flujo de candidatos, no el
freno de gasto.

## 7. Veredicto global y cierre de la línea

**Regla de avance variante (ii): NO PASA**, por los tres
componentes: precisión grounded 0,0 % contra vara 58,6 % (§2);
pureza de retención sin medir por ausencia del ledger en el
registro (§4) — un componente no acreditable no certifica el pase
de una regla conjuntiva —; pérdida inexplicada 66 contra vara 0
(§5). El titular del portal (augmented P 0 % · R 0 %, 1 hallazgo)
queda como lo que es: un titular de la familia del juez, que esta
vez coincide en dirección con el grounded adjudicado (0/0), sin
sustituirlo.

**Qué responde esto, en los términos de la pregunta pre-registrada
(¿la puerta 1.4.1 mejora al revisor?):** sobre esta corrida, la
puerta en modo ALMA no actuó como un filtro de precisión — no se
observa el intercambio «menos emisiones, más puras» que la variante
(ii) vino a medir — sino como una **supresión casi total del flujo**
(1/≤165) cuyo único sobreviviente ni siquiera acredita contra el
gold, dejando el recall en 0,00 % desde el 18,75 % de la base. Y la
corrida deja una segunda medición, sobre el instrumento: **el
portal, tal como corre este agente, no persiste el ledger de la
puerta** que el instrumento de la Adenda 3 §4 presume (ledger por
candidato con razones, split por familia). Cualquier medición
futura del efecto de una puerta en este examen exige fijar esa
persistencia antes de correr — es un defecto de observabilidad del
montaje, asentado acá con su recibo (main.py: el ledger solo se
escribe con `ALMA_LEDGER_PATH`/`RB_ALMA_LEDGER=1`; el zip no lo
trae).

**Lo que este veredicto NO dice:** no dice que la puerta 1.4.1 sea
«mala» en abstracto — su medición en seco (pre-registro de la
puerta: VP=4, falsos=0, equivalencia con la 1.4.0) sigue en pie
sobre su propio instrumento; dice que **integrada al revisor en
modo ALMA, sobre este examen, su efecto medido es el de arriba** y
que la regla de avance que el papel fijó para adoptarla no se
cumple. Tampoco dice nada del revisor, que produjo como siempre
(§3): lo que falló en esta comparación es el brazo con puerta,
medido entero.

**Cierre (Adenda 3 §5, conservado por la Adenda 4):** la nº 311
era el último acto del papel v2.3. Con este veredicto asentado —
NO PASA — **la línea de revisores de este papel se cierra**: la
base v2.3.1 queda como artefacto medido y congelado (P grounded
53,6 % · R 18,75 % · F1 27,8 %) y el efecto de la puerta 1.4.1
queda respondido con el instrumento de la Adenda 3 §4 hasta donde
el registro lo permite, con sus dos componentes medidos en contra
y el tercero declarado sin medir por ausencia del ledger.
Cualquier continuación — otra puerta, otra integración, otro
examen, o la persistencia del ledger como tema propio — es un
**papel nuevo**, con su pre-registro y su «sí» propios.

— Adjudicación completa de la nº 311, 2026-10-22. Insumos:
`runs/run-311-output.zip` (42.425 B, md5
`fd97ee0f28c6bbffe8ae2b7ee141857f`, extraído a `adj311/`), gold
público en `adjwork298/gold/` (el mismo de la adjudicación de la
298), cierre formal en `RESULTADO-PRACTICA-ALMA-V232-20261022.md`.
Trabajo de cotejo en `adj311/`. Gasto: **US$0**.
