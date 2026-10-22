# Manifiesto de publicación v2.3.1 — ReviewBench (imagen corregida)

**Versión del manifiesto:** run-manifest/2.3.1 · **Preparado:** 2026-10-22 ·
Pre-registro: [`PREREGISTRO-REVIEWBENCH-V23.md`](PREREGISTRO-REVIEWBENCH-V23.md)
(cuerpo congelado 2026-10-21 + **Adenda 2**, firmada por Alejandro el
2026-10-21 a las 23:20 EDT — «Bueno lo hagamos» — que pre-registra esta
reparación y su secuencia)

**Estado de este manifiesto: CERRADO — código publicado y verificado;
imagen construida y digest verificado y asentado.** El commit del paquete
v2.3.1 está en `main` (ver el sobre). El workflow `reviewbench-image`
(**corrida nº 7, SUCCESS**) completó y el digest quedó cotejado en dos
fuentes (resumen de la corrida y página del paquete GHCR), con el método
declarado en el sobre — el mismo procedimiento de cierre que la v2.1
(`4d1cf01`), la v2.2 (`cc4dbc8`) y la v2.3 (corrida nº 6). **Este
manifiesto cierra la PUBLICACIÓN; no lanza nada:** la secuencia de la
Adenda 2 §6 sigue con la actualización de la config base del portal a
esta imagen y, tras la compuerta de saldo, la práctica base relanzada.

**Qué es la v2.3.1:** la v2.3 con UNA reparación de dos piezas y nada
más (Adenda 2 §2): (i) el techo de completion de la pasada de
**selección** sube de **1.024 a 4.096 tokens** — el defecto (d) que mató
la práctica nº 296, donde el razonamiento agotaba el techo heredado y
el JSON volvía vacío/truncado, cerrando en falso `error:2` —; y (ii)
**observabilidad**: ante un contenido no parseable o vacío de cualquier
pasada, el revisor asienta `finish_reason` y un extracto acotado del
contenido crudo en el run-info (`parse_failures`), sin cambio de
comportamiento (el fail-closed no se movió). La justificación de
reparar, y no archivar la línea, es la adjudicación parcial de la
nº 296 contra el gold público (`ADJUDICACION-PARCIAL-296-20261021.md`):
sobre los 15 PRs completados, precisión grounded 51,9 % y recall del
subconjunto 22,1 %, con los 43 TP todos por la vía general —
**parcial y no puntaje**, declarado en su informe.

## El sobre

| Campo | Valor |
|---|---|
| Plataforma / juez | ReviewBench — golden set validado por ingenieros senior; severidad y categoría las asigna el clasificador de la plataforma |
| Reviewer | `alma-reviewer` (registrado 2026-10-18, aprobado 2026-10-19) |
| Imagen (digest) | `ghcr.io/almaoficial/alma-reviewbench@sha256:144756cea49ee33e8b16ddb0204556adb0f1c2430ea885ec6a206bbaa6964544` (64 caracteres, sin truncar) — workflow `reviewbench-image` **corrida nº 7**: https://github.com/almaoficial/alma-reviewbench/actions/runs/39720724484 (2026-10-22 00:09 EDT, **SUCCESS**, 21 s, `main` @ `cc56817`, inputs `tag=dev`, `package_dir=.`). **Verificación:** digest impreso por el resumen de la corrida («ReviewBench image published») y cotejado contra la página del paquete en GHCR (versión `1425887291`, tag `dev`, que reemplaza a la `1425525285` de la v2.3) — esa página es la constancia registral usada; el contenido se verificó por la cadena de build (el commit `cc56817` contiene `agent/llm_reviewer_v23.py` v2.3.1 — techo de selección 4.096 + observabilidad `parse_failures` — y el Dockerfile copia `agent/` a `/app/agent`; `.dockerignore` no excluye `agent/`). **Salvedad declarada:** la constancia registral es la página del paquete; método de cierre idéntico al de la v2.1, la v2.2 y la v2.3 |
| Repositorio | https://github.com/almaoficial/alma-reviewbench — commit del paquete v2.3.1: `cc56817b16daeb17620a77cad859520517bf13cd` (push verificado **21/21 archivos byte a byte** contra el remoto: el revisor 2.3.1, `agent/main.py` con el selector `RB_CONFIG_GATE=v141`, el paquete 1.4.1 completo, los tests nuevos y actualizados, el papel v2.3 con las Adendas 1 y 2, los diagnósticos v2.2/v2.3, el resultado formal de la nº 296, la adjudicación parcial, el resultado del arreglo y el de la sonda) |
| Modelo | `gpt-5.6-sol`, effort `medium`, vía `https://api.openai.com/v1` |
| Egress del contenedor | solo `api.openai.com:443` |
| Timeout por PR | 1800 s |
| Revisor | `llm_reviewer_v23` versión **`llm-reviewer/2.3.1`** (la etiqueta `reviewer` del portal **se mantiene en `v23`**, como manda la Adenda 2): la arquitectura v2.3 intacta — selección generalizada solo sobre el diff (9 categorías públicas + 19 clases de especialidad, tope compartido de 5 profundas, degradación declarada de C2) — con el **techo de completion de la selección en 4.096 tokens** y el **asiento de `finish_reason`/extracto ante parseos fallidos**. Las pasadas profundas conservan su techo; el comportamiento medido v2.3.0 queda reproducible fijando el techo en 1024 por configuración (con test) |
| Puerta incluida para el brazo ALMA futuro | `agent/alma_gate_v141.py` (**puerta 1.4.1, ADOPTADA** por su medición: VP = los mismos 4, falsos = 0 con S3 rechazado firme, equivalencia exacta; POLICY_SHA256 `73a403d8…`) seleccionable vía `RB_CONFIG_GATE=v141` en `agent/main.py`. Viaja en la imagen; **no se usa en la corrida base** (la base sigue `gate=v13`) ni se edita la config ALMA del portal hasta que la linterna pase (Adenda 1 §5 + Adenda 2 §6) |
| Configuración de la corrida base | **única**: base (`governance=base`, `gate=v13` declarado y omitido al validar — el revisor emite todo lo que encuentra, de las dos familias) |
| Suite del paquete | **245/245** en verde al publicar (236 heredadas + 9 nuevas de la v2.3.1: techo solo en la selección, pin 1024 reproducible por entorno y por config, delta de peor caso exacto, asiento de `finish_reason`/extracto ante truncado/vacío/no-JSON con fail-closed intacto) |
| Controles de gasto | `ALLOW_REAL_LLM=1` obligatorio; `RB_MAX_SPEND_USD=6.50` por PR (freno intacto, **no se toca**); presupuesto de la etapa según Adenda 2 §5: sonda ≤ US$8 (ejecutada) + práctica base relanzada **US$15–25** + brazo ALMA US$15–25 **solo si la linterna pasa**; compuerta de saldo vinculante antes de cada paso con gasto |

> **Los labels `reviewer=v23` y `gate=v13` de la config base no cambian
> en esta publicación.** Solo cambia el campo de imagen. La versión
> 2.3.1 se declara en este manifiesto, no en la etiqueta — así lo
> pre-registró la Adenda 2 para que la comparación contra la nº 296
> (misma config declarada, imagen corregida) no confunda dos cambios.

## Economía re-derivada con el techo nuevo (arreglo v2.3.1)

- Delta exacto por PR: **+US$0,2304** (3.072 tokens de salida extra de
  la selección × US$75/Mtok a precios de planificación). Solo se mueve
  el término de salida de la selección; las profundas no se tocan.
- **Plan ancla: US$5,6554 < US$6,50** — entra entero (selección + 5
  profundas). **Saturado: US$7,4828** → la degradación heredada
  absorbe: 4 profundas admitidas (total **US$6,2328**) y la 5ª queda
  **declarada** — igual que a 1.024.
- **Reconciliación asentada en el resultado del arreglo:** las cifras
  de la Adenda 2 (≈5,33 / ≈7,13 / ≈5,82) salen ~US$0,3 más bajas y no
  se reproducen con la aritmética del código; las conclusiones
  coinciden (ancla entra, saturado admite 4) y la aritmética operativa
  es la del código.
- **Práctica base relanzada (25 PRs, un solo brazo): banda US$15–25**
  (Adenda 2 §5, que supersede solo para esta etapa la banda/tope del
  papel; de ese tope la nº 296 ya consumió US$13,50 reales). Salvedad
  medida en la nº 296: la banda de planificación sobreestima la
  facturación ≥ 2,4× — el costo real se asienta por diferencia de
  saldo, como siempre.

## La sonda previa (Adenda 2 §4) — ÉXITO 8/8

- Antes de esta publicación se corrió la sonda pre-registrada: solo la
  pasada de selección arreglada (techo 4.096), en local con la
  credencial sancionada, una llamada por caso, **sin reintentos**:
  los **5 PRs que murieron 3/3** en la nº 296
  (`simnaut_emdash_2`, `scotthamilton77_agents-config_1`,
  `wirechat_wirechat_183`, `mheuss_chronicle_14`,
  `sdsykes_fastimage_165`) más los **3 intermitentes** — **JSON
  parseable en los 8/8**. Costo reportado **US$6,3282** contra el tope
  duro de **US$8**.
- **El mecanismo quedó leído, no inferido:** `finish_reason = "stop"`
  en los 8 y **4 casos con razonamiento ≥ el techo viejo de 1.024**
  (emdash 1.462; chronicle 1.536; agents-config 1.025; wirechat
  1.024) — bajo ese techo el contenido no podía existir. Con el techo
  nuevo, el completion máximo fue 1.676 (**2,4× de margen** en el caso
  más pesado). Detalle completo:
  [`RESULTADO-SONDA-V231-20261021.md`](RESULTADO-SONDA-V231-20261021.md).
- Alcance declarado de la sonda: no mide tasa de muertes ni detección;
  decide seguir o parar según la adenda — y decidió **seguir**.

## La secuencia que sigue (Adenda 2 §6)

1. ~~Adenda 2 firmada~~ ✓ · ~~construcción en seco v2.3.1 (suite
   245/245)~~ ✓ · ~~sonda (ÉXITO 8/8)~~ ✓ · ~~**publicación de la
   imagen corregida (este manifiesto)**~~ ✓.
2. **Config base del portal a esta imagen** — solo el campo de imagen
   por el digest del sobre; labels intactos (`backend=llm ·
   governance=base · model=gpt-5.6-sol · effort=medium ·
   reviewer=v23 · gate=v13`); `RB_MAX_SPEND_USD` no se abre ni se
   toca; config ALMA intacta en este paso.
3. **Práctica base relanzada** (corrida nueva), con la compuerta
   vinculante: **saldo verificado ≥ US$25 antes de lanzar**.
4. **Linterna del papel v2.3:** recall base grounded > **0,7 %** sobre
   352 TP → PASA. La métrica primaria sigue siendo grounded F1, con
   grounded precision co-primaria, y la predicción del papel (recall
   1–3 %, precisión 10–40 %) sigue en pie para la corrida completada.
5. **Si la linterna pasa:** brazo ALMA con **`gate=v141`** sobre la
   **misma** imagen corregida (la puerta 1.4.1 y su selector ya viajan
   en ella), con su compuerta de saldo y la regla de avance del papel
   (precisión ALMA ≥ base + 0,05, pureza de la retención, pérdida
   inexplicada = 0). Si no pasa, ALMA no corre — consecuencia
   pre-registrada, sin sustituciones.

## Honestidad y falsadores (Adenda 2 §7)

- La práctica **nº 296 queda FAILED para siempre**: esta publicación
  no la re-califica, la adjudicación parcial no es puntaje y la
  linterna no se pasa retroactivamente.
- **Falsador de la etapa:** si la práctica relanzada muere con la
  **misma firma** (JSON no parseable en la selección), la hipótesis
  del techo queda **refutada** y la línea se detiene **sin tercer
  intento automático**; si el cuerpo asentado por la observabilidad
  nueva mostrara truncación aun con 4.096, también se detiene a papel.
- **Falsador del papel v2.3, intacto:** recall base ≤ 0,7 % en la
  corrida completada → muere la hipótesis del encuadre; el problema
  pasa a ser capacidad del modelo en diffs reales y no hay v2.4 de
  encuadre.

## Nota de publicación

La batería (`fixtures_semaforo/`) y los directorios de corridas
(`runs/`) no viajan en el repo — la protección de push de GitHub
rechaza el secreto falso plantado del caso
`sem_02_hardcoded_secret`. Quedan en el paquete local con sus hashes
verificables. Las puertas congeladas 1.0.0–1.4.1 viajan sin cambios,
verificadas por hash antes del push. El commit `cc56817` arrastra
además, como custodia declarada en su mensaje, los documentos que
habían quedado solo locales: los guiones del portal v2.1–v2.3 y los
resultados formales de las prácticas v2.1 y v2.2.

## Resultados

*(Se asientan verbatim desde el portal al completarse la práctica
relanzada. Hasta entonces: sin número, sin historia. La nº 296 ya
tiene su resultado formal asentado en
`RESULTADO-PRACTICA-V23-20261021.md`: FAILED, sin puntaje, costo real
US$13,50.)*

| Brazo | Grounded F1 | Precisión | Recall | Gasto real |
|---|---|---|---|---|
| base-v23 (imagen v2.3.1) | — | — | — | — |
| ALMA-v231 (`gate=v141`) | **condicionado a la linterna** — corre solo si la base relanzada la pasa | | | |
