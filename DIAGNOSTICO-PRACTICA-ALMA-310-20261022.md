# Diagnóstico — Práctica ALMA nº 310: rechazo de gate=v141 (2026-10-22)

**Costo del diagnóstico: US$0** (solo lectura de archivos locales; sin
portal, sin GitHub, sin llamadas a modelos). La corrida tampoco gastó:
murió antes de cualquier llamada al modelo (saldo US$25,58 → US$25,58).

## La causa en una frase

La imagen v2.3.1 trae **dos** resolvedores de `RB_CONFIG_GATE` que no se
conocen entre sí: el selector de `agent/main.py` SÍ admite `v141` (y de
hecho cargó la puerta 1.4.1), pero el resolvedor interno del revisor
v2.3 — `agent/llm_reviewer_v23.py::_resolve_gate_v23` — tiene su propia
lista de admisión, escrita cuando la puerta más nueva era la 1.4.0, que
termina en `v14` y **rechaza `v141`** antes de construir el prompt de
selección. La Adenda 1 agregó la rama `v141` al selector de `main.py` y
el paquete de la puerta, pero nadie agregó la rama espejo en el revisor.

## Evidencia de los outputs (runs/run-310-output.zip)

Texto exacto del error, idéntico en los 4 `prs/<pr>/agent.log` y citado
por `logs/preflight.txt` y `summary.txt`:

> `alma-reviewbench error: backend=llm v2.3 refused: unknown gate version 'v141'; expected 'v1', 'v11', 'v12', 'v13' or 'v14' (RB_CONFIG_GATE); no model call was made`

Y la línea de arranque del mismo `agent.log` prueba que la puerta 1.4.1
SÍ había sido seleccionada y cargada por `main.py` antes del rechazo:

> `alma-reviewbench requested_model=gpt-5.6-sol effort=medium effective_backend=llm governance=alma validator=alma-evidence-gate/1.4.1 policy_sha256=73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46`
> `config gate=v141` · `config governance=alma` · `config reviewer=v23`

El `policy_sha256=73a403d8…` es el hash adoptado de la puerta 1.4.1.
Los 4 shards murieron igual en su primer PR (`error:2`, 3 intentos c/u,
~182–183 s); 21 PRs nunca fueron alcanzados; `findings = null` en todos
(`logs/run-status.jsonl`).

## 1. ¿Quién rechaza v141? El contenedor — código nuestro en la imagen

El rechazo lo emite nuestro propio binario dentro del contenedor, no el
portal. Evidencia:

- `logs/preflight.txt` (texto del portal) lo atribuye explícitamente a la
  salida del agente: *«From the agent's output: alma-reviewbench error:
  …»* y recomienda *«Check the credentials and the configuration
  labels»* — el portal se limita a relayar el error y cortar por
  preflight.
- `logs/run-shard-1.log` muestra que el portal hizo su parte bien:
  descargó la imagen por el digest exacto
  (`sha256:144756ce…`, «Status: Downloaded newer image») e inyectó la
  config pedida: `config: RB_CONFIG_GATE=v141` junto a backend=llm,
  governance=alma, model=gpt-5.6-sol, effort=medium, reviewer=v23.
- El mensaje de error existe **verbatim** en el código local publicado:
  `agent/llm_reviewer_v23.py:255-256` —
  `f"backend=llm v2.3 refused: unknown gate version {gate_version!r}; "`
  `"expected 'v1', 'v11', 'v12', 'v13' or 'v14' (RB_CONFIG_GATE); "`.
  Ningún otro módulo produce ese texto con esa lista (los revisores
  v2/v2.1/v2.2 tienen listas más cortas, sin `v14`).

## 2. El mecanismo: dos resolvedores, uno actualizado y el otro no

**Resolvedor A — `agent/main.py::_select_gate` (líneas 67–105).**
Admite `v141` desde la Adenda 1: línea 100,
`if gate_version == "v141": return AlmaGateV141()`, y su propio mensaje
de error (líneas 102–105) ya lista
`'v1', 'v11', 'v12', 'v13', 'v14' or 'v141'`. Por eso el `agent.log`
imprimió `validator=alma-evidence-gate/1.4.1` con el hash adoptado:
este resolvedor funcionó.

**Resolvedor B — `agent/llm_reviewer_v23.py::_resolve_gate_v23`
(líneas 235–259).** El revisor v2.3 resuelve por su cuenta el mismo
`RB_CONFIG_GATE` para obtener (tipos de claim, guía de clases, versión)
con los que arma el prompt de selección; se invoca en
`llm_reviewer_v23.py:552`, en el camino común del backend llm. Sus ramas
son `v1`, `v11`, `v12`, `v13` y `v14` (línea 253: `v14` devuelve
`KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V14_VERSION` — las 19
clases de la 1.3.0, que la 1.4.0 hereda por delegación). No hay rama
`v141` ni importación de la 1.4.1 en este módulo (las importaciones de
versión son línea 116, `GATE_V13_VERSION`, y línea 120,
`GATE_V14_VERSION`). Ante `v141` levanta `RealLLMRefused` — rechazo
fail-closed, sin llamada al modelo, exactamente como se observó.

**Por qué la base nº 298 pasó con la misma imagen:** corrió con
`gate=v13`, valor presente en AMBOS resolvedores. El brazo base saltea
la puerta en `main.py`, pero el revisor igual pasa por el resolvedor B
para armar su prompt — con `v13` resolvió sin fricción. La nº 310 es la
primera corrida que le presenta `v141` al resolvedor B.

**¿Pudo la imagen construirse desde otro árbol? No.** El MANIFIESTO-V231
(líneas 41–42) asienta que la imagen salió del commit `cc56817`,
verificado 21/21 archivos byte a byte contra el remoto, y que el
Dockerfile hace `COPY agent /app/agent` — es decir, la imagen contiene
estos dos archivos tal como están en el árbol local. El comportamiento
observado lo confirma dos veces: el header imprimió la puerta 1.4.1 con
su hash (resolvedor A del árbol local) y el error es byte-idéntico al
del resolvedor B del árbol local. **El defecto está en el código
publicado, no en el build.**

**Por qué no lo cazó ninguna prueba:** los tests del paquete 1.4.1
(`tests/test_gate_v141.py`, §6: label `gate=v141`, módulo
`alma_gate_v141.py`) cubren la puerta y el selector de `main.py`; ningún
test ejercía `_resolve_gate_v23` con `v141`, y el semáforo v2.3 corrió
solo el brazo base (`gate=v13`). El hueco es exactamente la combinación
revisor-v2.3 × gate-v141, que solo el brazo ALMA usa.

## 3. Arreglo mínimo propuesto (NO ejecutado — solo diagnóstico)

Un solo archivo: `agent/llm_reviewer_v23.py`.

1. Importar la identidad de la 1.4.1 junto a las demás (al lado de la
   línea 120):
   `from .alma_gate_v141 import POLICY_VERSION as GATE_V141_VERSION`
   (siguiendo el patrón exacto de las líneas 116 y 120).
2. Agregar la rama espejo en `_resolve_gate_v23`, después de la de
   `v14` (línea 253):
   `if gate_version == "v141": return KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V141_VERSION`
   Las clases y la guía son las mismas que devuelve `v14`: la 1.4.1
   hereda las 19 clases de la 1.3.0 a través de la 1.4.0 — su único
   cambio, según su pre-registro (PREREGISTRO-PUERTA-141.md §2), es de
   ruteo *dentro de la puerta* (el chequeo (f) vuelve a ser rechazo
   firme), no del conjunto de clases ni del prompt de selección.
3. Actualizar la lista del mensaje de error del resolvedor B para
   incluir `'v141'` (cosmético pero evita el próximo diagnóstico
   engañoso), y la docstring del resolvedor.
4. Test que cierra el hueco: un caso que resuelva
   `_resolve_gate_v23` con `gate=v141` y fije que devuelve las 19 clases
   y la versión de la 1.4.1 — la combinación que ninguna prueba cubría.

**Clasificación: CABLEADO / ADMISIÓN (infraestructura), no la puerta.**
El arreglo no toca `agent/alma_gate_v141.py` — la puerta 1.4.1
congelada queda byte-idéntica, con su POLICY y su hash intactos — ni
`agent/main.py`, cuyo selector ya era correcto. Es completar en el
revisor la tabla de admisión que la Adenda 1 actualizó solo en la mitad
del sistema: un defecto de integración entre dos tablas que debían
espejarse, no un cambio de comportamiento de la puerta ni del revisor
(mismos prompts, mismas clases, mismo techo de 4.096).

## 4. ¿Exige republicar la imagen? Sí — del lado del portal no hay nada que arreglar

El revisor viaja dentro de la imagen (Dockerfile: `COPY agent
/app/agent`, `ENTRYPOINT ["python", "-m", "agent"]`), así que el
arreglo solo llega al examen con **imagen republicada (nuevo digest)** y
la actualización del campo de imagen en la config ALMA del portal. El
label `gate=v141` del portal ya es el correcto y no se toca; el portal
inyectó la config pedida y relayó el error fielmente — no hay
resolución posible de su lado.

## Lo que este diagnóstico NO hace

No ejecuta el arreglo, no republica la imagen, no reintenta la corrida.
La nº 310 queda FAILED por ausencia de medición (sin emisiones, la
regla de avance variante (ii) no es evaluable), y cualquier relanzamiento
del brazo ALMA requiere la imagen corregida y una decisión nueva,
asentada antes de lanzar como manda la disciplina del laboratorio.
