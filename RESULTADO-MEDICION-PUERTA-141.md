# Resultado — Medición de adopción de la puerta 1.4.1 (§4 del PREREGISTRO-PUERTA-141)

- **Fecha:** 2026-10-21 (construcción en seco, US$0, offline, sin llamadas a modelo).
- **Autorización:** Alejandro, 21/10/2026 21:49 EDT («Sí al papel 1.4.1 — construirla en seco»). Ese sí habilitó solo construcción en seco + medición offline.
- **Instrumento:** `medir_adopcion_v141.py` (este directorio), determinista, re-ejecutable (corrido dos veces, veredicto idéntico).
- **Construcción medida:** `agent/alma_gate_v141.py` — `POLICY_VERSION: alma-evidence-gate/1.4.1`, `POLICY_SHA256: 73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46`. Selección `RB_CONFIG_GATE=v141` en `agent/main.py`; el default del paquete no cambió.
- **El cambio (único, §2 del papel):** el chequeo (f) «sin línea agregada» salió de los chequeos de completitud que habilitan `needs_validation`. Un candidato de clase cuya evidencia citada no contiene ninguna línea agregada por el cambio es **rechazo firme** en la frontera, y ese rechazo **domina** sobre los chequeos de completitud (a)/(b). Los únicos habilitantes del tercer estado quedan (a) co-ocurrencia y (b) construcción fuera del span citado. Todo lo demás — delegación a la 1.3.0, registro sin `severity`, blockers, sección separada del ledger, extensión a hallazgos generales — se heredó de la 1.4.0 sin retoques.

## Veredicto: **ADOPTADA**

El criterio del §4 es conjuntivo y se cumplió entero:

1. **VP recuperados = 4 — los mismos 4** de la medición de la 1.4.0, identidad por identidad ✓.
2. **Falsos nuevos = 0 en los tres universos**, con S3 rechazado firme como causal (f), sin movimiento ✓.
3. **Equivalencia exacta de aceptados con la 1.3.0** en los tres universos ✓.
4. **Suite completa verde: 236/236** (208 heredadas + 28 nuevas de `tests/test_gate_v141.py`) ✓.

Y la precisión que el papel agregó: los únicos movimientos de estado de toda la medición son los 4 VP del universo 1; en los universos 2 y 3 el mapa de estados es **idéntico** al de la 1.3.0, candidato por candidato — ningún movimiento no explicado por el cambio (f).

## Universo 1 — candidatos asentados de los semáforos (38 candidatos)

- Primario (semáforo v2.1, `runs/semaforo-v21-20261021/`): 15 candidatos, VP = 2, falsos = 0.
- Secundario (semáforo v2 intento 3, `runs/semaforo-intento3/`): 23 candidatos, VP = 2, falsos = 0.
- **Sanidad: OK** — el re-juicio offline con la 1.3.0 reproduce exactamente los estados de los ledgers ALMA asentados (0 discrepancias).
- Los 4 VP son los mismos de la medición anterior: el candidato `sql_injection` de **sem_01** (cita de líneas 11–14 de `app/orders.py`), en ambos brazos de ambas corridas, retenido con el blocker `co_occurrence`. Su cita contiene líneas agregadas, así que el cambio (f) no lo toca: la reparación de enrutamiento no costó ni un verdadero.
- Ningún otro candidato asentado cambia de estado; los conjuntos aceptados coinciden exactamente.

## Universo 2 — batería roja de la 1.3.0 (69 ataques)

- **Movimientos de estado: 0.** Conjuntos aceptados: idénticos (los residuales declarados C3 y X2 siguen aceptados).
- **S3** (`sql_injection`, «cita una línea de CONTEXTO — el PR no introduce el defecto»): rechazado en la 1.3.0 → **rechazado en la 1.4.1, sin movimiento**, sin registro `needs_validation`, con el chequeo (f) asentado en sus razones de rechazo («cited evidence contains no line added by this change») como causal firme. Contraste asentado: bajo la 1.4.0 este mismo ataque era el único movimiento de la batería (rechazado → `needs_validation`, blocker `no_added_line`) y ese único falso bastó para la NO adopción de la 1.4.0.
- Falsos nuevos (U2) = **0**.

## Universo 3 — equivalencia (36 candidatos)

- Pares heredados (INHERITED_PAIRS, 8 clases × aceptar/rechazar) + candidatos del revisor mock (`BaseReviewer`) sobre los diffs de las 33 fixtures del paquete (`fixtures/`, `fixtures_v2/`, `fixtures_v11/`, `fixtures_v13/`, `fixtures_semaforo/`).
- Movimientos de estado: **0**. Conjuntos aceptados: idénticos.

## Tests del enrutamiento (f) (§4, por categoría)

`tests/test_gate_v141.py` (28 tests, todos verdes), por categoría:

- **(i) Tipo S3 → rechazo firme:** el ataque S3 de la batería (rechazado sin registro NV, causal (f) en las razones) y un caso de solo-(f) con soporte presente (cita de solo contexto de `tls_verification_disabled`, que la 1.4.0 retenía vía (c)): ambos rechazados.
- **(ii) Tipo VP → sigue `needs_validation`:** la forma de co-ocurrencia con líneas agregadas (blocker `co_occurrence`, sin rastro de `no_added_line` en la frontera de clase), el candidato asentado real de sem_01, y un caso (b) de JWT (`construction_outside_cited_span`).
- **(iii) Mixto (f)+(a) → rechazo firme por dominancia:** la misma forma de co-ocurrencia citada solo en líneas de contexto — la 1.4.0 la retenía con blockers `co_occurrence` + `no_added_line`; la 1.4.1 la rechaza.
- Heredados de la frontera: rechazo firme por antídoto, placeholder, marca ausente, clase desconocida, malformado, anclaje falso y duplicado de un aceptado; registro retenido sin `severity` en ninguna parte, fuera de findings y del ledger, determinista bit a bit; equivalencia de aceptación en pares heredados, fixtures y batería roja (con **cero** movimientos en la batería, caracterización nueva frente al único movimiento S3 de la 1.4.0); residuales C3/X2 aceptados.
- La extensión a hallazgos generales quedó **sin tocar** (declarado en el §2 del papel): retenida con `sin_regla_de_verificacion_en_puerta`, y la cita de solo contexto sigue agregando el blocker `no_added_line` en esa vía, con el registro idéntico al de la 1.4.0 salvo los sellos de identidad.

## Invariantes verificadas al cierre

- Puertas congeladas byte-idénticas (sha256 de archivo, re-verificado al cierre): 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`, 1.2.0 `c5c32bfc…`, 1.3.0 `d3b993d4…` y **1.4.0 `b16c5a79…`** — y sus POLICY_SHA256 asentados (1.4.0: `b0c0aa66…`). La 1.4.0 queda intacta como artefacto construido y medido; su NO adopción sigue asentada y este resultado no la corrige encima.
- Papeles intactos: `PREREGISTRO-PUERTA-141.md` 14.247 B, `PREREGISTRO-PUERTA-140.md` 14.521 B, `PREREGISTRO-REVIEWBENCH-V23.md` 28.717 B.
- Gasto: US$0. Sin portal, sin publicación, sin llamadas a modelo.

## Qué sigue (y qué no)

- **Adoptada ≠ en uso.** Conforme al §6 del papel, el uso de la 1.4.1 en el brazo ALMA de la v2.3 exige ANTES una adenda firmada al `PREREGISTRO-REVIEWBENCH-V23.md` que declare el reemplazo de la 1.4.0 por la 1.4.1 y la etiqueta `gate=v141`. Sin esa adenda, la 1.4.1 — adoptada — no se usa en el brazo ALMA. Esa adenda y cualquier corrida son decisiones separadas, fuera de esta construcción.
- La 1.4.1 no mejora detección: recupera exactamente los mismos 4 VP que la 1.4.0 y su emisión sigue siendo idéntica a la de la 1.3.0. Su único efecto es el enrutamiento: la sala de espera dejó de admitir defectos que el cambio bajo revisión no introduce.
