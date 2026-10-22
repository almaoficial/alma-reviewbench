# Resultado de la práctica — ReviewBench v2.1 (2026-10-21)

**VEREDICTO: SIN VEREDICTO VÁLIDO.** La práctica v2.1 completó el brazo
base (primera corrida de práctica de un revisor post-v1 que llega a
puntaje), pero la **prueba de la linterna NO PASÓ**: el recall del brazo
base fue **0,4 %**, por debajo del 0,7 % de la v1. Por el papel v2.1
(§3, que hereda la regla del pre-registro v2), la hipótesis de contexto
queda falsada aunque el A/B pudiera «ganar» por precisión — el brazo
ALMA **no se lanzó** y la regla de avance no se aplica.

## 1. La corrida que cuenta (brazo base)

- **Corrida nº 290** del portal (agente `alma-reviewer`), configuración
  llm · base · gpt-5.6-sol · medium · v21 · v13; imagen
  `ghcr.io/almaoficial/alma-reviewbench@sha256:32da7c01181c3ebae61d6cb9d5d31590858ad328c7f292d56d153a5b0523a0bc`.
- Lanzada el **2026-10-21, 18:00:52 EDT**; estado final: **SUCCEEDED**.
- **Puntajes del portal: precisión 37,5 % · recall 0,4 %** · 8 hallazgos
  emitidos, 3 novedosos. El F1 no lo muestra el portal; calculado desde
  P y R: **F1 ≈ 0,8 %**.
- Es la primera corrida que COMPLETA en cada brazo lo que cuenta: es la
  válida del brazo base. No hay relanzamiento: nada falló en la
  plataforma; el resultado es del diseño medido, no de infraestructura.

## 2. La linterna y su consecuencia

- Prueba heredada intacta: «si el recall del brazo base no supera el
  0,7 % de la v1, la hipótesis de contexto queda falsada aunque el A/B
  gane por precisión». Recall base medido: **0,4 % ≤ 0,7 % → NO PASA.**
- Consecuencia según el papel: el brazo ALMA no se lanza (lanzarlo no
  mediría nada interpretable: con un base que no ve, cualquier «victoria»
  por precisión sería un artefacto) y la práctica v2.1 se asienta **sin
  veredicto** sobre «ALMA mejora».

## 3. Causa declarada: dilución C1 en PRs reales

Es el riesgo que la Adenda 6 declaró para C1 y que el §6 del papel v2.1
puso como falsador de práctica («linterna sin superar 0,7 %»):

- En la batería sintética (miniatura), la pasada única vio 7/8 en ambos
  brazos (semáforo v2.1, VERDE, costo US$0,5038).
- En PRs reales grandes, la misma pasada única diluye la detección por
  clase: 19 clases compitiendo por una sola salida acotada sobre
  contextos de decenas de miles de tokens produce recall 0,4 % — la
  mitad del 0,7 % que la v1 logró con su formato libre de una pasada.
- La economía, en cambio, quedó resuelta: la corrida completó sin
  negativas de la guardia (la cuenta de la §4 del papel se sostuvo: la
  práctica es financiable con la pasada única; el problema no es el
  costo, es la vista).

## 4. Camino que el propio papel dejaba escrito

El falsador de la §6 del papel v2.1 dice: linterna sin superar →
registrar el nulo de C1 y detener; la salida es **C2 de la Adenda 6**
(triage barato sobre el diff + pasadas profundas solo para las clases
marcadas, ≤5), con su propio papel — no un ajuste en caliente de la
v2.1. Decisión de Alejandro (21/10, 18:30 EDT): construir C2.

**Puertas 1.0.0–1.3.0: intactas.** Nada de este resultado toca la
puerta, la batería ni el set privado de 25 PRs.
