# Resultado — Medición de adopción de la puerta 1.4.0 (§6 del PREREGISTRO-PUERTA-140)

- **Fecha:** 2026-10-21 (construcción en seco, US$0, offline, sin llamadas a modelo).
- **Instrumento:** `medir_adopcion_v14.py` (este directorio), determinista, re-ejecutable.
- **Construcción medida:** `agent/alma_gate_v14.py` — `POLICY_VERSION: alma-evidence-gate/1.4.0`, `POLICY_SHA256: b0c0aa661f644b5229ea3ee1984b3fd2dbb17649d1eeae91e5945fd357fd6d19`.
- **Criterio (escrito antes de medir, §6):** se adopta SI Y SOLO SI VP recuperados ≥ 1 Y falsos nuevos = 0 Y equivalencia exacta de aceptados en los tres universos Y la suite previa sigue verde con los tests nuevos en verde.

## Veredicto: **NO ADOPTADA**

VP recuperados = **4** (≥ 1 ✓) · Equivalencia de aceptados = **exacta en los tres universos** (✓) · Suite = **208/208 verde** (163 heredadas + 45 nuevas) (✓) · **Falsos nuevos = 1 (≠ 0 ✗)**.

El criterio es conjuntivo: un solo falso nuevo basta. La 1.4.0 queda construida y medida, pero **no adoptada**: conforme al §4 del PREREGISTRO-REVIEWBENCH-V23, el brazo ALMA de la v2.3 **no corre** con ella y **no hay sustitución silenciosa por la 1.3.0**. Cualquier cambio de frontera (p. ej. excluir los movimientos por solo-(f)) es papel nuevo y medición nueva: este resultado no se re-afina.

## Universo 1 — candidatos asentados de los semáforos (38 candidatos)

- Primario (semáforo v2.1, `runs/semaforo-v21-20261021/`): 15 candidatos, VP = 2, falsos = 0.
- Secundario (semáforo v2 intento 3, `runs/semaforo-intento3/`): 23 candidatos, VP = 2, falsos = 0.
- **Sanidad: OK** — el re-juicio offline con la 1.3.0 reproduce exactamente los estados de los ledgers ALMA asentados (0 discrepancias).
- Los 4 VP son el mismo defecto conocido: el candidato `sql_injection` de **sem_01** (cita de líneas 11–14 de `app/orders.py`: esqueleto y construcción en la misma sentencia, en líneas citadas distintas), rechazado por la 1.3.0 en ambos brazos de ambas corridas y retenido por la 1.4.0 con el blocker `co_occurrence`. La hipótesis §2(1) del papel se confirma: el tercer estado recupera el VP que la binaria perdía tres corridas seguidas.
- Ningún otro candidato asentado cambia de estado; los conjuntos aceptados coinciden exactamente.

## Universo 2 — batería roja de la 1.3.0 (69 ataques)

- Conjuntos aceptados: idénticos (los residuales declarados C3 y X2 siguen aceptados; ningún ataque pasa a aceptado).
- **Un solo movimiento de estado: S3** (`sql_injection`, «cita una línea de CONTEXTO — el PR no introduce el defecto»): rechazado → `needs_validation`, blocker `no_added_line`.
- Por qué mueve: el candidato de S3 cita líneas de contexto donde esqueleto y construcción SQL **sí co-ocurren en la misma línea citada** — el chequeo de soporte de la 1.3.0 pasa — y el ÚNICO chequeo que falla es el (f) de la Adenda 2 («sin línea agregada»). La §3(5)(c) del papel incluye ese chequeo entre los de completitud que habilitan el tercer estado; aplicado tal cual está escrito, S3 entra en la sala de espera. Y la §6 cuenta **cualquier** ataque que se mueva de estado como falso nuevo. Las dos secciones, leídas literalmente, producen este resultado: la frontera tal como fue pre-registrada deja pasar exactamente un falso a la sala de espera — una inyección real pero preexistente, que el PR no introduce.
- falsos nuevos (U2) = **1**.

## Universo 3 — equivalencia (36 candidatos)

- Pares heredados (INHERITED_PAIRS, 8 clases × aceptar/rechazar) + candidatos del revisor mock (`BaseReviewer`) sobre los diffs de las 33 fixtures del paquete (`fixtures/`, `fixtures_v2/`, `fixtures_v11/`, `fixtures_v13/`, `fixtures_semaforo/`).
- Movimientos de estado: **0**. Conjuntos aceptados: idénticos.

## Qué queda en pie y qué no

- La construcción de la 1.4.0 es fiel al papel: delegación a la 1.3.0, frontera mecánica de 5 condiciones, registro sin severidad con blockers y requisito por blocker, extensión a hallazgos generales por el papel v2.3 (blocker `sin_regla_de_verificacion_en_puerta`). Las puertas 1.0.0–1.3.0 quedaron byte-idénticas (verificado por hash de archivo y POLICY_SHA256 al cierre de la construcción).
- La medición dice que la frontera, **tal como está escrita**, no cumple su propio criterio de adopción: recupera los VP (4) sin dejar pasar ningún falso en el universo de corridas reales (U1 falsos = 0) ni en equivalencia (U3), pero la batería adversarial registra el falso S3 por la vía (c).
- Consecuencia registrada en el papel v2.3 (§4, dependencia con compuerta): sin adopción no hay brazo ALMA de la v2.3. El revisor v2.3 está construido y probado en seco (suite verde, autochequeo 16/16 sin negativas ni degradación con freno US$6,50); su brazo base (gate=v13) no depende de la 1.4.0. Lo que sigue — adenda o papel nuevo sobre la frontera (c) — es decisión de Alejandro, no de esta construcción.
