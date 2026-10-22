# Registro en ReviewBench — formulario prellenado

**Estado:** compuerta A completa (digest obtenido) y **compuerta B
EJECUTADA el 2026-10-18**: `alma-reviewer` registrado en el portal, estado
**awaiting approval** (la review request de onboarding espera el merge de un
mantenedor; recién ahí se habilitan las corridas). Las dos configuraciones
(base y ALMA) quedaron creadas con el digest de abajo. Credenciales:
**missing** en ambas — los valores se cargan por configuración en el portal
(ver «Credenciales»); la key la pega Alejandro, nunca por chat.

**Fecha de preparación:** 2026-10-18. Contrato según
[CONTRACT.md](CONTRACT.md) (verificado en vivo el 2026-10-17) y experimento
según [PREREGISTRO-REVIEWBENCH.md](PREREGISTRO-REVIEWBENCH.md).

## Campos del portal

| Campo | Valor a cargar |
|---|---|
| Nombre visible del reviewer | `alma-reviewer` |
| Email de contacto | `alesalusso10@gmail.com` — cargado en el registro el 2026-10-18 |
| Imagen (digest) | `ghcr.io/almaoficial/alma-reviewbench@sha256:51b18cf15224022b668a8db8845bd4db5a8a85ffb64a0ead0d8d7130ed71f4b2` — **OBTENIDO 2026-10-18**: run nº 1 del workflow `reviewbench-image` en verde (22 s), package público en GHCR (tag `dev`) |
| Visibilidad de la imagen | Pública (GHCR público: el portal tira sin credencial) |
| URL de API del modelo | `https://api.openai.com/v1` — confirmado y cargado el 2026-10-18 (key de OpenAI; `api.openai.com` es el único host de egress) |
| Secretos / credenciales a declarar | Ver sección «Credenciales» — solo **nombres**, jamás valores por chat |
| Timeout por PR (segundos) | **En blanco** = default del portal: 1800 s (máximo permitido: 3600) |

## Configuraciones (labels) — el A/B sobre un mismo registro

Agregar una configuración nueva no requiere aprobación nueva: las dos van
sobre el mismo reviewer y el mismo digest. La única diferencia entre brazos
es `governance`, como manda el pre-registro.

**Configuración BASE:**

```text
governance=base
backend=llm
model=gpt-5.6-sol
effort=medium
```

**Configuración ALMA:**

```text
governance=alma
backend=llm
model=gpt-5.6-sol
effort=medium
```

(`model=gpt-5.6-sol` y `effort=medium` son los valores que Alejandro tipeó
en su captura del portal el 2026-10-17. Llegan al contenedor como
`RB_CONFIG_MODEL` / `RB_CONFIG_EFFORT` / `RB_CONFIG_GOVERNANCE` /
`RB_CONFIG_BACKEND`.)

Configuración opcional de referencia, solo para validación de formato con
`try-agent.sh` en local (no necesita key ni URL de modelo):

```text
governance=alma
backend=mock
model=deterministic-rules
effort=local
```

## Credenciales (compuerta B — nombres y mecanismo, sin valores)

El portal entrega las credenciales declaradas como variables de entorno al
contenedor, solo durante la corrida. Hay que declarar tres nombres:

| Nombre | Valor | Quién lo carga |
|---|---|---|
| `OPENAI_API_KEY` | La key del proveedor elegido | Alejandro, en el portal o por la bóveda segura — **nunca por chat** |
| `ALLOW_REAL_LLM` | `1` | Se declara como credencial de entorno: es el flag que arma el adaptador (sin él, `backend=llm` se niega a llamar, verificado por tests) |
| `RB_MAX_SPEND_USD` | El tope de gasto por PR aprobado en la compuerta C (p. ej. `5.00`) | Se declara junto con la key; sin este tope el adaptador también se niega a llamar |

Opcionales, para que el control de gasto use las tarifas reales del modelo
elegido en vez de la banda frontier conservadora por defecto (US$15/M
entrada, US$75/M salida): `RB_PRICE_INPUT_PER_MTOK_USD`,
`RB_PRICE_OUTPUT_PER_MTOK_USD`. Se fijan en la adenda de calibración del
pre-registro, antes de la compuerta C.

## Egress a declarar

- `api.openai.com:443` — host del modelo (el contrato lo autoriza
  automáticamente al declarar la URL del modelo; si el proveedor cambia,
  cambia este host).
- **Ningún otro host.** El agente no necesita nada más: sin búsqueda web y
  sin conectores que puedan leer respuestas del PR (regla del
  pre-registro). La descarga de la imagen desde GHCR la hace el runner, no
  el contenedor.

## Qué pasa al enviar

Registrar abre un PR con el manifiesto en `review-bench/ReviewBench`; el
merge de un mantenedor es la aprobación (referencia del contrato: ~1 día
hábil). Recién con el registro aprobado se habilita el test run puntuado
de 25 PRs.

## Compuertas de decisión (en orden — ninguna se salta)

- **A) Publicar la imagen en GHCR.** Aprobar que el código del adaptador se
  haga público en `ghcr.io/almaoficial/alma-reviewbench` y disparar a mano
  el workflow `reviewbench-image` (manual, `workflow_dispatch`). Costo:
  **US$0** de plataforma. Producto: el digest para el campo de arriba.
- **B) Cargar la API key en el portal.** La carga Alejandro (o por bóveda
  segura; nunca por chat) y se declaran `ALLOW_REAL_LLM=1` y
  `RB_MAX_SPEND_USD`. Costo directo: **US$0**; es la compuerta que habilita
  gasto, por eso va separada de la corrida. **Registro EJECUTADO el
  2026-10-18** (aprobación de Alejandro 11:08, «Vamos con la b y c»):
  reviewer creado con los nombres de credenciales declarados; los valores
  se pegan por configuración en submit → Existing reviewer → credentials
  de cada fila (`OPENAI_API_KEY` suya, `ALLOW_REAL_LLM=1`,
  `RB_MAX_SPEND_USD=5.00` por PR según el diseño de esta planilla).
- **C) Corrida de práctica puntuada, 25 PRs, A/B (base + ALMA).** Exige el
  sí con modelo, brazos, set, timeout (1800) y **tope de gasto nombrado**.
  Bandas del pre-registro para los dos brazos juntos: intermedia
  **US$3,00–21,00**; frontier **US$15,00–105,00**. Sugerencia de tope a
  nombrar si el modelo es clase frontier: **US$40** (cubre el escenario
  típico A/B ≈ US$37,50; el escenario largo se corta contra el tope por
  PR). Sin las tres condiciones de avance del pre-registro, no hay D.
- **D) Corrida final, 219 PRs × 3 rondas, A/B.** Solo si la práctica cumple
  la regla de avance (F1 ALMA ≥ base, precisión +0,05, recall no cae más
  de 0,03). Bandas para los dos brazos juntos: intermedia
  **US$78,84–551,88**; frontier **US$394,20–2.759,40**. Tope único a
  nombrar tras la calibración de la práctica, no antes.

## 19/10/2026 — Práctica: primer intento y re-largada (base)

- Corrida #241 (configuración base, iniciada 11:07:40 EDT): **FAILED** — «failed at run-agent (3, 4) / Run the vendor agent over this shard», sin puntaje. Se largó con la advertencia del portal de que una configuración no tenía credenciales; el adaptador LLM es fail-closed (sin ALLOW_REAL_LLM=1 + key + tope no llama), por lo que la falla de ejecución es consistente con corrida sin credenciales. No es un resultado: es un intento fallido, archivado como tal.
- Corrida #242 (configuración base, iniciada 11:15:11 EDT): en cola («queued») al momento de la captura de las 11:15. Presumiblemente largada después de guardar las credenciales en la configuración base.
- Brazo ALMA: credenciales y corrida sin confirmar al asentar esta entrada.
- Captura 11:17: #242 (base) «running · 2 min»; #243 (base, 11:17:21) «queued» — tercera corrida del MISMO brazo, largada por el botón «Start another» sin cambiar el selector de configuración. Brazo alma: todavía sin corrida. Regla pre-comprometida antes de conocer puntajes: el brazo base válido de la práctica es la primera corrida base que complete con credenciales guardadas; las duplicadas se declaran, no se elige la mejor.
- Captura 11:20: base suma #245 (11:19:55, «queued»); #242 y #243 «running» en paralelo. La lista filtrada por base muestra «4 of 5»: existe una quinta corrida fuera del filtro, presumiblemente #244 = brazo alma (a confirmar). Total potencial de gasto: 3 corridas base con gasto + 1 alma pueden exceder el tope US$40 aprobado para el par A/B; el gasto real se concilia contra el panel de uso de OpenAI. Regla ya asentada: brazo base válido = primera corrida base completa con credenciales guardadas.
- Captura «Show all» 11:21: #244 (11:18:32) es la corrida del brazo ALMA («running»). Brazo base en vuelo: #242, #243, #245 (todas «running»). #241 queda como intento fallido sin credenciales. La comparación A/B se mantiene: alma = corrida única #244; base = primera de las corridas con credenciales que complete, según la regla pre-comprometida.
- Captura 11:35: #242, #243 y #245 (base) FAILED en run-agent — «(3, 4)», «(1, 4)» y «(4, 4)» respectivamente, con la leyenda «Run the vendor agent over this shard». Las cuatro corridas base murieron con el mismo modo de falla, tuvieran o no credenciales al largarse: falla sistemática a diagnosticar antes de cualquier reintento (sin re-largadas a ciegas). Estado de #244 (alma) sin confirmar en esta vista.
- Diagnóstico asentado (19/10 11:37): el usuario confirma que su cuenta de OpenAI NO tiene saldo. Es la explicación que unifica las cuatro fallas en run-agent: sin crédito, la API rechaza las llamadas y el agente no puede completar ningún shard. Las corridas fallidas quedan archivadas como intentos con diagnóstico, no como resultados. Pendiente: carga de crédito (decisión de él, dentro del tope US$40 de la Compuerta C) y re-corrida secuencial del par.
- Decisión del usuario (19/10 11:39): no cargar crédito hasta cobrar el cheque del 20/10. Compuerta C queda estacionada con diagnóstico completo (falta de saldo) y protocolo de re-corrida secuencial definido. La clave que circuló por el chat se revoca al retomar y se crea una nueva.

## 19/10 — retomada anticipada (tarde)
- Saldo OpenAI verificado por captura suya (16:57): **US$5,49** de crédito API (esta mañana no había saldo: ese era el diagnóstico de las fallas). Él decidió adelantar la prueba sin esperar el cheque del 20 y lanzar con la clave actual (la del chat), difiriendo la rotación.
- **#244 (alma) — estado FINAL confirmado en el portal (17:00): FAILED «failed at run-agent (1, 4)»**. Cayó igual que las base de la mañana; sin puntaje. Con esto, las 5 corridas del 19/10 a la mañana quedaron fallidas por la misma causa (sin saldo).
- **#249 (base) LANZADA 16:59:32 EDT** — una sola, brazo base, práctica de 25 PR, sin tocar credenciales ni configuraciones. Estado a los ~5 min: «queued» (en cola, sin arrancar, sin fallar). Por la regla pre-comprometida, la #249 es la corrida base candidata del brazo base (primera lanzada con credenciales guardadas Y saldo).
- Pendiente: que la #249 complete y dé su F1; recién ahí se decide el lanzamiento del brazo alma. Conciliar el gasto real contra el saldo al cerrar.
- **#249 (base) — FAILED «failed at run-agent (3, 4)»** (verificado en el portal 17:15): estuvo en cola ~1 min y corriendo ~3+ min antes de caer en el shard 3 de 4; sin puntajes. IMPORTANTE: esta corrida SÍ tenía saldo (US$5,49 verificados 16:57), así que el diagnóstico «sin saldo» ya NO alcanza como explicación única. Hipótesis a discriminar con el saldo actual y el Usage de OpenAI: (a) el saldo se agotó a mitad de corrida (4 shards en paralelo consumiendo), (b) límites de tasa de cuenta nueva (tier bajo) bajo carga paralela, (c) falla del agente/modelo tras llamadas exitosas parciales. La corrida válida del brazo base sigue VACANTE: la #249 no completa, no cuenta.
- **Diagnóstico nuevo (17:16, lectura en vivo de su cuenta OpenAI):** la organización «alma» muestra saldo **US$0,00** y uso de octubre **US$0,00 — 0 requests, 0 tokens en todo modelo**. Es decir: la clave cargada en el portal NUNCA facturó una sola llamada exitosa (las 6 corridas fallidas nunca llegaron a consumir API). Su captura de las 16:57 mostraba US$5,49 en OTRA vista — hipótesis principal: los US$5,49 están en una organización distinta de la que pertenece la clave (cuenta con más de una org). Discriminador en curso: balances por organización + en qué org existe una clave creada hoy. La corrección queda asentada: mi «confirmado, era el saldo» de las 17:03 era prematuro; la versión fina es «la org de la clave no tiene saldo; el saldo visto está en otra org» — pendiente de confirmación.
- **#250 (base) apareció EN COLA a las 17:16:57** (captura suya del portal, 17:17): no la lancé yo — mis tareas de navegador eran de solo lectura (chequeos de estado y de cuenta); presumiblemente la lanzó él desde el teléfono al ver caer la #249. Se declara como intento base adicional según la regla (todas las duplicadas se declaran). Pronóstico asentado: caerá igual — la org de la clave registra 0 requests en todo octubre.
- Su captura confirma el tablero: Succeeded 0 · Failed 5 · Pending 1; #249 failed (3,4) visible.
- **Mapa de organizaciones (17:17–17:20, lectura en vivo):** la cuenta alesalusso10@gmail.com tiene 2 orgs («alma» y «Personal»): AMBAS con US$0,00 de crédito y **CERO claves API** — no existe ninguna clave creada hoy en esta cuenta. Además, el login de hoy en el navegador cayó en un flujo de bienvenida («Start building», paso plan): esta cuenta de plataforma está vacía/nueva.
- **Reconciliación:** su captura de US$5,49 (16:57, desde el teléfono) muestra una cuenta CON plan pay-as-you-go activo («Cancel plan», auto-reload) — NO puede ser esta cuenta. Hipótesis firme: hay DOS cuentas de OpenAI en juego; la del teléfono (posiblemente as10salusso@gmail.com) tiene los US$5,49; la clave pegada en el chat a las 11:09 no vive en la cuenta alesalusso10. Pendiente de su verificación en el teléfono: Usage y API keys de ESA sesión. Mi error asentado: tomé su captura como «su cuenta» sin verificar que fuera la misma sesión que la del navegador.
- **Capturas suyas de la cuenta del teléfono (17:20–17:21) — la que tiene los US$5,49:** (a) Usage, últimos 7 días, Default project, todas las claves: **«No data» — uso CERO también acá**; (b) API keys: 2 claves — **«Revi…» ACTIVA** ($0,00 de uso) y **«Alma» EXPIRADA**. Conclusión unificada y verificada: **ninguna llamada de ninguna corrida facturó jamás, en ninguna cuenta** — el dinero nunca fue la causa completa (mi «era el saldo» y su «no tengo saldo» quedan SUPERADOS como explicación). Causas candidatas ahora: clave del portal ≠ clave activa (¿pegó la expirada?), modelo gpt-5.6-sol sin acceso en su cuenta/tier (error previo a facturar), o egress del contenedor. Discriminador inmediato sin gasto: el detalle/logs de error de la corrida en ReviewBench.
- Nota de reconciliación: la cuenta vacía del navegador (orgs «alma»/«Personal» sin claves) puede ser otra cuenta u otro alcance org/proyecto — queda marcado como no resuelto; el hecho ancla es el uso cero en la cuenta con plata y claves.
- **CAUSA ENCONTRADA (19/10 17:23, del output descargado de la #249, leído por mí):** cada PR del agente termina con «alma-reviewbench error: model endpoint returned HTTP 400; failing closed without emitting findings» (agent.log de los 4 PR intentados; run-status.jsonl: error:2, 3 intentos, ~184 s por PR). Las credenciales CARGARON («credentials: loaded» en los logs de shard) y el endpoint RESPONDIÓ (no es egress): es HTTP **400**, no 401 (auth OK), no 404, no 429/cuota — por eso el uso es US$0 en todas las cuentas: los 400 no facturan. Las 7 corridas murieron de esto, desde la primera.
- **Sospechoso en NUESTRO código** (`agent/llm_reviewer.py`, build_payload): el payload a /chat/completions incluye `temperature: 0` y `max_tokens` — parámetros que los modelos de razonamiento de OpenAI rechazan con 400 (a confirmar con llamada de prueba mínima). Hueco de logging propio: el agente no registra el cuerpo del error — por eso el diagnóstico costó toda la tarde; a corregir en la misma pasada.
- Plan de arreglo: (1) confirmar con una llamada mínima (Playground o API, ~US$0) qué acepta gpt-5.6-sol; (2) corregir payload (fuera temperature, max_completion_tokens) + loguear cuerpo de error; (3) tests, rebuild de imagen (workflow reviewbench-image), digest nuevo; (4) actualizar el registro del agente en el portal (verificar si el digest es editable o requiere PR nuevo); (5) relanzar UNA base y verificar uso > 0. La clave nueva queda como higiene posterior, NO es el arreglo.
- #250 seguía «running» a las 17:22 reintentando contra el mismo 400; caerá sola, costo US$0.
- **Imagen corregida PUBLICADA (19/10 17:28):** fix del payload commiteado al repo público (commit 92ec8e2: fuera `temperature`, `max_completion_tokens`, cuerpo del error en el log; tests 24/24 y payload verificado en local). Workflow reviewbench-image nº 2 SUCCESS (30 s). **Digest nuevo: ghcr.io/almaoficial/alma-reviewbench@sha256:14a4bb3ed9b3f83bbdb7947fc1cba949cece2cb0f97c1d9cc8b22ca0fd6d5d3b** (reemplaza al 51b18cf1…). Paso siguiente: actualizar el digest en el registro del agente y relanzar la base.
- **Registro actualizado (19/10 17:31):** las DOS configuraciones (base y alma) quedaron apuntando al digest nuevo 14a4bb3e… (campo «Build on ghcr.io» editable por configuración en el portal; guardado confirmado en pantalla para ambas). Correcto para el diseño A/B: misma imagen en los dos brazos, única diferencia `governance`. Ninguna otra configuración fue tocada.
- **#251 (base, imagen corregida 14a4bb3e) LANZADA 17:31:43** — tras ~8 min de observación sigue «queued · 1 min»: no arrancó, no falló; espera un worker de ReviewBench. El arreglo sigue SIN VALIDAR hasta que ejecute. Tablero base según el portal: Failed 6 (la #250 cayó como estaba previsto, por el contador) · Pending 1 (la #251). Próximo chequeo: estado de la #251 cuando haya corrido; si pasa run-agent y produce hallazgos, el arreglo queda validado y su F1 es la del brazo base.
- **#251 (base, imagen corregida) SUCCEEDED (19/10 17:49, verificado en el portal):** completó los 4 shards. **Grounded F1 1,4% · Precision 42,9% · Recall 0,7%**; Augmented F1 4,4% · Precision 53,3% · Recall 2,3%; duración promedio 12 s; findings 14 (5 novel). Es la PRIMERA corrida base válida según la regla pre-comprometida (primera base que completa con credenciales guardadas): su F1 es la vara del brazo base. Lectura asentada: precisión respetable, recall en el piso (0,7%) — la limitación declarada del revisor base (la puerta ALMA filtra hallazgos: juega a precisión, no recupera recall). El arreglo del payload queda VALIDADO. Siguiente paso según la regla: UNA corrida del brazo alma (reemplazo de la #244).
- **#252 (ALMA) LANZADA 17:51:06** con la imagen corregida — corrida única del brazo alma según la regla (reemplaza a la #244). Quedó en cola al lanzarse. Manifiesto público ACTUALIZADO y pusheado (commit 7b27ab9): digest nuevo + resultado base #251 asentado verbatim; gasto real pendiente de la lectura de Usage de su cuenta.
- **Decisión de Alejandro (19/10 18:01):** al cerrar la #252 se arma el PAPEL DE LA V2 del revisor (pre-registro nuevo, práctica nueva): palancas acordadas = contexto completo (archivos enteros, no solo el diff), pasadas especializadas por clase de defecto, exploración del repo con herramientas, y anclaje exacto de líneas. Nada se toca del experimento en curso ni se estudian las respuestas de esta práctica para mejorar (la final son otros PRs).
- **#252 (ALMA, imagen corregida 14a4bb3e) — FAILED (verificado en el portal 19/10 18:12–18:15 EDT, corrida de vigilancia de las 18:12):** estado verbatim «failed»; error verbatim del portal: «failed at run-agent (3, 4) / Run the vendor agent over this shard». Sin puntajes: Grounded F1 – · Precision – · Recall – · Augmented F1/Precision/Recall – · Findings – (en la lista del registro: «P – R –»).
- **Causa textual del agent output de la #252 (descargado del portal, 18 KB, copia en `runs/run-252-output.zip`):** cada PR fallido cierra con «alma-reviewbench error: model endpoint returned HTTP 429; failing closed without emitting findings — body: { "error": { "message": "You have no credits remaining. Add credits to continue using the API at https://platform.openai.com/settings/organization/billing/.", "type": "insufficient_quota", "param": null, "code": "credit_balance_exhausted" } }». Resumen del output: «14 pull requests: 9 succeeded, 5 did not» — 5 PRs en error:2 (3 intentos, ~183 s c/u) y los shards con preflight se detuvieron tras el primer PR fallido, así que la corrida nunca completó el set. Lectura asentada: el crédito de US$5,49 verificado a las 16:57 se agotó entre la base #251 y la #252 (un PR exitoso de la #252 registra prompt_tokens 258471, costo estimado US$4,03824); la #252 NO es un resultado del brazo alma — es una corrida fallida por crédito agotado, sin número. La comparación A/B queda SIN CERRAR: base válida #251 (F1 1,4% · Precisión 42,9% · Recall 0,7%) sin contraparte alma. La regla de avance no se puede evaluar. NO se disparó la final de 219 PRs.
- **#253 (ALMA) LANZADA 19:43:05** — reemplazo de la #252 tras la carga de crédito de Alejandro (monto cargado no verificado por mí; la cuenta buena es la de su teléfono, NO la del navegador: la del navegador — alesalusso10@gmail.com, orgs «alma»/«Personal» — tiene US$0 y CERO claves, verificado 19:29). Quedó en cola al lanzarse. Si completa, es la corrida alma válida según la regla; #252 queda declarada como fallida por crédito.
- **#253 (ALMA) — agente COMPLETO, puntaje caído del lado de la plataforma (19/10 19:53, salida leída):** summary verbatim: «25 pull requests: 25 succeeded, 0 did not» — los 4 shards cerraron. El portal marca «failed at score / Summarise»: el paso de puntaje/resumen es de ReviewBench, no del agente; sin puntajes oficiales. **Hallazgos emitidos por el brazo ALMA: 1 en 25 PRs** (base #251: 14). Causa estructural medida en los agent.log: el modelo devuelve pocos hallazgos crudos (mayoría de PRs en 0) y la puerta congelada solo verifica 8 clases de reclamo (sql_injection, hardcoded_secret, tls_verification_disabled, silenced_bare_except, mutable_default, command_execution, unsafe_deserialization, race_condition) con evidencia específica; lo que el LLM propone fuera de esas clases se rechaza fail-closed (ej.: PR chronicle: 2 crudos → 0 emitidos). El único emitido ES de una de las 8: race_condition (simnaut/emdash #2, callback.ts 124–164). **Veredicto del A/B medido desde las salidas (no desde el portal): la regla de avance NO se cumple** (F1 ALMA ≈ 0 con 1 finding vs base 1,4%) → compuerta D no se abre. No se relanza la misma corrida (pesca prohibida por la disciplina propia). La cura queda para la v2: revisor que produce candidatos POR clase verificable con evidencia citada (las «pasadas especializadas» del papel aprobado).
- **Decisión de Alejandro (19/10 20:08):** la práctica de la v2 se lanza MAÑANA 20/10, después de la entrevista de Micro1. Orden del martes: Micro1 temprano (antes del fútbol de las 10) → publicación de imagen/manifiesto v2 → chequeo de saldo → práctica A/B v2 (tope US$30 del pre-registro).

## 21/10/2026 — Práctica v2: cierre sin medición (Adenda 5)

- **#282 (base v2, 14:35:38 EDT): FAILED** — «failed at run-agent (3, 4) / Run the vendor agent over this shard», sin puntajes. Falla de plataforma, sin completar.
- **Adenda 5 (asentada ANTES de relanzar, 15:59):** excepción de infraestructura — un solo relanzamiento con misma config/imagen/labels; si volvía a fallar en plataforma, la v2 cerraba sin medición, sin tercer intento.
- **#287 (base v2, relanzamiento, 16:03:34 EDT): FAILED** — verificado por lectura directa del portal en la vigilancia de las 16:19–16:21 EDT: estado verbatim «failed», detalle «failed at run-agent (1, 4) / Run the vendor agent over this shard», config «llm · base · gpt-5.6-sol · medium · v2 · v13». Sin puntajes: Grounded/Augmented F1, Precision y Recall todos en «–».
- **Consecuencia (Adenda 5): la práctica v2 CIERRA SIN MEDICIÓN. NO hay tercer intento. PROHIBIDO relanzar.** El brazo ALMA de la v2 nunca se lanzó (la prueba de la linterna nunca se pudo aplicar: no hay recall base). ALMA no fue medido hoy en el portal: dos fallas de infraestructura, cero evidencia en cualquier dirección. Patrón del portal: falló en 3 de las últimas 4 corridas (#253 en score, #282 y #287 en run-agent); solo #251 completó. No se tocó «Submit» (final de 219 PRs) ni credenciales. La noticia fue entregada por el chat principal el 21/10 a las 16:17; esta entrada es el asentamiento de cierre de la vigilancia, que se auto-elimina en esta misma corrida.

---

## Publicación v2.1 — estado al 2026-10-21 (posterior al semáforo VERDE)

- Suite del paquete: **149/149** en verde antes de publicar.
- Código v2.1 publicado en `almaoficial/alma-reviewbench` `main`:
  commit **`36ac93aca672326c72ac20af4cfbe7dbd35e6176`** (padre `e4a9dae`),
  «Revisor v2.1: una pasada, 19 clases en secciones (diseño C1 de la
  Adenda 6) + pre-registro v2.1 + semáforo v2.1 VERDE». Contenido
  verificado blob a blob contra el paquete local (4 agregados:
  `agent/llm_reviewer_v21.py`, `tests/test_llm_reviewer_v21.py`,
  `PREREGISTRO-REVIEWBENCH-V21.md`, `RESULTADO-SEMAFORO-V21-20261021.md`;
  2 modificados: `agent/main.py`, `PREREGISTRO-REVIEWBENCH-V2.md` con las
  Adendas 5–6). Puertas 1.0.0–1.3.0 sin cambios (blobs remotos idénticos;
  POLICY 1.3.0 `0a711435…`).
- **Imagen v2.1: PENDIENTE DE CONSTRUCCIÓN.** El workflow
  `reviewbench-image` (nº 388457270) es solo `workflow_dispatch` y las
  vías de API disponibles en esta VM no pueden dispararlo: la credencial
  fine-grained almacenada responde 403 «Resource not accessible by
  personal access token» en el endpoint de dispatches (sin permiso de
  Actions) y el MCP de GitHub no expone herramientas de Actions. El
  disparo requiere la UI de GitHub (Actions → reviewbench-image → Run
  workflow, tag `dev`, package_dir `.`) — el mismo gesto manual con el
  que se disparó el run nº 3 de la v2. Apenas el run exista, el digest se
  obtiene de GHCR por pull fresco (vía verificada: hoy el tag `dev`
  resuelve al digest v2 `f2da937c…`) y se asienta con su commit
  declarado, como en la v2.
- `MANIFIESTO-V21.md` preparado completo salvo el campo del digest
  (marcado PENDIENTE, sin inventar) y `GUION-PORTAL-V21.md` preparado
  (actualización de ambas configuraciones: imagen v2.1, labels
  `reviewer=v21`/`gate=v13`, freno 6,50 por verificar en Credentials de
  cada una) — portal sin tocar, práctica sin lanzar.

### Cierre del manifiesto v2.1 — imagen publicada (2026-10-21)

- El workflow `reviewbench-image` corrió sobre `main` @ `36ac93a` y
  publicó la imagen v2.1 en GHCR: el tag `dev` resuelve a
  `ghcr.io/almaoficial/alma-reviewbench@sha256:32da7c01181c3ebae61d6cb9d5d31590858ad328c7f292d56d153a5b0523a0bc`
  (digest completo, 64 caracteres), **verificado contra GHCR el
  2026-10-21**.
- `MANIFIESTO-V21.md` cerrado: el campo «Imagen (digest)» quedó asentado
  con ese digest y el manifiesto se subió al repo con commit declarado
  en `main` (ver el historial del repo).
- **Estado: imagen v2.1 publicada, digest asentado, práctica v2.1 por
  lanzar** — pendiente actualizar las configuraciones del portal (guion
  `GUION-PORTAL-V21.md`), el freno US$6,50 efectivamente cargado en
  Credentials de cada configuración y el «sí» de Alejandro al momento
  de lanzar.

### Práctica v2.1 — brazo base nº 290 y linterna (2026-10-21)

- Configuraciones actualizadas en el portal según `GUION-PORTAL-V21.md`
  (imagen v2.1 `sha256:32da7c01…`, labels `reviewer=v21`/`gate=v13` en
  ambas; único campo distinto = `governance`). Alejandro dio el «Corre»
  y la base se lanzó con «Test run» («Submit» jamás tocado).
- **Corrida nº 290 (base): SUCCEEDED** — lanzada 2026-10-21 18:00:52
  EDT. Puntajes del portal: **precisión 37,5 % · recall 0,4 %** · F1
  ≈0,8 % (calculado; el portal no lo muestra) · 8 hallazgos, 3
  novedosos. Primera práctica de un revisor post-v1 que completa y
  puntúa.
- **PRUEBA DE LA LINTERNA: NO PASA** (recall base 0,4 % ≤ 0,7 % de la
  v1). Por el papel v2.1 §3, el brazo ALMA **no se lanzó** y la
  práctica v2.1 queda **SIN VEREDICTO VÁLIDO** sobre «ALMA mejora»: la
  regla de avance no se aplica con un base que no ve.
- **Causa declarada:** dilución C1 en PRs reales — el riesgo de la
  Adenda 6 y falsador de la §6 del papel v2.1. La pasada única vio 7/8
  en la batería miniatura (semáforo VERDE) pero se diluye en contextos
  reales grandes. La economía quedó resuelta (sin negativas de la
  guardia); el problema es la vista, no el costo.
- Detalle completo en `RESULTADO-PRACTICA-V21-20261021.md`. Salida
  según el papel: C2 (triage + pasadas profundas ≤5) con su propio
  pre-registro (`PREREGISTRO-REVIEWBENCH-V22.md`) — decisión de
  Alejandro del 21/10, 18:30 EDT.

### Cierre del manifiesto v2.2 — imagen publicada (2026-10-21)

- El workflow `reviewbench-image` (corrida nº 5) corrió sobre `main` @
  `031dd0f` y publicó la imagen v2.2 en GHCR: el tag `dev` resuelve a
  `ghcr.io/almaoficial/alma-reviewbench@sha256:577bc2ec6780c5af4d3260caad74d3bd06b73dedf5b4e616ddbe03e44880206a`
  (digest completo, 64 caracteres), **verificado contra GHCR el
  2026-10-21** con token anónimo (fuente primaria: cabecera
  Docker-Content-Digest; contenido verificado: la imagen incluye
  `app/agent/llm_reviewer_v22.py`). La corrida nº 5 cerró
  completed/success con head_sha `031dd0f37bdb…` y esta vez sin la
  espera de la nº 4: creada 23:39:33 UTC, cerrada 23:40:04 UTC.
- `MANIFIESTO-V22.md` cerrado: el campo «Imagen (digest)» quedó asentado
  con ese digest y el manifiesto se subió al repo con commit
  `cc4dbc8a679cd739673bbecec46b96f944857a56` en `main` (conector oficial
  de GitHub, `push_files`; lectura de vuelta verificada contra el
  repo). Clon local sincronizado en ese commit.
- **Estado: imagen v2.2 publicada, digest asentado, práctica v2.2 por
  lanzar** — pendiente actualizar las configuraciones del portal
  (guion `GUION-PORTAL-V22.md`: imagen v2.2 `sha256:577bc2ec…`, labels
  `reviewer=v22`/`gate=v13` en ambas; único campo distinto =
  `governance`) y el «Corre» de Alejandro al momento de lanzar.
  Semáforo v2.2 VERDE asentado en el manifiesto (base 7/8 · ALMA 6/8 ·
  US$0,6221; triage 16/16; señal del brazo ALMA declarada con su
  anatomía de sem_01/sem_02).

### Práctica v2.2 — base nº 295 y linterna (2026-10-21)

- **Corrida nº 295 (base v22): SUCCEEDED** — lanzada 2026-10-21 19:57:18 EDT, config «llm · base · gpt-5.6-sol · medium · v22 · v13», imagen `sha256:577bc2ec…`. Verificado en el portal (review-bench.ai, alma-reviewer) en la vigilancia de las 20:10–20:26 EDT: estado verbatim «succeeded».
- **Puntajes del portal:** Grounded F1 0,0 % · Precision 0,0 % · Recall 0,0 %; Augmented F1 0,8 % · Precision 15,0 % · Recall 0,4 %; duración promedio 7 s; findings 11 (3 novel).
- **PRUEBA DE LA LINTERNA: NO PASA** — recall_base grounded 0,0 % (y augmented 0,4 %) ≤ 0,007 (0,7 %). Por el papel v22, el brazo ALMA **no se lanzó** y la práctica v2.2 queda **SIN VEREDICTO VÁLIDO** sobre «ALMA mejora»: la regla de avance no se aplica con un base que no ve.
- No existe ninguna corrida v22 más nueva que la #295 en ninguna configuración; la corrida ALMA más reciente sigue siendo la #253 del 19/10 (failed at score). No se tocó «Submit» ni credenciales ni el freno.
- **Falsador propio de C2 (§7):** en la evidencia disponible del portal (lista y puntajes) no se observaron eventos de degradación/truncación asentados; no se gatilla con la evidencia disponible — queda marcado como no verificado a nivel de outputs por PR.
- Detalle completo en `RESULTADO-PRACTICA-V22-20261021.md`. La vigilancia `vigilar-practica-v22-reviewbench` se elimina en esta misma pasada, como manda el protocolo ante linterna fallida.

### Semáforo v2.3 — SOLO brazo base: VERDE (2026-10-21)

- **Corrida:** revisor v2.3 (`RB_CONFIG_REVIEWER=v23`, `gate=v13`
  declarado/omitido — brazo base), gpt-5.6-sol effort medium, sobre
  la batería congelada (hashes 32/32 verificados; suite previa
  208/208 en seco; sonda de clave HTTP 200). Autorización de
  Alejandro 21/10 21:35 EDT; clave por la vía sancionada
  (`custom.openai-rbench`, sustituto solo en el entorno).
- **Brazo ALMA NO corrido, por papel:** la puerta 1.4.0 no pasó su
  medición de adopción (falsos nuevos = 1; `RESULTADO-MEDICION-PUERTA-140.md`)
  y la §4 del papel v2.3 prohíbe sustituirla por la 1.3.0. El
  veredicto se declara solo sobre el brazo base.
- **Resultado base: 16 emitidos, 8/8 detectados, US$0,53607**
  (tope duro US$20). 26 llamadas (8 selección + 18 profundas);
  degradación en 0/8, negativas 0/8, malformed/unanchored 0.
- **Marcas por familia:** especialidad 8/8 (siempre la plantada);
  general `security` 8/8 y `reliability` 2/8. Detección por vía de
  especialidad: 7/8. **sem_02: el silencio de la profunda de
  `hardcoded_secret` reapareció** (cuarto semáforo consecutivo),
  pero la pasada general `security` produjo el hallazgo
  (`app/billing.py:6`) y el caso puntuó — rescate por la vía nueva,
  asentado con su anatomía. sem_01 sin novedad: el rechazo de cita
  es fenómeno del brazo ALMA, que no corrió.
- **Declaración §9:** este semáforo afirma mecánica, economía en
  miniatura y que la vía de especialidad sobrevivió al ensanche;
  NO afirma detección general (la batería no tiene TP generales) y
  no predice recall en la práctica. Comparación base: v2 8/8 ·
  v2.1 7/8 · v2.2 7/8 · v2.3 8/8.
- **Consecuencia:** procede publicación v2.3 y práctica del brazo
  base (base primero, linterna) con el «sí» de Alejandro al lanzar;
  el brazo ALMA sigue bloqueado hasta un papel nuevo de puerta.
  Detalle completo en `RESULTADO-SEMAFORO-V23-20261021.md`; crudos
  en `runs/semaforo-v23-20261021/`.

### Publicación v2.3 — código en el repo; imagen y portal pendientes de UI (2026-10-21)

- **Autorización:** Alejandro, 21/10/2026 21:47 EDT («Publicar la
  v2.3 (base)»), tras el semáforo VERDE del brazo base.
- **Verificación previa al push (en seco, US$0):** suite completa
  **208/208** (163 heredadas + 27 de la puerta 1.4.0 + 18 del revisor
  v2.3); puertas congeladas byte-idénticas por sha256 — 1.0.0
  `4223cb05…`, 1.1.0 `fdd974f1…`, 1.2.0 `c5c32bfc…`, 1.3.0
  `d3b993d4d4f26b9df112dfd54abc391e8018faae024d23c63b4924d86d2dc1e0`
  (POLICY_SHA256 1.3.0
  `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`).
  El `agent/main.py` local se cotejó contra el remoto @ `cc4dbc8`:
  difiere solo en los agregados v2.3 (selector `reviewer=v23`,
  selector `gate=v14`, sección `needs_validation` del ledger).
- **Push (conector de GitHub, `push_files`; la VM no tiene
  credenciales de push):** commit
  **`a6838e60df8d754f361eb10e38eff815ae60708b`** en `main`, padre
  `cc4dbc8`, con 11 archivos: `agent/llm_reviewer_v23.py`,
  `agent/alma_gate_v14.py`, `agent/main.py`, `tests/test_gate_v14.py`,
  `tests/test_llm_reviewer_v23.py`, `medir_adopcion_v14.py`,
  `PREREGISTRO-REVIEWBENCH-V23.md`, `PREREGISTRO-PUERTA-140.md`,
  `PREREGISTRO-PUERTA-141.md`, `RESULTADO-MEDICION-PUERTA-140.md`,
  `RESULTADO-SEMAFORO-V23-20261021.md`. Verificado por relectura del
  repo: `agent/` remoto contiene `llm_reviewer_v23.py` y
  `alma_gate_v14.py` en ese commit. `fixtures_semaforo/` NO viajó
  (Push Protection), como en todas las publicaciones.
- **Imagen: PENDIENTE.** El workflow `reviewbench-image` es
  `workflow_dispatch` — se dispara desde la UI de GitHub Actions y la
  API de esta VM no puede (403, confirmado en v2.1/v2.2). Hasta que
  el workflow corra sobre `main` @ `a6838e6` y el digest se verifique
  contra GHCR (tag `dev` → digest; contenido con
  `app/agent/llm_reviewer_v23.py`), el campo «Imagen (digest)» de
  `MANIFIESTO-V23.md` queda **PENDIENTE** y no hay commit de cierre.
- **Portal: SIN TOCAR todavía.** Preparado `GUION-PORTAL-V23.md`:
  cuando exista el digest verificado, se actualiza SOLO la
  configuración base (imagen nueva; labels `backend=llm`,
  `governance=base`, `model=gpt-5.6-sol`, `effort=medium`,
  `reviewer=v23`, `gate=v13`; guardar y releer). La configuración
  ALMA **no se actualiza** (brazo bloqueado: puerta 1.4.0 NO
  adoptada — 1 falso nuevo, S3 — según
  `RESULTADO-MEDICION-PUERTA-140.md`). `RB_MAX_SPEND_USD` no se leyó
  ni se modificó. No se lanzó ninguna corrida; «Submit» intacto.
- **Manifiesto:** `MANIFIESTO-V23.md` redactado con el sobre completo
  y las declaraciones honestas (semáforo VERDE solo del brazo base,
  con el rescate de sem_02 por la vía general y la especialidad sola
  en 7/8; puerta 1.4.0 construida y medida pero NO ADOPTADA; brazo
  ALMA bloqueado; papel 1.4.1 escrito, sin construir). Su push viaja
  en el commit de cierre, con el digest asentado, como en la v2.2.
- **Siguiente paso (bloqueo exacto):** disparo del workflow
  `reviewbench-image` desde la UI de GitHub Actions — paso de
  navegador con la sesión de Alejandro, fuera del alcance de esta
  pasada. Con el digest verificado: commit de cierre del manifiesto,
  ejecución del guion del portal (solo base) y práctica v2.3 del
  brazo base con el «Corre» de Alejandro al lanzar.

### Puerta 1.4.1 — construida en seco y ADOPTADA en su medición (2026-10-21)

- **Autorización:** Alejandro, 21/10/2026 21:49 EDT («Sí al papel
  1.4.1 — construirla en seco»): solo construcción en seco +
  medición offline (US$0, sin portal, sin publicar).
- **Construcción:** `agent/alma_gate_v141.py` (delegación a la
  1.3.0; selector `RB_CONFIG_GATE=v141` en `agent/main.py`, default
  sin cambio) — `POLICY_VERSION: alma-evidence-gate/1.4.1`,
  `POLICY_SHA256: 73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46`.
  Cambio único del §2 del papel: el chequeo (f) «sin línea agregada»
  sale de los chequeos de completitud — candidato de clase sin
  ninguna línea agregada en su evidencia = **rechazo firme** en la
  frontera, dominante sobre (a)/(b); habilitantes del tercer estado
  quedan solo (a) co-ocurrencia y (b) construcción fuera del span.
  Registro `needs_validation` sin `severity`, con blockers, igual
  que la 1.4.0; la extensión a hallazgos generales NO se tocó.
- **Suite: 236/236 verde** (208 heredadas + 28 nuevas de
  `tests/test_gate_v141.py`, con las categorías del §4: tipo S3 →
  rechazo firme; tipo VP con línea agregada y co-ocurrencia partida
  → sigue `needs_validation`; mixto (f)+(a) → rechazo firme por
  dominancia).
- **Medición de adopción (§4, instrumento `medir_adopcion_v141.py`,
  tres universos re-corridos completos): ADOPTADA** — VP
  recuperados = **4, los mismos 4** de la medición de la 1.4.0
  (sem_01 `sql_injection` en ambos brazos de ambas corridas,
  blocker `co_occurrence`; U1: primario 2 + secundario 2, falsos
  U1 = 0, sanidad del re-juicio 1.3.0 OK); falsos nuevos = **0** en
  los tres universos; equivalencia exacta de aceptados con la
  1.3.0 en los tres universos; U2 (69 ataques) y U3 (36 candidatos)
  con **cero movimientos** de estado. **S3: rechazado en la 1.3.0 →
  rechazado en la 1.4.1, sin movimiento**, causal (f) asentada en
  sus razones (bajo la 1.4.0 era el único movimiento y el falso que
  la dejó no adoptada).
- **Invariantes:** puertas 1.0.0–1.3.0 y 1.4.0 byte-idénticas al
  cierre (archivo 1.4.0 sha256 `b16c5a79…`, POLICY `b0c0aa66…`);
  papeles intactos. Detalle completo en
  `RESULTADO-MEDICION-PUERTA-141.md`.
- **Consecuencia (§6 del papel):** adoptada ≠ en uso — el brazo
  ALMA de la v2.3 sigue sin correr hasta que exista la adenda
  firmada al papel v2.3 que declare el reemplazo de la 1.4.0 por la
  1.4.1 y la etiqueta `gate=v141`, anterior a cualquier corrida
  ALMA. Nada se corrió ni se publicó con ella.

### Adenda 1 al papel v2.3 — puerta del brazo ALMA: 1.4.0 → 1.4.1 (`gate=v141`) (2026-10-21)

- **Firma:** Alejandro, 21/10/2026 21:56 EDT («Firmar la adenda
  (gate=v141)»). Es la adenda que la §6 del
  `PREREGISTRO-PUERTA-141.md` exigía antes de cualquier corrida
  ALMA; quedó agregada al final del `PREREGISTRO-REVIEWBENCH-V23.md`
  sin alterar ni una línea del cuerpo original.
- **Declara:** la 1.4.0 fue construida y medida y **NO adoptada**
  (recibo `RESULTADO-MEDICION-PUERTA-140.md`: VP = 4, equivalencia
  exacta, 1 falso = S3), por lo que el brazo ALMA no podía correr
  con ella; la 1.4.1 fue pre-registrada, construida en seco y
  **ADOPTADA** (recibo `RESULTADO-MEDICION-PUERTA-141.md`: VP = los
  mismos 4, falsos = 0, S3 rechazado firme sin movimiento,
  equivalencia exacta, suite 236/236); en consecuencia la puerta
  del brazo ALMA de la v2.3 es la **`alma-evidence-gate/1.4.1`**,
  etiqueta de config **`gate=v141`** (módulo
  `agent/alma_gate_v141.py`, selector `RB_CONFIG_GATE=v141`). La
  etiqueta `v14` queda atada para siempre al artefacto 1.4.0.
- **Intacto:** todo lo demás del papel v2.3 — variante (ii)
  `needs_validation`, regla de avance de la §6 (linterna R_base
  grounded > 0,7 % primero; P_ALMA ≥ P_base + 0,05; pureza de
  retención; pérdida inexplicada = 0), orden base → linterna →
  ALMA, frenos y topes.
- **Secuencia pendiente:** el código v141 todavía NO está en la
  imagen publicada (la imagen v2.3 en curso contiene la 1.4.0);
  correr el brazo ALMA requerirá publicar el código v141 en una
  imagen verificada y editar la config ALMA del portal con
  `gate=v141` — pasos futuros, cada uno con su verificación, y solo
  pertinentes si la práctica base supera la linterna. La adenda no
  autoriza ninguna corrida. Gasto: US$0.

### Cierre de la publicación v2.3 — imagen verificada y config base del portal (2026-10-21)

- **Workflow:** `reviewbench-image` **corrida nº 6** —
  https://github.com/almaoficial/alma-reviewbench/actions/runs/39708506752
  — disparada y cerrada el **2026-10-21 21:55–21:56 EDT**, resultado
  **SUCCESS**, sobre `main` @ `a6838e6`, inputs `tag=dev`,
  `package_dir=.`.
- **Digest verificado y asentado:**
  `ghcr.io/almaoficial/alma-reviewbench@sha256:932ac3ffa1944d92cb4defd5b96b7b1146eb37bdd3b4245676039e7844b40e27`
  (64 caracteres, sin truncar). Método: el digest lo imprimió el
  resumen del workflow y se cotejó contra la **página del paquete en
  GHCR** (versión `1425525285`, tag `dev`) — esa página es la
  constancia registral usada. Contenido verificado por la cadena de
  build: el commit `a6838e6` contiene `agent/llm_reviewer_v23.py`
  (977 líneas), el Dockerfile copia `agent/` a `/app/agent` y
  `.dockerignore` no excluye `agent/`. **Salvedad declarada:** la API
  `/v2` de GHCR con token anónimo devolvió 401 por header en
  navegación y no se usó como constancia; es el mismo método de
  cierre que cerró la v2.1 y la v2.2. El digest quedó asentado en el
  campo «Imagen (digest)» de `MANIFIESTO-V23.md` (commit de cierre).
- **Config base del portal — relectura campo por campo tras guardar
  (verbatim):** imagen =
  `ghcr.io/almaoficial/alma-reviewbench@sha256:932ac3ffa1944d92cb4defd5b96b7b1146eb37bdd3b4245676039e7844b40e27`
  (el digest completo); labels exactos: `backend=llm`,
  `governance=base`, `model=gpt-5.6-sol`, `effort=medium`,
  `reviewer=v23`, `gate=v13`; fila del leaderboard:
  `rowalma-reviewer-llm-base-gpt-5-6-sol-medium-v23-v13`.
- **Constancias:** la configuración **ALMA no fue modificada** en
  esta publicación (queda con la imagen v2.2, `reviewer=v22`,
  `gate=v13`); `RB_MAX_SPEND_USD` **no fue leído ni modificado**
  (siguió enmascarado en todo momento); **ninguna corrida fue
  lanzada** y **«Submit» no fue tocado**.
- **Estado:** publicación v2.3 **cerrada** — código (`a6838e6`),
  imagen (digest verificado) y config base del portal alineados. La
  práctica («Test run», 25 PRs, solo brazo base) espera el «Corre»
  expreso de Alejandro; la linterna sigue siendo recall base grounded
  > 0,7 % sobre 352 TP. Gasto de este cierre: US$0.

### Adjudicación parcial de la nº 296 contra el gold (2026-10-21)

- **Qué se hizo:** adjudicación en seco (US$0, sin llamadas, sin
  portal) de los 106 findings que la práctica nº 296 alcanzó a
  emitir en los 15 PRs que completaron, contra el gold público de
  ReviewBench (352 TP / 213 FP), con el criterio de matching de la
  casa (mismo archivo + mismo defecto; el que reprodujo los números
  del portal en la nº 251). Aprobada por Alejandro («Ok lo hagamos»,
  2026-10-21 23:03 EDT). Informe completo:
  `ADJUDICACION-PARCIAL-296-20261021.md`.
- **Resultado del subconjunto (15 PRs, 195 TP gold):** precisión
  grounded parcial **51,9 %** (55 emisiones TP-grounded / 106);
  recall grounded **22,1 %** (43 TP gold distintos cubiertos / 195;
  macro por PR 24,1 %). Cobertura contada sobre el set completo:
  **43/352 = 12,2 %** como piso de estas emisiones — no es el recall
  de una corrida completa y **no** evalúa la linterna ni la regla de
  avance del papel v2.3; la nº 296 sigue FAILED (causa (d)) y sin
  puntaje oficial.
- **Corte por familia:** vía **general 55/55** emisiones grounded y
  43/43 TP cubiertos; **especialidad 0** (solo CrabTrap seleccionó
  una clase, `sql_injection`, sin sobrevivientes de su clase). La
  pregunta del Camino A quedó respondida: la vía general produce
  verdaderos grounded en diffs reales.
- **Casos alcanzables (diagnóstico v2.2):** 3 de 6 detectados en el
  subconjunto (LANdalf :184, pika `ContentView.swift:151`, konturio
  `GenericRenderer.ts:229`); los 3 perdidos (apilix, jadx :550,
  CrabTrap :325) se perdieron en la pasada profunda, no en la
  selección — en la nº 295 los 9 se habían perdido en selección.
- **Sin cambios:** ningún código, papel ni config fue modificado;
  no se relanzó nada. Pendiente intacto: el arreglo del techo de
  tokens requiere papel/adenda + decisión de gasto (del tope de
  US$30 del papel ya se consumieron US$13,50 en el intento fallido).

### Práctica v2.3 — base nº 296: FAILED en run-agent, sin puntaje (2026-10-21)

- **Corrida nº 296 (base v23): FAILED «at run-agent (3, 4)»** — lanzada 2026-10-21 22:26:40 EDT con el «Corre» de Alejandro; config «llm · base · gpt-5.6-sol · medium · v23 · v13», imagen `sha256:932ac3ffa194…`. Sin puntajes del portal (grounded/augmented sin valores).
- **Outputs (zip descargado y leído completo; copia en `runs/run-296-output.zip`, 44.799 B):** «The run ended with errors» — 20 PRs alcanzados de 25 (15 succeeded, 5 en `error:2`, 5 nunca alcanzados: el shard 2 se detuvo en su primer PR por preflight). Los 5 errores cierran con el mismo texto: «selection pass did not return parseable JSON; failing closed» (chronicle#14, emdash#2, agents-config#1, wirechat#183, fastimage#165; 3 intentos c/u). Hallazgos emitidos en los 15 PRs completados: **106, nunca puntuados**; malformed/unanchored = 0. Degradación `spend_cap` declarada en 3 PRs (figlet 5→3, pika 5→4, TechDebtMCP 5→4).
- **Costo real por diferencia de saldo (org Personal): US$16,52 (22:25 EDT) − US$3,02 (final) = US$13,50.** Dentro del tope de US$30. La suma de estimaciones del agente a tarifas de planificación (US$32,47 en los intentos finales de los 15 PRs) es estimación de guardia, no facturación.
- **LINTERNA: NO PASA por ausencia de medición** — sin recall grounded no hay prueba posible. **Consecuencia pre-registrada: el brazo ALMA NO se lanzó** y la práctica v2.3 queda **SIN VEREDICTO VÁLIDO** sobre «ALMA mejora»; tampoco se publica imagen con `gate=v141` ni se edita la config ALMA (Adenda 1 §5).
- **Lectura del falsador (§8):** el encuadre NO quedó juzgado — la corrida murió en la selección antes de medir detección. Causa (d), defecto del diseño: la selección generalizada heredó el techo de completion de 1.024 tokens y en diffs reales el razonamiento lo agota antes del JSON (inferencia declarada; el código no asienta `finish_reason`). Economía no gatillada (degradación 3/15 completados = 20 % < 1/4). Modo de falla nuevo asentado: la selección puede no responder, no solo no marcar.
- **Nota de integridad:** una pasada intermedia del navegador reportó «SUCCEEDED» con puntajes (P 11,1 % · R 0,3 %; findings 36); quedó DESCARTADA por contradecir el zip de outputs y el cierre asentado, y ningún número suyo se usa. Detalle completo en `RESULTADO-PRACTICA-V23-20261021.md`. La vigilancia `vigilar-practica-v23-reviewbench` se elimina en esta pasada.

### Adenda 2 al papel v2.3 — reparación del techo de la selección (v2.3.1) (2026-10-21)

- **Qué se asentó:** ADENDA 2 agregada al final de `PREREGISTRO-REVIEWBENCH-V23.md`, sin tocar el cuerpo original ni la Adenda 1, firmada por Alejandro el 2026-10-21 a las 23:20 EDT («Bueno lo hagamos»). Pre-registra la reparación de la causa **(d)** que mató la práctica nº 296. Recibos: `DIAGNOSTICO-PRACTICA-V23-20261021.md` (la selección generalizada heredó el techo de completion de 1.024 tokens; el razonamiento lo agota en diffs reales y el JSON vuelve vacío/truncado → fail-closed; paso fino declarado inferencia) y `ADJUDICACION-PARCIAL-296-20261021.md` (sobre los 15 PRs completados: P grounded 51,9 %, R del subconjunto 22,1 %, los 43 TP todos por la vía general — parcial, no puntaje).
- **El cambio (dos piezas, nada más):** (i) techo de completion de la pasada de **selección 1.024 → 4.096 tokens** (las pasadas profundas no se tocan); (ii) **observabilidad** — ante un parseo fallido, el revisor asienta `finish_reason` y un extracto acotado del contenido crudo en el run-info, sin cambio de comportamiento. La construcción corregida se nombra **v2.3.1**; la etiqueta `reviewer` del portal se mantiene en `v23` y la versión se declara en el manifiesto.
- **Peor caso re-derivado:** solo se mueve el término de salida de la selección (US$0,0768 → US$0,3072; **+US$0,2304 ≈ +US$0,23/PR**). Plan ancla completo ≈**US$5,33 < US$6,50** (entra entero); contexto saturado ≈US$7,13 → la **degradación heredada absorbe** (selección + 4 profundas ≈US$5,82; la 5ª se declara). Freno por PR intacto; `RB_MAX_SPEND_USD` no se toca.
- **Sonda previa obligatoria (antes de la práctica):** solo la pasada de selección arreglada, en local con la credencial sancionada, sobre los **5 PRs que murieron 3/3** en la nº 296 — `simnaut_emdash_2`, `scotthamilton77_agents-config_1`, `wirechat_wirechat_183`, `mheuss_chronicle_14`, `sdsykes_fastimage_165` — y, si el presupuesto lo permite, los 3 intermitentes (`PierreJanineh_TechDebtMCP_135`, `brianc_node-postgres_3650`, `cmik_apilix_12`). **Éxito = JSON parseable en TODOS los casos corridos**; **tope duro US$8**; si un caso no parsea, **no hay práctica** y se vuelve a diagnóstico en seco (ya sin inferencia, por la pieza (ii)).
- **Presupuesto de la etapa (supersede la banda/tope de práctica del papel — US$10–25 / tope US$30 — solo para esta etapa; de ese tope ya se consumieron US$13,50 en la nº 296):** sonda ≤ US$8 + práctica base relanzada US$15–25 + brazo ALMA US$15–25 **solo si la linterna pasa**. **Compuerta de saldo (vinculante):** saldo actual **US$3,02** — ningún paso con gasto corre sin carga previa de Alejandro y sin saldo verificado ≥ el costo esperado del paso (sonda ≥ US$8; práctica ≥ US$25; ALMA ≥ US$25 + linterna).
- **Secuencia declarada:** adenda → construcción en seco v2.3.1 (suite completa verde, con tests nuevos del techo y de la observabilidad) → sonda (tope US$8) → publicación de la imagen corregida (digest verificado contra GHCR, manifiesto v2.3.1; el commit incluye los documentos locales pendientes: paquete 1.4.1 completo, el papel con esta adenda, el diagnóstico y la adjudicación de la nº 296 y su resultado formal) → config base del portal a la imagen nueva (`reviewer=v23`, `gate=v13`; config ALMA intacta en este paso) → práctica base relanzada → linterna → si pasa, brazo ALMA con `gate=v141` sobre la **misma** imagen corregida (secuencia de la Adenda 1, §5).
- **Honestidad y falsadores:** la nº 296 queda **FAILED para siempre** (esta adenda no la re-califica; la adjudicación parcial no es puntaje). Si la práctica relanzada muere con la **misma firma** (JSON no parseable en la selección), la **hipótesis del techo queda refutada** y la línea se detiene **sin tercer intento automático**; si el cuerpo asentado mostrara truncación aun con 4.096, también se detiene a papel.
- **Gasto de este asiento:** US$0 — sin código, sin corridas, sin portal, sin publicar.

### Arreglo v2.3.1 construido en seco (2026-10-21)

- **Qué se construyó (las dos piezas de la Adenda 2, nada más), todo en `agent/llm_reviewer_v23.py` (`ce13389b…` → `55cba627…`):** (i) techo de completion de la selección **1.024 → 4.096** por la vía de config existente (`DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS`, entorno/config) — las profundas conservan su techo; el presupuesto medido v2.3.0 queda reproducible fijando 1024 (con test); `REVIEWER_VERSION = llm-reviewer/2.3.1`. (ii) **Observabilidad:** `_call` devuelve también `finish_reason`; ante un contenido no parseable o vacío de cualquier pasada, el run-info asienta un registro `parse_failures` (`pass`, `finish_reason`, `content_length`, extracto ≤500 caracteres) y el mensaje de la negativa lleva los mismos datos con el texto original como prefijo (llega también al `agent.log`); el run-info asienta además `triage_max_output_tokens`. **El fail-closed no se movió.**
- **Peor caso re-derivado con la aritmética del propio revisor** (método de construcción, que a 1.024 reproduce exacto 5,4250/7,2524): delta exacto **+US$0,2304/PR** (3.072 tokens × US$75/Mtok); **plan ancla 5,6554 < US$6,50** (entra entero, 5 profundas); saturado 7,4828 → **la degradación absorbe: 4 profundas admitidas (total 6,2328), la 5ª declarada** — igual que a 1.024. **Reconciliación asentada:** las cifras de la Adenda 2 (5,33 / 7,13 / 5,82) salen ~US$0,3 más bajas y no se reproducen con la aritmética del código; las conclusiones coinciden y la aritmética operativa es la del código (detalle en `RESULTADO-ARREGLO-V231-20261021.md`).
- **Pruebas: suite completa 245/245 en verde** (236 heredadas + 9 nuevas en `tests/test_llm_reviewer_v231.py`: techo solo en la selección, pin 1024 reproducible por entorno y por config, delta exacto, asiento de finish_reason/extracto ante truncado/vacío/no-JSON con fail-closed intacto, corrida exitosa sin registros). Autochequeo de la batería del semáforo dentro de la suite: **16/16 sin regresiones**. Aserciones actualizadas en los tests v2.3 solo donde fijaban el comportamiento corregido (versión ×2, pin 4096, cota de la selección ancla → banda 0,90–1,00, escenario `no_deep_pass_affordable` con selección que reporta haber usado su presupuesto — la declaración bajo prueba no cambió).
- **Invariantes:** puertas 1.0.0–1.4.1 byte-idénticas (hashes re-verificados al cierre); papeles y `agent/main.py` sin tocar. **Gasto US$0** — sin OpenAI, sin portal, sin publicar. Siguiente paso según la adenda: la sonda (≤US$8, compuerta de saldo: hay US$3,02 — requiere carga previa), no esta construcción.

### Sonda dirigida v2.3.1 — ÉXITO: 8/8 selecciones parseables (2026-10-21)

- **Veredicto: ÉXITO según el éxito pre-registrado de la Adenda 2 §4** — JSON parseable en **todos** los casos corridos: los **5 obligatorios** que murieron 3/3 en la nº 296 (`simnaut_emdash_2`, `scotthamilton77_agents-config_1`, `wirechat_wirechat_183`, `mheuss_chronicle_14`, `sdsykes_fastimage_165`) **y los 3 intermitentes** (`PierreJanineh_TechDebtMCP_135`, `brianc_node-postgres_3650`, `cmik_apilix_12`), alcanzados porque la compuerta de tope lo permitió. Una llamada por caso, sin reintentos, sin pasadas profundas, sin puerta, sin emisión.
- **Cifras:** costo reportado total **US$6,3282** (precios del revisor) contra el **tope duro de US$8**; facturado estimado ≤ ≈US$2,7 (razón ≤0,42 medida en la 296) y saldo estimado post-sonda ≈**US$22,4** sobre los US$25,02 verificados a las 23:27 EDT. Caso dominante: emdash **US$4,0198** (prompt 259.942 tokens — el mismo diff al token: la 295 asentó 259.630, Δ +312 = el system prompt más largo de la v2.3). Configuración idéntica a la del portal: revisor `llm-reviewer/2.3.1` (verificado), `gate=v13`, gpt-5.6-sol, effort medium, techo de selección **4.096**, pre-flight 1 por caso ≤ US$6,50.
- **El mecanismo, por primera vez leído y no inferido:** `finish_reason="stop"` en los 8 casos y **4 casos con razonamiento ≥ el techo viejo de 1.024** (emdash 1.462; chronicle 1.536; agents-config 1.025; wirechat 1.024) — bajo ese techo el contenido no podía existir: la muerte determinista de la 296 queda explicada al token. El intermitente node-postgres midió 886 de razonamiento + 134 visibles = 1.020, **en el borde exacto** del techo viejo: su historia (murió 2, pasó al 3º) es estocasticidad alrededor del borde, medida. Con el techo nuevo el completion máximo fue 1.676 — **2,4× de margen** en el caso más pesado. Las 8 selecciones asentaron sus marcas (38 de vía general + 1 de especialidad: `sql_injection` en chronicle); marcas desconocidas y entradas malformadas: 0 en todos.
- **Diffs:** regenerados en local con `git diff base...head` desde los SHAs base/head de `corpus/test/test.json` del repo público `review-bench/ReviewBench` (el zip de la 296 no los trae; el contrato declara el diff idéntico al que GitHub muestra en el PR; los heads coinciden con los sufijos de los directorios del zip). Detalle, sha256 por caso y tabla completa: `RESULTADO-SONDA-V231-20261021.md`.
- **Alcance (Adenda 2 §4):** la sonda no mide una tasa de muertes ni toca la detección; no se ajustó ningún prompt. **Siguiente paso de la secuencia (§6): publicación de la imagen v2.3.1** → config base a la imagen nueva → práctica relanzada — con la compuerta vinculante: **saldo verificado ≥ US$25 antes de lanzar la práctica**; con el saldo estimado post-sonda hará falta una carga chica antes de ese paso. **El falsador §7 sigue en pie** (misma firma en la relanzada = hipótesis del techo refutada y alto sin tercer intento); la nº 296 queda FAILED para siempre.


### Publicación v2.3.1 COMPLETA — imagen corregida en GHCR, digest verificado (2026-10-22)

- **Commit de publicación:** `cc56817b16daeb17620a77cad859520517bf13cd` en `main` de `almaoficial/alma-reviewbench` (push vía conector, verificado **21/21 archivos byte a byte** contra el remoto). Contenido: `agent/llm_reviewer_v23.py` **v2.3.1** (techo de selección 4.096 + observabilidad `parse_failures`; sha256 `55cba627…`), `agent/main.py` actual con el selector `RB_CONFIG_GATE=v141`, **paquete 1.4.1 completo** (`alma_gate_v141.py`, `tests/test_gate_v141.py`, `medir_adopcion_v141.py`, `RESULTADO-MEDICION-PUERTA-141.md`), `tests/test_llm_reviewer_v23.py` + `tests/test_llm_reviewer_v231.py`, el papel v2.3 completo (46.739 B, Adendas 1 y 2), diagnósticos v2.2 (con su adenda) y v2.3, resultado formal de la nº 296, adjudicación parcial, resultado del arreglo y resultado de la sonda (ÉXITO 8/8). **Extras de custodia declarados en el mensaje del commit** (solo locales hasta hoy): `GUION-PORTAL-V21.md`, `GUION-PORTAL-V22.md`, `GUION-PORTAL-V23.md`, `RESULTADO-PRACTICA-V21-20261021.md`, `RESULTADO-PRACTICA-V22-20261021.md`. **No subidos:** `fixtures_semaforo/` ni `runs/`, como manda la regla.
- **Imagen:** workflow `reviewbench-image` **corrida nº 7: SUCCESS** (21 s, 2026-10-22 00:09 EDT) — https://github.com/almaoficial/alma-reviewbench/actions/runs/39720724484 — disparada sobre `main` @ `cc56817` con inputs `tag=dev`, `package_dir=.`. **Digest: `ghcr.io/almaoficial/alma-reviewbench@sha256:144756cea49ee33e8b16ddb0204556adb0f1c2430ea885ec6a206bbaa6964544`** — el del resumen de la corrida («ReviewBench image published») **idéntico** al de la página del paquete GHCR (versión `1425887291`, tag `dev`, reemplaza a la `1425525285` de la v2.3). **Salvedad registral de siempre:** la constancia es la página del paquete; el contenido se verifica por cadena de build (el commit `cc56817` contiene `agent/llm_reviewer_v23.py` v2.3.1 y el Dockerfile copia `agent/` a `/app/agent`).
- **Qué lleva la imagen:** el revisor `llm-reviewer/2.3.1` con las dos piezas de la Adenda 2 (techo de completion de la selección **1.024 → 4.096** y asiento de `finish_reason`/extracto ante parseos fallidos, sin cambio del fail-closed), la arquitectura v2.3 intacta, la **puerta 1.4.1 adoptada** y su selector `v141` para el brazo ALMA futuro. La etiqueta `reviewer` del portal **se mantiene en `v23`** y la base sigue **`gate=v13`**, como pre-registró la adenda.
- **Cierre documental:** `MANIFIESTO-V231.md` (sobre con commit, corrida y digest cotejado en dos fuentes; economía re-derivada: ancla US$5,6554 < US$6,50, saturado con 4 profundas US$6,2328) + este asiento, subidos en el commit de cierre; el REGISTRO subido es el archivo local completo (58.100 B contra 43.874 B remotos — arrastra los asientos de esta noche desde el cierre v2.3, patrón anterior).
- **Secuencia de la Adenda 2 §6 — estado:** adenda ✓ · construcción en seco (suite 245/245) ✓ · sonda (ÉXITO 8/8, US$6,3282 ≤ tope US$8) ✓ · **publicación ✓**. **Queda:** config base del portal a la imagen nueva (solo el campo de imagen; labels intactos; `RB_MAX_SPEND_USD` no se toca; config ALMA intacta en ese paso) → **práctica base relanzada** (compuerta vinculante: saldo verificado ≥ US$25 antes de lanzar; Alejandro reportó saldo US$28 tras su carga de las 23:50 EDT, a verificar en el portal en el acto del lanzamiento) → **linterna** (recall grounded > 0,7 % sobre 352 TP) → **brazo ALMA con `gate=v141` sobre esta misma imagen, solo si la linterna pasa**. La nº 296 queda FAILED para siempre y el falsador §7 sigue en pie (misma firma en la relanzada = hipótesis del techo refutada, alto sin tercer intento automático).
- **Gasto de esta publicación: US$0** — sin portal, sin corridas, sin llamadas a modelos.

### Práctica v2.3.1 — base nº 298: SUCCEEDED, linterna no acreditada (2026-10-22)

- **Corrida nº 298 (base v23, imagen v2.3.1 `sha256:144756cea4…`): SUCCEEDED** — lanzada 2026-10-22 00:32:41 EDT; config «llm · base · gpt-5.6-sol · medium · v23 · v13», revisor `llm-reviewer/2.3.1`. Puntajes verbatim del portal (lista de corridas): **«P 89.4% · R 34.5% · 166 findings · 88 novel»**, **sin etiqueta** Grounded/Augmented.
- **Salvedad asentada:** el desglose Grounded/Augmented, cualquier F1 y la duración media **no aparecen en ninguna vista accesible del portal** para la 298 (búsqueda exhaustiva en dos pasadas: lista, detalle por PR, «Best run», configuración, «Final runs» = «None yet.», leaderboard público sin `alma-reviewer`). Comparación de integridad: el mismo portal hoy muestra la nº 295 solo como «P 15% · R 0.4%», que en su resultado asentado corresponde a su **Augmented** (Grounded 0,0 %/0,0 %) — el P/R de lista no se acredita como grounded.
- **Outputs (zip descargado, 69.389 B, md5 `9a224fb4…`; copia idéntica en `runs/run-298-output.zip`):** 25/25 PRs succeeded, 4/4 shards; 166 findings en los `findings.json` (= portal); `malformed = 0`, `unanchored = 2`; **`parse_failures = []` en los 25 PRs y cero errores «parseable JSON»** con techo de selección 4.096 asentado en todos; cero PRs con cero marcas; **degradación declarada en 10/25 PRs** (9 `spend_cap` + emdash `no_deep_pass_affordable` 5→0, único PR con 0 hallazgos). Duración media por PR según los outputs: 102,5 s. Estimación de la guardia: US$63,6736 (104 llamadas, tarifas de planificación — no es lo facturado).
- **Costo real por diferencia de saldo (org Personal): US$27,99 (00:31–00:32 EDT) − US$7,58 (billing, tras el cierre) = US$20,41** — dentro de la banda US$15–25 de la Adenda 2 §5.
- **LINTERNA: NO PASA por ausencia de medición grounded acreditada** (no por un recall medido bajo el umbral): el recall grounded no está publicado y el 34,5 % sin etiqueta no lo acredita. **Consecuencia: el brazo ALMA NO se lanzó**, la config ALMA no se tocó y ningún paso `gate=v141` se ejecutó. La práctica queda **SIN VEREDICTO VÁLIDO** sobre «ALMA mejora» hasta la adjudicación grounded de los 166 hallazgos contra el gold público (metodología de la adjudicación de la 296; el zip quedó para eso, US$0).
- **Falsadores:** Adenda 2 §7 (misma firma JSON) **NO disparado** — la hipótesis del techo no queda refutada y no hay tercer intento (la relanzada completó); encuadre (§8) **NO juzgado**; **economía (§8) GATILLADO** — degradación 10/25 = 40 % > 1/4 («registrar y detener», registrado tal cual; su aplicación a la secuencia la decide Alejandro); selección ciega **no gatillada** (0/25 sin marcas).
- Detalle completo en `RESULTADO-PRACTICA-V231-20261022.md`. La vigilancia `vigilar-practica-v231-reviewbench` se elimina en esta misma pasada, como manda su protocolo ante estado terminal.

### Adenda de acreditación de la nº 298 — linterna PASA por cota inferior (2026-10-22)

- **Desglose Grounded/Augmented de la nº 298: NO ACREDITABLE** con las fuentes agotadas. Zip inspeccionado completo (58 archivos): **cero puntajes ni etiquetas** — acredita las 166 emisiones, no el puntaje (la plataforma puntúa fuera del output). Portal: titular sin etiqueta y sin desglose en las vistas accesibles (búsqueda del cierre); **cotejo aritmético: el titular es imposible como grounded micro** — ningún entero k produce 89,4 % sobre 166 (ni sobre 168 crudos) ni 34,5 % sobre 352 — y la serie augmented tampoco es micro (nº 295: 15,0 % × 11 = 1,65; 0,4 % × 352 = 1,408, fraccionarios). Por el precedente asentado de la nº 295 (los valores de lista de este portal = su Augmented) y las definiciones públicas del benchmark, el 34,5 % es **augmented indescomponible**, no grounded.
- **LINTERNA: PASA — acreditada por cota inferior adjudicada desde fuentes primarias** (criterio de la casa: mismo archivo + mismo mecanismo; lado gold según `ADJUDICACION-PARCIAL-296-20261021.md` §5/§7, lado emisión según los `findings.json` de la 298): **5 TP gold distintos verificados cubiertos** — LANdalf `DeviceMonitoringService.cs:184` (cancelación tragada; 2 emisiones 173–186), pika `ContentView.swift:151-152` (`try?` descarta el error de export; emisión en :152), apilix `storageDriver.ts:179-191` (`store={}` borra las configs de otros workspaces; emisión 180–190), jadx-collaboration G6 (tests que saltean la vía con hilos; `PluginTest.kt:128/:138`) y konturio `GenericRenderer.ts:229-244` (estilo aplicado sin guarda; emisión 228–234 — el más débil, declarado). Casi-match declarado que NO cuenta: CrabTrap `api.go:325` (mismo ancla, defecto de performance ≠ el de consistencia del gold). **Recall grounded ≥ 5/352 = 1,42 %; con solo los 3 casos fuertes, ≥ 3/352 = 0,85 % > 0,7 %.** Supersede el «NO PASA por ausencia de medición» del cierre (correcto con portal+zip; esta adenda corrió la vía de adjudicación que el propio cierre señaló).
- **Consecuencia (Adenda 2 §6): la secuencia ALMA queda HABILITADA** (`gate=v141` sobre la imagen v2.3.1) — no lanzada por esta tarea. Salvedad intacta: el falsador de economía §8 quedó registrado GATILLADO en el cierre («registrar y detener») y su aplicación a la secuencia la decide Alejandro con ambos hechos sobre la mesa. El par grounded exacto sigue pendiente de la adjudicación completa de los 166 (US$0). Detalle y cuentas: `ADENDA-RESULTADO-PRACTICA-V231-20261022.md`. **Gasto de esta tarea: US$0.**

### Adjudicación completa de la nº 298 — par grounded exacto: P 53,6 % · R 18,75 % (2026-10-22)

- **Encargo y costo:** Alejandro eligió el 22/10 la adjudicación completa de los 166 «antes de decidir» la colisión linterna/§8. **Gasto US$0** — sin portal, sin corridas, sin modelos; cotejo local contra el gold público con el método de la casa (mismo archivo + mismo mecanismo; un TP primario por emisión; gemelas gold acreditadas una vez; reclamos de tests solo con mecanismo enunciado).
- **El par grounded EXACTO de la base v2.3.1 (micro, 25 PRs): emisiones grounded en TP 89/166 → precisión 53,6 %; TP gold distintos cubiertos 66/352 → recall 18,75 %; F1 27,8 %.** Tabla por PR sumada y validada por programa (`adjwork298/aggregate298.py` sobre `adjwork298/decisions.json`, sin errores de referencia). Destino de las 77 no-TP: **8 FPG** (sobre solo 6 FP gold distintos de 213), **17 en zona gris**, **52 novedosas sin veredicto gold** (no juzgadas: material de la familia augmented).
- **Familia: 100 % vía general, otra vez.** La selección marcó especialidad en 3/25 PRs; dos la perdieron por degradación y solo CrabTrap ejecutó la suya (`sql_injection`) sin producir una sola emisión de esa clase: especialidad = 0 emisiones, 0 TP.
- **Relación con la adenda de acreditación (diferencias declaradas):** 4 de sus 5 casos quedan TP confirmados (LANdalf, pika, apilix, jadx); **el 5º (konturio) BAJA A GRIS** con el cotejo completo — la linterna no se mueve (66 ≫ 3; aun los 3 fuertes solos cumplen la vara). En sentido contrario, **CrabTrap suma un TP que la adenda no contó**: la emisión de `api.go:325` matchea la entrada gold de performance (G19), no solo la de consistencia que la adenda cotejó — CrabTrap cubre 4.
- **Comparaciones asentadas:** predicción del papel (R 1–3 %, P 10–40 %) quedó **por debajo** del resultado en ambas — falsador principal del encuadre (§8) **NO gatillado**. Contra la parcial de la 296, la comparación limpia es sobre los mismos 15 PRs: 298 = P 60,2 % / R 21,0 % vs 296 = P 51,9 % / R 22,1 % (precisión +8,3 pp, recall −2 TP netos; figlet colapsó 8→1 cubiertos por no seleccionar `reliability`, NCATS/CrabTrap/apilix subieron). Sobre los 10 PRs que la 296 nunca midió: P 42,9 %, R 15,9 %. Contra la v1 #251 (P 42,9 %, R 0,7 %): +10,7 pp y ×26,8, con salvedad de no ser A/B controlado.
- **Métricas del sector con definiciones declaradas:** FDP (1−P) = 46,4 % sobre emisiones; falsos confirmados por el gold = 8/166 = 4,8 %; tasa de reproducción de FP gold = 6/213 = 2,8 %. **La FPR de manual (FP/(FP+TN)) NO es computable** — un revisor generativo no produce verdaderos negativos; no se publica sustituto con ese nombre. **El J de Youden NO se reporta como tal** (exige especificidad sobre negativos clasificados); el sustituto nombrado es el **índice de discriminación por reproducción de reclamos gold: J_rep = 66/352 − 6/213 = 0,159**.
- **Alcance:** no es el puntaje augmented del portal (89,4/34,5 — familia del juez, indescomponible), no re-califica la 296, no juzga las 52 novedosas y **no decide la colisión linterna/§8**: entrega el número exacto que la decisión necesita. Los dos hechos siguen sobre la mesa — linterna PASA por conteo completo y falsador de economía §8 GATILLADO (degradación 40 %; emdash con 0 emisiones es su caso extremo en la tabla). Detalle completo: `ADJUDICACION-COMPLETA-298-20261022.md`.

### Adenda 3 al papel v2.3 — lectura de la colisión linterna/§8: ALMA habilitada, línea del revisor cerrada (2026-10-22)

- **Firma y costo:** Alejandro, 22/10/2026 («Adenda de lectura y que corra ALMA»), tras la adjudicación completa de la 298 que encargó «antes de decidir». **Gasto US$0** — papel solamente: sin código, sin portal, sin corridas, sin publicar. El papel v2.3 pasa de 46.739 B a **59.330 B**; cuerpo y Adendas 1–2 intactos (verificado: la Adenda 2 sigue cerrando en su última línea y la Adenda 3 abre después).
- **Los dos hechos asentados sin maquillaje:** (i) **linterna PASA por conteo completo adjudicado** — 66 TP gold distintos cubiertos ≫ vara de 3; R grounded 18,75 %, P 53,6 %, F1 27,8 %; falsador principal del encuadre (§8) NO gatillado; 100 % vía general, especialidad 0 emisiones/0 TP. (ii) **Falsador de economía (§8) GATILLADO y firme para siempre** — degradación declarada 10/25 = 40 % > 1/4, con emdash en 0 emisiones (`no_deep_pass_affordable`) como caso extremo. La adenda no lo des-asienta ni lo reinterpreta retroactivamente.
- **El FALLO de la lectura:** la cláusula operativa del falsador es su afirmación — «la economía tampoco cierra con revisor general» — y su «registrar y detener» obliga sobre la pretensión que nombra: la **continuación de la línea del revisor general**. Evidencia en los dos sentidos, declarada entera: a favor del gatillo, degradación 40 % y emdash (bajo este freno y estos precios, la línea no cierra como empresa viable); en contra de extenderlo, la nº 298 **completó dentro de su banda** (US$20,41 ∈ US$15–25, Adenda 2 §5), la degradación es el mecanismo de declaración del diseño §3(c) — jamás silenciosa — y la corrida produjo la medición más fuerte de la línea. Resultado: **base v2.3.1 CONGELADA como medida** (sin v2.4 ni nuevas iteraciones de base bajo este papel) y **la medición del brazo ALMA NO queda prohibida**: responde a otra pregunta pre-registrada (el efecto de la puerta, variante (ii) + 1.4.1) cuya cadena de habilitación (Adenda 1 §5, Adenda 2 §6 paso 8) estaba condicionada solo a la linterna — que pasó. Límite declarado en la adenda: leerla como «el §8 no importa» sería falso — el §8 es el que cierra la línea del revisor con la 298 como su último acto de base.
- **La corrida ALMA habilitada (declarada antes de lanzar):** imagen v2.3.1 ya publicada (`ghcr.io/almaoficial/alma-reviewbench@sha256:144756cea4…`, sin publicación nueva: ya contiene revisor 2.3.1, puerta 1.4.1 y selector `v141`); config ALMA del portal cambia **solo** imagen + etiquetas `reviewer=v23` y `gate=v141` (resto de la fila verificado al editar; `RB_MAX_SPEND_USD` jamás se toca). **Compuerta vinculante: saldo ≥ US$25 verificado antes de lanzar** — saldo actual **US$7,58**, requiere carga de Alejandro. Economía heredada declarada de antemano: costo esperado US$15–25 y **degradación esperada ≈ 40 % como hecho conocido**, no sorpresa; si excede su banda o muere por causa propia, se registra igual. Un solo lanzamiento; nada de «Submit».
- **Cómo se mide el efecto (declarado ahora):** el grounded del portal no es acreditable (recibo: adenda de acreditación de la 298), así que la regla de avance variante (ii) se evalúa sobre **adjudicación local completa (US$0)** de las emisiones ALMA contra el gold, con el método de las adjudicaciones 296/298; el titular del portal se reporta como augmented con su salvedad. **Vara de precisión: P_ALMA ≥ 58,6 %** (= 53,6 % adjudicada de base + 0,05); pureza de retención ≤ 1 de cada 3 retenidos/rechazados era TP grounded; **pérdida inexplicada = 0**; F1 reportado, no compuerta. Conteos de la puerta (aceptados / `needs_validation` / rechazados, por familia) desde los run-info de la propia corrida. Si la adjudicación no pudiera ejecutarse, el efecto queda «sin medir» y así se asienta — no se sustituye por el titular.
- **Cierre de la línea:** la corrida ALMA es el **último acto del papel v2.3** — pase o no pase la regla de avance, la línea de revisores de este papel se cierra con su resultado; cualquier continuación es un papel nuevo. Detalle completo: `PREREGISTRO-REVIEWBENCH-V23.md`, Adenda 3 (§§1–5).

### Práctica ALMA v2.3.1 — corrida nº 310: FAILED en run-agent, efecto sin medir (2026-10-22)

- **Corrida nº 310 (brazo ALMA): FAILED «at run-agent (4, 4) / Run the vendor agent over this shard»** — lanzada 2026-10-22 07:15:27 EDT por autorización expresa de Alejandro (Adenda 3); config «llm · alma · gpt-5.6-sol · medium · v23 · v141», imagen v2.3.1 `sha256:144756cea4…`. Puntajes del portal verbatim: **«P — · R —»**, sin línea de hallazgos ni botón «per PR» — no hay titular; cuando lo hay, el titular de este portal es la familia augmented (juez), no grounded acreditable (acreditación de la nº 298).
- **Causa leída en los outputs (zip 8.317 B, md5 `9ca6332178…`; copia en `runs/run-310-output.zip`):** 4 PRs alcanzados de 25, 0 succeeded, 4 en `error:2` (3 intentos c/u), 4 shards detenidos en su primer PR por preflight, `findings=null`, ningún `findings.json`. Texto idéntico en los 4 shards: «backend=llm v2.3 refused: unknown gate version 'v141'; expected 'v1', 'v11', 'v12', 'v13' or 'v14' (RB_CONFIG_GATE); no model call was made». El revisor publicado rechaza la etiqueta `gate=v141` pre-registrada antes de cualquier llamada; la cabecera declara `validator=alma-evidence-gate/1.4.1` (`policy_sha256=73a403d8…`) pero la puerta nunca operó: no hubo emisiones.
- **Costo real por diferencia de saldo (org Personal): US$25,58 (07:13 EDT, previo) − US$25,58 (billing, ~07:29–07:33 EDT) = US$0,00** — consistente con cero llamadas al modelo.
- **Regla de avance variante (ii) (Adenda 3 §4): SIN MEDIR.** No hay emisiones que adjudicar (0/0, precisión indefinida, no cero); conteos de la puerta sin datos. La vara (P_ALMA grounded ≥ 58,6 %, pureza de retención ≤ 1 de cada 3, pérdida inexplicada = 0) no se evalúa ni se sustituye por titular alguno, como manda la propia adenda para este caso. La falla está explicada por completo, pero es explicación de la corrida, no de la puerta.
- **Cierre de la línea:** la nº 310 era el último acto del papel v2.3 (Adenda 3 §5) — la línea se cierra con FAILED por integración, efecto sin medir y costo US$0,00. Corregir la lista de versiones y relanzar sería un papel nuevo con decisión nueva de Alejandro; esta pasada no relanzó nada, no tocó «Submit» ni configuraciones. Detalle completo: `RESULTADO-PRACTICA-ALMA-V231-20261022.md`. La vigilancia `vigilar-practica-alma-v231` se elimina en esta misma pasada.

### Adenda 4 al papel v2.3 — reparación de la admisión `v141` (v2.3.2) y relanzamiento ALMA autorizado (2026-10-22)

- **Firma y costo:** Alejandro, 22/10/2026 07:37 EDT («Lo hagamos»), sobre el informe de la falla de la nº 310. **Gasto US$0** — papel solamente. El papel v2.3 pasa de 59.330 B a **65.828 B**; cuerpo y Adendas 1–3 intactos (la Adenda 4 abre tras el cierre de la Adenda 3). Esta adenda SUPERSEDE el cierre asentado en la entrada de la nº 310 («relanzar sería un papel nuevo con decisión nueva»): la decisión nueva llegó y quedó asentada como Adenda 4 ANTES del arreglo y del relanzamiento.
- **Hechos que la motivan:** la nº 310 FAILED en run-agent (4,4) con **costo real US$0,00** (saldo US$25,58 → US$25,58), cero llamadas al modelo y cero emisiones. Causa diagnosticada con recibos (`DIAGNOSTICO-PRACTICA-ALMA-310-20261022.md`): doble resolvedor de `RB_CONFIG_GATE` no espejado — `main.py` admite `v141` y cargó la puerta 1.4.1 (`policy_sha256=73a403d8…` en la cabecera), pero `_resolve_gate_v23` (`agent/llm_reviewer_v23.py:235–259`) tiene su propia lista que termina en `v14` y rechazó `v141` fail-closed (error verbatim: «unknown gate version 'v141'; expected 'v1', 'v11', 'v12', 'v13' or 'v14'»). La base nº 298 pasó con la misma imagen porque usó `gate=v13`, presente en ambos resolvedores.
- **Clasificación:** falla de admisión/cableado (infraestructura), NO medición — la regla de avance variante (ii) quedó **SIN MEDIR, no caída**, y la nº 310 **no cuenta como el acto ALMA del papel**: el último acto (Adenda 3 §5) sigue pendiente de una corrida que mida.
- **El arreglo declarado (Adenda 4 §3):** un solo archivo, `agent/llm_reviewer_v23.py` — importación `POLICY_VERSION as GATE_V141_VERSION` desde `alma_gate_v141`, rama `v141` en `_resolve_gate_v23` que devuelve `(KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V141_VERSION)` (las 19 clases y la guía idénticas: la 1.4.1 las hereda de la 1.3.0 vía la 1.4.0; su único cambio es el ruteo interno), mensaje de error actualizado con `'v141'`, `REVIEWER_VERSION → llm-reviewer/2.3.2`, y un test nuevo que fija la resolución `v141` (con `v13`/`v14` sin cambios). **`alma_gate_v141.py` byte-idéntica (congelada) y `main.py` sin tocar.** La reparación implica imagen nueva (digest nuevo); en el portal se actualiza SOLO el campo de imagen de la config ALMA (labels `reviewer=v23`/`gate=v141` ya correctos; `RB_MAX_SPEND_USD` jamás).
- **Compuerta y falsador:** relanzamiento solo con saldo verificado ≥ US$25 (US$25,58 al 22/10 07:33 EDT). **Falsador de la reparación:** si la relanzada muere con la misma firma («unknown gate version 'v141'»), la reparación queda refutada y la línea se detiene **sin tercer intento**. Para la relanzada rige entera la Adenda 3 §4 (vara P_ALMA grounded ≥ 58,6 %, pureza de retención ≤ 1 de cada 3, pérdida inexplicada = 0; adjudicación local completa US$0; titular del portal = augmented) y la §5: **la relanzada ES el último acto del papel v2.3**. Detalle completo: `PREREGISTRO-REVIEWBENCH-V23.md`, Adenda 4 (§§1–5).
