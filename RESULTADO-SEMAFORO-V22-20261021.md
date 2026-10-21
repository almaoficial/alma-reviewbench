# Resultado del semáforo — ReviewBench v2.2 (2026-10-21)

**VEREDICTO: VERDE.** Ambos brazos emitieron (base 7, ALMA 6), la
guardia no se negó en ninguno de los 16 códigos y la regla de
degradación no se disparó en ningún código de la batería (§6 del
pre-registro v2.2). **Costo real total: US$0,6221** (tope duro US$20 —
3,1% usado; estimación previa US$1–3).

**Medición C2 central: el triage acertó 16/16.** En todos los códigos
de ambos brazos la pasada de selección marcó exactamente una clase —
la plantada — y esa clase recibió su pasada profunda. Triage misses:
**0**. Las tres pérdidas de detección no son del triage: sem_02 (ambos
brazos) fue silencio de la pasada profunda, y sem_01 ALMA fue el
rechazo de cita de la puerta 1.3.0, idéntico al de la v2 y la v2.1.
Detalle en §4 y §5.

**Señal declarada (no altera el veredicto):** el brazo ALMA detectó
MENOS plantados que su par v2.1 (6/8 contra 7/8) y el base igualó a su
par v2.1 (7/8) quedando debajo de su par v2 (8/8). Se registra como
señal según la §6 del papel, sin corregir nada contra el semáforo.
Detalle en §6.

## 1. Autorización y vía de clave

- «Sí» explícito de Alejandro a esta corrida, sobre la estimación
  declarada de ≈US$1–3 y el tope duro de US$20 (Adenda 3 del papel
  v2). La construcción de C2 la había aprobado el 21/10 18:30 EDT
  («Construir C2»).
- Clave por la vía sancionada: conector de bóveda
  `custom.openai-rbench`. El ejecutor obtuvo el valor sustituto en
  memoria (`dynamic_credentials`) y lo pasó solo en el entorno de los
  procesos de la corrida; la capa de salida lo intercambia por la
  clave real únicamente hacia `api.openai.com`. El valor no se
  imprimió ni se escribió en ningún archivo, log ni informe.
- Sonda previa a costo cero: **HTTP 200** (`GET /v1/models`,
  `gpt-5.6-sol` visible) antes de gastar un centavo.
- Papel que manda: `PREREGISTRO-REVIEWBENCH-V22.md` §6 (criterio de
  veredicto) y §7 (secuencia y falsadores), congelado antes de
  correr (incluida su Adenda 1 sobre el fallback del caso degenerado,
  que en esta batería no hizo falta).

## 2. Verificaciones previas (costo cero, en regla)

- **Batería congelada íntegra:** los 32 archivos de
  `fixtures_semaforo/` (8 casos × diff.patch, pr.json,
  ground_truth.json y archivo head) coinciden en bytes y sha256 con
  `MANIFIESTO-BATERIA.json` (congelado 2026-10-20). Sin extras ni
  faltantes.
- **Puertas congeladas intactas:** el archivo de la 1.3.0 da sha256
  `d3b993d4d4f26b9df112dfd54abc391e8018faae024d23c63b4924d86d2dc1e0`
  y las cuatro constantes POLICY_SHA256 coinciden con la §5 del
  papel (1.0.0 `3ad514ed…`, 1.1.0 `6a7a7aa4…`, 1.2.0 `a768afa4…`,
  1.3.0 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`).
  Todos los ledger del brazo ALMA de esta corrida llevan el
  POLICY_SHA256 de la 1.3.0.
- **Suite completa en seco: 163/163** (mock, US$0), incluidos los
  tests de la batería del semáforo de la v2.2 (selección ≤5, guardia
  en dos etapas, degradación registrada).
- **Regla de puntuación** (la misma de las corridas v2 y v2.1): un
  caso cuenta como detectado si algún hallazgo emitido cae en el
  archivo del ground truth y su rango de líneas cubre la línea del
  defecto plantado.

## 3. Resultados por brazo y por caso

Configuración (único campo distinto entre brazos = gobernanza):
`RB_CONFIG_REVIEWER=v22`, `RB_CONFIG_GATE=v13`, modelo gpt-5.6-sol,
effort medium, `ALLOW_REAL_LLM=1`, `RB_MAX_SPEND_USD=6.50` por PR
(Adenda 4), tope duro acumulado US$20. Costo = estimación del propio
revisor desde el uso reportado por la API, sumando todas las llamadas
del código (selección + profundas). En los 16 códigos el triage marcó
exactamente 1 clase (la plantada), corrió exactamente 1 pasada
profunda, y no hubo marcas desconocidas, overflow ni degradación.

| Caso (defecto plantado) | base-v22 emitidos | base acierta | alma-v22 emitidos | alma acierta | costo base | costo alma |
|---|---|---|---|---|---|---|
| sem_01 sql_injection | 1 | sí | 0 | no | 0,0469 | 0,0503 |
| sem_02 hardcoded_secret | 0 | no | 0 | no | 0,0380 | 0,0386 |
| sem_03 tls_verification_disabled | 1 | sí | 1 | sí | 0,0372 | 0,0364 |
| sem_04 unsafe_deserialization | 1 | sí | 1 | sí | 0,0367 | 0,0368 |
| sem_05 weak_hash | 1 | sí | 1 | sí | 0,0367 | 0,0366 |
| sem_06 jwt_verification_disabled | 1 | sí | 1 | sí | 0,0374 | 0,0375 |
| sem_07 debug_mode_enabled | 1 | sí | 1 | sí | 0,0376 | 0,0378 |
| sem_08 command_execution | 1 | sí | 1 | sí | 0,0385 | 0,0392 |
| **Total** | **7** | **7/8** | **6** | **6/8** | **US$0,3090** | **US$0,3132** |

**Costo total real: US$0,6221.** Sin negativas de la guardia, sin
degradación, sin casos cortados por infraestructura, sin
re-corridas: los 16 códigos completaron en la primera pasada
(exit=0 en todos).

## 4. Anatomía de los tres fallos (diagnóstico, sin ajuste)

- **sem_02, AMBOS brazos (no es triage miss):** el triage marcó y
  seleccionó `hardcoded_secret` en los dos brazos y la pasada
  profunda corrió (2 llamadas por código), pero devolvió **cero
  hallazgos crudos** — silencio del modelo en la pasada profunda, sin
  malformados ni descartes por anclaje, y ledger vacío en ambos
  brazos (la puerta ni siquiera vio un candidato). Es el mismo modo
  de fallo que este caso mostró en la v2.1 base y en la v2 ALMA; la
  diferencia es que acá golpeó a los dos brazos a la vez. En la v2,
  el base sí lo detectó con esta misma pasada profunda: un solo caso
  que oscila entre corridas es varianza del modelo, y se asienta como
  tal — no se re-corrió ni se ajustó nada.
- **sem_01, brazo ALMA (idéntico al de la v2 y la v2.1):** el triage
  marcó `sql_injection`, la profunda propuso el candidato y la
  puerta 1.3.0 lo RECHAZÓ con la misma razón asentada en el intento 3
  de la v2 y en el semáforo v2.1: «a SQL skeleton and an unsafe
  construction marker must co-occur on the same cited line». La
  puerta falló cerrada sobre la cita, como está diseñada. En el brazo
  base el mismo caso se emitió y detectó. Es la tercera corrida
  consecutiva con este mismo rechazo sobre este mismo caso.

## 5. Mediciones C2 declaradas (§6 del papel)

- **Triage:** 16/16 aciertos (`triage_hit` en todos los códigos de
  ambos brazos); **triage misses: 0**. Marcas por código: exactamente
  1 en los 16 (siempre la plantada). Marcas desconocidas: 0.
  `selection_overflow`: vacío en los 16.
- **Pasadas profundas corridas:** exactamente 1 por código (la de la
  clase marcada), en el formato de la v2. Ningún código necesitó más.
- **Degradación:** ninguna en los 16 códigos (`degradation` nulo en
  todos los run-info); el fallback de pasada única del caso degenerado
  no se invocó. La cuenta de la §4 del papel queda en pie para esta
  batería: el freno no mordió ni de cerca (peor código: US$0,0503
  contra el freno por PR de US$6,50).
- **Falsadores de la §7:** ninguno gatillado. Triage misses por brazo:
  0 (el falsador pedía ≥4). Ningún brazo en ≤3/8 (base 7/8, ALMA 6/8).

## 6. Comparación declarada contra v2 y v2.1 (§6 del papel)

| Brazo | v2 emitidos | v2 detectados | v2.1 emitidos | v2.1 detectados | v2.2 emitidos | v2.2 detectados |
|---|---|---|---|---|---|---|
| base | 16 | 8/8 | 7 | 7/8 | 7 | 7/8 |
| ALMA | 6 | 6/8 | 7 | 7/8 | 6 | 6/8 |

- **Base:** iguala a su par v2.1 (7/8) y queda debajo de su par v2
  (8/8) por el silencio de la profunda de sem_02 (§4). Sin señal de
  triage: el triage no perdió ningún caso.
- **ALMA:** detecta MENOS que su par v2.1 (6/8 < 7/8) → **señal
  registrada** según la §6, con su anatomía: no es triage (16/16) ni
  es degradación (ninguna); es la suma del rechazo de cita de sem_01
  (presente en las tres versiones) y el silencio de sem_02 (que en la
  v2.1 este brazo sí resolvió). Igual que manda el papel: se declara,
  no se «corrige» el sistema contra el semáforo.
- **Economía:** US$0,6221 total — entre la v2.1 (US$0,5038, una
  llamada por código) y la v2 (US$2,7457, ~20 pasadas por código):
  C2 pagó 2 llamadas por código (selección + 1 profunda) porque el
  triage marcó una sola clase por código en esta batería. La guardia
  no se negó en ningún código (criterio de ROJO por economía: no se
  gatilló).

## 7. Veredicto y consecuencia

**VERDE** según la §6 del pre-registro v2.2: ambos brazos emiten
sobre la batería (7 y 6), sin negativas de la guardia y sin que la
regla de degradación se dispare en ningún código. Consecuencia según
el papel: se procede a la práctica v2.2 con el «sí» de Alejandro al
momento de lanzar (imagen y manifiesto nuevos, mismo procedimiento
que la v2/v2.1), declarando en el manifiesto la señal del brazo ALMA
aquí registrada y la medición del triage (16/16 en miniatura; su
prueba real es la práctica, donde los diffs no son de juguete).
Nada del sistema se ajustó a partir de este semáforo.

Salidas crudas: `runs/semaforo-v22-20261021/` (salida, ledger y
run-info por código y brazo, `log.txt`, `summary.json`).
