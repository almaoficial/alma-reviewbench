# Adenda al diagnóstico — Práctica v2.2: cierre con los outputs reales (295 y 290)

**Fecha:** 2026-10-21 · **Costo:** US$0 (descarga y lectura local de outputs;
sin llamadas a OpenAI, sin corridas nuevas)
**Función:** ejecutar el cierre mecánico que la §5 del
`DIAGNOSTICO-PRACTICA-V22-20261021.md` dejó pre-escrito, con los zips de
outputs de las corridas **295** (base v2.2) y **290** (base v2.1) ya en
disco (`~/workspace/browser_downloads/sess-1849668839/`). No modifica el
diagnóstico: lo completa.

## 0. Método

Por cada PR se leyó la línea `llm_run` del `agent.log` (JSON del run info)
y el `findings.json` emitido, y se cruzó contra el gold público
(`golden/*.json`, el mismo verificado por el diagnóstico). En la 295 los
campos decisivos son `selection_selected`, `passes`, `raw_findings`,
`malformed_findings`, `unanchored_findings`, `selection_overflow` y
`degradation`. Las categorías son las del diagnóstico: **(a)** el triage
no marcó la clase del TP; **(b)** marcó y la profunda devolvió silencio o
candidatos caídos antes de emisión; **(c)** se emitió y el corrector no lo
contó; **(d)** degradación/overflow por el freno en ese PR. El universo de
análisis son los **≤9 TP alcanzables** de la §1 del diagnóstico (1 claro +
8 fronterizos); los otros 343 TP son la categoría estructural (a0), ya
cerrada ahí.

## 1. Corrida 295 (v2.2, triage + profundas): los 9 alcanzables, PR por PR

| PR | TP alcanzable (gold) | Triage marcó | Pasada profunda que corrió | raw | Veredicto |
|---|---|---|---|---|---|
| LANdalf#88 | `swallowed_exception` — `DeviceMonitoringService.cs:184` (el claro) | `race_condition` | `race_condition` | 0 | **(a)** |
| pika#200 | análogo swallowed (`try?`) — `ContentView.swift:151` | — (nada) | ninguna | 0 | **(a)** |
| chronicle#14 | análogo swallowed — `retention.rs:150` | `sql_injection` | `sql_injection` | 0 | **(a)** |
| chronicle#14 | análogo swallowed — `media.rs:296` | `sql_injection` | `sql_injection` | 0 | **(a)** |
| apilix#12 | análogo swallowed — `storageDriver.ts:179` | — (nada) | ninguna | 0 | **(a)** |
| Mcp-Docker#29 | análogo `resource_leak` — `session.go:44` | — (nada) | ninguna | 0 | **(a)** |
| konturio#1230 | análogo race — `GenericRenderer.ts:229` | — (nada) | ninguna | 0 | **(a)** |
| jadx#3 | análogo race — `Plugin.kt:550` | — (nada) | ninguna | 0 | **(a)** |
| CrabTrap#15 | análogo race — `api.go:325` | `sql_injection` | `sql_injection` | 0 | **(a)** |

Notas de lectura, para que nadie reclasifique mal:

- En los 5 PRs donde el triage no marcó nada, **no corrió ninguna pasada
  profunda** (`calls=1`, solo `selection`) — y el contexto sí incluía el
  archivo del TP (p. ej. `storageDriver.ts` en apilix, `Plugin.kt` en
  jadx, `GenericRenderer.ts` en konturio, `ContentView.swift` en pika).
  La pérdida no es de contexto ausente: el modelo vio el archivo y no
  levantó la clase.
- En LANdalf, chronicle y CrabTrap corrió una profunda de una clase
  **distinta** de la del TP y devolvió silencio. Eso no convierte el miss
  en (b): la pasada de la clase del TP nunca existió. (b) exige que la
  clase correcta haya sido marcada.
- El único PR donde la clase `swallowed_exception` fue marcada y su
  profunda produjo candidatos es DisciplinedSoftware (10 raw → 10
  emitidos), que no contiene ningún TP alcanzable: sus TP gold son de
  correctness/otros, fuera del universo.

### Conteos finales de la 295 (sobre los 9 TP alcanzables)

| Categoría | Conteo |
|---|---|
| **(a) El triage no marcó la clase del TP** | **9 / 9** |
| (b) Marcó y la profunda devolvió silencio o candidatos caídos | **0** |
| (c) Emitido y no contado por el corrector | **0** |
| (d) Degradación/overflow en el PR | **0** |

### Falsador de degradación del papel v22

`degradation` es `null` en los **25/25** PRs y `selection_overflow` es
vacío en los 25/25. Eventos de degradación: **0 % de los PRs**, contra el
umbral del falsador (>1/4). **Falsador NO gatillado** — la economía de C2
cerró en la práctica igual que en seco: ningún PR se degradó ni se negó.

### El lado de las emisiones de la 295 (categoría (c) a nivel puntaje)

11 emitidos = 11 raw; `malformed=0` y `unanchored=0` en los 25 PRs:
**(c) interno es 0** — ningún candidato murió por anclaje o formato en
todo el set. A nivel corrector, el portal contó 0 como cobertura grounded,
3 como novel (solo augmented) y 8 sin contar. La emisión del tarfile en
DisciplinedSoftware (`fetcher.py:85`, extractall sin filtro) coincide
semánticamente con el gold **FP** de `fetcher.py:94` (el Zip Slip juzgado
no-TP), el mismo patrón (c) puro que la v1 sufrió en PROTRIDER. Las 10
emisiones de DisciplinedSoftware son, defecto por defecto, casi idénticas
a las 8 que la 290 emitió en ese PR (mismos archivos y líneas): donde la
clase sí se marca, las profundas de C2 reproducen lo que la pasada única
ya encontraba.

## 2. Corrida 290 (v2.1, pasada única): descomposición resuelta

### ¿El «P 37,5 % · R 0,4 %» del registro era grounded o augmented? **Augmented.**

Prueba, en dos pasos independientes:

1. **Su cobertura grounded fue 0.** La 290 emitió 8 findings, todos en un
   solo PR (DisciplinedSoftware; `raw=8`, `malformed=0`, `unanchored=0`;
   los otros 24 PRs devolvieron silencio). Adjudicados contra el gold de
   ese PR (31 TP, 23 FP): **ninguna emisión coincide con un golden TP**.
   La del tarfile (`fetcher.py:85`, extractall sin filtro) coincide
   semánticamente con el gold **FP** de `fetcher.py:94` — el Zip Slip que
   el corpus juzgó no-TP — y las otras 7 (excepciones tragadas en
   `llm_client.py`, `reporter.py`, `strategies/`) no tienen contraparte
   en el gold de esos archivos. Cobertura: **0 de 352 TP → grounded
   P 0,0 % · R 0,0 % · F1 0,0 %**, igual que la 295.
2. **El 37,5 % es exactamente el cociente augmented.** El portal contó
   «3 novel» sobre 8 emitidos: 3/8 = 37,5 %. Y el R 0,4 % es consistente
   con el recall augmented macro: los 3 novel viven en el único PR
   emisor, (0 + 3)/(31 TP + 3 novel) = 8,8 % en ese PR, ÷ 25 PRs ≈
   0,35 % ≈ 0,4 %. El par del registro era el **augmented**; el grounded
   de la 290 nunca quedó asentado y era 0,0 % en las tres métricas.

Consecuencia para la comparación entre prácticas: la «dilución» que se
leyó al pasar de la 290 a la 295 (P 37,5 % → 15,0 %) compara augmented
contra augmented y es real en esos términos, pero **en grounded las dos
corridas empatan en 0,0 %** — ninguna cubrió un solo TP. La v1 (nº 251,
grounded R 0,7 %, 3 TP cubiertos) sigue siendo la única base que puntuó
en grounded en una práctica.

### Sus pérdidas alcanzables, clasificadas

La v2.1 no tiene triage (pasada `single`, contexto completo): la categoría
(a) no aplica como paso separado, y su `llm_run` ni siquiera trae campos
`selection_*`/`degradation` (la (d) tampoco existe como mecanismo por PR
en el revisor 2.1.0; la corrida completó 25/25).

| Categoría análoga | Conteo (sobre los 9 TP alcanzables) |
|---|---|
| **(b)-análoga: la pasada única vio el PR entero y devolvió silencio** (`raw=0` en los 8 PRs alcanzables: LANdalf, pika, chronicle, apilix, Mcp-Docker, konturio, jadx, CrabTrap) | **9 / 9** |
| (c) Emitido-no-contado entre los alcanzables | 0 (sus emisiones fueron en DisciplinedSoftware, sin TP alcanzables; 1 de ellas — el tarfile — es (c) puro contra un gold FP) |
| Fuera de universo (a0) | 343, idénticos por construcción |

Simetría que conviene dejar escrita: la (a) de la 295 y la (b)-análoga de
la 290 son **el mismo evento en distinta posición del pipeline** — el
modelo, mirando el diff real, no levanta la clase del defecto. C1 lo
pierde en la única pasada que tiene; C2 lo pierde en la selección que
decide qué pasadas existen. Ninguna de las dos arquitecturas llega a
ejercitar la pasada profunda sobre la clase correcta en ningún PR
alcanzable del set.

## 3. La predicción falsable sobre LANdalf: **CONFIRMADA**

El diagnóstico (§6) predijo: *«en LANdalf el triage no marcó
`swallowed_exception` o la profunda devolvió silencio»*, y declaró qué la
falsaría: triage marcando la clase + profunda corriendo + candidato
anclado emitido que el portal igual no contara (eso movería el cuello a
(c) y voltearía la conclusión).

El `agent.log` de la 295 en LANdalf#88 muestra exactamente el primer
disyunto de la predicción:

- `selection_candidates = ["race_condition"]`, `selection_selected =
  ["race_condition"]` — `swallowed_exception` **nunca fue marcada**,
  aunque `DeviceMonitoringService.cs` estaba en el contexto.
- La única profunda que corrió fue `race_condition`: `raw_findings = 0`.
- `findings.json` del PR: vacío. `degradation = null`, sin overflow.

**La condición de falsación no ocurrió; la predicción se confirma por su
primer disyunto**, el mismo modo de pérdida que la v1 tuvo en ese PR por
emisión directa (0 findings).

## 4. Cierre: qué queda establecido

1. **El split (a)/(b)/(c)/(d) de la 295 está cerrado con outputs, no con
   cotas:** de los 9 TP alcanzables, 9 son (a); (b) = 0, (c) = 0,
   (d) = 0, y el falsador de degradación del papel v22 no se gatilló
   (0/25 PRs).
2. **La 290 quedó descompuesta:** su par del registro era augmented; su
   grounded fue 0,0 % en todo, y sus 9 pérdidas alcanzables son silencio
   de la pasada única — el mismo evento que la (a) de la 295, un paso
   antes en el pipeline.
3. **La conclusión de la §6 del diagnóstico sobrevive a su propia prueba
   de falsación.** El cuello dominante sigue siendo el universo de
   emisión (343/352 estructurales). Lo que esta adenda agrega, medido y
   ya no pendiente: **en el margen alcanzable, la pérdida también está
   aguas arriba de las profundas** — en los 9 casos el defecto murió en
   la etapa que decide qué mirar (selección en C2, pasada única en C1),
   nunca dentro de una profunda correctamente convocada. Las profundas,
   cuando se las convoca con la clase justa (DisciplinedSoftware en
   ambas corridas), producen y emiten sin pérdidas de formato.
4. Nada de esto ajusta el veredicto de la práctica v2.2 (linterna no
   superada, sin brazo ALMA, sin veredicto válido): lo explica con el
   mecanismo exacto, defecto por defecto.

---
*Fuentes: zips de outputs de las corridas 295 y 290 en
`~/workspace/browser_downloads/sess-1849668839/` (`agent.log` +
`findings.json` por PR); gold público `golden/*.json` del repo
ReviewBench; `DIAGNOSTICO-PRACTICA-V22-20261021.md` §§1–6;
`RESULTADO-PRACTICA-V21-20261021.md`; `REGISTRO-REVIEWBENCH.md`. Sin
gasto, sin corridas nuevas, sin tocar el portal, las puertas congeladas
ni los documentos fuente.*
