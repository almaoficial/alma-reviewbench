# Manifiesto de corrida v2.1 — ReviewBench A/B (base-v21 vs. ALMA-v21)

**Versión del manifiesto:** run-manifest/2.1.0 · **Preparado:** 2026-10-21 ·
Pre-registro: [`PREREGISTRO-REVIEWBENCH-V21.md`](PREREGISTRO-REVIEWBENCH-V21.md)
(congelado antes de correr; diseño C1 de la Adenda 6 del pre-registro v2)

Regla de comparación de este experimento: si dos corridas difieren en
cualquier campo de este sobre fuera del único campo declarado distinto, la
comparación queda rechazada de plano. El número que salga de esta corrida se
publica junto a este manifiesto, nunca suelto.

**Estado de este manifiesto:** código e imagen publicados y verificados;
el campo «Imagen (digest)» quedó asentado con el digest completo,
verificado contra GHCR, con su commit declarado (el mismo procedimiento
que asentó la v2 en sus commits `08079681`/`e4a9dae`). Ningún número de
la práctica existe todavía: la práctica está por lanzar.

## El sobre

| Campo | Valor |
|---|---|
| Plataforma / juez | ReviewBench — golden set validado por ingenieros senior; severidad y categoría las asigna el clasificador de la plataforma |
| Reviewer | `alma-reviewer` (registrado 2026-10-18, aprobado 2026-10-19) |
| Imagen (digest) | `ghcr.io/almaoficial/alma-reviewbench@sha256:32da7c01181c3ebae61d6cb9d5d31590858ad328c7f292d56d153a5b0523a0bc` (pública, linux/amd64, GitHub Actions, tag `dev`, desde el commit `36ac93a` de `main`; digest completo de 64 caracteres, **verificado contra GHCR el 2026-10-21**: el tag `dev` resuelve a este digest) |
| Repositorio | https://github.com/almaoficial/alma-reviewbench — commit del paquete v2.1: `36ac93aca672326c72ac20af4cfbe7dbd35e6176` («Revisor v2.1: una pasada, 19 clases en secciones (diseño C1 de la Adenda 6) + pre-registro v2.1 + semáforo v2.1 VERDE», padre `e4a9dae`) |
| Modelo | `gpt-5.6-sol`, effort `medium`, vía `https://api.openai.com/v1` |
| Egress del contenedor | solo `api.openai.com:443` |
| Timeout por PR | 1800 s |
| Revisor | `llm_reviewer_v21` (`reviewer=v21`): **UNA sola llamada por PR** con las 19 clases de la puerta 1.3.0 en secciones, la disciplina de cita exacta de la v2 y el archivo head completo en contexto (diseño C1) |
| Puerta de evidencia (brazo ALMA) | `alma-evidence-gate/1.3.0`, fail-closed · policy sha256 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78` (puertas 1.0.0–1.3.0 intactas, verificadas por hash de blob contra el repo y por POLICY_SHA256 contra el papel) |
| Suite del paquete | **149/149** en verde al publicar (137 heredados + 12 del revisor v21) |
| Controles de gasto | `ALLOW_REAL_LLM=1` obligatorio; `RB_MAX_SPEND_USD=6.50` por PR (Adenda 4 al pre-registro v2, firmada por Alejandro el 2026-10-21); sobre total de la práctica: **US$30** (tope duro heredado) |

## Los dos brazos (un solo campo difiere)

| | Configuración base-v21 | Configuración ALMA-v21 |
|---|---|---|
| Labels | `backend=llm, governance=base, reviewer=v21, gate=v13, model=gpt-5.6-sol, effort=medium` | `backend=llm, governance=alma, reviewer=v21, gate=v13, model=gpt-5.6-sol, effort=medium` |
| Puerta | declarada (`gate=v13` define el universo de 19 clases del revisor) pero **omitida al validar** — el revisor emite directo | activa — todo finding pasa por la puerta 1.3.0 |

**Único campo distinto: `governance`.** Todo lo demás — imagen, modelo,
esfuerzo, timeout, egress, dataset y el universo de clases del revisor — es
idéntico por construcción (misma imagen, mismo registro, dos configuraciones).

> **Los labels `reviewer=v21` y `gate=v13` son obligatorios.** Sin ellos,
> `agent/main.py` usa sus defaults históricos: `RB_CONFIG_REVIEWER=v1` y
> puerta v1 — la práctica mediría el sistema viejo con la imagen nueva.
> (En la v2 pasó lo mismo con `reviewer=v2`; es el error que este campo
> existe para prevenir.)

## Economía esperada de la práctica (papel v2.1 §4)

- Peor caso de pre-vuelo sobre el PR ancla medido (cmik_apilix_12):
  **US$0,9484**; con el contexto saturado, **US$1,31** — el freno de
  US$6,50 queda con ~5× de margen y la guardia no debería negarse sobre
  ningún PR que quepa en el presupuesto de contexto. (La v2 estimaba
  US$36,80 para ese mismo PR: 39× más, y se negó en #282 y #287.)
- **Práctica completa (50 códigos): costo real esperado ≈ US$10–25**,
  bajo el tope duro de **US$30**. Si el tope se alcanza, la práctica se
  detiene y se registra, como manda el papel.

## La corrida

- **Tipo:** práctica puntuada del portal, set privado de 25 PRs, 1 corrida
  por configuración; la primera que complete en cada brazo es la válida.
- **Métrica primaria:** grounded F1 · **co-primaria:** grounded precision
  (idénticas a v1 y v2).
- **Regla de avance a la final (219 PRs × 3):** F1 ALMA ≥ F1 base-v21,
  precisión ALMA ≥ precisión base-v21 + 0,05, recall ALMA no cae más
  de 0,03.
- **Prueba de la linterna (independiente de la regla):** el recall del
  brazo base-v21 debe superar el 0,7% de la v1; si no, la hipótesis de
  contexto queda falsada aunque el A/B «gane» por precisión.
- **Estado:** imagen publicada y digest asentado (ver el sobre);
  configuraciones del portal por actualizar (guion preparado:
  `GUION-PORTAL-V21.md`); práctica por lanzar, pendiente del freno en
  US$6,50 efectivamente cargado y del «sí» de Alejandro al momento de
  lanzar.

## Semáforo previo v2.1 (2026-10-21) — VERDE

- Misma batería sintética congelada de 8 códigos con defectos plantados,
  hashes verificados 32/32 contra su manifiesto de batería.
- base-v21: 7 hallazgos emitidos, **7/8** defectos plantados detectados.
  alma-v21: 7 emitidos, **7/8** detectados.
- Costo real total: **US$0,5038** (tope duro US$20). Sin negativas de la
  guardia en los 16 códigos; sin re-corridas.
- Registro completo:
  [`RESULTADO-SEMAFORO-V21-20261021.md`](RESULTADO-SEMAFORO-V21-20261021.md).
- Sin ajustes al sistema a partir del simulacro (regla del papel).

### Declaración de la señal de dilución C1 (obligatoria por el papel §5)

Contra la corrida del semáforo v2 del mismo día (base 16 emitidos / 8/8;
ALMA 6 emitidos / 6/8):

- **Brazo base: señal de dilución C1 registrada** — detectó menos
  plantados que su par v2 (**7/8 contra 8/8**). Los emitidos caen de 16 a
  7 porque la pasada única emite un hallazgo por caso acertado, sin las
  duplicaciones de las 20 pasadas por clase de la v2. La señal se declara
  acá, como manda el papel; **no** se «corrigió» el revisor contra el
  semáforo.
- **Brazo ALMA: sin señal de dilución** — detectó más que su par v2
  (**7/8 contra 6/8**) y emitió más (7 contra 6).
- Anatomía de los dos fallos, sin ajuste: sem_01 en ALMA — la puerta
  1.3.0 rechazó el candidato sql_injection porque esqueleto SQL y
  marcador inseguro no co-ocurren en la misma línea citada (falló cerrada
  por diseño, idéntico a la v2); sem_02 en base — silencio del revisor en
  la pasada única (en el brazo ALMA el mismo caso se detectó).

## Nota de publicación

La batería (`fixtures_semaforo/`) no viaja en el repo — la protección de
push de GitHub rechaza el secreto falso plantado del caso
`sem_02_hardcoded_secret`. Queda congelada en el paquete local con sus
hashes 32/32 verificables contra el manifiesto de batería asentado en el
registro del semáforo.

## Resultados

*(Se asientan verbatim desde el portal al completarse la práctica. Hasta
entonces: sin número, sin historia.)*

| Brazo | Grounded F1 | Precisión | Recall | Gasto real |
|---|---|---|---|---|
| base-v21 | — | — | — | — |
| ALMA-v21 | — | — | — | — |

## Nota de diseño

La puerta no mejora el recall por diseño: solo filtra findings cuya
evidencia no se puede verificar en el diff. La v2.1 no cambia esa
filosofía; cambia la economía del revisor — las mismas 19 clases con la
misma disciplina de cita, en una llamada en vez de veinte — para que el
veredicto sea alcanzable dentro del tope. Si el brazo ALMA gana, gana en
precisión; si pierde, el manifiesto alcanza para que cualquiera
reproduzca la corrida y lo compruebe — mismo digest, mismo sobre.
