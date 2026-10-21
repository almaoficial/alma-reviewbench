# Manifiesto de corrida v2.2 — ReviewBench A/B (base-v22 vs. ALMA-v22)

**Versión del manifiesto:** run-manifest/2.2.0 · **Preparado:** 2026-10-21 ·
Pre-registro: [`PREREGISTRO-REVIEWBENCH-V22.md`](PREREGISTRO-REVIEWBENCH-V22.md)
(congelado antes de correr; diseño C2 de la Adenda 6 del pre-registro v2)

Regla de comparación de este experimento: si dos corridas difieren en
cualquier campo de este sobre fuera del único campo declarado distinto, la
comparación queda rechazada de plano. El número que salga de esta corrida se
publica junto a este manifiesto, nunca suelto.

**Estado de este manifiesto:** código e imagen publicados y verificados;
el campo «Imagen (digest)» quedó asentado con el digest completo,
verificado contra GHCR, con su commit declarado (el mismo procedimiento
que asentó la v2.1 en su cierre `4d1cf01`). Ningún número de la práctica
existe todavía: la práctica está por lanzar.

## El sobre

| Campo | Valor |
|---|---|
| Plataforma / juez | ReviewBench — golden set validado por ingenieros senior; severidad y categoría las asigna el clasificador de la plataforma |
| Reviewer | `alma-reviewer` (registrado 2026-10-18, aprobado 2026-10-19) |
| Imagen (digest) | `ghcr.io/almaoficial/alma-reviewbench@sha256:577bc2ec6780c5af4d3260caad74d3bd06b73dedf5b4e616ddbe03e44880206a` (pública, linux/amd64, GitHub Actions — workflow `reviewbench-image` corrida nº 5, tag `dev`, desde el commit `031dd0f` de `main`; digest completo de 64 caracteres, **verificado contra GHCR el 2026-10-21**: el tag `dev` resuelve a este digest, y el contenido de la imagen incluye `app/agent/llm_reviewer_v22.py`) |
| Repositorio | https://github.com/almaoficial/alma-reviewbench — commit del paquete v2.2: `031dd0f37bdb8c753c8e6192fd8c872a72798866` («Revisor v2.2: triage + pasadas profundas (diseño C2 de la Adenda 6) + pre-registro v2.2 + semáforo v2.2 VERDE», padre `4d1cf01`) |
| Modelo | `gpt-5.6-sol`, effort `medium`, vía `https://api.openai.com/v1` |
| Egress del contenedor | solo `api.openai.com:443` |
| Timeout por PR | 1800 s |
| Revisor | `llm_reviewer_v22` (`reviewer=v22`): **pasada de selección solo sobre el diff** (≤5 clases marcadas, en orden de prioridad) + **pasadas profundas con el formato exacto de la v2** solo para las clases marcadas, con el archivo head completo en contexto; guardia en dos etapas con **regla de degradación pre-registrada** — si selección + profundas superan el freno, corren las profundas de mayor prioridad que quepan y la truncación queda **declarada** en la salida; si ni una cabe, respaldo diff-only marcado. La truncación reemplaza a la negativa: ningún PR se niega entero (diseño C2) |
| Puerta de evidencia (brazo ALMA) | `alma-evidence-gate/1.3.0`, fail-closed · policy sha256 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78` (puertas 1.0.0–1.3.0 intactas, verificadas por hash antes del semáforo) |
| Suite del paquete | **163/163** en verde al publicar (149 heredados + 14 del revisor v22) |
| Controles de gasto | `ALLOW_REAL_LLM=1` obligatorio; `RB_MAX_SPEND_USD=6.50` por PR (Adenda 4 al pre-registro v2, firmada por Alejandro el 2026-10-21); sobre total de la práctica: **US$30** (tope duro heredado) |

## Los dos brazos (un solo campo difiere)

| | Configuración base-v22 | Configuración ALMA-v22 |
|---|---|---|
| Labels | `backend=llm, governance=base, reviewer=v22, gate=v13, model=gpt-5.6-sol, effort=medium` | `backend=llm, governance=alma, reviewer=v22, gate=v13, model=gpt-5.6-sol, effort=medium` |
| Puerta | declarada (`gate=v13` define el universo de 19 clases del revisor) pero **omitida al validar** — el revisor emite directo | activa — todo finding pasa por la puerta 1.3.0 |

**Único campo distinto: `governance`.** Todo lo demás — imagen, modelo,
esfuerzo, timeout, egress, dataset y el universo de clases del revisor — es
idéntico por construcción (misma imagen, mismo registro, dos configuraciones).
Ambos brazos hacen la misma selección y las mismas pasadas profundas; sin
pasada general en ningún brazo (paridad A/B heredada de la v2.1).

> **Los labels `reviewer=v22` y `gate=v13` son obligatorios.** Sin ellos,
> `agent/main.py` usa sus defaults históricos: `RB_CONFIG_REVIEWER=v1` y
> puerta v1 — la práctica mediría el sistema viejo con la imagen nueva.
> (Es el error que este campo existe para prevenir desde la v2.)

## Economía esperada de la práctica (papel v2.2 §4)

- Pasada de selección (solo diff) sobre el PR ancla: peor caso ≈ **US$0,26**
  (medida en seco: US$0,2372). Pasada profunda (formato v2, contexto
  completo): ≈ **US$0,95** (medida en seco: US$0,9380); con el contexto
  saturado, ≈ US$1,31.
- **Plan completo en el PR ancla (selección + 5 profundas): ≈ US$5,01**
  por papel (medido en seco: US$4,9273) — dentro del freno de US$6,50.
  Saturado ≈ US$6,8: territorio de la regla de degradación, que corre
  las profundas que caben y **declara** las caídas. (La v2 estimaba
  US$36,80 para ese mismo PR y se negó; la v2.2 no puede negarse:
  planifica sobre lo que va a correr.)
- **Práctica completa (50 códigos): costo real esperado ≈ US$10–25**,
  bajo el tope duro de **US$30**. Si el tope se alcanza, la práctica se
  detiene y se registra, como manda el papel.
- **Falsador propio del papel (§7):** degradación declarada en más de
  1/4 de los PRs de la práctica → la economía de C2 tampoco cierra
  sobre PRs reales: registrar y detener.

## La corrida

- **Tipo:** práctica puntuada del portal, set privado de 25 PRs, 1 corrida
  por configuración; la primera que complete en cada brazo es la válida.
- **Métrica primaria:** grounded F1 · **co-primaria:** grounded precision
  (idénticas a v1, v2 y v2.1).
- **Regla de avance a la final (219 PRs × 3):** F1 ALMA ≥ F1 base-v22,
  precisión ALMA ≥ precisión base-v22 + 0,05, recall ALMA no cae más
  de 0,03.
- **Prueba de la linterna (independiente de la regla):** el recall del
  brazo base-v22 debe superar el 0,7% de la v1; si no pasa con pasadas
  de formato v2, la hipótesis falsada ya no es la estructura de pasadas
  — es la de contexto (falsador de la §7 del papel v2.2).
- **Estado:** imagen publicada y digest asentado (ver el sobre);
  configuraciones del portal por actualizar (guion preparado:
  `GUION-PORTAL-V22.md`); práctica por lanzar, pendiente del «Corre»
  de Alejandro al momento de lanzar, con las configuraciones ya
  guardadas.

## Semáforo previo v2.2 (2026-10-21) — VERDE

- Misma batería sintética congelada de 8 códigos con defectos plantados,
  hashes verificados 32/32 contra su manifiesto de batería antes de
  correr; puertas 1.0.0–1.3.0 verificadas por hash, intactas.
- base-v22: 7 hallazgos emitidos, **7/8** defectos plantados detectados —
  **US$0,3090**. alma-v22: 6 emitidos, **6/8** detectados —
  **US$0,3132**. **Costo real total: US$0,6221** (tope duro US$20).
- **Medición C2: triage 16/16** — en los 16 códigos (8 × 2 brazos) la
  selección marcó exactamente 1 clase, siempre la plantada, y esa clase
  recibió su pasada profunda. Triage misses: **0**. Marcas desconocidas:
  0. `selection_overflow`: vacío en los 16.
- **0 degradaciones y 0 negativas** de la guardia en los 16 códigos;
  sin re-corridas (16/16 exit=0 en la primera pasada).
- Registro completo:
  [`RESULTADO-SEMAFORO-V22-20261021.md`](RESULTADO-SEMAFORO-V22-20261021.md).
- Sin ajustes al sistema a partir del simulacro (regla del papel).

### Declaración de la señal del brazo ALMA (obligatoria por el papel §6)

Contra las corridas de semáforo anteriores del mismo día (v2: base 16
emitidos / 8/8, ALMA 6 / 6/8; v2.1: base 7 / 7/8, ALMA 7 / 7/8):

- **Brazo ALMA: señal registrada** — detectó MENOS plantados que su
  par v2.1 (**6/8 contra 7/8**). La anatomía muestra que **no es
  triage** (16/16) **ni degradación** (ninguna): es la suma de dos
  fallos ya conocidos. sem_01 — la puerta 1.3.0 rechazó el candidato
  `sql_injection` con la misma razón de cita de la v2 y la v2.1
  («a SQL skeleton and an unsafe construction marker must co-occur on
  the same cited line»): tercera corrida consecutiva con el mismo
  rechazo sobre el mismo caso; la puerta falló cerrada sobre la cita,
  como está diseñada, y en el brazo base el mismo caso se emitió y
  detectó. sem_02 — la profunda de `hardcoded_secret` corrió (el
  triage la marcó en ambos brazos) y devolvió **cero hallazgos
  crudos**: silencio del modelo, ledger vacío; golpeó a los dos brazos
  a la vez (en la v2.1 este brazo sí lo resolvió; en la v2 el base sí
  lo detectó con esta misma pasada → varianza, asentada sin ajustar).
- **Brazo base: sin señal de triage ni de degradación** — iguala a su
  par v2.1 (**7/8**) y queda debajo de su par v2 (8/8) por el mismo
  silencio de sem_02.
- La señal se declara acá, como manda el papel; **no** se «corrigió»
  el revisor contra el semáforo. Su prueba real es la práctica, donde
  los diffs no son de juguete.

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
| base-v22 | — | — | — | — |
| ALMA-v22 | — | — | — | — |

## Nota de diseño

La puerta no mejora el recall por diseño: solo filtra findings cuya
evidencia no se puede verificar en el diff. La v2.2 no cambia esa
filosofía; cambia la economía del revisor por la vía del medio que la
Adenda 6 definió: ni las 20 pasadas de la v2 (veía pero no podía pagar
su vista: la guardia se negó en la práctica) ni la pasada única de la
v2.1 (pagaba pero no veía: linterna 0,4 %). Una pasada barata decide
qué clases merecen el formato caro, y cuando el freno no alcanza para
todas, la truncación se declara en vez de negarse. Si el brazo ALMA
gana, gana en precisión; si pierde, el manifiesto alcanza para que
cualquiera reproduzca la corrida y lo compruebe — mismo digest, mismo
sobre.
