# Resultado — Arreglo v2.3.1 del revisor (construcción en seco)

**Veredicto: CONSTRUIDO EN SECO, suite completa en verde, US$0** —
sin llamadas a OpenAI, sin portal, sin publicar. Alejandro aprobó la
reparación el 2026-10-21 («Bueno lo hagamos») y la Adenda 2 al papel
v2.3 la pre-registró (firmada 23:20 EDT): dos piezas, nada más, contra
la causa (d) que mató la práctica nº 296
(`DIAGNOSTICO-PRACTICA-V23-20261021.md`).

## 1. Qué cambió, dónde

Todo en `agent/llm_reviewer_v23.py` (sha256 del módulo:
`ce13389b…` → `55cba627…`). La construcción corregida se declara
`llm-reviewer/2.3.1` (`REVIEWER_VERSION`); la etiqueta `reviewer`
del portal no cambia (`v23`, Adenda 2).

**(i) Techo de completion de la selección: 1.024 → 4.096 tokens.**
`DEFAULT_TRIAGE_MAX_OUTPUT_TOKENS = 4096`, por la vía de
configuración que ya existía (`RB_LLM_V23_TRIAGE_MAX_OUTPUT_TOKENS`
/ `RB_CONFIG_TRIAGE_MAX_OUTPUT_TOKENS`). 4.096 es el techo que las
pasadas profundas ya usaban (`LLMSettings.max_output_tokens`,
default 4096) — **las profundas no se tocaron**. El comportamiento
medido v2.3.0 queda **reproducible por configuración**: fijar el
techo en 1024 por cualquiera de las dos vías restaura exactamente
el presupuesto bajo el que murió la nº 296 (fijado por test, §3).

**(ii) Observabilidad de parseos fallidos.** `_call` ahora devuelve
también el `finish_reason` de la respuesta. Cuando el contenido de
**cualquier** pasada (selección, profunda o fallback) no parsea o
vuelve vacío, antes de cerrar en falso el revisor asienta en el
run-info un registro `parse_failures` — `{pass, finish_reason,
content_length, content_excerpt}` con el extracto acotado a 500
caracteres — y el mensaje de la negativa lleva los mismos datos
apéndice (el texto original queda como prefijo, para que los
contrastes de logs construidos sobre él sigan funcionando), de modo
que también llega al `agent.log`, que en una negativa solo imprime
la excepción. El run-info asienta además `triage_max_output_tokens`
(el techo en vigor de la corrida). **El fail-closed no se movió:**
una respuesta no parseable sigue emitiendo cero hallazgos y
saliendo con error — ahora, con la causa a la vista. La próxima
muerte en esta etapa se lee; no se infiere.

## 2. Peor caso re-derivado (aritmética del propio revisor)

Precios de planificación 15/75 por Mtok, método `_pad_until` de los
tests de construcción (dif ancla = 41.160 tokens estimados;
saturado = 60.000). Con el techo viejo el método reproduce exacto
las cifras de construcción de la v2.3 (ancla 5,4250; saturado
7,2524), así que la comparación es sobre la misma regla:

| Cantidad (US$) | Techo 1.024 (v2.3.0) | Techo 4.096 (v2.3.1) |
|---|---|---|
| Selección, piso (solo el prompt) | 0,1111 | 0,3415 |
| Selección, dif ancla | 0,7349 | 0,9653 |
| Profunda, ancla (sin cambios) | 0,9380 | 0,9380 |
| **Plan ancla (selección + 5 profundas)** | 5,4250 | **5,6554 < 6,50** |
| Selección, saturado | 1,0023 | 1,2327 |
| Profunda, saturado (sin cambios) | 1,2500 | 1,2500 |
| Saturado con 5 profundas | 7,2524 | 7,4828 |
| **Profundas admitidas en saturado** | **4** (total 6,0024) | **4** (total 6,2328 < 6,50) |

El delta es exactamente **+US$0,2304 por PR** = 3.072 tokens de
salida × US$75/Mtok (fijado por test). **El plan ancla entra entero
bajo el freno de US$6,50** (las 5 profundas), y en el saturado **la
regla de degradación heredada absorbe la diferencia**: siguen
entrando 4 profundas y la 5ª se declara — el margen de las 4
(US$0,4976 bajo el techo viejo) era mayor que el delta.

**Nota de reconciliación (dos versiones, ninguna pisada):** la
Adenda 2 asentó para esta misma etapa «plan ancla ≈US$5,33»,
«saturado ≈US$7,13» y «selección + 4 profundas ≈US$5,82». Esas
cifras no se reproducen con la aritmética del código (la de esta
tabla, que sí reproduce las cifras de construcción de la v2.3);
son ~US$0,3 más bajas en los tres casos. Las **conclusiones
coinciden** — el ancla entra entero y el saturado admite 4 — pero
la aritmética operativa es la del código: para cualquier decisión
de freno valen 5,6554 / 7,4828 / 6,2328.

## 3. Pruebas

- **Suite completa: 245/245 en verde** (236 heredadas + 9 nuevas),
  `python3 -m unittest discover -s tests`. El autochequeo en seco
  sobre la batería del semáforo va dentro de la suite
  (`BatteryDryRunTests`): **16/16 sin negativas ni degradación**,
  como la v2.3.
- **Tests nuevos** (`tests/test_llm_reviewer_v231.py`, 9): el techo
  nuevo es el default y aplica **solo** a la selección (la profunda
  conserva el suyo); el presupuesto medido v2.3.0 (1024) se
  reproduce por pin de entorno y por pin de config; el delta de
  peor caso es exactamente US$0,2304; una selección truncada con
  `finish_reason="length"` asienta el registro completo (pasada,
  finish_reason, longitud, extracto) y el mensaje de la negativa lo
  lleva, con el fail-closed intacto; una selección vacía asienta
  igual (longitud 0); el extracto se acota a 500 caracteres; una
  profunda no parseable asienta su registro con su nombre de pasada
  y sigue cerrando en falso; una corrida exitosa asienta
  `triage_max_output_tokens=4096` y `parse_failures=[]`.
- **Aserciones actualizadas en `tests/test_llm_reviewer_v23.py`**
  (las que fijaban el comportamiento corregido; ninguna otra):
  `reviewer_version` → `llm-reviewer/2.3.1` (×2); el pin del payload
  de selección 1024 → 4096; la cota del peor caso de la selección
  ancla 0,80 → banda 0,90–1,00 (el valor re-derivado es 0,9653); y
  el escenario `no_deep_pass_affordable` reporta ahora una
  selección que usó su presupuesto (completion 4.000,
  `HeavySelectionTransport`) — con los techos igualados, un tope
  calculado sobre el peor caso de la selección admitiría una
  profunda chica si el costo *reportado* de la selección fuera
  mínimo, porque la admisión corre sobre el costo reportado; la
  declaración bajo prueba (`no_deep_pass_affordable`, cero
  emitidos) no cambió. La aserción del saturado (4 admitidas) no
  necesitó cambios: se sostiene con el techo nuevo.

## 4. Invariantes verificados al cierre

- Puertas congeladas **byte-idénticas** (sha256 de archivo,
  antes/después): 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`, 1.2.0
  `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0 `b16c5a79…`, 1.4.1
  `08d813e9…` — sin diferencia.
- Papeles intactos; `agent/main.py` sin tocar; ningún otro módulo
  del revisor modificado (v1/v2/v2.1/v2.2 reproducibles).
- Sin gasto (US$0), sin portal, sin publicación, sin llamadas.

## 5. Qué sigue (fuera de esta construcción, según la Adenda 2)

Sonda previa obligatoria (solo la selección arreglada, sobre los 5
PRs que murieron 3/3 en la nº 296; éxito = JSON parseable en todos;
tope duro US$8) — paso con gasto, separado, con su compuerta de
saldo (el saldo asentado es US$3,02: requiere carga previa de
Alejandro). Después, publicación de la imagen corregida y práctica
relanzada, en la secuencia de la adenda. El falsador de la adenda
queda en pie: si la práctica relanzada muere con la misma firma, la
hipótesis del techo cae y la línea se detiene sin tercer intento
automático.

— Construcción en seco, 2026-10-21. Fuentes: `DIAGNOSTICO-
PRACTICA-V23-20261021.md` (§5–§6), Adenda 2 en
`PREREGISTRO-REVIEWBENCH-V23.md`, `agent/llm_reviewer_v23.py`
(antes `ce13389b…`, después `55cba627…`), suite 245/245.
