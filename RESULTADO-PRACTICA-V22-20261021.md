# Resultado — Práctica v2.2 de ReviewBench (2026-10-21)

## Brazo base — corrida nº 295

- Lanzada: 2026-10-21 19:57:18 EDT
- Configuración: llm · base · gpt-5.6-sol · medium · v22 · v13
  (labels: backend=llm, governance=base, model=gpt-5.6-sol, effort=medium, reviewer=v22, gate=v13)
- Imagen: ghcr.io/almaoficial/alma-reviewbench@sha256:577bc2ec6780c5af4d3260caad74d3bd06b73dedf5b4e616ddbe03e44880206a
- Estado (portal review-bench.ai, alma-reviewer, verificado 20:10–20:26 EDT): **succeeded**
- Puntajes del portal:
  - Grounded: F1 0,0 % · Precision 0,0 % · Recall 0,0 %
  - Augmented: F1 0,8 % · Precision 15,0 % · Recall 0,4 %
  - Duración promedio: 7 s
  - Findings: 11 (3 novel)

## Prueba de la linterna

- Regla: recall_base > 0,007 (0,7 %)
- Recall base grounded: 0,0 % — **NO PASA**
- Recall base augmented: 0,4 % — también por debajo del umbral
- **Veredicto: LINTERNA FALLIDA**

## Consecuencia

- El brazo ALMA v22 **no se lanzó** (no existe ninguna corrida ALMA v22; la más reciente con esa configuración en el portal es la #253 del 19/10/2026, failed at score, de la v1).
- La práctica v2.2 queda **SIN VEREDICTO VÁLIDO** sobre «ALMA mejora»: la regla de avance (F1_alma ≥ F1_base, precisión_alma ≥ precisión_base + 0,05, caída de recall ≤ 0,03) no se puede aplicar sin un base que vea.
- No se tocó «Submit» (final de 219 PRs), ni credenciales, ni el freno RB_MAX_SPEND_USD. Sin relanzamientos.
- La vigilancia `vigilar-practica-v22-reviewbench` se elimina en esta pasada, como manda el protocolo ante linterna fallida.

## Falsador propio de C2 (papel v22, §7)

- Criterio: eventos de degradación/truncación en más de 1/4 de los PRs en los outputs de la práctica.
- Estado: **no gatillado con la evidencia disponible** — la lectura del portal (lista de runs y puntajes) no mostró esos eventos asentados. Queda marcado como no verificado a nivel de outputs por PR (no se descargaron los outputs completos en esta pasada).

## Lectura

La economía y la ejecución quedaron resueltas (la corrida completó y puntuó, a diferencia de las fallas de plataforma/guardia anteriores), pero la detección grounded fue cero: 11 findings emitidos, ninguno grounded correcto según el portal. El cuello sigue siendo la vista del revisor base en PRs reales, no el costo ni la plataforma.
