# Contrato de ReviewBench — fuente primaria verificada

**Fecha de verificación:** 2026-10-17. Este resumen se ajusta al contrato en
vivo informado desde el portal y a la documentación pública enlazada por
ReviewBench. En caso de conflicto, manda el contrato en vivo.

Fuentes oficiales:

- Portal: https://review-bench.ai
- Contrato del agente: https://github.com/review-bench/ReviewBench/blob/main/AGENT_CONTRACT.md
- Runner local: https://github.com/review-bench/ReviewBench/blob/main/docs/RUNNER.md
- Onboarding: https://github.com/review-bench/ReviewBench/blob/main/docs/ONBOARDING.md
- Evaluación offline: https://github.com/review-bench/ReviewBench/blob/main/docs/OFFLINE_EVAL.md
- Metodología: https://review-bench.ai/methodology

## Ejecución

- Un contenedor fresco por PR, plataforma `linux/amd64`, sin argumentos.
  El `ENTRYPOINT` o `CMD` debe arrancar el adaptador.
- Runner estándar de GitHub, sin GPU. La red sale solo por proxy HTTPS a los
  hosts declarados en el manifiesto (`egress`); el host de la URL del modelo
  se autoriza automáticamente.
- Montajes:
  - `/work/repo`: checkout en el commit head, con `.git`.
  - `/work/pr/diff.patch`: diff three-dot `base...head`.
  - `/work/pr/pr.json`: `{repo, pr_number, base, head, nwo, title, body}`.
  - `/work/out`: directorio de salida montado por el runner.
- Variables de entorno:
  - `RB_NWO`, `RB_PR_NUMBER`, `RB_BASE`, `RB_HEAD`.
  - `RB_AGENT`: nombre registrado; debe usarse como `agent` y `producer`.
  - `RB_DIFF=/work/pr/diff.patch`, `RB_PR_JSON=/work/pr/pr.json`,
    `RB_OUT=/work/out/findings.json`.
  - `RB_MODEL_BASE_URL` si se registró una URL de modelo.
  - `RB_ATTEMPT` cuando hay reintento.
  - `RB_CONFIG_<KEY>` por cada label de configuración: la key pasa a
    mayúsculas y todo carácter no alfanumérico se convierte en `_`.
- Las credenciales declaradas llegan como variables de entorno y/o archivos.
- Límite de tiempo: 1800 segundos por PR por defecto; máximo 3600.

## Salida obligatoria

Un único JSON en `$RB_OUT` con este esquema exacto:

```json
{
  "pr": {
    "repo": "https://github.com/owner/repo",
    "pr_number": 1938,
    "base": "<sha completo>",
    "head": "<sha completo>"
  },
  "agent": "nombre-registrado",
  "findings": [
    {
      "file": "src/pool.ts",
      "start_line": 42,
      "end_line": 45,
      "message": "Qué está mal y por qué",
      "producer": "nombre-registrado"
    }
  ]
}
```

Reglas:

- `pr.head` debe ser exactamente `RB_HEAD` y `pr.pr_number` debe ser
  exactamente `RB_PR_NUMBER`; si no, ese PR falla.
- `file` es relativo al repo, con `/`, sin `./` inicial.
- Las líneas se refieren al archivo en `RB_HEAD`; para una línea,
  `start_line == end_line`.
- Una entrada por problema lógico, cubriendo su rango completo.
- `message` debe decir qué está mal y por qué; el juez lo compara con los
  findings expertos.
- Exit 0 con JSON válido = aceptado. `findings: []` también = aceptado.
- Exit no-cero, archivo ausente, JSON inválido o identidad del PR incorrecta
  = PR fallido; hay reintento y después puede caer la corrida completa.
- **El agente no emite `severity` ni `category`.** Esos labels los asigna el
  clasificador/juez de ReviewBench. Las categorías públicas incluyen
  correctness, security, reliability, maintainability y testing; las
  severidades se cortan como critical/medium/low en el sitio y
  high/medium/low en la metodología.

## Imagen y registro

- La imagen vive en `ghcr.io` y se registra por **digest**
  `ghcr.io/<owner>/<image>@sha256:<64 hex>`, nunca por tag.
- Pública por defecto: se puede tirar sin credencial. Si es privada, el
  registro declara `GHCR_PULL_TOKEN`, un token clásico de GitHub con el único
  scope `read:packages`.
- El formulario pide nombre visible, email de contacto, digest, labels de
  configuración (por ejemplo `model`, `effort`), URL de API del modelo,
  nombres de secretos y timeout opcional por PR.
- Registrar abre un PR con el manifiesto en `review-bench/ReviewBench`; el
  merge de un mantenedor es la aprobación humana (referencia: ~1 día hábil).
- Agregar una configuración nueva (otro digest y labels) no requiere una
  aprobación nueva. Esto habilita el A/B base vs. ALMA sobre el mismo registro.

## Práctica y corridas

- `scripts/try-agent.sh <image> [--set test|full] [--pr <index>] [-e NAME[=VALUE]...]`
  corre localmente el set de prueba (25 PRs por defecto), monta cada PR como
  el benchmark y valida el formato de findings, pero **no puntúa**.
- No hay práctica con un backend de modelo sin la key propia de ese modelo.
  El backend mock determinista de este paquete no necesita key ni red.
- El test run del portal también usa 25 PRs, sí puntúa y exige registro previo.
- La corrida final son 3 rondas sobre los 219 PRs.
- El sitio no cobra fee: el costo del participante es su propia inferencia.

## Huecos que el contrato público no cierra

1. Si el portal acepta sin fricción un revisor determinista sin URL de modelo
   ni secreto: el contrato admite agentes no-GPU y credenciales declaradas,
   pero la UI de registro está orientada a un modelo. Confirmar al registrar.
2. La concurrencia y el wall-clock total de las corridas del portal no están
   publicados; solo está acotado el tiempo por PR.
3. El costo real por PR depende del modelo, el tamaño de contexto y los
   reintentos; por eso el pre-registro usa escenarios y exige una calibración
   aprobada antes de cualquier corrida paga.
4. El contrato manda el archivo de findings; no promete tolerar archivos
   extra en `/work/out`. Por eso el ledger de ALMA queda apagado por defecto
   en corridas del portal y se activa solo con `RB_ALMA_LEDGER=1` o una ruta
   explícita local.
