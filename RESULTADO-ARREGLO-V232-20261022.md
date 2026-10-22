# Resultado — Arreglo v2.3.2: la admisión de `gate=v141` en el revisor (2026-10-22)

**Costo: US$0** — todo en seco, con transportes guionados; sin
portal, sin corridas, sin llamadas a modelos. Autorización:
Alejandro, 2026-10-22 07:37 EDT («Lo hagamos»), asentada ANTES de
tocar el código en la **Adenda 4** del papel v2.3 (el papel pasó
de 59.330 B a **65.828 B**; cuerpo y Adendas 1–3 byte-intactos).
Diagnóstico que lo motiva: `DIAGNOSTICO-PRACTICA-ALMA-310-20261022.md`
— la práctica ALMA nº 310 murió en admisión (run-agent 4,4, costo
real US$0,00, cero llamadas) porque la imagen trae dos resolvedores
de `RB_CONFIG_GATE` no espejados: `main.py` admite `v141` y cargó
la puerta 1.4.1, pero `_resolve_gate_v23` en el revisor tenía su
propia lista que terminaba en `v14`.

## Qué cambió — un solo archivo de código

`agent/llm_reviewer_v23.py` (sha256 del archivo: `55cba627…` →
`a78bdd6d…`):

1. **Importación** junto a las existentes:
   `from .alma_gate_v141 import POLICY_VERSION as GATE_V141_VERSION`.
2. **Rama espejo en `_resolve_gate_v23`**, tras la de `v14`:
   `gate=v141` devuelve `(KNOWN_CLAIM_TYPES_V13, _CLASS_GUIDANCE_V13, GATE_V141_VERSION)`
   — las 19 clases y la guía de la 1.3.0, que la 1.4.1 hereda a
   través de la 1.4.0, con la identidad de la 1.4.1. Su único
   cambio respecto de `v14` es esa identidad: el ruteo distinto
   vive dentro de la puerta, no en el prompt de selección.
3. **Mensaje de error** del resolvedor: la lista de esperados pasa
   a «'v1', 'v11', 'v12', 'v13', 'v14' or 'v141'»; la docstring del
   resolvedor declara la herencia de clases de la 1.4.1.
4. **`REVIEWER_VERSION = "llm-reviewer/2.3.2"`** (era 2.3.1) y un
   párrafo «Fix v2.3.2» en la docstring del módulo, en el estilo
   de la casa.

Tests: archivo nuevo `tests/test_llm_reviewer_v232.py` (4 tests)
que fija la combinación que ninguna prueba cubría — revisor v2.3 ×
gate=v141: la resolución directa devuelve las 19 clases con
`GATE_V141_VERSION`; `v13`/`v14` resuelven como antes; un gate
desconocido sigue rechazando fail-closed y el mensaje lista
`'v141'`; y el revisor se construye entero con la config ALMA
`v141` (`gate_version = alma-evidence-gate/1.4.1`). Además, tres
aser­ciones existentes que fijan la constante vigente en el
run-info asentado se movieron con el bump (`llm-reviewer/2.3.1` →
`2.3.2`): `tests/test_llm_reviewer_v23.py` (×2) y
`tests/test_llm_reviewer_v231.py` (×1) — fijan la versión actual
del revisor, no un comportamiento histórico.

## Verificación

- **Suite completa: 249/249 OK** (`python3 -m unittest discover -s tests`)
  = 245 previas + 4 nuevas, cero fallos.
- **Batería semáforo: 16/16** — el test de batería corre dentro de
  la suite (`BatteryDryRunTests.test_battery_16_of_16_without_refusals`,
  OK en corrida individual también), sin regresiones.
- **Puertas congeladas byte-idénticas** (sha256 de archivo, antes
  = después): 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`, 1.2.0
  `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0 `b16c5a79…`, 1.4.1
  `08d813e9…`; la POLICY de la 1.4.1 recomputada sigue
  **`73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46`**.
- **`agent/main.py` sin cambios** (sha256 `9ac76b6f…`, antes =
  después). El único archivo de `agent/` que cambió es
  `llm_reviewer_v23.py`.

## Qué sigue (fuera de este resultado)

La reparación solo llega al examen con **imagen republicada
(digest nuevo)**: manifiesto en `MANIFIESTO-V232.md`. Con la
imagen publicada, el agente principal actualiza SOLO el campo de
imagen de la config ALMA del portal y relanza — compuerta
vinculante de la Adenda 4: saldo ≥ US$25 verificado en el acto
(US$25,58 al 22/10 07:33 EDT); falsador de la reparación: si la
relanzada muere con la misma firma («unknown gate version
'v141'»), la línea se detiene sin tercer intento.
