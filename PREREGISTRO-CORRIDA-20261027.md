# Pre-registro — corrida del 27/10/2026 (ReviewBench)

Firmado por Alejandro en el chat el 27/10/2026, 09:15 EDT («Corré hoy con la vara firmada»), ANTES de lanzar. Adelanta la decisión que el plan del 26/10 dejaba para el cheque del 5/11; la razón asentada: la carga ya fue hecha por él, y el resultado alimenta el juicio del 29/10.

## Qué se corre
- **Candidato:** v2.4 con el arreglo del tope (imagen `sha256:25c4b7e4…`, tope de salida 16.384 + un reintento interno a 32.768 ante vacío por `length`). Config: `reviewer=v24 · gate=v150`, freno `RB_MAX_SPEND_USD` como está configurado — no se toca.
- **Contra:** base nº 298 (congelada: P grounded 53,6 % · R 18,75 % · F1 27,8 % · neto +81).
- **Formato:** UN Test run de práctica (25 PR). **«Submit» JAMÁS.**
- **Costo de referencia:** US$20,41 (costo de la nº 298, portal · 22/10). Saldo previo asentado: US$7,05 (portal · 24/10). La carga de hoy la hizo Alejandro; el monto lo confirma el portal al abrir (queda asentado acá al volver el resultado).

## La vara (firmada hoy — borrador §5 de VARA-CORRIDAS-MEMO-20261026.md, adoptado)
- **Victoria provisoria:** ΔF1 ≥ +7,6 pp (F1 ≥ 35,4 %) **Y** Δneto ≥ +52 (neto ≥ +133) en la misma corrida, sin regresión de P/R fuera de banda.
- **Sin señal:** por debajo de victoria sin llegar a derrota → no se adopta, no se relanza «hasta que salga».
- **Derrota:** ΔF1 ≤ −7,6 pp o neto ≤ 0.
- **Confirmación:** SOLO con la repetición de estabilidad (PREREGISTRO-REPETICION-ESTABILIDAD.md), que se lanza únicamente tras victoria provisoria y con confirmación de Alejandro. Sin repetición, la victoria queda provisoria para siempre.
- **ENMIENDA 27/10 09:18 EDT (decisión de Alejandro en el chat: «No quiero hacer repetición»):** la repetición de estabilidad NO se corre. Consecuencia asentada: el techo de esta corrida es «victoria provisoria» — ningún resultado de hoy, por bueno que sea, habilita adopción. La carga necesaria baja a una sola corrida: US$20,41 − US$7,05 = US$13,36 (≈US$14).

## No se hace
- No se corre ningún otro brazo hoy. No se toca el freno ni la configuración. No se usa «Submit».
- El pipeline del semáforo con el protocolo apareado se construye hoy a la tarde igual (movimiento 1 del plan del 26/10): esta corrida no lo reemplaza.

## Lanzamiento (27/10/2026, verificado en el portal)
- **Corrida nº 373**, creada 09:21:16 EDT, Test run (25 PR), estado al lanzar: en cola.
- **Saldo al lanzar: US$32,05** (portal OpenAI · 27/10) — implica una carga de US$25 sobre los US$7,05 previos (computado).
- Config verificada en pantalla antes de lanzar: imagen `ghcr.io/almaoficial/alma-reviewbench@sha256:25c4b7e4d60cc05f43af26f07db24f94313692b73c5f480a6ce90c4bb431c106` (exacta), `reviewer=v24 · gate=v150`, modelo gpt-5.6-sol medium; el freno `RB_MAX_SPEND_USD` no se tocó. «Submit» nunca.

## Resultado nº 373 (27/10/2026, portal + salida descargada)
- Estado: SUCCEEDED (arrancó 09:21:16 EDT; verificada terminada 09:42). Salida del agente descargada: `~/workspace/browser_downloads/sess-1094806584/browser-download-20261027T134144.412206006Z-0-alma-reviewer-run-373-output.zip` (58 KB).
- Grounded: **F1 16,6 % · P 72,5 % · R 9,4 %**. Augmented: F1 23,8 % · P 76,7 % · R 14,1 %. Findings: 74 (31 novel). Duración media 1m34s por PR.
- Costo: **US$14,40** (diferencia de saldo OpenAI: 32,05 → 17,65; computado, el portal no muestra costo). Total histórico de la línea: 88,65 + 14,40 = **US$103,05 (piso)**.
- **Veredicto contra la vara firmada: DERROTA.** ΔF1 grounded = 16,6 − 27,8 = **−11,2 pp**, más allá de la línea de derrota (−7,6 pp). El neto no se muestra en el portal y no hace falta: el criterio de derrota por F1 ya está gatillado (la regla es «o»).
- Perfil: precisión +18,9 pp contra la base (53,6 → 72,5) y recall a la mitad (18,75 → 9,4); 74 findings contra 166 de la nº 298. El arreglo del tope curó la muerte de la nº 344 (la corrida terminó y costó menos) pero el v2.4 quedó mucho más selectivo. Causa del colapso de recall: SIN DETERMINAR — la autopsia US$0 sobre la salida descargada es el paso que lo responde.
- Consecuencia según la regla: el v2.4 se archiva con causa; no se relanza; el resultado entra al juicio del 29/10.
