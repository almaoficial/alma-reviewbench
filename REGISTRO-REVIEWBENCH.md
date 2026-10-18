# Registro en ReviewBench — formulario prellenado

**Estado:** listo para cargar. Faltan solo el **digest** de la imagen
(compuerta A) y las **credenciales** (compuerta B). Nada de esto fue enviado.

**Fecha de preparación:** 2026-10-18. Contrato según
[CONTRACT.md](CONTRACT.md) (verificado en vivo el 2026-10-17) y experimento
según [PREREGISTRO-REVIEWBENCH.md](PREREGISTRO-REVIEWBENCH.md).

## Campos del portal

| Campo | Valor a cargar |
|---|---|
| Nombre visible del reviewer | `alma-reviewer` |
| Email de contacto | **A CONFIRMAR** por Alejandro antes de enviar (el portal lo pide; no se carga ningún email sin su palabra) |
| Imagen (digest) | `ghcr.io/almaoficial/alma-reviewbench@sha256:<DIGEST>` — **PENDIENTE**: sale del run manual del workflow `reviewbench-image` (ver `workflows/README.md`) |
| Visibilidad de la imagen | Pública (GHCR público: el portal tira sin credencial) |
| URL de API del modelo | `https://api.openai.com/v1` — **a confirmar en la compuerta B** según el proveedor de la key que se cargue (si la key no es de OpenAI, esta URL cambia y su host queda auto-autorizado en el egress) |
| Secretos / credenciales a declarar | Ver sección «Credenciales» — solo **nombres**, jamás valores por chat |
| Timeout por PR (segundos) | **En blanco** = default del portal: 1800 s (máximo permitido: 3600) |

## Configuraciones (labels) — el A/B sobre un mismo registro

Agregar una configuración nueva no requiere aprobación nueva: las dos van
sobre el mismo reviewer y el mismo digest. La única diferencia entre brazos
es `governance`, como manda el pre-registro.

**Configuración BASE:**

```text
governance=base
backend=llm
model=gpt-5.6-sol
effort=medium
```

**Configuración ALMA:**

```text
governance=alma
backend=llm
model=gpt-5.6-sol
effort=medium
```

(`model=gpt-5.6-sol` y `effort=medium` son los valores que Alejandro tipeó
en su captura del portal el 2026-10-17. Llegan al contenedor como
`RB_CONFIG_MODEL` / `RB_CONFIG_EFFORT` / `RB_CONFIG_GOVERNANCE` /
`RB_CONFIG_BACKEND`.)

Configuración opcional de referencia, solo para validación de formato con
`try-agent.sh` en local (no necesita key ni URL de modelo):

```text
governance=alma
backend=mock
model=deterministic-rules
effort=local
```

## Credenciales (compuerta B — nombres y mecanismo, sin valores)

El portal entrega las credenciales declaradas como variables de entorno al
contenedor, solo durante la corrida. Hay que declarar tres nombres:

| Nombre | Valor | Quién lo carga |
|---|---|---|
| `OPENAI_API_KEY` | La key del proveedor elegido | Alejandro, en el portal o por la bóveda segura — **nunca por chat** |
| `ALLOW_REAL_LLM` | `1` | Se declara como credencial de entorno: es el flag que arma el adaptador (sin él, `backend=llm` se niega a llamar, verificado por tests) |
| `RB_MAX_SPEND_USD` | El tope de gasto por PR aprobado en la compuerta C (p. ej. `5.00`) | Se declara junto con la key; sin este tope el adaptador también se niega a llamar |

Opcionales, para que el control de gasto use las tarifas reales del modelo
elegido en vez de la banda frontier conservadora por defecto (US$15/M
entrada, US$75/M salida): `RB_PRICE_INPUT_PER_MTOK_USD`,
`RB_PRICE_OUTPUT_PER_MTOK_USD`. Se fijan en la adenda de calibración del
pre-registro, antes de la compuerta C.

## Egress a declarar

- `api.openai.com:443` — host del modelo (el contrato lo autoriza
  automáticamente al declarar la URL del modelo; si el proveedor cambia,
  cambia este host).
- **Ningún otro host.** El agente no necesita nada más: sin búsqueda web y
  sin conectores que puedan leer respuestas del PR (regla del
  pre-registro). La descarga de la imagen desde GHCR la hace el runner, no
  el contenedor.

## Qué pasa al enviar

Registrar abre un PR con el manifiesto en `review-bench/ReviewBench`; el
merge de un mantenedor es la aprobación (referencia del contrato: ~1 día
hábil). Recién con el registro aprobado se habilita el test run puntuado
de 25 PRs.

## Compuertas de decisión (en orden — ninguna se salta)

- **A) Publicar la imagen en GHCR.** Aprobar que el código del adaptador se
  haga público en `ghcr.io/almaoficial/alma-reviewbench` y disparar a mano
  el workflow `reviewbench-image` (manual, `workflow_dispatch`). Costo:
  **US$0** de plataforma. Producto: el digest para el campo de arriba.
- **B) Cargar la API key en el portal.** La carga Alejandro (o por bóveda
  segura; nunca por chat) y se declaran `ALLOW_REAL_LLM=1` y
  `RB_MAX_SPEND_USD`. Costo directo: **US$0**; es la compuerta que habilita
  gasto, por eso va separada de la corrida.
- **C) Corrida de práctica puntuada, 25 PRs, A/B (base + ALMA).** Exige el
  sí con modelo, brazos, set, timeout (1800) y **tope de gasto nombrado**.
  Bandas del pre-registro para los dos brazos juntos: intermedia
  **US$3,00–21,00**; frontier **US$15,00–105,00**. Sugerencia de tope a
  nombrar si el modelo es clase frontier: **US$40** (cubre el escenario
  típico A/B ≈ US$37,50; el escenario largo se corta contra el tope por
  PR). Sin las tres condiciones de avance del pre-registro, no hay D.
- **D) Corrida final, 219 PRs × 3 rondas, A/B.** Solo si la práctica cumple
  la regla de avance (F1 ALMA ≥ base, precisión +0,05, recall no cae más
  de 0,03). Bandas para los dos brazos juntos: intermedia
  **US$78,84–551,88**; frontier **US$394,20–2.759,40**. Tope único a
  nombrar tras la calibración de la práctica, no antes.
