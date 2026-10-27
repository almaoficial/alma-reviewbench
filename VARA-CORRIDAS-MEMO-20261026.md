# Memo — La vara numérica de las corridas: incertidumbre de la base nº 298 y efecto mínimo detectable

**Fecha:** 2026-10-26 (EDT). **Costo: US$0** — cómputo local
sobre datos ya pagados y adjudicados; sin llamadas a modelos,
sin portal, sin push. **Estado: BORRADOR.** La regla de
decisión de la §5 **no está firmada**: queda para la decisión
del 5/11/2026. Ningún papel vigente se modifica con este memo.

## 0. El problema que este memo cierra

Hasta hoy, cada «medición» de la línea es **una corrida paga
única** (~US$20) sin repetición. Con n = 1 por brazo, el ruido
de medición es indistinguible de un efecto real: un brazo que
suba 3 puntos de F1 puede haber mejorado, o puede ser el mismo
brazo en otro día. Este memo cuantifica ese ruido desde los
datos existentes de la base y fija **por escrito, antes de
correr**, cuánto tiene que superar un brazo a la base para que
cuente como mejora.

## 1. Datos usados (rutas exactas) y reproducción

Fuentes primarias, todas locales:

- Adjudicación grounded de la nº 298 (por emisión, con
  veredicto TP/FPG/GREY/NOVEL y puntero al gold):
  `~/workspace/alma-prototype/reviewbench/adjwork298/decisions.json`
- Emisiones crudas de la nº 298 (25 PRs):
  `adjwork298/run298/prs/<PR>/findings.json`
- Gold (352 TP / 213 FP sobre los 25 PRs):
  `adjwork298/gold/golden/*.json`
- Programa de agregación de la casa (sin tocar, solo corrido):
  `adjwork298/aggregate298.py`

**Reproducción exacta antes de computar nada nuevo:** el
programa de la casa cierra sin errores y devuelve los números
asentados de la base — emisiones 166, TP 89, TP gold cubiertos
66, FPG 8, GREY 17, NOVEL 52; gold 352 TP / 213 FP. De ahí:
P grounded = 89/166 = 53,61 %; R grounded = 66/352 = 18,75 %;
F1 grounded = 27,78 %; neto Breken (TP − FPG) = **+81**
(definición de `ADENDA-PUNTAJE-NETO.md` §2). Todo número de
este memo sale de este cómputo, en esta sesión.

**La nº 311 no entra al cómputo.** Su adjudicación existe solo
como papel (`ADJUDICACION-COMPLETA-311-20261022.md`: 1 emisión,
0 TP / 0 FPG / 1 GREY) — no hay `decisions.json` por reclamo
(defecto de observabilidad ya asentado). Con 1 emisión no hay
distribución que remuestrear; entra solo como antecedente.

## 2. Método

- **Unidad de remuestreo: el PR** (bootstrap por conglomerados,
  25 conglomerados). Las emisiones dentro de un PR no son
  independientes — mismo repo, mismo diff, misma pasada del
  modelo — así que remuestrear emisiones sueltas subestima el
  ruido (chequeo de la §6). Cada réplica sortea 25 PRs con
  reposición y recomputa P, R, F1, neto crudo y neto/100 desde
  las sumas remuestreadas, con las fórmulas de la casa.
- **B = 10.000 réplicas. Semilla fija: 20261026.**
  Intervalos: percentil 2,5–97,5 de la distribución bootstrap.
- **Ruido de la diferencia:** dos conjuntos independientes de
  réplicas del MISMO brazo (la base contra sí misma) dan la
  distribución de la diferencia cuando no hay efecto alguno:
  es el ruido que una comparación corrida-única contra
  corrida-única tiene que superar.

## 3. La incertidumbre de la base (nº 298)

| Métrica | Punto | DE bootstrap | IC 95 % | Ancho |
|---|---:|---:|---:|---:|
| P grounded | 53,61 % (89/166) | 6,6 pp | [41,3 % · 66,7 %] | 25,4 pp |
| R grounded | 18,75 % (66/352) | 1,9 pp | [15,0 % · 22,6 %] | 7,6 pp |
| F1 grounded | 27,78 % | 2,7 pp | [22,4 % · 33,1 %] | 10,7 pp |
| Neto crudo | +81 | 18,7 | [+49 · +122] | 73 |
| Neto / 100 em. | +48,8 | 7,9 | [+33,0 · +63,9] | 30,9 |

Lectura: la base no es «27,78 % de F1» — es **F1 entre 22 %
y 33 %** con la evidencia que hay. La precisión es el número
más flojo: su intervalo cubre 25 puntos, porque unas pocas
emisiones por PR la mueven mucho (hay PRs de 19 emisiones y
PRs de 1). El neto crudo, la vara absoluta de la casa, oscila
entre +49 y +122 según qué PRs caigan en la muestra.

## 4. Efecto mínimo detectable (EMD)

Diferencia entre **dos corridas únicas del mismo brazo** (sin
efecto real, solo ruido, según la §2):

| Métrica | DE de la diferencia | IC 95 % de la diferencia | EMD unilateral 95 % | EMD bilateral 95 % |
|---|---:|---:|---:|---:|
| P grounded | 9,3 pp | [−18,0 · +18,1 pp] | +15,4 pp | **+18,3 pp** |
| R grounded | 2,7 pp | [−5,4 · +5,5 pp] | +4,5 pp | **+5,3 pp** |
| F1 grounded | 3,9 pp | [−7,6 · +7,7 pp] | +6,4 pp | **+7,6 pp** |
| Neto crudo | 26,5 | [−52 · +53] | +44 | **+52** |
| Neto / 100 em. | 11,2 | [−21,4 · +22,0] | +18,4 | **+22,0** |

**La vara numérica de victoria** (EMD bilateral, la lectura
conservadora de la casa): para que una corrida única supere a
la base más allá del ruido tiene que mostrar, en la misma
corrida, **F1 grounded ≥ 35,4 %** (27,78 + 7,6) **y neto
crudo ≥ +133** (81 + 52). En unilateral (solo importa que
suba): F1 ≥ 34,2 % y neto ≥ +125. Referencia de escala: los
replays con puerta medidos sobre este mismo corpus movieron
la precisión entre +0 y +6 pp — **todos por debajo del EMD de
precisión (+18,3 pp)**: con corrida única, efectos de ese
tamaño son literalmente invisibles contra el ruido.

**Qué pasa si la corrida futura también es muestra única:**
nada la salva de esta tabla — la comparación hereda el ruido
de AMBAS corridas (por eso la DE de la diferencia es √2 veces
la de una sola). Tratar la base como valor fijo y cobrarle el
ruido solo a la corrida nueva subestima el EMD (F1 daría
+5,4 pp bilateral en vez de +7,6): queda asentado como el
error que este memo prohíbe.

## 5. BORRADOR de regla de decisión pre-registrada (SIN FIRMAR — decisión del 5/11)

Para la próxima corrida paga de la línea (mismo examen de
25 PRs, adjudicación completa grounded, neto reportado junto
a P/R según `ADENDA-PUNTAJE-NETO.md`):

1. **Victoria (provisoria):** ΔF1 ≥ **+7,6 pp** (F1 ≥ 35,4 %)
   **y** Δneto crudo ≥ **+52** (neto ≥ +133), en la misma
   corrida. Las dos: F1 es la vara sintética de P/R y el neto
   es la escala absoluta; una sola no alcanza.
2. **Sin regresión fuera de banda:** R no cae más de 5,3 pp
   ni P más de 18,3 pp contra la base (las bandas de ruido de
   la §4). Un «ganador» que compra F1 destruyendo recall
   fuera de banda no es victoria.
3. **Empate / ruido:** ΔF1 entre 0 y +7,6 pp, o Δneto entre
   0 y +52, sin cumplir (1) completo: **indistinguible de
   ruido**. No es victoria ni derrota; el brazo queda en sala
   de espera, no se adopta, y el resultado se asienta como
   «sin señal», no como «casi».
4. **Derrota:** ΔF1 ≤ −7,6 pp, o neto crudo ≤ 0 (regla
   Breken §3.3: con neto ≤ 0 ningún brazo se declara mejora).
5. **De provisoria a confirmada — la repetición de
   estabilidad.** Toda victoria de corrida única nace
   provisoria. La confirmación es la repetición ya diseñada
   en `PREREGISTRO-REPETICION-ESTABILIDAD.md`: repetir el
   brazo ganador **idéntico** (misma imagen, misma config,
   mismo examen, ~US$20,41, con su doble compuerta: saldo y
   confirmación de Alejandro al lanzar). Su objeto no es
   re-juzgar la vara — el veredicto no se revisa — sino
   descomponer el resultado en **clima** (lo que recurre
   entre corridas: señal) y **cielo** (lo de una sola
   corrida: ruido), el dato que hoy no existe del lado del
   revisor. Sin repetición comprada, la victoria queda
   asentada como provisoria para siempre.

## 6. Limitaciones (declaradas, no escondidas)

- **Este bootstrap mide la varianza entre PRs, no la
  varianza entre corridas.** Remuestrea qué PRs caen en el
  examen; NO remuestrea qué haría el modelo si corriera el
  MISMO examen otra vez (estocasticidad de generación +
  ruido del juez, el que el estudio clima/cielo ya vio del
  lado del juez: 3 de 7 eventos recurrentes). La corrida
  futura corre sobre los mismos 25 PRs, así que una parte
  de la heterogeneidad entre PRs se cancela en el diseño
  apareado — en ese sentido el EMD de la §4 es conservador
  para el diseño real — pero el componente corrida-a-corrida
  a examen fijo es **inobservable con n = 1**: solo la
  repetición de estabilidad de la §5.5 lo mide. La vara de
  este memo es, entonces, un piso de exigencia construido
  con la única varianza computable hoy, no el ruido total.
- **25 conglomerados es el piso de lo presentable** para un
  bootstrap por conglomerados: los intervalos son
  aproximados y sus extremos, frágiles.
- **La varianza de un brazo nuevo puede diferir de la de la
  base** (otro volumen de emisiones, otra mezcla por PR). El
  remuestreo usa la distribución de la base como modelo del
  ruido; es la única disponible sin gastar.
- **Chequeo del método:** el bootstrap ingenuo por emisión
  (ignorando el conglomerado) da para P un IC 95 % de
  [45,8 % · 61,5 %] — 10 puntos más angosto que el correcto
  por PR [41,3 % · 66,7 %]. Quien remuestree emisiones
  sueltas va a creer que la vara es más fina de lo que es.

## 7. Cierre

Antes de este memo, «mejorar» no tenía número: lo tenía la
corrida que saliera. Desde este borrador, la próxima corrida
nace sabiendo su vara — **F1 ≥ 35,4 % y neto ≥ +133, o es
ruido** — y sabiendo que su victoria, si llega, es provisoria
hasta que la repetición la descomponga en clima y cielo. La
firma de la §5 es decisión del 5/11, con el cheque sobre la
mesa y el total de la línea en un solo número, como manda la
regla de la casa.
