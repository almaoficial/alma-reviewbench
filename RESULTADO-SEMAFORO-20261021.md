# Resultado del semáforo — ReviewBench v2 (2026-10-21)

**Estado: DETENIDO ANTES DE CORRER. Gasto real: US$0,00. Ningún brazo corrió.**

Motivo de la detención (regla del propio encargo y de la Adenda 3): la única vía
local sancionada para la clave de API — la credencial guardada `custom.openai`
del conector `custom.legacy-openai` — está **vencida**. Sin poder establecer una
clave viva que facture a la cuenta correcta (la de «Continue with Apple», clave
«Reviewbench»), gastar desde cualquier otra vía invalidaría la corrida. No se
hizo ninguna llamada paga, no se tocó ninguna puerta, no se tocó la batería.

## 1. La verificación de identidad de la clave (costo cero)

- Sonda sin consumo: `GET https://api.openai.com/v1/models` con la credencial
  de la bóveda adjunta por el mecanismo sancionado del conector
  (`dynamic_credentials.add_surrogate_to_request`, host único api.openai.com).
- Respuesta: **HTTP 401**, código `expired_secret_key` — «Your API key has
  expired. Create a new API key to continue.»
- Lectura: la bóveda guarda la clave vieja («configurada de antes», memoria
  19/10), que calza con la clave **«Alma» expirada** que la cuenta correcta
  muestra en su página de claves. La clave activa **«Reviewbench»** (creada el
  19/10/2026 en la cuenta de Apple) nunca quedó guardada en la bóveda: vive en
  la configuración del portal, cargada por Alejandro, y por regla no se pide
  ni se recibe por chat.
- Las otras dos cuentas de Alejandro (Google: alesalusso10 y as10salusso)
  muestran saldo US$0 y **cero claves**: ninguna clave viva puede salir de ahí.
- Conclusión: no existe hoy una ruta local sancionada y viva hacia la cuenta
  correcta. Correr el semáforo en estas condiciones era imposible sin violar
  la regla de identidad de la cuenta.

## 2. Verificaciones previas completadas (todo costo cero)

- **Batería congelada íntegra:** los 32 archivos de `fixtures_semaforo/`
  (8 casos × diff.patch, pr.json, ground_truth.json y archivo head)
  coinciden en bytes y sha256 con `MANIFIESTO-BATERIA.json` (congelado
  2026-10-20). Sin desvíos.
- **Puerta 1.3.0 intacta:** `agent/alma_gate_v13.py` reporta
  POLICY_VERSION `alma-evidence-gate/1.3.0` y POLICY_SHA256
  `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`,
  idéntico al asentado en la Adenda 3 del pre-registro. No se modificó
  ninguna puerta (1.0.0 / 1.1.0 / 1.2.0 / 1.3.0) ni el revisor.
- **Autorizaciones en regla:** «Corre» de Alejandro (21/10), Adenda 4 firmada
  (freno por PR `RB_MAX_SPEND_USD` 5,00 → **6,50**), saldo ≈US$21,85 en la
  cuenta correcta verificado en pantalla (US$1,85 + carga de US$20), por
  encima del tope duro de US$20 del simulacro.

## 3. La corrida que quedó lista para ejecutar (sin cambios)

En cuanto exista una clave viva de la cuenta correcta por la vía sancionada,
la corrida es exactamente la pre-registrada, sin ajustar nada:

- **Batería:** `fixtures_semaforo` (sem_01…sem_08), una sola pasada por brazo.
- **Brazo base-v2:** revisor v2 (`RB_CONFIG_REVIEWER=v2`) sin gobernanza
  (`governance=base`; incluye la pasada general que el papel permite solo
  en este brazo).
- **Brazo alma-v2:** el mismo revisor v2 con gobernanza y puerta 1.3.0
  (`governance=alma`, `RB_CONFIG_GATE=v13`).
- **Modelo:** gpt-5.6-sol, effort medium, `RB_MODEL_BASE_URL=
  https://api.openai.com/v1` (manifiesto de corrida v1; único campo
  distinto entre brazos = gobernanza).
- **Frenos:** `RB_MAX_SPEND_USD=6.50` por PR (Adenda 4) y **tope duro
  US$20** sumando ambos brazos, con cuenta del gasto tras cada PR.
- **Criterio (Adenda 3, palanca 3):** si algún brazo emite CERO hallazgos
  sobre los defectos plantados → semáforo ROJO, no procede ninguna corrida
  puntuada y se asienta el diagnóstico. Si ambos emiten → VERDE, sin
  ajustar nada del sistema a partir del simulacro.

## 4. Cómo se destraba (acción de Alejandro, una sola)

1. En la cuenta correcta de OpenAI (la de «Continue with Apple», la que
   muestra la clave «Reviewbench»), crear si hace falta una clave nueva, o
   usar la existente, y **reconectar la credencial `custom.openai`** por el
   flujo seguro de credenciales (el conector prevé `reconnect` cuando una
   clave es rechazada): la clave se carga en la página segura, nunca por
   chat. Alternativa equivalente: guardar esa clave como la credencial del
   conector con el nombre que el flujo indique.
2. Avisar «clave reconectada». La corrida se relanza tal cual está
   pre-registrada: misma batería, mismos frenos, mismo criterio. El saldo
   (≈US$21,85) ya está cargado y alcanza.

## 5. Veredicto y desvíos

- **Veredicto del semáforo: SIN VEREDICTO** — no es verde ni rojo: la
  corrida no ocurrió. El criterio de la Adenda 3 se aplica sobre hallazgos
  emitidos, y no hubo emisiones porque no hubo llamadas.
- **Hallazgos por brazo y por PR:** ninguno (0 corridas, 0 llamadas).
- **Costo real total: US$0,00** (por PR: US$0,00 × 16). Saldo consumido: 0.
- **Desvíos del papel:** uno solo, de infraestructura de credenciales, no
  del diseño: la vía de clave prevista por los conectores del workspace
  resultó estar vencida. Todo lo demás (batería, puerta, frenos, criterio,
  saldo, autorizaciones) quedó verificado y en regla antes de la detención.
- **Prohibiciones respetadas:** sin re-corridas, sin ajustes de prompts,
  puerta o batería, sin tocar validadores congelados, sin gastar un centavo
  desde una cuenta no verificada.

## Intento 2 — tras reconexión de credencial (2026-10-21)

**Estado: DETENIDO EN EL PASO 0, antes de correr. Gasto real: US$0,00. Ningún brazo corrió.**

### La sonda de identidad (costo cero) — RECHAZADA

- Sonda sin consumo: `GET https://api.openai.com/v1/models` con la credencial
  `custom.openai` ya reconectada, adjunta por el mecanismo sancionado del
  conector (`dynamic_credentials.add_surrogate_to_request`, host único
  api.openai.com). La credencial **sí viajó adjunta**: OpenAI recibió una
  clave real en formato `sk-proj-…` (el surrogate fue reemplazado en la
  salida) y la rechazó.
- Respuesta: **HTTP 401**, código `invalid_api_key` — «Incorrect API key
  provided: sk-proj-…N2YA». Distinto del intento 1 (`expired_secret_key`):
  el contenido de la bóveda cambió hoy, pero lo guardado **no es una clave
  válida**.
- Cruce de pistas enmascaradas (las que la propia plataforma muestra):
  - clave «semaforo», creada hoy en la cuenta correcta: pista `sk-...SIAA`;
  - clave «Reviewbench» (activa, en el portal): pista `sk-...AekA`;
  - clave hoy guardada en la bóveda (eco de OpenAI en el error): termina en
    **N2YA** — no coincide con ninguna de las dos.
- Lectura: el valor pegado en la página segura no es el valor de la clave
  «semaforo» recién creada (ni el de «Reviewbench»). Contexto asentado en
  el chat: Alejandro reportó «No me la pega» / «La copié pero no te la
  puedo pegar» / «No me deja entrar» durante la carga. Sin una clave viva
  verificada de la cuenta correcta, correr invalidaría la corrida: se
  aplicó la detención mandada por el encargo. No se hizo ninguna llamada
  paga; no se reintentó la sonda con cambios.

### Verificaciones completadas (costo cero, en regla)

- **Batería congelada íntegra:** 32/32 archivos de `fixtures_semaforo/`
  coinciden en bytes y sha256 con `MANIFIESTO-BATERIA.json`.
- **Puerta 1.3.0 intacta:** POLICY_VERSION `alma-evidence-gate/1.3.0`,
  POLICY_SHA256 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`,
  idéntico al de la Adenda 3. Nada fue tocado: ni puertas, ni revisor,
  ni batería, ni prompts.

### Veredicto, hallazgos, costo y desvíos

- **Veredicto: SIN VEREDICTO** (segunda detención previa a la corrida; no
  es verde ni rojo: no hubo emisiones que puntuar).
- **Hallazgos por brazo y por PR:** ninguno (0 corridas, 0 llamadas pagas).
- **Costo real total: US$0,00** (por PR: US$0,00 × 16). Saldo consumido: 0.
- **Desvío del papel:** uno solo, el mismo tipo que el intento 1 —
  infraestructura de credenciales: la reconexión se completó en la página
  segura («Added»), pero el valor guardado no corresponde a una clave
  válida de la cuenta correcta.

### Cómo se destraba (una sola acción, por la página segura)

El valor completo de una clave se muestra **una sola vez**, al crearla.
Si el diálogo de creación de «semaforo» ya se cerró, ese valor no se
puede volver a ver: hay que crear **otra clave** en la cuenta correcta
(la de «Continue with Apple») y pegar su valor en la página segura en
ese mismo momento, con el botón Copy del diálogo de creación. Con la
credencial re-guardada, la sonda a costo cero debe responder **200**
antes de relanzar; la corrida se relanza tal cual está pre-registrada,
sin ajustar nada.

## Intento 3 — corrida ejecutada (2026-10-21, 13:53–14:07 EDT)

**Vía de clave:** Alejandro creó la clave «Semaforo1» en la cuenta correcta y, tras tres intentos fallidos de transferencia a la bóveda, la entregó por el chat por decisión propia. Sonda previa: HTTP 200 (viva, cuenta correcta). Uso transitorio, solo en el entorno del proceso ejecutor; el valor no se escribió en ningún archivo. Recomendación asentada al cierre: revocarla en la plataforma por haber viajado por chat.

**Incidente de infraestructura (declarado):** a mitad de la corrida el runtime se reinició y mató el proceso ejecutor. Estado al corte: brazo base completo (8/8); brazo ALMA con sem_05 y sem_06 cortados por la caída de conexión y sem_07–08 sin intentar. Se re-corrieron ÚNICAMENTE los casos cortados y los faltantes del brazo ALMA (causa de infraestructura declarada, la única re-corrida que el papel admite); ningún caso completado se repitió.

**Resultados por brazo y por caso** (costo = estimación del propio revisor desde el uso reportado por la API):

| Caso (defecto plantado) | base-v2 emitidos | base acierta | alma-v2 emitidos | alma acierta | costo base | costo alma |
|---|---|---|---|---|---|---|
| sem_01 sql_injection | 2 | sí | 0 | no | 0,2118 | 0,1989 |
| sem_02 hardcoded_secret | 1 | sí | 0 | no | 0,1887 | 0,1692 |
| sem_03 tls_verification_disabled | 3 | sí | 1 | sí | 0,1960 | 0,1680 |
| sem_04 unsafe_deserialization | 2 | sí | 1 | sí | 0,1590 | 0,1444 |
| sem_05 weak_hash | 2 | sí | 1 | sí | 0,1675 | 0,1517 |
| sem_06 jwt_verification_disabled | 2 | sí | 1 | sí | 0,1642 | 0,1507 |
| sem_07 debug_mode_enabled | 2 | sí | 1 | sí | 0,1765 | 0,1581 |
| sem_08 command_execution | 2 | sí | 1 | sí | 0,1789 | 0,1621 |
| **Total** | **16** | **8/8** | **6** | **6/8** | **US$1,4427** | **US$1,3030** |

**Costo total real: US$2,7457** (tope duro US$20 — 14% usado). Costo medio por código ≈ US$0,17. Saldo restante en la cuenta ≈ US$19,10.

**Anatomía de los dos fallos del brazo ALMA (diagnóstico, sin ajuste):**
- sem_01: el revisor SÍ propuso el candidato sql_injection, pero la puerta 1.3.0 lo RECHAZÓ: «a SQL skeleton and an unsafe construction marker must co-occur on the same cited line» — la cita del modelo no reunió esqueleto y construcción en la misma línea. La puerta falló cerrada sobre una cita mal formada, como está diseñada.
- sem_02: el revisor no produjo NINGÚN candidato para hardcoded_secret en la configuración ALMA (ledger vacío: ni aceptados ni rechazados). Silencio del modelo en esa pasada de clase, no rechazo de la puerta.

**VEREDICTO: VERDE.** Criterio de la Adenda 3 (palanca 3): luz roja solo si algún brazo emite CERO hallazgos sobre la batería. Base emitió 16 y ALMA 6 — ningún brazo en cero. La catástrofe de emparejamiento de la v1 (1 hallazgo en 25 PRs) no se repite: el revisor v2 ve, y la puerta deja pasar 6 de 8 defectos plantados.

**Consecuencia según el papel:** se procede a la práctica v2 SIN AJUSTAR NADA del sistema a partir de este simulacro. Decisión del tope (regla del borrador de adenda del 20/10): proyección = costo real por código × 50 ≈ US$8,6 ≤ US$30 → **banda 1: corre el tope congelado de US$30, sin adenda**. Freno por PR: el costo real (~US$0,17) queda muy por debajo del freno de US$6,50 (Adenda 4); para la práctica en el portal, el valor cargado en la bóveda del portal deberá reflejar ese freno (acción de Alejandro, a declarar en el manifiesto v2 antes de lanzar).
