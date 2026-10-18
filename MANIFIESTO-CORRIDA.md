# Manifiesto de corrida — ReviewBench A/B (base vs. ALMA)

**Versión del manifiesto:** run-manifest/1.0.0 · **Registrado:** 2026-10-18 ·
Versión legible por máquina: [`manifiesto-corrida.json`](manifiesto-corrida.json)

Regla de comparación de este experimento: si dos corridas difieren en
cualquier campo de este sobre fuera del único campo declarado distinto, la
comparación queda rechazada de plano. El número que salga de esta corrida se
publica junto a este manifiesto, nunca suelto.

## El sobre

| Campo | Valor |
|---|---|
| Plataforma / juez | ReviewBench — golden set validado por ingenieros senior; severidad y categoría las asigna el clasificador de la plataforma |
| Reviewer | `alma-reviewer` (registrado 2026-10-18, estado: *awaiting approval* del mantenedor) |
| Imagen (digest) | `ghcr.io/almaoficial/alma-reviewbench@sha256:51b18cf15224022b668a8db8845bd4db5a8a85ffb64a0ead0d8d7130ed71f4b2` — pública, linux/amd64, construida por GitHub Actions (corrida nº 1 del workflow, 2026-10-18) |
| Repositorio | https://github.com/almaoficial/alma-reviewbench |
| Modelo | `gpt-5.6-sol`, effort `medium`, vía `https://api.openai.com/v1` |
| Egress del contenedor | solo `api.openai.com:443` |
| Timeout por PR | 1800 s |
| Puerta de evidencia (brazo ALMA) | `alma-evidence-gate/1.0.0`, fail-closed · policy sha256 `3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35` |
| Controles de gasto | `ALLOW_REAL_LLM=1` obligatorio; `RB_MAX_SPEND_USD=5.00` por PR; sobre total de la práctica: US$40 (aprobado por el dueño, 2026-10-18) |

## Los dos brazos (un solo campo difiere)

| | Configuración base | Configuración ALMA |
|---|---|---|
| Labels | `backend=llm, governance=base, model=gpt-5.6-sol, effort=medium` | `backend=llm, governance=alma, model=gpt-5.6-sol, effort=medium` |
| Puerta | omitida — el revisor emite directo | activa — todo finding pasa por la puerta congelada |
| Fila en el portal | `alma-reviewer-llm-base-gpt-5-6-sol-medium` | `alma-reviewer-llm-alma-gpt-5-6-sol-medium` |

**Único campo distinto: `governance`.** Todo lo demás — imagen, modelo,
esfuerzo, timeout, egress, dataset — es idéntico por construcción (misma
imagen, mismo registro, dos configuraciones).

## La corrida

- **Tipo:** práctica puntuada del portal, set privado de 25 PRs, 1 corrida
  por configuración.
- **Métrica primaria:** grounded F1 · **co-primaria:** grounded precision
  (pre-registro: `PREREGISTRO-REVIEWBENCH.md`, congelado antes de correr).
- **Regla de avance a la final (219 PRs × 3):** F1 ALMA ≥ base, precisión
  ALMA ≥ base + 0,05, recall ALMA no cae más de 0,03.
- **Estado:** PENDIENTE — espera la aprobación del mantenedor y la carga de
  credenciales.

## Resultados

*(Se asientan verbatim desde el portal al completarse la práctica, en esta
tabla y en el JSON. Hasta entonces: sin número, sin historia.)*

| Brazo | Grounded F1 | Precisión | Recall | Gasto real |
|---|---|---|---|---|
| base | — | — | — | — |
| ALMA | — | — | — | — |

## Nota de diseño

La puerta no mejora el recall por diseño: solo filtra findings cuya
evidencia no se puede verificar en el diff. Si el brazo ALMA gana, gana en
precisión; si pierde, el manifiesto alcanza para que cualquiera reproduzca
la corrida y lo compruebe — mismo digest, mismo sobre.
