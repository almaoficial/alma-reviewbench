# Resultado del semáforo — ReviewBench v2.3 (2026-10-21)

**VEREDICTO: VERDE para el brazo base** — el único brazo corrido.
El brazo base emitió sobre los 8 códigos (16 hallazgos, **8/8
defectos plantados detectados**), la guardia no se negó en ningún
código y la regla de degradación no se disparó en ninguno: ninguno
de los criterios de ROJO de la §9 del pre-registro v2.3 se gatilló.
**Costo real total: US$0,53607** (tope duro US$20 — 2,7% usado).

**El brazo ALMA NO se corrió, por diseño pre-registrado, no por
falla de esta corrida:** la puerta 1.4.0 no pasó su medición de
adopción (§6 de su papel: falsos nuevos = 1 ≠ 0; ver
`RESULTADO-MEDICION-PUERTA-140.md`), y la §4 del papel v2.3 prohíbe
correr el brazo ALMA con otra puerta en su lugar — no hay
sustitución silenciosa por la 1.3.0. El VERDE de la §9 está escrito
para dos brazos («ambos brazos emiten»); acá se declara contra el
brazo que corrió, con esta salvedad asentada: **este semáforo no
dice nada del brazo ALMA**, ni a favor ni en contra.

**Medición central: la vía de especialidad sobrevivió al ensanche.**
La selección generalizada marcó la clase plantada en **8/8**
códigos (familia especialidad) y su pasada profunda la detectó en
**7/8**; el octavo caso (sem_02) lo rescató la vía nueva: la
categoría general `security` — marcada en los 8 códigos — produjo
el hallazgo que cubre el defecto. La selección marcó además
`reliability` en 2 códigos (sem_07, sem_08). Marcas desconocidas:
0. Overflow: vacío en los 8. Degradación: ninguna. Detalle en §3–§5.

## 1. Autorización y vía de clave

- «Corre» de Alejandro al semáforo v2.3 brazo base, 21/10/2026
  21:35 EDT, sobre la estimación declarada del papel (§11, paso 5:
  esperado US$1–3 para ambos brazos, tope duro US$20). El brazo
  base solo costó US$0,53607 — bajo la banda esperada porque corrió
  un solo brazo y la batería es miniatura.
- Clave por la vía sancionada: conector de bóveda
  `custom.openai-rbench`. El ejecutor obtuvo el valor sustituto en
  memoria (`dynamic_credentials`) y lo pasó solo en el entorno de
  los procesos de la corrida; la capa de salida lo intercambia por
  la clave real únicamente hacia `api.openai.com`. El valor no se
  imprimió ni se escribió en ningún archivo, log ni informe.
- Sonda previa a costo cero: **HTTP 200** (`GET /v1/models`, 133
  modelos, `gpt-5.6-sol` visible) antes de gastar un centavo.
- Papel que manda: `PREREGISTRO-REVIEWBENCH-V23.md` §9 (qué puede
  afirmar este semáforo y criterios de veredicto) y §11 (secuencia
  y frenos), congelado antes de correr.

## 2. Verificaciones previas (costo cero, en regla)

- **Batería congelada íntegra:** los 32 archivos de
  `fixtures_semaforo/` (8 casos × diff.patch, pr.json,
  ground_truth.json y archivo head) coinciden en bytes y sha256 con
  `MANIFIESTO-BATERIA.json` (congelado 2026-10-20). Sin extras ni
  faltantes. Los 8 códigos llevan defectos plantados **de clase**
  (no hay códigos de control separados en esta batería).
- **Puertas congeladas intactas:** el archivo de la 1.3.0 da sha256
  `d3b993d4d4f26b9df112dfd54abc391e8018faae024d23c63b4924d86d2dc1e0`
  (y los de 1.0.0/1.1.0/1.2.0, `4223cb05…` / `fdd974f1…` /
  `c5c32bfc…`); las cuatro constantes POLICY_SHA256 coinciden con
  lo asentado (1.0.0 `3ad514ed…`, 1.1.0 `6a7a7aa4…`, 1.2.0
  `a768afa4…`, 1.3.0 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`).
  Todos los ledger de esta corrida llevan el POLICY_SHA256 de la
  1.3.0 (la puerta declarada del brazo base, omitida al validar).
- **Suite completa en seco: 208/208** (mock, US$0) — 163 heredadas
  + 27 de la puerta 1.4.0 + 18 del revisor v2.3.
- **Regla de puntuación** (la misma de las corridas v2, v2.1 y
  v2.2): un caso cuenta como detectado si algún hallazgo emitido
  cae en el archivo del ground truth y su rango de líneas cubre la
  línea del defecto plantado.

## 3. Resultados por caso (brazo base)

Configuración: `RB_CONFIG_REVIEWER=v23`, `RB_CONFIG_GATE=v13`
(puerta declarada, omitida al validar — brazo base), modelo
gpt-5.6-sol, effort medium, `ALLOW_REAL_LLM=1`,
`RB_MAX_SPEND_USD=6.50` por PR, tope duro acumulado US$20. Costo =
estimación del propio revisor desde el uso reportado por la API,
sumando todas las llamadas del código (selección + profundas). En
los 8 códigos: `malformed = 0`, `unanchored = 0`, marcas
desconocidas = 0, entradas malformadas de selección = 0, overflow
vacío, degradación nula, exit = 0, sin re-corridas.

| Caso (defecto plantado) | marcas especialidad | marcas generales | profundas | crudos | emitidos | acierta | costo |
|---|---|---|---|---|---|---|---|
| sem_01 sql_injection | sql_injection | security | 2 | 2 | 2 | sí — ambas vías | 0,06708 |
| sem_02 hardcoded_secret | hardcoded_secret | security | 2 | 1 | 1 | sí — **solo vía general** | 0,05706 |
| sem_03 tls_verification_disabled | tls_verification_disabled | security | 2 | 2 | 2 | sí — ambas vías | 0,05541 |
| sem_04 unsafe_deserialization | unsafe_deserialization | security | 2 | 2 | 2 | sí — ambas vías | 0,05616 |
| sem_05 weak_hash | weak_hash | security | 2 | 2 | 2 | sí — ambas vías | 0,06103 |
| sem_06 jwt_verification_disabled | jwt_verification_disabled | security | 2 | 2 | 2 | sí — ambas vías | 0,05673 |
| sem_07 debug_mode_enabled | debug_mode_enabled | security, reliability | 3 | 2 | 2 | sí — ambas vías | 0,09271 |
| sem_08 command_execution | command_execution | security, reliability | 3 | 3 | 3 | sí — ambas vías | 0,08988 |
| **Total** | **8/8 plantadas marcadas** | security 8/8 · reliability 2/8 | **18** | **16** | **16** | **8/8** | **US$0,53607** |

Llamadas totales: 26 (8 de selección + 18 profundas). Tokens:
22.483 de prompt, 2.651 de completion. Las 16 emisiones caen todas
sobre el archivo y la línea del defecto plantado de su caso — cero
emisiones fuera de blanco en la batería.

## 4. Anatomía de los fallos conocidos (diagnóstico, sin ajuste)

- **sem_02 — el silencio de la profunda de clase REAPARECIÓ, pero
  ya no cuesta el caso.** La selección marcó `hardcoded_secret` y
  su pasada profunda corrió, y devolvió **cero candidatos** — el
  mismo silencio asentado en la v2 (brazo ALMA), la v2.1 (brazo
  base) y la v2.2 (ambos brazos). La diferencia de anatomía contra
  la v2.2: acá `raw = 1`, no 0 — la pasada general de la categoría
  `security` produjo el candidato (`app/billing.py:6`, la clave de
  Stripe plantada) y el caso puntuó detectado **por la vía
  general, no por la de especialidad**. El rescate es exactamente
  el mecanismo que el camino A vino a construir; se asienta como
  lo que es: en esta batería la vía general cubrió el hueco de la
  vía de clase en 1 de 8 casos.
- **sem_01 — el rechazo de cita de la puerta NO aplica a este
  brazo.** Ese fallo (v2, v2.1 y v2.2) es del brazo ALMA: la puerta
  1.3.0 rechazando el candidato `sql_injection` por co-ocurrencia
  de la cita. El brazo base no pasa por la puerta: emitió el
  candidato de especialidad (`app/orders.py:11–14`, cubre la línea
  13 plantada) y también el de la pasada `security` — igual que el
  base de la v2.2. Nada puede decirse desde esta corrida sobre ese
  rechazo: el brazo ALMA no corrió y la 1.4.0 no fue adoptada.

## 5. Mediciones declaradas (§9 del papel)

- **Marcas por familia:** especialidad 8/8 (siempre la plantada,
  siempre en primera posición de la lista mezclada); general:
  `security` 8/8, `reliability` 2/8 (sem_07, sem_08). Tope
  compartido de 5: nunca alcanzado (máximo 3 marcas por código);
  `selection_overflow` vacío en los 8.
- **Detección por vía:** vía especialidad 7/8 (falla solo sem_02,
  por silencio de su profunda); vía general 8/8 (el hallazgo de la
  pasada `security` cubre la línea plantada en todos los casos —
  esperado en una batería cuyos 8 defectos son de seguridad; ver
  la declaración de alcance en §7).
- **Pasadas profundas corridas:** 18 (2 por código; 3 en sem_07 y
  sem_08), todas con el formato de la v2 para marcas de clase y la
  misma plantilla para marcas de categoría.
- **Degradación:** ninguna en los 8 códigos (`degradation` nulo en
  todos los run-info); el fallback del caso degenerado no se
  invocó. Peor código: US$0,09271 contra el freno por PR de
  US$6,50 — el freno no mordió ni de cerca en miniatura.
- **Falsadores de la §9 (ROJO):** ninguno gatillado — el brazo
  emitió 16 hallazgos (no cero), la guardia no se negó en ningún
  código, la degradación no se disparó en ninguno.

## 6. Comparación declarada contra v2, v2.1 y v2.2 (brazo base)

| Brazo base | v2 | v2.1 | v2.2 | v2.3 |
|---|---|---|---|---|
| Emitidos | 16 | 7 | 7 | 16 |
| Detectados | 8/8 | 7/8 | 7/8 | **8/8** |
| Costo del brazo | (total ambos brazos US$2,7457) | (total ambos brazos US$0,5038) | US$0,3090 | US$0,53607 |
| Llamadas por código | ~20 pasadas | 1 | 2 | 3–4 |

- **Detección:** el base v2.3 iguala el 8/8 del base v2 — pero el
  v2 lo lograba con ~20 pasadas por código (la arquitectura que la
  guardia se negó a pagar en la práctica), y este 8/8 llega con
  3–4 llamadas por código. Contra v2.1 y v2.2 (7/8, con la pérdida
  siempre en sem_02), la diferencia es el rescate de sem_02 por la
  vía general (§4): la vía de especialidad, sola, habría dado el
  mismo 7/8 de la v2.2. Se declara así, sin redondear: **la
  especialidad no mejoró; el ensanche cubrió su hueco conocido**.
- **Economía:** US$0,53607 contra US$0,3090 del base v2.2 (+74%):
  la selección generalizada corre 2–3 profundas por código donde
  la v2.2 corría 1 (la marca general `security` acompañó a la de
  clase en los 8 códigos). Sigue siendo el 2,7% del tope duro y
  dos órdenes de magnitud bajo el freno por PR; la cuenta de la §7
  del papel para PRs reales no se toca con este número de
  miniatura.
- **Sin señal de selección:** la familia especialidad marcó la
  plantada en 8/8 — la medición de marcas por familia que la §9
  pedía declarar. Que la selección acierte en miniatura ya se
  sabía que no predice diffs reales (16/16 en la v2.2 → 0/9 en la
  práctica); se asienta el dato sin inflarlo.

## 7. Qué afirma y qué NO afirma este semáforo (§9 del papel)

**SÍ afirma** (solo sobre el brazo base):

- **Mecánica:** selección generalizada → profundas por marca →
  emisión, sin negativas de la guardia y sin degradación, en los 8
  códigos de la batería (26 llamadas, 8/8 exit = 0, cero
  malformados, cero sin anclar).
- **Economía en miniatura:** US$0,53607 total, peor código
  US$0,09271 contra el freno de US$6,50 por PR.
- **La vía de especialidad sobrevivió al ensanche:** las marcas de
  clase siguen llegando (8/8) y detectando los plantados (7/8 por
  su propia pasada; 8/8 contando el rescate general de sem_02),
  con la comparación declarada de la §6.

**NO afirma:**

- **Detección general.** La batería no contiene ningún TP de
  categorías generales: que la pasada `security` re-encuentre
  defectos de seguridad plantados no es evidencia sobre
  correctness, reliability o cualquier otra categoría en diffs
  reales. Un VERDE no predice recall en la práctica — medido dos
  veces (triage 16/16 en miniatura → 0/9 en diffs reales). **La
  detección de la v2.3 se juzga únicamente en la práctica.**
- **Nada del brazo ALMA:** no corrió (puerta 1.4.0 no adoptada;
  §4 del papel). Este semáforo no lo habilita ni lo condena.

## 8. Veredicto y consecuencia

**VERDE (brazo base)** según los criterios de la §9 aplicados al
brazo corrido: emite (16 hallazgos, 8/8 detectados), sin negativas
de la guardia y sin degradación en ningún código. Consecuencia
según el papel (§9 y §11, paso 6): se procede a la publicación
v2.3 y a la práctica v2.3 del brazo base con el «sí» de Alejandro
al momento de lanzar — base primero y **linterna** (recall base
grounded > 0,7% sobre 352 TP); el brazo ALMA queda bloqueado
hasta que un papel nuevo repare la frontera de la 1.4.0 y su
medición de adopción pase. Nada del sistema se ajustó a partir de
este semáforo.

Salidas crudas: `runs/semaforo-v23-20261021/` (salida, ledger y
run-info por código, `log.txt`, `summary.json`).
