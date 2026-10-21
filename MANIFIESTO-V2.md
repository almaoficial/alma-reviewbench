# Manifiesto de corrida v2 — ReviewBench A/B (base-v2 vs. ALMA-v2)

**Versión del manifiesto:** run-manifest/2.0.0 · **Preparado:** 2026-10-21 ·
Pre-registro: [`PREREGISTRO-REVIEWBENCH-V2.md`](PREREGISTRO-REVIEWBENCH-V2.md)
(congelado antes de correr, con sus Adendas 1–4)

Regla de comparación de este experimento: si dos corridas difieren en
cualquier campo de este sobre fuera del único campo declarado distinto, la
comparación queda rechazada de plano. El número que salga de esta corrida se
publica junto a este manifiesto, nunca suelto.

## El sobre

| Campo | Valor |
|---|---|
| Plataforma / juez | ReviewBench — golden set validado por ingenieros senior; severidad y categoría las asigna el clasificador de la plataforma |
| Reviewer | `alma-reviewer` (registrado 2026-10-18, aprobado 2026-10-19) |
| Imagen (digest) | `ghcr.io/almaoficial/alma-reviewbench@sha256:f2da937c2fa4a0e3cbdf3dae09c821419f34920cf4ab3394fc2cc226` — pública, linux/amd64, construida por GitHub Actions (corrida nº 3 del workflow, 2026-10-21; tag `dev`, desde el commit `8eeacb7` de `main`) |
| Repositorio | https://github.com/almaoficial/alma-reviewbench |
| Modelo | `gpt-5.6-sol`, effort `medium`, vía `https://api.openai.com/v1` |
| Egress del contenedor | solo `api.openai.com:443` |
| Timeout por PR | 1800 s |
| Revisor | `llm_reviewer_v2` (`reviewer=v2`): una pasada por clase verificable citando evidencia exacta + archivo head completo en contexto |
| Puerta de evidencia (brazo ALMA) | `alma-evidence-gate/1.3.0`, fail-closed · policy sha256 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78` |
| Controles de gasto | `ALLOW_REAL_LLM=1` obligatorio; `RB_MAX_SPEND_USD=6.50` por PR (Adenda 4 al pre-registro v2, firmada por Alejandro el 2026-10-21); sobre total de la práctica: **US$30** (tope duro del pre-registro v2 §5 — la regla de decisión del tope dio banda 1: proyección desde el semáforo ≈ US$8,6) |

## Los dos brazos (un solo campo difiere)

| | Configuración base-v2 | Configuración ALMA-v2 |
|---|---|---|
| Labels | `backend=llm, governance=base, reviewer=v2, gate=v13, model=gpt-5.6-sol, effort=medium` | `backend=llm, governance=alma, reviewer=v2, gate=v13, model=gpt-5.6-sol, effort=medium` |
| Puerta | declarada (`gate=v13` define el universo de 19 clases del revisor) pero **omitida al validar** — el revisor emite directo | activa — todo finding pasa por la puerta 1.3.0 |

**Único campo distinto: `governance`.** Todo lo demás — imagen, modelo,
esfuerzo, timeout, egress, dataset y el universo de clases del revisor — es
idéntico por construcción (misma imagen, mismo registro, dos configuraciones).

## La corrida

- **Tipo:** práctica puntuada del portal, set privado de 25 PRs, 1 corrida
  por configuración; la primera que complete en cada brazo es la válida.
- **Métrica primaria:** grounded F1 · **co-primaria:** grounded precision
  (pre-registro v2 §4, idénticas a v1).
- **Regla de avance a la final (219 PRs × 3):** F1 ALMA ≥ F1 base-v2,
  precisión ALMA ≥ precisión base-v2 + 0,05, recall ALMA no cae más de 0,03.
- **Prueba de la linterna (independiente de la regla):** el recall del brazo
  base-v2 debe superar el 0,7% de la v1; si no, la hipótesis 2 queda falsada
  aunque el A/B «gane» por precisión.
- **Estado:** imagen v2 por publicar (workflow manual); práctica **sin
  lanzar** — requiere el «sí» de Alejandro al momento de lanzar (§7.3) y el
  freno de la bóveda del portal actualizado a 6.50 (acción suya, declarada
  en este manifiesto).

## Semáforo previo (2026-10-21)

- Batería sintética congelada de 8 códigos con defectos plantados, hashes
  verificados 32/32 contra su manifiesto de batería.
- base-v2: 16 hallazgos emitidos, **8/8** defectos plantados detectados.
  alma-v2: 6 emitidos, **6/8** detectados.
- Costo real total: **US$2,7457**. Veredicto: **VERDE** (criterio de la
  Adenda 3: ningún brazo en cero).
- Registro completo: [`RESULTADO-SEMAFORO-20261021.md`](RESULTADO-SEMAFORO-20261021.md)
  (intentos 1 y 2 detenidos por credenciales, gasto US$0; intento 3
  ejecutado, con incidente de infraestructura declarado y re-corrida solo
  de los casos cortados).
- Sin ajustes al sistema a partir del simulacro (regla del papel).
- **Nota de publicación:** la batería (`fixtures_semaforo/`) no viaja en
  este repo — la protección de push de GitHub rechazó el secreto falso
  plantado del caso `sem_02_hardcoded_secret` (un `sk_live_…exampleplanted…`
  sintético). La batería queda congelada en el paquete local con sus hashes
  32/32 verificables contra el manifiesto de batería asentado en el
  registro del semáforo.

## Resultados

*(Se asientan verbatim desde el portal al completarse la práctica. Hasta
entonces: sin número, sin historia.)*

| Brazo | Grounded F1 | Precisión | Recall | Gasto real |
|---|---|---|---|---|
| base-v2 | — | — | — | — |
| ALMA-v2 | — | — | — | — |

## Nota de diseño

La puerta no mejora el recall por diseño: solo filtra findings cuya
evidencia no se puede verificar en el diff. Si el brazo ALMA gana, gana en
precisión; si pierde, el manifiesto alcanza para que cualquiera reproduzca
la corrida y lo compruebe — mismo digest, mismo sobre.
