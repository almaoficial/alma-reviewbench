# Adjudicación completa de la práctica nº 298 (base v2.3.1) — el par grounded exacto

**Fecha:** 2026-10-22 · **Costo de esta adjudicación: US$0** (sin portal, sin
corridas, sin llamadas a modelos; cotejo local contra el gold público).
**Objeto:** las 166 emisiones de la corrida nº 298 (base v2.3.1, SUCCEEDED,
25/25 PRs) contra el gold público del benchmark (`review-bench/ReviewBench`:
`golden/*.json` + `corpus/test/findings.json`). **Encargo:** Alejandro eligió
el 22/10/2026 la adjudicación completa de los 166 «antes de decidir» la
colisión linterna/§8 — este informe entrega el número que esa decisión
necesita; no la toma.

## 0. Veredicto

| Métrica grounded (micro) | Valor |
|---|---|
| Emisiones grounded en TP gold | **89 / 166** |
| TP gold distintos cubiertos | **66 / 352** |
| **Precisión grounded** | **89/166 = 53,6 %** |
| **Recall grounded** | **66/352 = 18,75 %** |
| **F1 grounded** | **27,8 %** |
| Emisiones sobre FP gold (falsos confirmados) | 8 (sobre 6 FP gold distintos) |
| Emisiones en zona gris | 17 |
| Emisiones novedosas sin veredicto gold | 52 |

- **La linterna queda acreditada con el conteo completo, no con una cota:**
  66 TP gold distintos cubiertos ≫ los 3 que exige la vara (0,7 % de 352).
  La cota de la adenda de acreditación (≥5) queda contenida y superada.
- **Contra la predicción del papel v2.3:** recall predicho 1–3 % → real
  **18,75 %**; precisión predicha 10–40 % → real **53,6 %**. Ambas bandas
  quedan por debajo del resultado (ver §7, con sus salvedades).
- **Falsador principal del papel (§8, encuadre): NO gatillado** — exigía
  R_base ≤ 0,7 % otra vez; el recall medido es 18,75 %.
- **El destino de las 77 emisiones no-TP:** solo 8 caen sobre reclamos que
  el gold ya juzgó falsos; 52 son reclamos nuevos que el gold no juzga
  (los acredita o no la familia augmented vía juez — §5); 17 quedan en
  zona gris declarada.

## 1. Método y denominadores

El de la casa, idéntico al de `DIAGNOSTICO-PRACTICA-V22-20261021.md` y al de
`ADJUDICACION-PARCIAL-296-20261021.md`:

- **Match grounded (TP):** mismo archivo + región de líneas que cubre la
  línea del defecto + **el mismo defecto/mecanismo**. Las líneas orientan;
  el mecanismo manda. Que una emisión «suene parecida» no alcanza.
- **Una emisión, un TP primario como máximo.** Emisiones duplicadas sobre
  el mismo defecto cuentan como emisiones grounded pero la cobertura se
  acredita una sola vez. **Entradas gold gemelas** (el mismo defecto
  asentado dos o tres veces en el archivo golden) se acreditan una vez.
- **Reclamos de «falta test»:** cuentan como TP solo si enuncian el
  mecanismo del defecto gold; si el defecto gold ES la ausencia de tests
  con ese alcance, el reclamo de ausencia matchea. Reclamar «sin tests»
  sobre un defecto de comportamiento no cuenta (precedente: pika E5 en
  la parcial de la 296).
- **FPG:** la emisión coincide con un reclamo que el gold juzgó falso
  positivo (mismo archivo, mismo reclamo). **GREY (zona gris):** mismo
  archivo y territorio, mecanismo dudoso, opuesto o no cerrable con el
  estándar. **NOVEL:** reclamo sin contraparte en el gold — esta
  adjudicación **no lo juzga** (ni verdadero ni falso); es el material
  que la familia augmented acredita vía juez.
- **Denominadores:** emisiones = 166 (los `findings.json` del zip de la
  298; 168 crudos − 2 `unanchored`); TP gold = 352 y FP gold = 213 (los
  25 archivos golden de los PRs de la práctica, sumados por programa).
- Precisión se mide **sobre emisiones**; recall, **sobre TP gold
  distintos cubiertos**. Todo micro (sin promediar por PR).

## 2. Tabla por PR (los 25) — sumada por programa desde las decisiones

| PR | Emis. | TP-grounded | TP cubiertos | FPG | Gris | Novel | TP gold | R del PR |
|---|---|---|---|---|---|---|---|---|
| AA-Factory aafactory-prototype #17 | 4 | 4 | 2 | 0 | 0 | 0 | 9 | 22,2 % |
| AY2526S2-CS2103T-W14-3 tp_152 | 12 | 4 | 3 | 0 | 2 | 6 | 14 | 21,4 % |
| DisciplinedSoftware Codebase-Conversion #1 | 11 | 5 | 5 | 0 | 3 | 3 | 31 | 16,1 % |
| Marvell-Consulting statswales-frontend #626 | 2 | 2 | 2 | 0 | 0 | 0 | 6 | 33,3 % |
| NCATSTranslator translator-ingests #336 | 19 | 18 | 6 | 0 | 0 | 1 | 17 | 35,3 % |
| PaulStSmith figlet-comment-generator #32 | 9 | 3 | 1 | 0 | 1 | 5 | 9 | 11,1 % |
| PierreJanineh TechDebtMCP #135 | 6 | 1 | 1 | 2 | 1 | 2 | 9 | 11,1 % |
| allan-mobley-jr gimmes #468 | 4 | 0 | 0 | 2 | 1 | 1 | 6 | 0,0 % |
| ardevd jadx-collaboration #3 | 6 | 5 | 2 | 0 | 0 | 1 | 9 | 22,2 % |
| brexhq CrabTrap #15 | 4 | 4 | 4 | 0 | 0 | 0 | 16 | 25,0 % |
| brianc node-postgres #3650 | 6 | 4 | 4 | 0 | 0 | 2 | 11 | 36,4 % |
| cmik apilix #12 | 7 | 7 | 7 | 0 | 0 | 0 | 36 | 19,4 % |
| gagneurlab PROTRIDER #10 | 5 | 2 | 2 | 0 | 2 | 1 | 21 | 9,5 % |
| k1LoW gh-copilot-review #9 | 4 | 3 | 2 | 0 | 0 | 1 | 7 | 28,6 % |
| konturio disaster-ninja-fe #1230 | 3 | 1 | 1 | 1 | 1 | 0 | 13 | 7,7 % |
| mheuss chronicle #14 | 5 | 1 | 1 | 1 | 2 | 1 | 10 | 10,0 % |
| renedierking LANdalf #88 | 3 | 2 | 1 | 0 | 0 | 1 | 6 | 16,7 % |
| scotthamilton77 agents-config #1 | 7 | 1 | 1 | 2 | 0 | 4 | 25 | 4,0 % |
| scottlz0310 Mcp-Docker #29 | 10 | 6 | 6 | 0 | 1 | 3 | 22 | 27,3 % |
| sdsykes fastimage #165 | 9 | 3 | 3 | 0 | 0 | 6 | 14 | 21,4 % |
| simnaut emdash #2 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0,0 % |
| superhighfives pika #200 | 12 | 4 | 4 | 0 | 2 | 6 | 19 | 21,1 % |
| superyyrrzz ForgeMap #106 | 6 | 3 | 3 | 0 | 0 | 3 | 15 | 20,0 % |
| vanyastaff nebula #224 | 1 | 1 | 1 | 0 | 0 | 0 | 9 | 11,1 % |
| wirechat wirechat #183 | 11 | 5 | 4 | 0 | 1 | 5 | 12 | 33,3 % |
| **Total (micro)** | **166** | **89** | **66** | **8** | **17** | **52** | **352** | **18,75 %** |

Verificación de la suma (por programa, `adjwork298/aggregate298.py` sobre
`adjwork298/decisions.json`): emisiones 4+12+11+2+19+9+6+4+6+4+6+7+5+4+3+
5+3+7+10+9+0+12+6+1+11 = **166**; TP-grounded = **89**; cubiertos = **66**;
FPG+gris+novel = 8+17+52 = **77** = 166 − 89. Sin errores de referencia
(toda emisión TP/FPG apunta a una entrada gold del tipo correcto).

Lecturas de la tabla:

- **Precisión por PR:** 12 de 25 PRs emiten ≥50 % grounded; los dos
  extremos son NCATS (18/19) y apilix (7/7) por arriba, gimmes (0/4) y
  agents-config (1/7) por abajo.
- **emdash emitió 0** (degradación `no_deep_pass_affordable`: las 5
  pasadas profundas quedaron fuera del freno): su recall 0/6 no es un
  fallo de detección sino de economía — es el PR que materializa el
  falsador §8 (ver §8 de este informe).
- **figlet es la regresión declarada frente a la 296:** la selección de
  la 298 no incluyó `reliability` en este PR y las 6 TP de filtros de
  paths del gold quedaron fuera (en la 296 el mismo PR rindió 15
  emisiones TP y 8 cubiertos). La cobertura que queda (1 TP) viene del
  defecto insert-vs-replace, reclamado 3 veces.

## 3. Corte por familia (general vs especialidad)

| Familia | Pasadas ejecutadas | Emisiones atribuibles | Emisiones TP-grounded | TP cubiertos |
|---|---|---|---|---|
| General | todas | 166 | **89** | **66** |
| Especialidad (19 clases) | 1 (`sql_injection` en CrabTrap) | 0 | **0** | **0** |

- La selección marcó clases de especialidad en solo **3 de 25 PRs**:
  Codebase-Conversion (`tarfile_unsafe_extract`, `swallowed_exception`)
  y chronicle (`sql_injection`) las perdieron por degradación
  (`spend_cap`) antes de correr; solo CrabTrap ejecutó la suya
  (`sql_injection`) y **ninguna de sus 4 emisiones reclama un defecto de
  inyección SQL** — son de vía general por contenido.
- Conclusión idéntica a la de la parcial de la 296: **el 100 % del recall
  grounded de la base viene de la vía general**. La capa de especialidad
  de las 19 clases no aportó un solo TP en la práctica completa, igual
  que el diagnóstico v2.2 anticipó (techo solo-clases 0,3–2,6 %): el
  grueso del gold vive fuera de las 19 clases y la vía general es la que
  lo alcanza.

## 4. El destino de las 77 emisiones que no son TP grounded

| Destino | Emisiones | % de 166 | Qué significa |
|---|---|---|---|
| **FPG** — caen sobre FP gold | 8 | 4,8 % | El revisor reprodujo reclamos que el gold ya juzgó **falsos**: error confirmado contra el gold. Cubren solo **6 FP gold distintos de 213** (2,8 %). |
| **GREY** — zona gris | 17 | 10,2 % | Mismo archivo/territorio que una entrada gold, mecanismo dudoso, de signo opuesto o no cerrable con el estándar (detalle y borde en §4.1). Ni acreditadas ni refutadas. |
| **NOVEL** — sin veredicto gold | 52 | 31,3 % | Reclamos sin contraparte en el gold. **Esta adjudicación no los juzga**: son el material que la familia **augmented** del portal acredita vía juez (el titular 89,4/34,5 vive en esa familia). |

### 4.1 Criterio de borde y los casos límite, declarados

- **El caso más débil de toda la adjudicación — konturio E1 (GREY, no
  TP):** la adenda de acreditación de la linterna emparejó esta emisión
  (`GenericRenderer.ts:228-234`, estilo aplicado sin guarda ante
  cambios concurrentes) con el gold de concurrencia y la contó como el
  5º caso verificado, «el más débil, declarado». Con el cotejo completo
  del archivo golden, el mecanismo de la emisión no cierra contra
  ninguna entrada TP con el estándar de mecanismo idéntico: **la
  adjudicación completa la baja a GRIS**. Diferencia declarada contra la
  adenda — y sin efecto sobre la linterna: quedan 66 TP cubiertos, y aun
  con solo los 3 casos fuertes de la adenda (LANdalf, pika, apilix) la
  vara de 3 TP se cumple (ver §5).
- **El TP acreditado más débil — wirechat E5 → G0:** la emisión señala
  una ruta concreta (un *early return* del servidor que no despacha
  `older-loaded`) por la que los flags `pendingPrependRestore`/
  `loadingOlder` quedan trabados; el gold G0 asienta el mismo defecto
  desde el lado cliente (los flags dependen solo de ese evento, sin
  *finally* que los resetee). Mismo defecto y misma dependencia; el
  disparador descrito difiere. Se acredita y se marca.
- **Otros bordes asentados en las decisiones:** agents-config E5/E6
  (comportamiento *dry-run*) caen sobre el FP gold G16 — el gold juzgó
  falso ese reclamo familiar, aunque las emisiones lo enmarcan como
  violación de contrato; pika E1 (doble decremento vía `triggerSwap`)
  queda GRIS contra el FP gold G10, que afirma el signo opuesto sobre
  el mismo cableado; pika E9 y Mcp-Docker E9 muestran las dos caras de
  la regla de tests: E9 de pika nombra el mecanismo gold pero su
  hallazgo es la ausencia de tests (GRIS, sin crédito), mientras que en
  Mcp-Docker el defecto gold **es** la ausencia de tests de la fachada
  OAuth con ese alcance (TP).
- **Duplicadas:** 23 de las 89 emisiones grounded son repeticiones sobre
  un defecto ya cubierto por otra emisión (89 emisiones → 66 TP
  distintos). El caso extremo es NCATS: 18 emisiones grounded sobre 6
  defectos (el defecto del `break` reclamado 8 veces).

## 5. Relación con la adenda de acreditación de la linterna

Los 5 casos verificados caso por caso en
`ADENDA-RESULTADO-PRACTICA-V231-20261022.md`, cotejados con esta
adjudicación completa:

| Caso de la adenda | Estado en la adjudicación completa |
|---|---|
| LANdalf `DeviceMonitoringService.cs:184` (cancelación tragada) | **TP confirmado** (G0; 2 emisiones) |
| pika `ContentView.swift:151-152` (`try?` descarta el error) | **TP confirmado** (G9) |
| apilix `storageDriver.ts:179-191` (`store={}` borra otros workspaces) | **TP confirmado** (G7) |
| jadx G6 (tests saltean la vía de acciones) | **TP confirmado** (G6; 2 emisiones) |
| konturio `GenericRenderer.ts:229-244` (el más débil) | **BAJADO A GRIS** (§4.1) — konturio cubre otro TP (G16, test que solo aserta `disable`) |

Y una corrección en sentido contrario: la adenda declaró «casi-match que
NO cuenta» la emisión de CrabTrap en `api.go:325`, cotejándola solo
contra la entrada gold de consistencia. La adjudicación completa
encuentra en el mismo ancla la entrada gold de **performance** (G19),
que reclama exactamente el defecto de la emisión: **CrabTrap cubre 4 TP,
no 3**.

**Efecto neto sobre la linterna: ninguno en la conclusión, todo en la
solidez.** La vara era ≥3 TP distintos; el conteo completo da 66. La
acreditación ya no depende de ningún caso débil.

## 6. Métricas del sector, con definiciones declaradas

Para la contabilidad pública de esta corrida. Cada métrica lleva su
denominador; ninguna usa un denominador que el material no provea.

| Métrica (nombre usado) | Definición y denominador | Valor |
|---|---|---|
| Precisión grounded | emisiones grounded en TP / emisiones totales = 89/166 | **53,6 %** |
| Proporción de descubrimientos falsos (FDP = 1 − precisión) | emisiones no grounded / emisiones = 77/166 — incluye grises y novedosas sin juzgar, **no** es «falsos» a secas | **46,4 %** |
| Falsos confirmados por el gold, sobre emisiones | emisiones que coinciden con un FP gold / emisiones = 8/166 | **4,8 %** |
| Tasa de reproducción de FP gold | FP gold distintos que el revisor re-emitió / FP gold del set = 6/213 | **2,8 %** |
| Recall grounded (sensibilidad sobre reclamos TP) | TP gold distintos cubiertos / TP gold = 66/352 | **18,75 %** |

**La tasa de falsos positivos de manual (FPR = FP/(FP+TN)) NO es
computable en esta tarea, y no se publica ningún sustituto con ese
nombre.** Un revisor generativo no clasifica un universo de negativos:
nunca emite «esto está bien», así que no existen verdaderos negativos
(TN) contra los cuales contar. El denominador FP+TN no existe en el
material; inventarlo sería fabricar la métrica. Lo más cercano con
denominador real es la fila 4: de los 213 reclamos que el gold ya juzgó
falsos para estos PRs, el revisor reprodujo 6 (2,8 %).

**El índice J de Youden NO se reporta como tal.** Su definición
(J = sensibilidad + especificidad − 1) exige especificidad sobre un
universo de negativos clasificados, que aquí no existe (misma razón que
arriba). El sustituto más cercano, con su nombre correcto y su
definición explícita, es el **índice de discriminación por reproducción
de reclamos gold**:

> J_rep = (TP cubiertos / TP gold) − (FP gold reproducidos / FP gold)
> = 66/352 − 6/213 = 0,1875 − 0,0282 = **0,159**

Mide cuánto discrimina el revisor entre el universo de reclamos
verdaderos y el de reclamos falsos del benchmark (1 = reproduce todos
los verdaderos y ningún falso; 0 = reproduce ambos en la misma
proporción). Es un proxy declarado sobre universos de reclamos, **no**
el J de Youden clínico, y debe citarse con ese nombre o no citarse.

## 7. Comparación asentada

### 7.1 Contra la predicción del papel v2.3

| | Predicción registrada | Real (nº 298) |
|---|---|---|
| Recall grounded base | 1–3 % (≈4–10 TP) | **18,75 % (66 TP)** |
| Precisión grounded base | 10–40 % | **53,6 %** |

Ambas predicciones quedaron **por debajo** del resultado — el encuadre
«ensanchar la base» rindió más que lo pre-registrado. Salvedad: la
predicción se registró para la práctica de la base v2.3; la corrida que
la mide es la v2.3.1 (mismo revisor salvo el techo de selección de la
Adenda 2, que no toca la detección: cambia que la corrida *complete*, no
qué detecta por PR). El falsador principal del §8 (R ≤ 0,7 % → muere el
encuadre) **no se gatilló**.

### 7.2 Contra la adjudicación parcial de la nº 296

| | 296 (parcial, 15 PRs) | 298 (completa, 25 PRs) |
|---|---|---|
| Precisión grounded | 51,9 % (55/106) | **53,6 % (89/166)** |
| Recall grounded | 22,1 % del subconjunto (43/195); piso 12,2 % sobre 352 | **18,75 % (66/352)** |
| Familia de los TP | 100 % vía general | 100 % vía general |

**Salvedad de comparabilidad (la importante):** la 296 solo pudo
adjudicar los 15 PRs que completaron; su 22,1 % es recall sobre un
subconjunto con sesgo de supervivencia (los 10 que murieron incluían
emdash y otros con gold denso). La comparación limpia es **sobre los
mismos 15 PRs**: la 298 obtiene ahí precisión **60,2 %** (62/103) y
recall **21,0 %** (41/195), contra 51,9 % y 22,1 % de la 296 — es decir,
**precisión +8,3 pp y recall −1,1 pp (−2 TP netos) entre v2.3.0 y
v2.3.1 sobre el mismo material**. Los movimientos por PR se compensan:
figlet colapsó (8 cubiertos → 1; §2) mientras NCATS (4 → 6), CrabTrap
(1 → 4) y apilix (5 → 7) subieron. Sobre los 10 PRs que la 296 nunca
midió, la 298 rinde precisión 42,9 % (27/63) y recall 15,9 % (25/157) —
ese bloque explica la diferencia entre el 21,0 % del subconjunto y el
18,75 % total. **Esta adjudicación no re-califica la 296**: su parcial
queda como fue asentada.

### 7.3 Contra la base v1 (nº 251)

| | v1 #251 | v2.3.1 #298 |
|---|---|---|
| Precisión grounded | 42,9 % | **53,6 %** (+10,7 pp) |
| Recall grounded | 0,7 % | **18,75 %** (×26,8) |

Salvedad: la v1 era otro revisor (una sola pasada, sin selección ni
pasadas profundas) y su par se midió en su momento con el mismo gold; la
comparación vale como trayectoria de la base entre versiones, no como
A/B controlado (difieren modelo, arquitectura y costo por PR).

## 8. Qué afirma y qué NO afirma esta medición (alcance)

**Afirma**, con el gold público como única vara:

1. El par grounded exacto de la base v2.3.1 en la práctica nº 298 es
   **P 53,6 % · R 18,75 % · F1 27,8 %** (micro, 25 PRs, 166 emisiones,
   352 TP / 213 FP gold).
2. La **linterna PASA con el conteo completo** (66 TP distintos ≫ 3
   requeridos), no ya por cota inferior. El falsador principal del
   papel (encuadre) no se gatilló.
3. El 100 % del recall grounded vino de la **vía general**; la
   especialidad de 19 clases aportó 0 (1 sola pasada ejecutada en 25
   PRs, 0 emisiones atribuibles).
4. De las emisiones no grounded, solo **8 son falsos confirmados por el
   gold**; 52 son reclamos novedosos que este método no juzga y 17
   quedan en zona gris declarada.

**NO afirma:**

1. **No es el puntaje del portal.** El titular «P 89,4 % · R 34,5 % ·
   88 novel» pertenece a la familia **augmented** (juez que acredita
   novedosos y expande el denominador), indescomponible desde las
   fuentes — como asentó la adenda de acreditación. Este informe mide la
   otra familia (grounded, contra el gold) y no valida ni refuta el
   titular.
2. **No re-califica la nº 296** ni reescribe su adjudicación parcial:
   la comparación de §7.2 es entre informes, cada uno con su
   denominador declarado.
3. **No decide la colisión linterna/§8.** Los dos hechos quedan sobre la
   mesa, ahora con el par exacto: la linterna pasa por conteo completo
   (este informe, §0/§5) **y** el falsador de economía del §8 sigue
   gatillado por el registro de la corrida (degradación declarada en
   10/25 PRs = 40 % > 1/4, con emdash en 0 emisiones como su caso
   extremo). La adjudicación no encontró ningún hecho que apague ese
   falsador: la degradación y sus efectos están en la tabla de §2.
   Decidir si corre el brazo ALMA — por la letra del §8 («registrar y
   detener») o por una adenda de lectura previa — es la decisión de
   Alejandro que este número vino a alimentar.
4. **No juzga las 52 emisiones novedosas.** Que el gold no las contenga
   no las hace falsas (el gold es la revisión de referencia del
   benchmark, no el universo de defectos reales); su veredicto pertenece
   a la familia augmented o a una adjudicación humana que no es esta.

## 9. Procedencia y reproducibilidad

- Decisiones emisión por emisión (las 166, con su entrada gold o su
  destino y las notas de borde): `adjwork298/decisions.json`.
- Agregación y validación por programa: `adjwork298/aggregate298.py`
  (suma la tabla de §2, verifica que toda referencia TP/FPG apunta a una
  entrada gold del tipo correcto y que los destinos suman 166; salida
  sin errores).
- Fuentes: `runs/run-298-output.zip` (emisiones y logs de la corrida) y
  el gold público clonado en `adjwork298/gold/` (repo
  `review-bench/ReviewBench`).
- Informes previos que este trabajo replica y cita:
  `ADJUDICACION-PARCIAL-296-20261021.md`,
  `ADENDA-RESULTADO-PRACTICA-V231-20261022.md`,
  `RESULTADO-PRACTICA-V231-20261022.md`,
  `DIAGNOSTICO-PRACTICA-V22-20261021.md`.

**Gasto de esta tarea: US$0.** Sin portal, sin corridas, sin modelos,
sin publicar; ningún código ni papel fue tocado — solo este informe y su
asiento en el registro.
