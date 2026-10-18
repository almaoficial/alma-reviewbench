# Pre-registro — Experimento A/B de ALMA en ReviewBench

- **Fecha:** 2026-10-17.
- **Estado:** pre-registrado antes de cualquier corrida real o paga.
- **Trabajo ejecutado hasta este papel:** solo paquete local mock/US$0.
- **Registro en ReviewBench:** no realizado.
- **Inferencia paga:** no realizada.

## Pregunta

¿La capa de gobernanza de ALMA mejora a un revisor de código cuando ambos
brazos usan exactamente el mismo revisor base, modelo, configuración y set,
y la única diferencia es que los findings candidatos deben superar un
validador congelado de evidencia antes de emitirse?

## Hipótesis

1. **H1 — precisión:** el brazo ALMA tendrá mayor grounded precision que el
   brazo base, porque rechaza findings plausibles pero no sostenidos por el
   diff citado.
2. **H2 — F1:** el brazo ALMA tendrá grounded F1 igual o mayor que el brazo
   base en el set de práctica de 25 PRs. Una suba de precisión con una caída
   grande de recall no cuenta como éxito automático.
3. **H3 — mecanismo:** la mejora, si existe, vendrá de menos falsos positivos
   por evidencia insuficiente, no de que ALMA «encuentre» defectos nuevos:
   la puerta filtra candidatos; no genera recall de la nada.

## Brazos

- **Base:** mismo contenedor y mismo backend, configuración
  `governance=base`. Emite todos los candidates del revisor base.
- **ALMA:** mismo contenedor y mismo backend, configuración
  `governance=alma`. Emite solo los candidates aceptados por
  `alma-evidence-gate/1.0.0` (SHA-256 de política calculado en el código y
  registrado en cada ledger local).
- En el paquete mock, el backend es `backend=mock`,
  `model=deterministic-rules`, `effort=local`. Ese mock sirve para validar
  contrato, formato y mecanismo; **no** estima el puntaje de un LLM real.
- Para una corrida paga futura, primero hay que implementar/probar el adapter
  del proveedor elegido y congelar en una adenda: proveedor, modelo exacto,
  effort, temperatura si aplica, timeout por PR, egress, tope de gasto y
  versión/digest de la imagen. Sin esa adenda, este papel no autoriza gasto.

## Métricas

- **Primaria:** grounded F1 del test run de 25 PRs.
- **Co-primaria de mecanismo:** grounded precision.
- **Secundarias:** grounded recall, augmented precision/F1, precisión en
  severidad crítica, cantidad de findings por PR, tasa de PRs fallidos,
  tiempo por PR y costo real por PR.
- **Diagnóstico obligatorio:** ledger por candidato con estado
  aceptado/rechazado, evidencia citada y motivo. En el portal el ledger no se
  sube salvo que el contrato lo permita; se conserva localmente por corrida.

## Orden y congelamiento

1. Validación local de formato con `try-agent.sh` y backend mock: US$0.
2. Si se aprueba una corrida con modelo, calibración mínima necesaria para
   medir tokens/costo por PR, sin cambiar reglas después de ver puntajes.
3. Test run del portal sobre 25 PRs, brazo base y brazo ALMA, con la misma
   configuración salvo `governance`.
4. Solo si se cumple la regla de avance, corrida final de 219 PRs × 3 rondas.
5. Ningún ajuste del validador entre el test run y la corrida final. Si el
   validador cambia, es otro experimento y exige papel nuevo.

## Regla de avance a la corrida completa

Avanzar solo si en los 25 PRs se cumplen las tres condiciones:

- grounded F1 de ALMA ≥ grounded F1 base;
- grounded precision de ALMA supera a la base por al menos **+0,05**
  absoluto;
- grounded recall de ALMA no cae más de **0,03** absoluto frente a la base.

Si no se cumplen, no hay corrida completa automática. Las opciones son
archivar el experimento o escribir un papel nuevo; no se tunea el validador
contra el mismo set para «hacerlo pasar».

## Costo estimado de inferencia

La plataforma no cobra fee. El costo es la inferencia del revisor con la key
propia; el juez del portal lo provee ReviewBench. La evaluación offline con
juez propio sería otro costo y no está incluida ni autorizada aquí.

Fórmula por intento de PR:

`costo = tokens_entrada / 1.000.000 × tarifa_entrada + tokens_salida / 1.000.000 × tarifa_salida`

Escenarios de planificación — no son cotizaciones del proveedor:

| Escenario por PR | Supuesto de tokens | Banda intermedia ilustrativa: US$3/M entrada, US$15/M salida | Banda frontier ilustrativa: US$15/M entrada, US$75/M salida |
|---|---:|---:|---:|
| Corto | 15k entrada + 1k salida | US$0,06 | US$0,30 |
| Típico | 40k entrada + 2k salida | US$0,15 | US$0,75 |
| Largo | 120k entrada + 4k salida | US$0,42 | US$2,10 |

Totales por escenario (sin reintentos ni fallas):

| Corrida | Intentos | Intermedia corto–largo | Frontier corto–largo |
|---|---:|---:|---:|
| Práctica portal, 25 PRs × 1 brazo | 25 | US$1,50–10,50 | US$7,50–52,50 |
| Práctica A/B, 25 PRs × 2 brazos | 50 | US$3,00–21,00 | US$15,00–105,00 |
| Final, 219 PRs × 3 rondas × 1 brazo | 657 | US$39,42–275,94 | US$197,10–1.379,70 |
| Final A/B, 219 × 3 × 2 brazos | 1.314 | US$78,84–551,88 | US$394,20–2.759,40 |

El presupuesto exigible antes de aprobar no es este rango: es un **tope único**
calculado con el modelo elegido y una calibración de tokens. Si el gasto
proyectado toca el tope, la corrida se detiene; no se «completa igual».

## Tiempo

- Tope por PR: 1800 segundos por defecto; máximo registrable 3600.
- El wall-clock total depende de la concurrencia del portal, que no está
  publicada. Ninguna aprobación es válida si no nombra timeout por PR y tope
  monetario; el tiempo total se estima después de la calibración.

## Regla de autorización

Toda corrida que use una key real — práctica, calibración o final — exige el
**sí explícito de Alejandro** con, en el mismo mensaje de aprobación:

1. modelo y configuración exactos;
2. brazos a correr (base, ALMA o ambos);
3. set (25 o 219×3);
4. tope de gasto en US$;
5. timeout por PR.

Sin esos cinco datos, el estado autorizado es únicamente: código local, tests
mock y validación de formato sin inferencia paga.

## Riesgos y límites declarados

- El revisor determinista tiene recall bajo y reglas estrechas: valida el
  mecanismo y el contrato, no predice el ranking de un revisor LLM.
- La puerta no puede aceptar un defecto que el revisor base nunca propuso.
- Un validador de evidencia puede rechazar un finding verdadero si su
  evidencia directa no está en el diff; ese costo se mide como caída de recall.
- ReviewBench asigna severidad/categoría con su clasificador; este paquete no
  controla esos campos porque el contrato de salida no los incluye.
- El set completo y el golden set son públicos: queda prohibido usarlos para
  ajustar reglas durante una corrida; cualquier ajuste posterior exige otro
  set/papel y queda registrado como posible contaminación.
- La red del contenedor debe quedar limitada al host del modelo; se deben
  desactivar búsqueda web y conectores que puedan leer las respuestas del PR.

---

## Adenda 2026-10-18 — secuencia de ejecución y compuertas

Esta adenda **no mueve** la pregunta, las hipótesis H1–H3, las métricas ni
la regla de avance escritas arriba. Registra el estado de implementación y
la secuencia concreta para llegar a la corrida, que el papel original
dejaba como pasos 1–5 sin las compuertas de decisión separadas.

**Hechos nuevos desde el papel original:**

1. El adapter del proveedor quedó implementado (`agent/llm_reviewer.py`,
   protocolo chat-completions compatible) y probado **offline** con HTTP
   mockeado: 24/24 tests en verde (8 originales + 16 del adapter). El
   backend real es fail-closed: exige `ALLOW_REAL_LLM=1`, key por entorno,
   `RB_MODEL_BASE_URL`, modelo configurado y `RB_MAX_SPEND_USD` positivo;
   controla el tope antes de llamar (peor caso) y después (usage
   reportado). Sus candidatos pasan por la misma puerta congelada
   `alma-evidence-gate/1.0.0` que los del revisor mock.
2. La VM de trabajo no tiene Docker ni ningún builder de contenedores
   (verificado 2026-10-18: docker/podman/buildah/nerdctl/kaniko ausentes;
   no se instalaron paquetes del sistema). El entrypoint se validó sin
   argumentos contra los 4 fixtures en ambos brazos, con salida `$RB_OUT`
   conforme al contrato. La imagen se construirá por GitHub Actions
   (workflow manual en `workflows/`, sin subir todavía a ningún repo).
3. El paquete de registro está preparado en `REGISTRO-REVIEWBENCH.md` con
   todos los campos del portal prellenados salvo digest y credenciales, y
   las dos configuraciones A/B (`governance=base|alma`, `backend=llm`,
   `model=gpt-5.6-sol`, `effort=medium`).

**Secuencia de ejecución (cada compuerta exige el sí de Alejandro):**

1. ✅ Local US$0: tests, fixtures y validación de formato del entrypoint.
2. **Compuerta A** — publicar la imagen en GHCR vía workflow manual y
   obtener el digest. Costo US$0; el código del adaptador se hace público.
3. Enviar el registro en el portal con el digest (abre el PR del
   manifiesto; el merge del mantenedor es la aprobación, ~1 día hábil).
4. **Compuerta B** — cargar la API key en el portal (él o por bóveda
   segura, nunca por chat) y declarar `ALLOW_REAL_LLM=1` y
   `RB_MAX_SPEND_USD` como entorno.
5. Calibración mínima (paso 2 del orden original): medir tokens/costo por
   PR y congelar en una **segunda adenda** proveedor, modelo exacto,
   effort, tarifas, timeout por PR, tope de gasto y digest de imagen.
   Sin esa adenda, este papel sigue sin autorizar gasto.
6. **Compuerta C** — test run puntuado de 25 PRs, brazos base y ALMA.
   Bandas A/B del papel original: intermedia US$3,00–21,00; frontier
   US$15,00–105,00.
7. Evaluar la regla de avance tal como está escrita arriba. Si se cumple,
   **Compuerta D** — corrida final 219 × 3, A/B (bandas: intermedia
   US$78,84–551,88; frontier US$394,20–2.759,40). Si no se cumple, se
   archiva o se escribe papel nuevo; no se tunea el validador contra el
   mismo set.
