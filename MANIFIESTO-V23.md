# Manifiesto de corrida v2.3 — ReviewBench (SOLO brazo base)

**Versión del manifiesto:** run-manifest/2.3.0 · **Preparado:** 2026-10-21 ·
Pre-registro: [`PREREGISTRO-REVIEWBENCH-V23.md`](PREREGISTRO-REVIEWBENCH-V23.md)
(congelado antes de construir; camino A — ensanchar la base — elegido por
Alejandro el 2026-10-21 tras el diagnóstico de la práctica v2.2)

Regla de comparación: si dos corridas difieren en cualquier campo de este
sobre fuera de los campos declarados distintos, la comparación queda
rechazada de plano. El número que salga de esta corrida se publica junto a
este manifiesto, nunca suelto.

**Estado de este manifiesto: CERRADO — código publicado y verificado;
imagen verificada y asentada; configuración base del portal actualizada
y releída.** El commit del paquete v2.3 está en `main` (ver el sobre).
El workflow `reviewbench-image` (corrida nº 6, SUCCESS) completó y el
digest quedó verificado y asentado en el campo «Imagen (digest)» del
sobre, con el método declarado ahí — el mismo procedimiento de cierre
que la v2.1 (`4d1cf01`) y la v2.2 (`cc4dbc8`). La configuración **base**
del portal quedó con esa imagen y los labels `reviewer=v23` /
`gate=v13`, guardada y releída campo por campo (asiento de cierre en
`REGISTRO-REVIEWBENCH.md`); la configuración ALMA no se tocó. La
práctica espera el «Corre» expreso de Alejandro.

**Alcance de esta corrida: SOLO el brazo base.** No hay brazo ALMA en la
v2.3 — está **bloqueado por pre-registro** (ver la declaración obligatoria
de abajo). Este manifiesto no describe una comparación A/B: describe la
corrida del brazo base contra la vara re-derivada del papel v2.3.

## El sobre

| Campo | Valor |
|---|---|
| Plataforma / juez | ReviewBench — golden set validado por ingenieros senior; severidad y categoría las asigna el clasificador de la plataforma |
| Reviewer | `alma-reviewer` (registrado 2026-10-18, aprobado 2026-10-19) |
| Imagen (digest) | `ghcr.io/almaoficial/alma-reviewbench@sha256:932ac3ffa1944d92cb4defd5b96b7b1146eb37bdd3b4245676039e7844b40e27` (64 caracteres, sin truncar) — workflow `reviewbench-image` **corrida nº 6**: https://github.com/almaoficial/alma-reviewbench/actions/runs/39708506752 (2026-10-21 21:55–21:56 EDT, SUCCESS, `main` @ `a6838e6`, inputs `tag=dev`, `package_dir=.`). **Verificación:** digest impreso por el resumen del workflow y cotejado contra la página del paquete en GHCR (versión `1425525285`, tag `dev`) — esa página es la constancia registral usada; el contenido se verificó por la cadena de build (el commit `a6838e6` contiene `agent/llm_reviewer_v23.py`, 977 líneas; el Dockerfile copia `agent/` a `/app/agent`; `.dockerignore` no excluye `agent/`). **Salvedad declarada:** la API `/v2` de GHCR con token anónimo devolvió 401 por header en navegación y no se usó como constancia; método de cierre idéntico al de la v2.1 y la v2.2 |
| Repositorio | https://github.com/almaoficial/alma-reviewbench — commit del paquete v2.3: `a6838e60df8d754f361eb10e38eff815ae60708b` («Revisor v2.3: selección generalizada (camino A) + puerta 1.4.0 construida y NO adoptada + semáforo v2.3 VERDE (brazo base)», padre `cc4dbc8`) |
| Modelo | `gpt-5.6-sol`, effort `medium`, vía `https://api.openai.com/v1` |
| Egress del contenedor | solo `api.openai.com:443` |
| Timeout por PR | 1800 s |
| Revisor | `llm_reviewer_v23` (`reviewer=v23`): **selección generalizada solo sobre el diff** — una lista de prioridad mezclada con las **9 categorías públicas del benchmark** (`correctness`, `reliability`, `maintainability`, `testing`, `security`, `documentation`, `api-architecture`, `performance`, `accessibility`) **más las 19 clases de especialidad** de la puerta 1.3.0 como especialidad — con **tope compartido de 5 pasadas profundas** y la **regla de degradación declarada** de C2 (si el plan supera el freno, corren las profundas de mayor prioridad que caben y la truncación queda declarada; ningún PR se niega entero). Taxonomía declarada de temario público: el papel **prohíbe diseñar contra el detalle por PR del gold** |
| Configuración de la corrida | **única**: base (`governance=base`, `gate=v13` declarado y omitido al validar — el revisor emite todo lo que encuentra, de las dos familias) |
| Suite del paquete | **208/208** en verde al publicar (163 heredadas + 27 de la puerta 1.4.0 + 18 del revisor v2.3) |
| Controles de gasto | `ALLOW_REAL_LLM=1` obligatorio; `RB_MAX_SPEND_USD=6.50` por PR (Adenda 4 al pre-registro v2, firmada por Alejandro el 2026-10-21); sobre total de la práctica: **US$30** (tope duro heredado) |

> **Los labels `reviewer=v23` y `gate=v13` son obligatorios.** Sin ellos,
> `agent/main.py` usa sus defaults históricos: `RB_CONFIG_REVIEWER=v1` y
> puerta v1 — la práctica mediría el sistema viejo con la imagen nueva.
> (Es el error que este campo existe para prevenir desde la v2.)

## Economía esperada de la práctica (papel v2.3 §7, medida en seco)

- Pasada profunda en el PR ancla (41.160 tokens): ≈ **US$0,94**
  (medida en seco: US$0,9380 la de clase, US$0,9367 la de categoría).
  Selección con el diff completo del ancla: hasta US$0,7349.
- **Plan completo en el PR ancla (selección + 5 profundas): ≈ US$5,43**
  conservador — dentro del freno de US$6,50. Saturado (contexto de
  60.000 tokens): US$7,25 > freno → entran exactamente **4 profundas** y
  la 5ª queda **declarada** por la regla de degradación, como predijo
  el papel.
- **Práctica completa (25 PRs, un solo brazo): costo real esperado
  ≈ US$10–25**, bajo el tope duro de **US$30**. Si el tope se alcanza,
  la práctica se detiene y se registra, como manda el papel.
- **Falsador de economía:** degradación declarada en más de 1/4 de los
  PRs de la práctica → registrar y detener.

## La corrida

- **Tipo:** práctica puntuada del portal, set privado de 25 PRs,
  **1 corrida, un solo brazo (base)**; la primera que complete es la
  válida.
- **Métrica primaria:** grounded F1 · **co-primaria:** grounded
  precision (idénticas a v1, v2, v2.1 y v2.2) — sobre el gold público
  del benchmark: **352 TP**.
- **Prueba de la linterna:** el recall grounded del brazo base debe
  superar **0,7 %** (sobre 352 TP). Es la compuerta que detuvo las
  prácticas v2.1 y v2.2 (recall 0,4 % en ambas, brazo ALMA nunca
  lanzado); acá decide si la hipótesis del encuadre vive.
- **Predicción pre-registrada del papel:** recall base grounded
  **1–3 %** (≈4–10 TP), precisión **10–40 %**, F1 ≈ **2–5 %**.
- **Falsador principal:** recall base ≤ 0,7 % otra vez → muere la
  hipótesis del encuadre; el problema pasa a ser capacidad del modelo
  en diffs reales y **no hay v2.4 de encuadre**.
- **Regla de avance re-derivada (papel v2.3 §5):** se mantienen la
  linterna y, para un eventual brazo ALMA, precisión ALMA ≥ precisión
  base + 0,05 (con declaración de no-falsabilidad si la precisión base
  ≥ 0,90); las cláusulas heredadas de F1 ≥ y caída de recall ≤ 0,03
  quedan **reemplazadas** por pureza de la retención (≤ 1 de cada 3
  retenidos/rechazados era TP grounded) y pérdida inexplicada = 0.
  **Las cláusulas ALMA están dormidas mientras el brazo esté
  bloqueado**; este manifiesto no las convierte en promesa.
- **Estado:** código publicado y verificado (commit `a6838e6`);
  imagen publicada y digest verificado (corrida nº 6 del workflow);
  configuración base del portal actualizada y releída con la imagen
  v2.3 y los labels de este sobre (guion ejecutado:
  `GUION-PORTAL-V23.md`); práctica por lanzar, pendiente del «Corre»
  de Alejandro al momento de lanzar.

## Semáforo previo v2.3 (2026-10-21) — VERDE solo del brazo base

- Misma batería sintética congelada de 8 códigos con defectos plantados
  de clase, hashes verificados 32/32 contra su manifiesto de batería
  antes de correr; puertas 1.0.0–1.3.0 verificadas por hash, intactas;
  suite completa en seco 208/208.
- **Brazo base: 16 hallazgos emitidos, 8/8 defectos plantados
  detectados — US$0,53607** (tope duro US$20; 2,7 % usado). 26 llamadas
  (8 de selección + 18 profundas); degradación 0/8, negativas de la
  guardia 0/8, `malformed = 0`, `unanchored = 0`, overflow vacío en
  los 8, cero emisiones fuera de blanco.
- **El 8/8 es obra del ensanche, declarado sin redondear:** por la vía
  de especialidad sola fueron **7/8 — idénticos a la v2.2**. El octavo
  caso (sem_02) lo rescató la vía nueva: la profunda de la clase
  (`hardcoded_secret`) calló por cuarto semáforo consecutivo, y la
  pasada general de la categoría `security` produjo el hallazgo
  (`app/billing.py:6`). La especialidad no mejoró; el ensanche cubrió
  su hueco conocido en 1 de 8 casos de miniatura.
- **Costo +74 % contra el brazo base v2.2** (US$0,53607 vs US$0,3090):
  2–3 profundas por código donde la v2.2 corría 1 — el precio de la
  arquitectura de dos familias, ya contabilizado contra el freno en la
  contabilidad de peor caso del papel (ancla US$5,43 < US$6,50).
- **Alcance (§9 del papel):** este semáforo afirma mecánica, economía
  en miniatura y emisión, y que la vía de especialidad sobrevivió al
  ensanche. **No afirma detección general** — la batería no contiene
  ningún TP de categorías generales — y un VERDE no predice recall en
  la práctica (medido dos veces: triage 16/16 en miniatura → 0/9 en
  diffs reales). La detección de la v2.3 se juzga solo en la práctica.
- Registro completo:
  [`RESULTADO-SEMAFORO-V23-20261021.md`](RESULTADO-SEMAFORO-V23-20261021.md).
- Sin ajustes al sistema a partir del simulacro (regla del papel).

## Declaración obligatoria — la puerta 1.4.0 y el brazo ALMA bloqueado

- La puerta **1.4.0** (`agent/alma_gate_v14.py`, POLICY_SHA256
  `b0c0aa661f644b5229ea3ee1984b3fd2dbb17649d1eeae91e5945fd357fd6d19`)
  se construyó fiel a su papel (`PREREGISTRO-PUERTA-140.md`): la 1.3.0
  por delegación más el tercer estado `needs_validation`. Viaja en
  este paquete como **artefacto medido, no como puerta en uso**.
- Su **medición de adopción** (§6 de su papel; resultado:
  `RESULTADO-MEDICION-PUERTA-140.md`) dio **NO ADOPTADA**: recuperó
  **4 VP** (≥ 1 ✓), equivalencia de aceptados **exacta** en los tres
  universos (✓), y **1 falso nuevo** (≠ 0 ✗) — el ataque **S3** de la
  batería roja: una inyección real pero preexistente, citada solo en
  líneas de contexto, cuyo único chequeo fallido es «sin línea
  agregada»; la frontera tal como fue pre-registrada lo deja entrar a
  la sala de espera. En las corridas reales (U1) los falsos fueron 0.
- **Consecuencia pre-registrada (papel v2.3 §4): el brazo ALMA de la
  v2.3 NO corre.** No hay sustitución silenciosa por la 1.3.0: correr
  ALMA con la puerta vieja mediría otra cosa que la declarada en el
  papel. Por eso este manifiesto tiene un solo brazo, el semáforo
  corrió un solo brazo, y **la configuración ALMA del portal NO se
  actualiza en esta publicación** (queda con la imagen y los labels
  de la v2.2).
- La reparación está pre-registrada en `PREREGISTRO-PUERTA-141.md`
  (papel escrito y congelado el 2026-10-21, **sin construir**): mover
  el chequeo «sin línea agregada» fuera de los habilitantes del tercer
  estado — rechazo firme — y re-correr la medición de adopción
  completa (VP = los mismos 4 o no se adopta). Si la 1.4.1 se adopta,
  su uso en el brazo ALMA exige además una adenda firmada al papel
  v2.3 con la etiqueta `gate=v141`, antes de cualquier corrida ALMA.
  Si no se adopta, no hay 1.4.2 automática.

## Nota de publicación

La batería (`fixtures_semaforo/`) no viaja en el repo — la protección
de push de GitHub rechaza el secreto falso plantado del caso
`sem_02_hardcoded_secret`. Queda congelada en el paquete local con sus
hashes 32/32 verificables contra el manifiesto de batería asentado en
el registro del semáforo. Las puertas congeladas 1.0.0–1.3.0 viajan sin
cambios, verificadas por hash antes del push (1.3.0: sha256 de archivo
`d3b993d4d4f26b9df112dfd54abc391e8018faae024d23c63b4924d86d2dc1e0`,
POLICY_SHA256
`0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`).

## Resultados

*(Se asientan verbatim desde el portal al completarse la práctica.
Hasta entonces: sin número, sin historia.)*

| Brazo | Grounded F1 | Precisión | Recall | Gasto real |
|---|---|---|---|---|
| base-v23 | — | — | — | — |
| ALMA-v23 | **bloqueado — no corre** (puerta 1.4.0 no adoptada) | | | |

## Nota de diseño

La v1 sigue siendo la única base que puntuó en grounded (F1 1,4 %): su
pasada era general y sin restricción de clases. El diagnóstico de la
práctica v2.2 midió por qué: el 97,4 % de los 352 TP del gold vive
fuera del universo de las 19 clases (techo de recall grounded para un
revisor solo-clases: 0,3 % estricto – 2,6 % generoso). La v2.3 es la
primera arquitectura que puede, por construcción, puntuar en ese
terreno: la selección mira el diff con el temario público entero y las
profundas corren por marca. Si la base supera la linterna, el encuadre
era el problema; si no la supera, el papel ya escribió el veredicto —
capacidad del modelo en diffs reales — y no hay v2.4 de encuadre que
lo maquille. La puerta, cuando vuelva, volverá por su propio papel:
su trabajo no es mejorar el recall, es que lo que el sistema afirma
tenga la evidencia citada en el diff.
