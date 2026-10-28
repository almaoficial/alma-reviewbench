# BORRADOR SIN FIRMAR — Adenda 4 al pre-registro ReviewBench v2: decisión del tope

_Preparado el 2026-10-20 para la decisión que Alejandro difirió el 19/10: «Lo del tope lo definimos mañana antes de lanzar». Este borrador NO forma parte del pre-registro hasta que Alejandro lo apruebe y se asiente fechado en `PREREGISTRO-REVIEWBENCH-V2.md`. El papel congelado no se editó._

## El conflicto, con números del propio papel
- §5 del pre-registro (congelado): práctica v2 completa (2 brazos × 25 PRs) estimada en US$15–25, **tope duro US$30**, freno por PR de US$5,00. Esa estimación suponía 9 pasadas por PR.
- Adenda 3 (20/10 00:46 EDT): el revisor final corre **19 pasadas** por PR (puerta 1.3.0, 19 clases). Estimación de peor caso asentada en el propio papel: **≈US$5,97 por PR**, por encima del freno del portal (RB_MAX_SPEND_USD = 5,00).
- La estimación realista comunicada la noche del 19/10 para la pareja de corridas: **US$30–60** — es decir, el tope congelado de US$30 puede no alcanzar, y ampliarlo «en caliente» está prohibido por el propio §5.

## La medición que ordena la decisión (ya aprobada y paga)
El simulacro semáforo (tope US$20, 8 códigos sintéticos, ambas configuraciones reales, una sola pasada) corre ANTES de la práctica y su función declarada incluye medir el **costo real por código**. Con ese dato, la decisión deja de ser una apuesta:

**Costo proyectado de la práctica = costo real por código del semáforo × 50 (25 PRs × 2 brazos).**

## Regla de decisión propuesta (a aprobar o corregir por Alejandro)
1. **Proyección ≤ US$30** → no hay adenda: corre el tope congelado de US$30 tal cual.
2. **US$30 < proyección ≤ US$60** → esta adenda, si se firma, enmienda el tope duro a **US$60** para la práctica v2, sin tocar ninguna otra cláusula: freno por PR, regla de avance, anti-pesca y «no ampliar en caliente» quedan intactos. Si la proyección supera US$60 a mitad de corrida, la práctica se detiene y se registra así — el nuevo tope tampoco se mueve en caliente.
3. **Proyección > US$60** → no se lanza la práctica; se registra el freno por costo y se decide de nuevo con el dato a la vista.

## El freno por PR, decisión gemela
- Si el semáforo muestra costo real por código cercano o mayor a US$5,00, el freno del portal puede cortar PRs a mitad de la práctica y arruinar la corrida válida (la primera que completa en cada brazo es la que cuenta, §4).
- Subir RB_MAX_SPEND_USD en la bóveda del portal es **acción de Alejandro** (él carga credenciales y valores, nunca por chat) y, si se hace, se declara en el manifiesto v2 antes de lanzar — como ya advierte la nota operativa de la Adenda 3.

## Lo que este borrador no hace
No autoriza gasto alguno, no lanza ninguna corrida y no modifica el pre-registro. La secuencia sigue siendo: Micro1 → semáforo (US$20 ya aprobado) → decidir el tope con el costo real → recién ahí, práctica v2 con el «sí» de Alejandro al momento de lanzar (§7.3).
