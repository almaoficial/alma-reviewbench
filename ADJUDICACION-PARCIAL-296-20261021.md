# Adjudicación parcial de la práctica nº 296 (base v2.3) — en seco, US$0

**Fecha:** 2026-10-21 (noche, EDT). **Corrida adjudicada:** nº 296,
práctica v2.3, brazo base — cerrada por la plataforma como FAILED
«at run-agent (3, 4)», sin puntajes (diagnóstico en
`DIAGNOSTICO-PRACTICA-V23-20261021.md`: causa (d), defecto del diseño —
techo de 1.024 tokens de completion heredado por la selección
generalizada). **Aprobación:** Alejandro, «Ok lo hagamos»
(2026-10-21 23:03 EDT). **Costo de esta adjudicación: US$0** — sin
llamadas a modelos, sin portal, sin relanzar nada; ningún archivo de
código ni de papeles fue modificado.

La corrida murió, pero 15 de los 25 PRs completaron y dejaron **106
findings nunca puntuados**. Esta adjudicación los contrasta, uno por
uno, contra el gold público de ReviewBench. Es una medición
**parcial y de salvataje diagnóstico**: no re-califica la práctica
(la nº 296 sigue FAILED y sin puntaje oficial) y no evalúa la regla
de avance del papel v2.3.

## 1. Método y denominadores

- **Materiales:** el zip de outputs de la corrida nº 296 (por PR:
  `findings.json` + `agent.log` con el `llm_run` del revisor
  `llm-reviewer/2.3.0`, puerta `alma-evidence-gate/1.3.0`) y el gold
  público del repo `review-bench/ReviewBench` (`golden/*.json`):
  **352 TP y 213 FP** sobre los 25 PRs del set.
- **Criterio de matching (el de la casa, no uno nuevo):** el mismo
  aplicado en la adjudicación del diagnóstico v2.2 y que reprodujo
  los números del portal en la nº 251. Match semántico = **mismo
  archivo + mismo defecto (mecanismo)**; la cercanía de líneas
  orienta, no es compuerta. Cada emisión matchea a lo sumo un TP
  gold (el primario); cada TP gold se cubre una sola vez; las
  emisiones duplicadas cuentan como TP-grounded pero no como
  cobertura extra; las entradas gold casi-duplicadas (gemelas) se
  acreditan una sola vez; una emisión que coincide con un gold FP
  cuenta como emisión FP, con la coincidencia asentada.
- **Dos conteos distintos, nunca mezclados:** la **precisión** se
  mide sobre emisiones (emisiones TP-grounded / emisiones totales);
  el **recall** se mide sobre cobertura (TP gold distintos
  cubiertos / denominador).
- **Denominadores declarados:** el subconjunto de los 15 PRs
  completados concentra **195 de los 352 TP** del gold (55,4 %).
  El denominador de la linterna del papel v2.3 es el set completo:
  352.

## 2. Tabla por PR (los 15 que completaron)

| PR | Emitidos | Emisiones TP-grounded | TP gold cubiertos | Emisiones FP | TP gold del PR | Recall del PR |
|---|---|---|---|---|---|---|
| AA-Factory aafactory-prototype #17 | 2 | 2 | 2 | 0 | 9 | 22,2 % |
| AY2526S2-CS2103T-W14-3 tp_152 | 11 | 3 | 2 | 8 | 14 | 14,3 % |
| Marvell-Consulting statswales-frontend #626 | 2 | 2 | 2 | 0 | 6 | 33,3 % |
| NCATSTranslator translator-ingests #336 | 10 | 4 | 4 | 6 | 17 | 23,5 % |
| PaulStSmith figlet-comment-generator #32 | 23 | 15 | 8 | 8 | 9 | 88,9 % |
| PierreJanineh TechDebtMCP #135 | 9 | 1 | 1 | 8 | 9 | 11,1 % |
| allan-mobley-jr gimmes #468 | 2 | 1 | 1 | 1 | 6 | 16,7 % |
| ardevd jadx-collaboration #3 | 4 | 3 | 2 | 1 | 9 | 22,2 % |
| brexhq CrabTrap #15 | 5 | 2 | 1 | 3 | 16 | 6,3 % |
| brianc node-postgres #3650 | 9 | 2 | 2 | 7 | 11 | 18,2 % |
| cmik apilix #12 | 7 | 5 | 5 | 2 | 36 | 13,9 % |
| konturio disaster-ninja-fe #1230 | 4 | 2 | 2 | 2 | 13 | 15,4 % |
| renedierking LANdalf #88 | 3 | 3 | 1 | 0 | 6 | 16,7 % |
| superhighfives pika #200 | 9 | 6 | 6 | 3 | 19 | 31,6 % |
| superyyrrzz ForgeMap #106 | 6 | 4 | 4 | 2 | 15 | 26,7 % |
| **Total subconjunto** | **106** | **55** | **43** | **51** | **195** | — |

Notas de la tabla: figlet tiene 9 TP gold en el manifiesto, pero uno
(G20) es una entrada vacía fantasma, sin defecto enunciado —
incontable por cualquier revisor; sobre TP sustantivos, figlet
cubrió 8 de 8. apilix es el PR con más gold del subconjunto (36 TP)
y el de menor conversión relativa: el revisor acertó 5 defectos
reales pero el PR escondía muchos más.

## 3. Agregados del subconjunto

- **Precisión grounded parcial = 55/106 = 51,9 %** (sobre emisiones:
  55 TP-grounded, 51 FP).
- **Recall grounded del subconjunto = 43/195 = 22,1 %** (micro,
  sobre TP gold distintos cubiertos). Como referencia secundaria,
  el promedio simple por PR (macro) es 24,1 %.
- **Cota sobre el set completo:** las emisiones de la nº 296 cubren,
  contadas una por una, **43 de los 352 TP = 12,2 %**. Es el piso de
  cobertura de *estas emisiones concretas* si los 10 PRs restantes
  aportaran cero — un hecho contado, no una estimación. **No** es
  el recall que daría una corrida completa ni es comparable con la
  linterna del papel v2.3 (recall base grounded > 0,7 % sobre 352,
  en corrida completa puntuada por la plataforma): esta
  adjudicación no evalúa esa regla y la práctica sigue FAILED.
- **Sesgo declarado del subconjunto:** los 15 PRs que completaron
  no son una muestra aleatoria de los 25 — son los que sobrevivieron
  al defecto del techo de tokens de la selección (y 3 de ellos solo
  al 2º/3er intento). Precisión y recall del subconjunto describen
  a esos 15 PRs; no se extrapolan a los 25.
- **Sensibilidad:** hay un match débil marcado por juicio del
  adjudicador (pika E1 → G0, §7). Sin él: precisión 50,9 %,
  recall del subconjunto 21,5 %, piso sobre 352 = 11,9 %. Ninguna
  conclusión de este informe cambia.
- **Contraste con la predicción del papel v2.3:** el papel predijo
  R_base de 1–3 % para la corrida completa puntuada por la
  plataforma. El piso contado acá (12,2 %) ya supera esa banda, con
  dos salvedades honestas: la predicción era para el puntaje
  grounded de la plataforma, no para una adjudicación manual con el
  criterio de la casa; y el subconjunto completado puede ser más
  favorable que el set entero.

## 4. Corte por familia: general vs especialidad

La pregunta que el Camino A vino a responder: ¿la vía general
produce verdaderos en diffs reales?

Atribución desde los `llm_run` de los `agent.log` del zip (la
selección que efectivamente corrió en cada PR):

- En **14 de los 15 PRs** completados, `selection_specialty`
  quedó **vacía**: ninguna pasada de especialidad corrió, así que
  todo hallazgo sobreviviente es de la **vía general por
  construcción**.
- El único PR con especialidad fue **CrabTrap**
  (`selection_specialty = ["sql_injection"]`): la pasada corrió y
  dejó **0 hallazgos sobrevivientes de su clase** — ninguna de las
  5 emisiones de CrabTrap reclama un defecto de inyección SQL; sus
  2 emisiones TP-grounded (el error tragado de `QuerySummaries` que
  termina en HTTP 200 con total positivo) vienen de las pasadas
  generales de reliability/api-architecture/correctness.

**Resultado del corte:**

| Familia | Emisiones TP-grounded | TP gold cubiertos |
|---|---|---|
| General | **55** | **43** |
| Especialidad | **0** | **0** |

Respuesta: **sí** — la vía general produce verdaderos grounded en
diffs reales: 55 emisiones grounded y 43 TP gold distintos, en 14
de 15 PRs y a través de las 9 categorías públicas. El matiz
honesto: esto no mide que la especialidad no sirva; mide que en
esta corrida casi no participó (1 selección en 15 PRs, 0
sobrevivientes). El contraste con el diseño anterior es el punto:
el techo grounded de un revisor restringido a las 19 clases era
0,3–2,6 % de recall (diagnóstico v2.2: 343/352 TP viven fuera de
las clases); la base v2.3, con la selección generalizada, cubrió
contando el 12,2 % del set completo solo con los PRs que
completaron.

## 5. Los casos alcanzables del diagnóstico v2.2

El diagnóstico de la v2.2 identificó ≤9 TP del gold dentro o en la
frontera de las 19 clases («alcanzables»). Seis caen en los 15 PRs
que completaron en la nº 296:

| Caso alcanzable | PR | ¿Detectado? |
|---|---|---|
| Cancelación tragada por el catch genérico, `DeviceMonitoringService.cs:184` (reliability) | LANdalf | **SÍ** — 3 emisiones grounded, vía general |
| Error de escritura de export descartado con `try?`, `ContentView.swift:151-152` (reliability) | pika | **SÍ** — E4, vía general |
| Sin guarda ante cambios de estilo concurrentes, `GenericRenderer.ts:229-244` (reliability) | konturio | **SÍ** — E3, vía general |
| Catch que cae a `{}` y borra las credenciales de otros workspaces, `storageDriver.ts:179-191` (correctness) | apilix | **NO** — hubo emisiones en la misma función (:185-190) pero sobre otros defectos (credenciales en texto plano, `lastSynced` ausente) |
| Lecturas de estado compartido en hilo de fondo, `Plugin.kt:550` | jadx | **NO** — las emisiones se concentraron en el spawn de hilos de :44-45 y en los tests |
| Count y query no transaccionales, `api.go:325` | CrabTrap | **NO** — la emisión vecina (:331) reclama otra cosa (rotura del contrato de respuesta) |

**3 de 6 detectados.** El contraste con la práctica nº 295 es
estructural: ahí los 9 alcanzables se perdieron **todos en la etapa
de selección**. Acá la selección generalizada eligió las categorías
correctas en los tres casos perdidos también — se perdieron en la
**pasada profunda**, no en la selección. Son dos hechos distintos:
la selección ya no es el cuello de botella; la pasada profunda
convierte alrededor de la mitad de los alcanzables que tiene a la
vista.

Sin veredicto posible: los dos casos de chronicle (el PR murió en
la nº 296) y el de Mcp-Docker (nunca intentado; su shard se cortó
en el preflight de plataforma).

## 6. Qué afirma y qué NO afirma esta medición

**Afirma (hechos contados sobre las emisiones reales de la 296):**

- De los 106 findings que la corrida alcanzó a emitir, 55 están
  grounded en TP reales del gold y cubren 43 TP gold distintos.
- Los 43 vinieron de la vía general (la especialidad aportó 0).
- La cobertura contada de estas emisiones sobre el set completo es
  43/352 = 12,2 % como piso.
- 3 de los 6 casos alcanzables del diagnóstico v2.2 que cayeron en
  el subconjunto fueron detectados esta vez (en la nº 295: 0 de 9,
  perdidos en selección).

**NO afirma:**

- No es un puntaje del portal ni re-califica la nº 296: la práctica
  sigue **FAILED por causa (d)** y sin puntajes oficiales. El
  matcher de la plataforma (augmented) no es este criterio y podría
  puntuar distinto.
- No evalúa la **regla de avance del papel v2.3** (linterna sobre
  352 en corrida completa): un subconjunto auto-seleccionado por
  supervivencia al defecto no puede pasar ni caer una linterna.
- No dice nada del **brazo ALMA** (no corrió en la 296), ni de la
  puerta 1.4.1, ni de pureza de retención, ni de la comparación
  ALMA vs base.
- Precisión y recall del subconjunto **no se extrapolan** a los 25
  PRs: los 10 restantes incluyen PRs que murieron 3/3 y 5 que nunca
  se intentaron.

**Lectura honesta:** la pregunta del Camino A quedó respondida con
margen — ensanchar la base a la vía general produce verdaderos
medibles en diffs reales, y el cuello se movió de la selección a la
pasada profunda. Lo que esta medición no resucita es la práctica:
para la linterna y la regla de avance sigue haciendo falta una
corrida completa puntuada, que exige primero arreglar el techo de
tokens de la selección (con papel o adenda) y una decisión de gasto
(el tope de US$30 del papel ya consumió US$13,50 en este intento).

## 7. Notas de adjudicación (casos borde y reglas aplicadas)

- **Gemelas gold acreditadas una vez:** NCATS G0/G9 (mismo defecto
  de manifiesto) y apilix G30/G20 (mismo defecto de snapshots
  huérfanos) — la segunda entrada de cada par no suma cobertura.
- **figlet G20:** entrada gold TP con el texto vacío en el
  manifiesto (:254-256); ningún revisor puede cubrir un defecto no
  enunciado. Se declara y se mantiene en el denominador (9).
- **Coincidencias con gold FP (cuentan FP, asentadas):** en
  TechDebtMCP, las emisiones de ReDoS caen sobre los gold FP G16/
  G17 y las de TOCTOU sobre el gold FP G3 — el mismo patrón de la
  v1: reclamos plausibles que el gold registra como FP. En figlet,
  E19 coincide con el gold FP G13. En ForgeMap, E5 (@import de
  Google Fonts, reclamo de performance) coincide en líneas con el
  gold FP G5 (reclamo GDPR): reclamos distintos sobre la misma
  línea — FP sin coincidencia de defecto.
- **Regla para reclamos de «falta test»:** una emisión cuenta como
  TP-grounded solo si enuncia el defecto con su mecanismo, aunque
  lo encuadre como gap de testing. Así, LANdalf E2 (enuncia la
  cancelación tragada por el catch) cuenta TP-grounded duplicada de
  G0, y jadx E2 *es* el defecto gold G6 (los tests que saltean la
  vía con hilos). En cambio pika E5 (falta test de la migración,
  sin enunciar el mecanismo del TP vecino G5) cuenta FP.
- **Match más débil (marcado):** pika E1 → G0 — la emisión y el
  gold describen el mismo defecto raíz del undo en paletas con
  nombre (el snapshot de `pushUndo` no cubre la paleta activa),
  con el daño encuadrado distinto (corrupción de la pila vs swap
  no restaurable). La sensibilidad sin este match está en §3.
- **CrabTrap E0/E3 → G2:** el defecto es una cadena (el helper
  traga el error y devuelve nil; el handler lo convierte en 200
  con total positivo); la emisión lo ancla en el helper y el gold
  en el handler. Mismo defecto, dos anclas — match asentado.
