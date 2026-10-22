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
