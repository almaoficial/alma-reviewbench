# Adenda al resultado de la práctica v2.3.1 (nº 298) — desglose y linterna

**Fecha:** 2026-10-22 (EDT). **Costo de esta tarea: US$0** — sin
llamadas a modelos, sin lanzar corridas, sin tocar el portal en
vivo, sin modificar configuraciones ni papeles (salvo esta adenda
y el asiento de registro). **Relación con el cierre:** el
`RESULTADO-PRACTICA-V231-20261022.md` cerró la nº 298 con
«LINTERNA: NO PASA por ausencia de medición grounded acreditada»
tras agotar el portal y el zip. Esta adenda agrega las fuentes
que ese cierre no corrió — el cotejo aritmético del titular y una
acreditación por cota inferior desde fuentes primarias — y
**supersede solo el veredicto de la linterna**. Todo lo demás del
resultado (hechos de la corrida, costo real US$20,41, lectura de
falsadores) queda intacto.

## 1. Fuente 1 — el zip de outputs (agotado)

Inspección completa de los 58 archivos de
`runs/run-298-output.zip` (69.389 B, md5 `9a224fb4…`): `README.txt`,
`summary.txt`, `logs/run-status.jsonl`, 4 logs de shard y, por PR,
`agent.log` + `findings.json`. Búsqueda de `grounded`, `augmented`,
`precision`, `recall`, `score`, `f1`, TP/FP sobre todo el árbol:
**cero apariciones de puntajes o etiquetas** (las únicas menciones
son texto de hallazgos y el digest de la imagen). El zip acredita
las **emisiones** — `run-status.jsonl` y los 25 `findings.json`
suman **166**, idéntico al titular del portal; 25/25 PRs
`success` — y los `llm_run` de los `agent.log` acreditan revisor
`llm-reviewer/2.3.1`, puerta 1.3.0 y `parse_failures = []`. La
plataforma puntúa fuera del output del agente: **el zip no trae
ningún desglose Grounded/Augmented ni conteo TP/FP.**

## 2. Fuente 2 — el portal y las definiciones públicas

- La búsqueda exhaustiva del cierre (dos pasadas, con sesión:
  lista, detalle por PR, «Best run», configuración, «Final runs»,
  leaderboard público) ya consta en el resultado y en el registro:
  el titular «P 89.4% · R 34.5% · 166 findings · 88 novel» va **sin
  etiqueta** y el desglose no aparece en ninguna vista accesible.
  **Limitación declarada:** esta tarea corrió como subagente sin
  navegador en vivo y no pudo re-correr esa búsqueda; se apoya en
  la búsqueda documentada del cierre, no la repite ni la inventa.
- Precedente asentado del mismo portal y la misma lista: la
  nº 295 se muestra hoy solo como «P 15% · R 0.4%», que en su
  resultado corresponde a sus valores **Augmented** (Grounded
  0,0 %/0,0 %). Los valores de lista de este portal son la serie
  augmented.
- Definiciones públicas del benchmark (blog de GitHub y prensa,
  leídas hoy): **grounded** = contra el set dorado (352 TP del set
  de práctica); **augmented** = un juez acredita hallazgos
  novedosos válidos fuera del gold y el denominador del recall
  augmented **se expande con los descubrimientos propios** del
  agente; GitHub usa el recall grounded como vara de comparación
  entre sistemas. El «88 novel» del titular es un artefacto de la
  familia augmented: el puntaje grounded no tiene noción de
  «novedoso».

## 3. Fuente 3 — cotejo aritmético del titular

Con 166 emisiones y el gold de 352 TP, el titular **no puede ser
el grounded micro** — no existe entero que lo produzca:

| Lectura candidata | Cuenta | Resultado |
|---|---|---|
| P grounded micro, k/166 → 89,4 % | k debería caer en [148,32; 148,49] | **ningún entero** (148 → 89,2 %; 149 → 89,8 %) |
| P micro sobre 168 crudos, k/168 → 89,4 % | k ∈ [150,11; 150,28] | **ningún entero** |
| R grounded micro, k/352 → 34,5 % | k ∈ [121,26; 121,62] | **ningún entero** (121 → 34,4 %; 122 → 34,7 %) |

- La serie augmented tampoco es micro sobre (hallazgos, 352):
  en la nº 295, P augmented 15,0 % × 11 hallazgos = **1,65** y
  R augmented 0,4 % × 352 = **1,408** — fraccionarios: promedio
  macro por PR y/o crédito parcial del juez. El titular de la
  298 es por tanto **indescomponible** con lo visible: no se
  puede derivar de él ningún par grounded/augmented exacto.
- Consistencia (no acreditación): con la fórmula pública del
  recall augmented, (C + V)/(352 + V), el 34,5 % se reproduce
  exacto si C = 64 TP cubiertos y V = 88 novedosos todos válidos
  (152/440 = 34,545 % → 34,5 %). El mismo supuesto no reproduce
  el P — se asienta como consistencia de lectura con la familia
  augmented, no como medición.
- **Conclusión del desglose: NO ACREDITABLE.** Ni el zip, ni el
  portal accesible, ni la aritmética producen el par
  Grounded/Augmented de la nº 298. El 34,5 % es augmented (por
  precedente del portal y por imposibilidad aritmética de que
  sea grounded micro) y **no acredita por sí solo la linterna** —
  en eso el cierre tenía razón. La linterna se acredita abajo
  por otra vía.

## 4. La linterna, acreditada por cota inferior (fuentes primarias)

La linterna (papel v2.3 §6) exige recall base grounded > 0,7 %
sobre 352 TP — es decir, **≥ 3 TP gold distintos cubiertos**
(2/352 = 0,568 % no alcanza; 3/352 = 0,852 % sí). No hace falta
el recall exacto para acreditar el cruce: basta una cota inferior
verificada caso por caso con el criterio de la casa (mismo
archivo + mismo defecto/mecanismo; las líneas orientan, no son
compuerta; emisiones duplicadas = una cobertura), el mismo de la
adjudicación de la nº 296 que reprodujo los números del portal
en la nº 251. El lado gold de cada caso es la descripción leída
de `golden/*.json` y asentada en
`ADJUDICACION-PARCIAL-296-20261021.md` §5/§7 (registro primario
de la casa); el lado emisión es el `findings.json` de la nº 298
en el zip:

1. **LANdalf #88 — CUBIERTO (fuerte).** Gold: «Cancelación
   tragada por el catch genérico, `DeviceMonitoringService.cs:184`
   (reliability)». La 298 emitió **dos** hallazgos sobre ese
   archivo (líneas 173–186, rango que cubre la 184) que enuncian
   exactamente ese mecanismo: la `OperationCanceledException` del
   ping cae en el catch genérico y se convierte en un falso
   «dispositivo inalcanzable». Una cobertura.
2. **pika #200 — CUBIERTO (exacto).** Gold: «Error de escritura
   de export descartado con `try?`, `ContentView.swift:151-152`
   (reliability)». La 298 emitió en `ContentView.swift:152`:
   «The export write error is discarded with `try?`…» — mismo
   archivo, misma línea, mismo mecanismo, casi verbatim.
3. **apilix #12 — CUBIERTO (fuerte).** Gold: «Catch que cae a
   `{}` y borra las credenciales de otros workspaces,
   `storageDriver.ts:179-191` (correctness)». La 298 emitió en
   `storageDriver.ts:180-190` que en modo browser `store` queda
   `{}` y la función escribe solo la entrada del workspace
   actual, **borrando las configuraciones guardadas de los demás
   workspaces** — el mecanismo y el daño del gold. (Contraste
   asentado: en la nº 296 este caso fue casi-match y no contó;
   en la 298 la emisión enuncia el defecto gold mismo.)
4. **jadx-collaboration #3 — CUBIERTO (medio).** El registro de
   la casa (§7 de la adjudicación 296) caracteriza el gold G6 de
   este PR como «los tests que saltean la vía con hilos». La 298
   emitió en `PluginTest.kt:128` y `:138` exactamente eso: los
   helpers de test llaman `Plugin.pull()`/`Plugin.push()`
   directos en vez de la acción registrada, salteando la vía de
   despacho con hilos de fondo. Una cobertura.
5. **konturio #1230 — CUBIERTO (el más débil, declarado).**
   Gold: «Sin guarda ante cambios de estilo concurrentes,
   `GenericRenderer.ts:229-244` (reliability)». La 298 emitió en
   `GenericRenderer.ts:228-234` que el estilo se aplica sin
   importar `isVisible` y que el `willHide` posterior no puede
   deshacerlo — la aplicación asíncrona sin guarda pisa el cambio
   de estado concurrente, dentro del rango gold. Se acredita con
   el juicio asentado; un lector puede revocarlo sin tocar los
   casos 1–3.
- **Casi-match declarado (NO cuenta):** CrabTrap #15 — gold
  «Count y query no transaccionales, `api.go:325`»; la 298 ancló
  una emisión exactamente en `api.go:325` sobre el COUNT + la
  query separada, pero reclama un defecto de **performance**, no
  el de consistencia del gold. Mismo ancla, otro defecto: no es
  cobertura (precedente: ForgeMap E5 en la adjudicación 296).

**Cota acreditada:** 5 TP gold distintos verificados (3 fuertes
por sí solos). Recall grounded de la nº 298 **≥ 5/352 = 1,42 %**;
con solo los 3 casos fuertes, **≥ 3/352 = 0,85 %**. Cota
superior condicional: si «novel» significa fuera del gold (el
uso augmented del benchmark), las emisiones grounded son ≤ 78 y
el recall grounded ≤ 22,2 % — condicional a un término del
portal sin etiqueta, declarado como tal.

**Lo que esta cota NO acredita:** el par grounded exacto
(P/R/F1) ni el augmented de la nº 298, ni la regla de avance del
papel (que compara contra el brazo ALMA, todavía no corrido).
El camino a las cifras grounded exactas sigue siendo el que el
cierre nombró: la adjudicación completa de los 166 hallazgos
contra el gold público con la metodología de la 296 (US$0).

## 5. Veredicto

- **Desglose Grounded/Augmented de la nº 298: NO ACREDITABLE**
  con las fuentes agotadas (zip sin puntajes; portal sin
  etiqueta ni desglose en las vistas accesibles; titular
  aritméticamente imposible como grounded micro e
  indescomponible como augmented). Ningún valor de desglose se
  inventó ni se derivó en esta adenda.
- **LINTERNA: PASA** — acreditada por cota inferior adjudicada
  desde fuentes primarias: recall base grounded ≥ 0,85 % sobre
  352 TP (cota conservadora, casos 1–3) y ≥ 1,42 % contando los
  5 verificados, contra el umbral > 0,7 %. Este veredicto
  **supersede** el «NO PASA por ausencia de medición» del cierre:
  ese cierre fue correcto con las fuentes que corrió (portal y
  zip); esta adenda agrega la vía de adjudicación que el propio
  cierre señaló como el paso que podía dirimirla.
- **Consecuencia (Adenda 2 §6): la secuencia ALMA queda
  HABILITADA** — brazo ALMA con `gate=v141` sobre la misma
  imagen v2.3.1 (`sha256:144756cea4…`). Habilitada no es
  lanzada: esta tarea no ejecutó ningún paso de esa secuencia
  (prohibido), y el lanzamiento sigue sujeto a sus pasos propios
  (config ALMA a la imagen corregida con `gate=v141`, compuerta
  de saldo) y a una salvedad que esta adenda no reinterpreta:
  **el falsador de economía del §8 quedó registrado como
  GATILLADO en el cierre** (degradación 10/25 = 40 % > 1/4, con
  el texto «registrar y detener») y el propio resultado dejó su
  aplicación a la secuencia en manos de Alejandro. Con la
  linterna acreditada y ese falsador asentado, la decisión de
  lanzar el brazo ALMA es de Alejandro con ambos hechos sobre la
  mesa.
- La nº 296 sigue FAILED para siempre; la nº 298 queda
  SUCCEEDED con su linterna acreditada por cota y su desglose
  exacto pendiente de la adjudicación completa (US$0) si se
  quiere la cifra, no el cruce.

— Adenda de acreditación, 2026-10-22. Fuentes: zip de outputs de
la nº 298 (inspección completa), cierre
`RESULTADO-PRACTICA-V231-20261022.md` y su búsqueda del portal
documentada, definiciones públicas del benchmark (blog de
GitHub), `ADJUDICACION-PARCIAL-296-20261021.md` (criterio y lados
gold), cotejo aritmético propio reproducido en §3–§4.
