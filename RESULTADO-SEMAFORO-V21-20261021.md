# Resultado del semáforo — ReviewBench v2.1 (2026-10-21)

**VEREDICTO: VERDE.** Ambos brazos emitieron (base 7, ALMA 7) y la guardia
de gasto no se negó en ninguno de los 16 códigos. **Costo real total:
US$0,5038** (tope duro US$20 — 2,5% usado).

**Señal de dilución C1 registrada (no altera el veredicto):** el brazo
base detectó MENOS defectos plantados que su par de la v2 (7/8 contra
8/8). El brazo ALMA detectó MÁS que su par de la v2 (7/8 contra 6/8).
Detalle en §3.

## 1. Autorización y vía de clave

- «Corre» de Alejandro para el semáforo v2.1: 21/10/2026 17:20 EDT,
  sobre la estimación declarada de ~US$1.
- Clave de la cuenta correcta entregada para esta corrida; sonda previa
  a costo cero: **HTTP 200** (viva). Uso transitorio, solo en el entorno
  del proceso ejecutor; el valor no se escribió en ningún archivo, log
  ni informe de esta corrida. Recomendación heredada de la corrida v2:
  revocar en la plataforma toda clave que haya viajado por chat.
- Papel que manda: `PREREGISTRO-REVIEWBENCH-V21.md` §5 (criterio de
  veredicto) y §6 (secuencia y falsadores), congelado antes de correr.

## 2. Verificaciones previas (costo cero, en regla)

- **Batería congelada íntegra:** los 32 archivos de `fixtures_semaforo/`
  (8 casos × diff.patch, pr.json, ground_truth.json y archivo head)
  coinciden en bytes y sha256 con `MANIFIESTO-BATERIA.json` (congelado
  2026-10-20). Sin extras ni faltantes.
- **Puerta 1.3.0 intacta:** todos los ledger del brazo ALMA llevan
  POLICY_SHA256 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`
  (el de la Adenda 3 / §3 del papel v2.1). No se modificó ninguna puerta
  ni la batería.
- **Regla de puntuación** (la misma que reproduce exacta la tabla del
  intento 3 de la v2): un caso cuenta como detectado si algún hallazgo
  emitido cae en el archivo del ground truth y su rango de líneas cubre
  la línea del defecto plantado. Verificado contra las salidas guardadas
  de la v2 antes de correr: reproduce base 16 emitidos / 8/8 y ALMA 6 / 6/8.

## 3. Resultados por brazo y por caso

Configuración (único campo distinto entre brazos = gobernanza):
`RB_CONFIG_REVIEWER=v21`, `RB_CONFIG_GATE=v13`, modelo gpt-5.6-sol,
effort medium, `ALLOW_REAL_LLM=1`, `RB_MAX_SPEND_USD=6.50` por PR
(Adenda 4), tope duro acumulado US$20. Costo = estimación del propio
revisor desde el uso reportado por la API (una sola llamada por código).

| Caso (defecto plantado) | base-v21 emitidos | base acierta | alma-v21 emitidos | alma acierta | costo base | costo alma |
|---|---|---|---|---|---|---|
| sem_01 sql_injection | 1 | sí | 0 | no | 0,0354 | 0,0355 |
| sem_02 hardcoded_secret | 0 | no | 1 | sí | 0,0379 | 0,0423 |
| sem_03 tls_verification_disabled | 1 | sí | 1 | sí | 0,0292 | 0,0292 |
| sem_04 unsafe_deserialization | 1 | sí | 1 | sí | 0,0279 | 0,0281 |
| sem_05 weak_hash | 1 | sí | 1 | sí | 0,0308 | 0,0291 |
| sem_06 jwt_verification_disabled | 1 | sí | 1 | sí | 0,0289 | 0,0289 |
| sem_07 debug_mode_enabled | 1 | sí | 1 | sí | 0,0299 | 0,0299 |
| sem_08 command_execution | 1 | sí | 1 | sí | 0,0304 | 0,0304 |
| **Total** | **7** | **7/8** | **7** | **7/8** | **US$0,2504** | **US$0,2534** |

**Costo total real: US$0,5038.** Costo medio por código ≈ US$0,031
(la v2 costó ≈US$0,17 por código: la pasada única cuesta ~5,5× menos,
como predecía la §4 del papel). Sin negativas de la guardia, sin casos
cortados por infraestructura, sin re-corridas: los 16 códigos
completaron en la primera pasada (exit=0 en todos).

## 4. Anatomía de los dos fallos (diagnóstico, sin ajuste)

- **sem_01, brazo ALMA (idéntico al de la v2):** el revisor SÍ propuso
  el candidato sql_injection, pero la puerta 1.3.0 lo RECHAZÓ con la
  misma razón asentada en el intento 3 de la v2: «a SQL skeleton and an
  unsafe construction marker must co-occur on the same cited line». La
  puerta falló cerrada sobre la cita, como está diseñada. En el brazo
  base el mismo caso se emitió y detectó.
- **sem_02, brazo base (sin puerta de por medio):** el revisor no
  produjo NINGÚN candidato (ledger vacío: ni aceptados ni rechazados).
  Silencio del modelo en la pasada única, no rechazo de validación —
  el mismo modo de fallo que la v2 mostró en su brazo ALMA para este
  caso. Notable: en el brazo ALMA de la v2.1 el caso SÍ se detectó —
  el revisor propuso el hardcoded_secret y la puerta lo aceptó
  («a credential-like name is assigned to a non-placeholder literal»).

## 5. Comparación declarada contra la v2 (§5 del papel)

| Brazo | v2 emitidos | v2 detectados | v2.1 emitidos | v2.1 detectados |
|---|---|---|---|---|
| base | 16 | 8/8 | 7 | 7/8 |
| ALMA | 6 | 6/8 | 7 | 7/8 |

- **Base:** detecta menos que su par v2 (7/8 < 8/8) → **señal de
  dilución C1 registrada** para este brazo, como manda el papel: se
  declara, no se «corrige» el revisor contra el semáforo. Los emitidos
  caen de 16 a 7 porque la pasada única emite un hallazgo por caso
  acertado, sin las duplicaciones de las pasadas por clase de la v2.
- **ALMA:** detecta más que su par v2 (7/8 > 6/8) y emite más (7 > 6);
  sin señal de dilución en este brazo.
- **Economía:** la guardia no se negó en ningún código (criterio de
  ROJO por economía del §5: no se gatilló). El peor caso de pre-vuelo
  quedó ~180× por debajo del freno de US$6,50 en esta batería.
- **Falsadores del §6:** ninguno gatillado (ALMA no emitió 0 ni cayó a
  ≤3/8; no hubo negativas de la guardia).

## 6. Veredicto y consecuencia

**VERDE** según el §5 del pre-registro v2.1: ambos brazos emiten sobre
la batería (7 y 7) y la guardia completó las 16 llamadas. Consecuencia
según el papel: se procede a la práctica v2.1 con el «sí» de Alejandro
al momento de lanzar (imagen y manifiesto nuevos, mismo procedimiento
que la v2), declarando en el manifiesto la señal de dilución del brazo
base aquí registrada. Nada del sistema se ajustó a partir de este
semáforo.

Salidas crudas: `runs/semaforo-v21-20261021/` (salida y ledger por
código y brazo, `log.txt`, `summary.json`).
