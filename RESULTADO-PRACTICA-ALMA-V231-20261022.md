# Resultado formal — Práctica ALMA v2.3.1, corrida nº 310 (2026-10-22)

## Estado terminal

- **Corrida nº 310 (brazo ALMA): FAILED** — portal review-bench.ai, agente
  `alma-reviewer`, lista de corridas (lectura 2026-10-22 ~07:26–07:28 EDT).
- Config verbatim de la fila: «#310 · llm · alma · gpt-5.6-sol · medium ·
  v23 · v141» — `backend=llm, governance=alma, model=gpt-5.6-sol,
  effort=medium, reviewer=v23, gate=v141`.
- Imagen: `ghcr.io/almaoficial/alma-reviewbench@sha256:144756cea49ee33e8b16ddb0204556adb0f1c2430ea885ec6a206bbaa6964544`
  (v2.3.1; el portal muestra el digest truncado en la fila y completo en
  los logs de shard del zip).
- Lanzada: **2026-10-22 07:15:27 EDT** (única marca temporal que muestra
  el portal), por autorización expresa de Alejandro (Adenda 3 al
  pre-registro v2.3).
- Error / etapa verbatim del portal: **«failed at run-agent (4, 4) /
  Run the vendor agent over this shard»**.

## Puntajes del portal — sin titular

- Puntajes verbatim: **«P — · R —»** (guiones, sin porcentajes).
- **Sin línea de hallazgos:** el portal no muestra total ni novedosos
  para la nº 310 (a diferencia de una corrida exitosa, p. ej. la nº 298
  con «166 findings · 88 novel»), y no hay botón «per PR».
- **Salvedad declarada:** no hay titular que reportar. Cuando el portal
  muestra un titular P/R, ese titular es la familia **augmented** (la
  puntúa un juez; el grounded del portal no es acreditable, según la
  acreditación de la nº 298). En la nº 310 ni siquiera existe ese
  titular: la corrida murió antes de emitir.

## Causa — leída en los outputs, no inferida

- Zip de outputs descargado del enlace «agent output»
  (`/api/vendors/alma-reviewer/runs/310/output`): **8.317 B, md5
  `9ca633217892948294f7991c30b07c92`**; copia idéntica en
  `runs/run-310-output.zip` y en `~/workspace/browser_downloads/`.
- Contenido: 13 archivos. `summary.txt`: «The run ended with errors» —
  **4 PRs alcanzados de 25, 0 succeeded, 4 en `error:2`** (3 intentos
  c/u, ~182–183 s por PR); los 4 shards se detuvieron en su primer PR
  por preflight; 21 PRs nunca alcanzados. `findings = null` en los 4;
  ningún `findings.json` en el zip.
- **Causa exacta, idéntica en los 4 shards y en los 4 `agent.log`:**
  «alma-reviewbench error: backend=llm v2.3 refused: unknown gate
  version 'v141'; expected 'v1', 'v11', 'v12', 'v13' or 'v14'
  (RB_CONFIG_GATE); **no model call was made**».
- Lectura: el revisor v2.3 dentro de la imagen v2.3.1 **rechaza la
  etiqueta `gate=v141` en su lista de versiones admitidas** antes de
  cualquier llamada al modelo. La cabecera de cada `agent.log` sí
  declara `validator=alma-evidence-gate/1.4.1` con su
  `policy_sha256=73a403d8…`, pero la validación de config del revisor
  LLM corta primero: la puerta nunca llegó a operar sobre emisión
  alguna porque no hubo emisiones.
- Esto es un defecto de integración/configuración de la corrida ALMA
  (la etiqueta pre-registrada en la Adenda 3 no es aceptada por el
  propio revisor publicado), no un resultado sobre el efecto de la
  puerta 1.4.1.

## Costo real

- Saldo previo (portal de billing, org Personal, 07:13 EDT, asentado
  al lanzar): **US$25,58**.
- Saldo actual (Billing > Overview, org «Personal», lectura
  2026-10-22 ~07:29–07:33 EDT): **API credit balance US$25,58**
  (wallet US$0,00).
- **Costo real por diferencia: US$25,58 − US$25,58 = US$0,00** —
  consistente con el «no model call was made» de los cuatro shards.

## Regla de avance variante (ii) — SIN MEDIR

- Declaración pre-registrada (Adenda 3 §4): la regla de avance
  variante (ii) se evalúa sobre la **adjudicación local completa**
  de las emisiones ALMA contra el gold — vara **P_ALMA grounded
  ≥ 58,6 %** (= 53,6 % adjudicada de la base + 0,05), **pureza de
  retención ≤ 1 de cada 3**, **pérdida inexplicada = 0**, F1
  reportado y no compuerta.
- **Aplicación a la nº 310: no hay nada que adjudicar.** Emisiones =
  0, `findings.json` = ninguno, conteos de la puerta (aceptados /
  `needs_validation` / rechazados) = sin datos porque la corrida
  murió en la validación de config, antes del revisor y de la puerta.
  La precisión grounded es **indefinida (0/0)**, no cero.
- **Veredicto: el efecto de la puerta 1.4.1 queda SIN MEDIR** y así
  se asienta, como manda la propia Adenda 3 §4 para el caso en que
  la adjudicación no pueda ejecutarse («el efecto queda "sin medir"
  y así se asienta — no se sustituye por el titular»). Acá ni
  siquiera hay titular con el que sustituirlo.
- La pérdida está **explicada por completo** (rechazo de `v141` en
  los 4 shards, con el texto exacto), pero esa explicación es de la
  falla de la corrida, no la «pérdida inexplicada = 0» de la vara,
  que mide emisiones perdidas por la puerta y no aplica sin emisiones.

## Cierre

- La corrida ALMA era el **último acto del papel v2.3** (Adenda 3
  §5): con este resultado asentado, la línea de revisores de este
  papel se cierra — FAILED por causa propia de integración, efecto
  de la puerta sin medir, costo US$0,00. Cualquier continuación
  (corregir la lista de versiones del revisor para admitir `v141`
  y relanzar) es **un papel nuevo y una decisión nueva de
  Alejandro**: esta vigilancia no relanza nada, no toca «Submit»,
  no modifica configuraciones.
- Vigilancia `vigilar-practica-alma-v231`: se elimina en esta misma
  pasada, como manda su protocolo ante estado terminal.
- Gasto de esta pasada de cierre: **US$0** — solo lectura del portal,
  lectura de billing, descarga del zip y cotejo local.
