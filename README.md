# ALMA para ReviewBench — paquete mock-first

Este directorio contiene un adaptador local **US$0 por defecto** para
probar a ALMA como capa de gobernanza sobre un revisor de código de
ReviewBench, el benchmark público de GitHub para agentes de code review.

**Estado al 2026-10-19 (v1 CERRADA):** el agente `alma-reviewer` fue
registrado y **aprobado** — el mantenedor fusionó el PR #89 el 2026-10-19 —
y la imagen se publicó en GHCR por digest
(`ghcr.io/almaoficial/alma-reviewbench@sha256:14a4bb3ed9b3f83bbdb7947fc1cba949cece2cb0f97c1d9cc8b22ca0fd6d5d3b`).
La práctica puntuada del portal (set privado de 25 PRs) ya se corrió contra
el modelo real, con el sobre completo en
[MANIFIESTO-CORRIDA.md](MANIFIESTO-CORRIDA.md):

- **Brazo base (corrida #251):** grounded **F1 1,4%** · precisión 42,9% ·
  recall 0,7% (augmented F1 4,4%); 14 findings, 5 novel.
- **Brazo ALMA (corrida #253):** el agente completó 25/25 PRs y la puerta
  emitió **1 finding**; la plataforma falló en su propio paso de puntaje
  (score / Summarise) y no produjo nota oficial.

**Veredicto v1:** la regla de avance pre-registrada (F1 ALMA ≥ base,
precisión ALMA ≥ base + 0,05, recall ALMA no cae más de 0,03) **no se
cumplió** → la corrida final de 219 × 3 **no se abre**. Sigue el
pre-registro v2 (`PREREGISTRO-REVIEWBENCH-V2.md`), en curso. El paquete
local sigue siendo US$0 por defecto (mock-first) y el backend LLM sigue
siendo fail-closed fuera del portal.

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
  llamada. Está probado offline con HTTP mockeado (`tests/test_llm_adapter.py`)
  y corrió contra el modelo real por primera vez el 2026-10-19, en la
  práctica puntuada del portal (corridas #251 y #253; ver el manifiesto).

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
tampoco podman/buildah/nerdctl/kaniko), así que la imagen **no** se
construyó localmente; el Dockerfile está cubierto por test estático y
el entrypoint sin argumentos se validó contra los 4 fixtures en ambos
brazos, con salida `$RB_OUT` conforme al contrato (evidencia en
`runs/entrypoint-sim-output.txt`). La construcción real se hizo por
GitHub Actions: `workflows/reviewbench-image.yml` (solo disparo manual)
construyó `linux/amd64` y publicó en GHCR — la corrida nº 2 del workflow
(2026-10-19, SUCCESS) emitió el digest vigente,
`ghcr.io/almaoficial/alma-reviewbench@sha256:14a4bb3ed9b3f83bbdb7947fc1cba949cece2cb0f97c1d9cc8b22ca0fd6d5d3b`
(la nº 1 había publicado el digest anterior, reemplazado tras corregir el
payload del agente) — ver `workflows/README.md`. Esa imagen es la que el
portal ejecutó en la práctica puntuada (#251 y #253), que es la validación
de punta a punta asentada en el manifiesto. La validación local con el
runner oficial, desde un clon de `review-bench/ReviewBench`, sigue siendo:

```bash
scripts/try-agent.sh ghcr.io/almaoficial/alma-reviewbench:dev --pr 0
```

Ese script valida formato sobre el set de 25 PRs y no puntúa. Con el backend
mock no hace falta pasar ninguna key. Si en el futuro se usa un backend LLM,
la key se pasa solo por entorno al runner local (por ejemplo
`-e OPENAI_API_KEY`) y jamás se escribe en el repo ni en los findings.

## Estado de las compuertas

El formulario completo está en
[REGISTRO-REVIEWBENCH.md](REGISTRO-REVIEWBENCH.md) y el sobre de la
corrida en [MANIFIESTO-CORRIDA.md](MANIFIESTO-CORRIDA.md). Las cuatro
compuertas, en el orden en que se cruzaron (cada una con el sí de
Alejandro):

1. **A — Imagen publicada en GHCR** ✓ (workflow manual de `workflows/`;
   digest vigente emitido por la corrida nº 2, 2026-10-19).
2. **Registro aprobado** ✓ — el portal registró por digest las dos
   configuraciones A/B sobre el mismo registro (`governance=base|alma`,
   `backend=llm`, `model=gpt-5.6-sol`, `effort=medium`) y el mantenedor
   fusionó el PR #89 el 2026-10-19.
3. **B y C — Credenciales cargadas y práctica puntuada corrida** ✓
   (2026-10-19): brazo base #251 con nota oficial (grounded F1 1,4%);
   brazo ALMA #253 con el agente completo y sin nota oficial por una
   falla de la plataforma en su paso de puntaje.
4. **D — Corrida final 219 × 3: NO se abre.** La regla de avance del
   pre-registro no se cumplió; relanzar la misma corrida está prohibido
   por la propia declaración anti-pesca del experimento. Lo que sigue es
   el pre-registro v2 (`PREREGISTRO-REVIEWBENCH-V2.md`): revisor por
   clases verificables con contexto completo, misma puerta congelada.

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
- La práctica puntuada ya se ejecutó (2026-10-19) y su puntaje es el de
  arriba: bajo en el brazo base (grounded F1 1,4%) y sin nota oficial en
  el brazo ALMA por la falla de puntaje de la plataforma. La corrida
  completa (219 × 3) no se ejecutó ni quedó autorizada: la regla de
  avance no se cumplió, y ese no es un trámite pendiente sino el
  veredicto de la v1.
