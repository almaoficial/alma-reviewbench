# Resultado formal — Práctica ALMA v2.3.2, corrida nº 311 (2026-10-22)

## Estado terminal

- **Corrida nº 311 (brazo ALMA): SUCCEEDED** — portal review-bench.ai,
  agente `alma-reviewer`, lista de corridas «Test runs» (test set,
  25 PRs); lecturas 2026-10-22 ~08:29–08:35 EDT.
- Config verbatim de la fila: «#311 · llm · alma · gpt-5.6-sol ·
  medium · v23 · v141» — `backend=llm, governance=alma,
  model=gpt-5.6-sol, effort=medium, reviewer=v23, gate=v141`.
- Imagen: `ghcr.io/almaoficial/alma-reviewbench@sha256:fbf1fe48364f915fed703a0a618bea48e0e7b379f7afaa645b8b4bf712850498`
  (v2.3.2, según el manifiesto de la corrida asentado al lanzar).
- Lanzada: **2026-10-22 08:08:14 EDT** (marca verbatim del portal:
  «10/22/2026, 8:08:14 AM»). Es el relanzamiento autorizado por la
  **Adenda 4** al pre-registro v2.3 (la nº 310 murió por la falla de
  admisión de cableado de `gate=v141`, costo US$0, sin medición; la
  v2.3.2 espejó la rama v141 en el resolvedor del revisor).
- **Sin error:** la corrida no muestra etapa ni mensaje de error.
  En particular, **la firma de admisión de la Adenda 4
  («unknown gate version 'v141'») NO reapareció**: la reparación
  quedó confirmada en admisión — la corrida corrió completa.

## Puntajes del portal — titular augmented, con su salvedad

- Puntajes verbatim de la fila: **«P 0 % · R 0 %»**. El portal no
  muestra F1 para esta corrida, ni en la fila ni en la vista por PR.
- Hallazgos verbatim: **«1 findings · 0 novel»** (total 1,
  novedosos 0).
- **Salvedad declarada:** este titular P/R es la familia
  **augmented** (la puntúa un juez; el grounded no es acreditable
  desde el portal, según la acreditación de la nº 298). El par
  grounded exacto de esta corrida solo sale de la adjudicación
  local completa contra el gold, que sigue a este cierre.
- Par de comparación pre-registrado: base nº 298, grounded exacto
  adjudicado **P 53,6 %, R 18,75 %** (166 hallazgos).

## Outputs — verificados en disco

- Zip descargado del enlace «agent output»
  (`/api/vendors/alma-reviewer/runs/311/output`): **42.425 B, md5
  `fd97ee0f28c6bbffe8ae2b7ee141857f`**; copias idénticas (mismo md5)
  en `~/workspace/browser_downloads/alma-reviewer-run-311-output.zip`
  y en `runs/run-311-output.zip`.
- Contenido: 58 archivos. `summary.txt`: «25 pull requests:
  25 succeeded, 0 did not» — los 4 shards cerraron y el único
  hallazgo emitido está en
  `DisciplinedSoftware_Codebase-Conversion_1` (1 finding; los otros
  24 PRs, 0). Hay `findings.json` y `agent.log` por PR: es el
  insumo completo de la adjudicación (emitidos, retenidos en
  `needs_validation` y rechazados por la puerta, desde los
  run-info).

## Costo real

- Saldo previo (portal de billing, org Personal, 08:08 EDT,
  asentado al lanzar): **US$25,58**.
- Saldo actual (Billing > Overview, org «Personal», lectura
  2026-10-22 ~08:32–08:35 EDT): **API credit balance US$5,31**
  (wallet US$0,00).
- **Costo real por diferencia: US$25,58 − US$5,31 = US$20,27.**

## Regla de avance variante (ii) — se evalúa sobre la adjudicación

- Declaración pre-registrada (Adenda 3 §4, conservada por la
  Adenda 4): la regla de avance variante (ii) de la Adenda 3 §4 se
  evalúa sobre la **adjudicación local completa** que sigue a este
  cierre — vara **P_ALMA grounded ≥ 58,6 %** (= 53,6 % adjudicada
  de la base nº 298 + 0,05), **pureza de retención ≤ 1 de cada 3**,
  **pérdida inexplicada = 0**.
- **No se sustituye por el titular:** el titular augmented del
  portal (P 0 % · R 0 %, 1 hallazgo) NO es el veredicto de la
  regla. Con una sola emisión, la adjudicación completa es la que
  dirá la precisión grounded de esa emisión y, desde los run-info,
  cuántos candidatos retuvo (`needs_validation`) o rechazó la
  puerta 1.4.1 — ese conteo es el efecto de la puerta que esta
  práctica vino a medir.
- Estado al asentar: **adjudicación del efecto EN CURSO** (insumo
  ya en disco, verificado arriba).

## Cierre

- La corrida ALMA era el **último acto del papel v2.3**: con este
  resultado asentado, la práctica queda cerrada en el portal —
  SUCCEEDED, titular augmented P 0 % · R 0 %, 1 hallazgo ·
  0 novedosos, costo real US$20,27 — y el juicio del efecto de la
  puerta 1.4.1 queda enteramente en la adjudicación local completa.
- Vigilancia `vigilar-practica-alma-v232`: se elimina en esta
  misma pasada, como manda su protocolo ante estado terminal.
- Gasto de esta pasada de cierre: **US$0** — solo lectura del
  portal, lectura de billing, descarga del zip y cotejo local.
  No se lanzó ninguna corrida, no se tocó «Submit», no se
  modificaron configuraciones ni la config BASE ni
  `RB_MAX_SPEND_USD`.
