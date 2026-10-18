# ALMA para ReviewBench — paquete mock-first

Este directorio contiene un adaptador local **US$0 por defecto** para
probar a ALMA como capa de gobernanza sobre un revisor de código de
ReviewBench, el benchmark público de GitHub para agentes de code review.

**Estado al 2026-10-18:** paquete construido y testeado localmente
(24/24 tests). Incluye el backend LLM real implementado pero **desarmado**
(fail-closed, ver abajo). No se registró ningún agente, no se cargó
ninguna API key, no se hizo ninguna llamada a un modelo real y no se
publicó ninguna imagen.

## Qué hace

1. Un **revisor base** determinista lee el diff y propone findings candidatos
   con reglas simples. Incluye a propósito tres heurísticas demasiado amplias
   que generan «éxitos falsos» plausibles pero sin evidencia suficiente.
2. La **capa ALMA** (`alma-evidence-gate/1.0.0`) valida cada candidato contra
   el diff:
   - el archivo y cada línea citada existen en el diff;
   - el texto de evidencia guardado coincide exactamente con esas líneas;
   - la evidencia contiene el soporte específico del claim (por ejemplo, SQL
     + interpolación para inyección SQL; `verify=False` para TLS desactivado);
   - todo claim desconocido se rechaza — fail-closed.
3. Los aceptados se escriben en el formato exacto de ReviewBench. Los
   rechazados quedan en un ledger opcional con motivo y evidencia.

El experimento es A/B: el mismo revisor puede correr con
`governance=base` (emite todo) o `governance=alma` (emite lo que pasa la
puerta). La puerta no inventa findings: si el base no propone un defecto, ALMA
no lo descubre.

El **backend** también es intercambiable sin tocar la puerta:

- `backend=mock` (default): el revisor determinista de arriba. US$0, sin red.
- `backend=llm`: un modelo real (protocolo chat-completions) propone los
  findings en JSON; el adaptador les rellena la evidencia desde el diff real
  y pasan por la **misma puerta congelada**. El backend es fail-closed: se
  niega a llamar si falta cualquiera de `ALLOW_REAL_LLM=1`, la API key por
  entorno, `RB_MODEL_BASE_URL`, el modelo configurado o un
  `RB_MAX_SPEND_USD` positivo; y controla el tope antes y después de la
  llamada. Está probado offline con HTTP mockeado (`tests/test_llm_adapter.py`);
  nunca corrió contra un modelo real.

## Contrato implementado

Ver [CONTRACT.md](CONTRACT.md). En síntesis:

- Contenedor fresco por PR, `linux/amd64`, sin argumentos.
- Entrada: `/work/repo`, `/work/pr/diff.patch`, `/work/pr/pr.json` y env
  `RB_*`, incluidas `RB_CONFIG_<KEY>`.
- Salida: un JSON en `$RB_OUT` con `pr`, `agent` y `findings[]` de campos
  exactos `{file, start_line, end_line, message, producer}`.
- `pr.head == RB_HEAD` y `pr.pr_number == RB_PR_NUMBER`, o el PR falla.
- El agente **no** emite severidad ni categoría: las asigna el clasificador
  de ReviewBench.
- La imagen real se registra en GHCR por digest `sha256`, nunca por tag.

## Cómo correr el mock local

Desde este directorio:

```bash
python3 -m unittest discover -s tests -v
```

La última corrida queda en `runs/local-test-output.txt`. Hay 4 fixtures en
`fixtures/`, cada uno con `diff.patch`, `pr.json` y `expected.json`:

- `01_sql`: inyección SQL real aceptada; un execute parametrizado que el base
  sobre-marca como posible inyección es rechazado.
- `02_error_handling`: `except:` + `pass` aceptado; una «race condition» por la
  sola palabra cache es rechazada.
- `03_mutable_default`: default mutable aceptado; una credencial inferida solo
  del nombre de variable, cuyo valor viene de `os.getenv`, es rechazada.
- `04_secrets_tls`: secreto literal y `verify=False` aceptados.

Corrida manual de un fixture con ledger:

```bash
python3 -m agent \
  --diff fixtures/01_sql/diff.patch \
  --pr-json fixtures/01_sql/pr.json \
  --out /tmp/alma-findings.json \
  --ledger /tmp/alma-ledger.json \
  --mode alma
```

Modo base, para comparar:

```bash
python3 -m agent \
  --diff fixtures/01_sql/diff.patch \
  --pr-json fixtures/01_sql/pr.json \
  --out /tmp/base-findings.json \
  --mode base
```

## Docker y validación con el runner oficial

Construir la imagen en la plataforma que exige el contrato:

```bash
docker build --platform linux/amd64 \
  -t ghcr.io/almaoficial/alma-reviewbench:dev .
```

Este entorno no tiene Docker disponible (verificado el 2026-10-18:
tampoco podman/buildah/nerdctl/kaniko), así que la imagen **no** fue
construida ni corrida aquí; el Dockerfile está cubierto por test estático y
el entrypoint sin argumentos se validó contra los 4 fixtures en ambos
brazos, con salida `$RB_OUT` conforme al contrato (evidencia en
`runs/entrypoint-sim-output.txt`). El camino de construcción sin Docker
local es GitHub Actions: `workflows/reviewbench-image.yml` (solo disparo
manual) construye `linux/amd64`, publica en
`ghcr.io/almaoficial/alma-reviewbench` y emite el digest — ver
`workflows/README.md`. La validación pendiente con el runner oficial,
desde un clon de `review-bench/ReviewBench`, es:

```bash
scripts/try-agent.sh ghcr.io/almaoficial/alma-reviewbench:dev --pr 0
```

Ese script valida formato sobre el set de 25 PRs y no puntúa. Con el backend
mock no hace falta pasar ninguna key. Si en el futuro se usa un backend LLM,
la key se pasa solo por entorno al runner local (por ejemplo
`-e OPENAI_API_KEY`) y jamás se escribe en el repo ni en los findings.

## Qué falta para el registro real

El formulario completo, prellenado salvo digest y credenciales, está en
[REGISTRO-REVIEWBENCH.md](REGISTRO-REVIEWBENCH.md). En síntesis, cuatro
compuertas en orden, cada una con el sí de Alejandro:

1. **A — Publicar la imagen en GHCR** con el workflow manual de
   `workflows/` y obtener el digest `sha256` (costo US$0; el código se
   hace público).
2. Registrar en el portal **por digest**, con las dos configuraciones A/B
   sobre el mismo registro (`governance=base|alma`, `backend=llm`,
   `model=gpt-5.6-sol`, `effort=medium`) y esperar el merge del mantenedor.
3. **B — Cargar la API key** en el portal (él o por bóveda segura, nunca
   por chat) y declarar `ALLOW_REAL_LLM=1` y `RB_MAX_SPEND_USD`.
4. **C — Test run puntuado de 25 PRs (A/B)** con tope de gasto nombrado
   (bandas: intermedia US$3–21; frontier US$15–105), y solo si se cumple
   la regla de avance del pre-registro, **D — corrida final 219 × 3**.

Hueco práctico que persiste: el portal está orientado a revisores con
modelo; las configuraciones LLM de arriba declaran URL y secreto, pero la
aceptación final la confirma el mantenedor al mergear el manifiesto.

## Estructura

```text
agent/       parser de diff, revisor base, puerta ALMA, adaptador LLM
             (fail-closed) y entrypoint
fixtures/    4 diffs sintéticos con defectos y falsos éxitos conocidos
tests/       24 tests unittest: parser, puerta, contrato, CLI, Dockerfile
             y adaptador LLM con HTTP mockeado
runs/        salidas de tests y de la simulación del entrypoint
workflows/   GitHub Actions manual para construir/publicar la imagen
             linux/amd64 en GHCR y emitir el digest (sin subir a ningún repo)
CONTRACT.md  contrato de ReviewBench extraído de la fuente primaria
PREREGISTRO-REVIEWBENCH.md
             hipótesis, métricas, costos y regla de autorización del A/B
             (+ adenda 2026-10-18 con la secuencia y las compuertas)
REGISTRO-REVIEWBENCH.md
             formulario del portal prellenado y compuertas de decisión
Dockerfile   imagen linux/amd64, entrypoint sin argumentos
```

## Límites honestos

- El revisor base es un sustituto determinista para validar mecanismo y
  contrato; no es competitivo como revisor de producción.
- La puerta mejora precisión solo si el base genera falsos positivos
  filtrables. No mejora el recall de defectos nunca propuestos.
- El puntaje real, la práctica puntuada del portal y la corrida completa
  siguen sin ejecutar: requieren los pasos y aprobaciones de arriba.
