# Pre-registro CONDICIONAL — Repetición de estabilidad del brazo ganador de la validación del 24/10

**Fecha de este papel:** 2026-10-23. **Aprobación del
diseño:** Alejandro, 23/10/2026 («Bueno»), como tercera pata
de la recomendación adoptada ese día (puerta de recurrencia
+ la corrida del 24/10 no se toca + esta repetición si hay
ganador). **Costo de este papel: US$0.** Este papel **NO
autoriza el gasto**: la repetición solo se lanza con la
compuerta de la §5 cumplida y la confirmación de Alejandro
en el momento del lanzamiento.

## 1. Condición de disparo (sin ella, este papel no existe)

Que **un brazo** de la validación del 24/10 — v2.4, v2.5 o
v2.6 — **supere la vara** de `PREREGISTRO-VALIDACION-20261024.md`
§2 (la del diseño estacionado §4 del papel del productor +
`ADENDA-PUNTAJE-NETO`: neto reportado junto a P/R y neto
crudo ≤ 0 no declarable mejora), con adjudicación completa
bajo la regla de su §6 (registro de sesión auditado completo
antes de adjudicar).

**Si ningún brazo gana mañana, este pre-registro queda SIN
EFECTO** y se asienta así en el REGISTRO, sin más trámite.

## 2. El objeto: repetir al ganador, idéntico

- **Brazo:** el que supere la vara (si más de uno la supera,
  el de mayor neto crudo; el desempate, si hiciera falta, lo
  asienta el papel de la corrida del 24/10 antes de lanzar
  esta repetición).
- **Imagen:** la misma de la validación, digest asentado en
  la §4 de su papel —
  `ghcr.io/almaoficial/alma-reviewbench@sha256:a46ca3791f13936b459c726253ba9a484b6d363b9a067a9e6859e26620b3f501`
  — como `RB_IMAGE_SHA256`.
- **Config:** idéntica a la del brazo en la validación
  (backend `llm`, modelo gpt-5.6-sol, esfuerzo medium, modo
  `alma`, `RB_CONFIG_REVIEWER` y `RB_CONFIG_GATE` del brazo
  ganador, freno por PR **`RB_MAX_SPEND_USD` = US$6,50 —
  intocable**).
- **Examen:** el mismo «Test run» de 25 PRs. **Un solo
  lanzamiento. «Submit» JAMÁS.**

## 3. El propósito declarado (y lo que esta repetición NO es)

**Propósito:** descomponer el error del brazo ganador en
**clima** (error que recurre entre las dos corridas del mismo
brazo) y **cielo** (error de una sola corrida), con las
definiciones congeladas de `ADENDA-RECURRENCIA.md`. Es la
primera medición de recurrencia del lado del revisor — el
dato que la `ADENDA-PUERTA-RECURRENCIA.md` (§4) declara
faltante y del que depende su falsador.

**NO es una segunda oportunidad ante la vara.** El veredicto
de la validación del 24/10 queda como se adjudique mañana y
**no se revisa** con esta repetición: ni lo confirma ni lo
rehace. La adjudicación de ESTA corrida es la recurrencia
entre las dos, no el puntaje de ninguna.

## 4. Procedimiento y adjudicación de la recurrencia

1. **`RB_RUN_ID` único** (p. ej. `estabilidad-20261025-v26`),
   distinto del de la validación. **`run-ledger.jsonl` es
   salida requerida** y se audita (cadena + completitud)
   **antes** de adjudicar, por la misma regla vinculante de
   la §6 del papel de la validación: si no audita completo,
   se diagnostica, no se adjudica.
2. **Adjudicación completa** de esta corrida contra el gold,
   con el mismo procedimiento de las nº 298/311 y de la
   validación — necesaria no para re-puntuar al brazo, sino
   para tener las celdas de error comparables.
3. **El cruce (el entregable):** por cada celda de error
   adjudicada en cualquiera de las dos corridas del brazo
   (la del 24/10 y esta): error en **ambas** = **CLIMA**;
   error en **una sola** = **CIELO**; sin celdas mixto (con
   dos observaciones no hay término medio). Se reportan:
   conteos absolutos por clase, fracción aprendible estricta
   y laxa según `ADENDA-RECURRENCIA.md`, y el espejo del lado
   de los aciertos (emisiones TP recurrentes vs. de una sola
   corrida). El neto de cada corrida se reporta como contexto
   (`ADENDA-PUNTAJE-NETO`), **sin** re-veredicto.
4. **Reconciliación:** el `spend` estimado del registro
   contra el saldo real de la cuenta, asentado en el papel
   de esta corrida.

## 5. Economía y compuerta de lanzamiento

- **Costo estimado: ~US$20,41** — el costo real de la nº 298,
  la referencia de la línea para una pasada completa del
  examen (los brazos de la validación se estiman en el mismo
  rango, ~US$20–21).
- **Compuerta (las dos, vinculantes):** saldo de la cuenta
  verificado **≥ US$25** antes de lanzar, **y** confirmación
  de Alejandro en el momento del lanzamiento. Este papel con
  su «Bueno» de diseño no sustituye ninguna de las dos.

## 6. Altos

Si la repetición muere por causa propia (admisión, parseo,
freno), se registra igual, con su costo real, y **no se
relanza**: la descomposición queda sin medir y se asienta
así. La única excepción de la línea es el corte de
infraestructura, declarado en el acto — el mismo criterio
del papel de la validación §8.

— Pre-registro condicional escrito el 2026-10-23, antes de
conocerse el resultado de la validación del 24/10. Su
disparo, su sin-efecto o su resultado se asientan en el
REGISTRO a su tiempo.
