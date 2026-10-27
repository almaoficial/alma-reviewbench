# Corrección en seco — recalibración del presupuesto de planificación (27/10/2026)

**Encargo:** corrección US$0 aprobada por Alejandro el
27/10/2026 («Ok lo hagamos») sobre la autopsia de la nº 373
(`AUTOPSIA-373-20261027.md`, piso 1). **Papel previo:**
`ADENDA-RECALIBRACION-PRESUPUESTO-20261027.md`, escrita
ANTES del código, como manda el precedente de la línea.
**Alcance cumplido:** solo código local + tests. Sin
publicar imagen, sin pushear, sin corridas pagas, sin tocar
la puerta.

## 1. Qué se cambió

La admisión del pre-flight 2 preciaba cada pasada profunda
a su peor caso (salida completa al tope de 16.384 =
US$1,2288 de salida por pasada) y el freno por PR de
US$6,50 compraba la mitad del diseño: en la 373,
degradación en 19/25 PRs y 54 pasadas caídas, con gasto
real (US$14,40) MENOR que el de la base (US$20,41) — el
sistema se frenaba por precio supuesto. Ahora la admisión
precia la salida a una **línea de planificación** propia de
la familia, `DEFAULT_DEEP_PLANNING_OUTPUT_TOKENS = 6144`,
fundada en el uso observado de la 373 (completación por
pasada profunda: media ≈ 2.336, máximo por promedio de PR
≈ 5.164 tokens, computado de las líneas `llm_run` de los 25
`agent.log`): queda por encima del máximo observado con
~19 % de aire, a US$0,4608 de salida proyectada por pasada.
La línea se resuelve como sus hermanas (config
`deep_planning_output_tokens` → entorno
`RB_LLM_V24_DEEP_PLANNING_OUTPUT_TOKENS` → default;
inválido rehúsa en construcción) y se asienta por corrida
en el run info (`deep_planning_output_tokens`), atravesando
las reconstrucciones del v2.5 y del v2.6.

**No se tocó:** el payload (su tope sigue en 16.384), el
reintento por `length` a 32.768 ni su guardia a peor caso,
el pre-flight 1, el chequeo acumulativo de costo real que
cierra en falso contra `RB_MAX_SPEND_USD` (US$6,50 por PR —
ni subido, ni bajado, ni removido), la puerta 1.5.0 y sus
descartes por forma (piso 2: otra corrección), los prompts,
la base v1 y los revisores v2–v2.3.

Archivos tocados (sha256 nuevo):
- `agent/llm_reviewer_v24.py` →
  `3b33238f4fc53bc368da47ccaf12f8715bc13cec300ac9b506182396116f5677`
  (constante + resolver + `planning_estimate` + admisión y
  fallback a la línea + campo del run info)
- `agent/llm_reviewer_v25.py` →
  `47ae82e69589f88be68557eb12747b16acd5d7c7a5a38f776c3d13b4b5a17606`
  (solo el pase del campo nuevo en su reconstrucción)
- `agent/llm_reviewer_v26.py` →
  `a24523722a980172aa3fcbe26d4a11b69a3e16d304dcc41a0a7f59ecfb5ea43d`
  (idem)
- `tests/test_llm_reviewer_v24.py` (3 tests nuevos, clase
  `PlanningBudgetTests`, + ayudantes), y los re-fijados
  declarados en `tests/test_llm_reviewer_v25.py`
  (`FROZEN_V25`) y `tests/test_llm_reviewer_v26.py`
  (`FROZEN_V26`) — solo las entradas de los archivos
  tocados, ningún otro valor.

## 2. Suite y semáforo

- **Suite completa: 394/394 → 397/397 OK** (3 tests
  nuevos): (i) la línea por defecto es 6.144, su resolución
  config/entorno/inválido se comporta como la de sus
  hermanos, el payload profundo conserva su tope de 16.384
  y `planning_estimate` forzado a 16.384 reproduce la
  aritmética vieja exacta; (ii) en un PR sintético de
  contexto grande (~42.100 tokens, la banda donde la 373
  degradó) con 5 pasadas planificadas, la aritmética vieja
  admite 3 y degrada (caen testing y security) mientras la
  línea por defecto admite las 5 sin degradación;
  (iii) el freno sigue cortando ante gasto REAL excesivo:
  una pasada admitida por planificación cuyo uso reportado
  supera `RB_MAX_SPEND_USD` cierra en falso en el chequeo
  acumulativo, igual que hoy.
- **Semáforo en seco, 3/3 VERDE:** (1) batería congelada
  íntegra contra su manifiesto — **32/32 archivos**, bytes
  y sha256, sin extras ni faltantes; (2) puertas
  congeladas 1.0.0–1.5.0, `claim_contract.py` y
  `birth_shaper.py` byte-idénticos — verificados por las
  tablas de congelados de la propia suite (en verde) y por
  el estado de git del repo: ningún archivo de puerta,
  contrato o formador figura modificado; (3) suite entera
  en verde, que incluye la batería en seco 16/16 por cada
  portador (v2.4, v2.5, v2.6).

## 3. Verificación del efecto esperado

**Sin verificación de replay sobre la 373 real**: no
existe harness local que la reproduzca, y la descarga de
la corrida no trae los diffs ni los contextos de los 25
PRs — solo sus agregados por PR. Declarado, no disimulado.
Lo que sí se verificó en US$0:

- **Demostración por transporte guionado** (test (ii) de
  la §2): mismo PR grande, misma selección — la única
  variable es la línea de planificación: 3/5 pasadas con
  la aritmética vieja, **5/5 con la nueva**.
- **Simulación de planificación sobre los agregados
  reales de la 373** (supuestos declarados: input por
  payload = solo el contexto estimado, sin el diff; el
  costo de selección no se carga — ambas líneas quedan
  favorecidas por igual y la señal es el delta): de 103
  pasadas planificadas, la línea vieja deja caer 24 y
  degrada 14 PRs; **la nueva deja caer 4 y degrada 4
  PRs**. La realidad de la 373 fue peor que su propia
  simulación (54 caídas, 19 PRs) porque el input real
  incluye el diff; la restauración esperada en vivo es de
  esa dirección y orden, no de ese número exacto.

El diseño queda listo para que la próxima corrida paga
sea la medición: misma vara firmada, `RB_RUN_ID` nuevo,
imagen nueva por el pipeline asentado (esta tarea no
publica ni empuja).

## 4. Costo esperado de la próxima corrida (ESTIMADO)

**ESTIMADO: US$20–26**, con su base declarada: la nº 298 —
el diseño corriendo casi completo, 104 llamadas — costó
**US$20,41** reales (portal); la nº 373, estrangulada,
costó US$14,40. Una corrida recalibrada vuelve a correr
las pasadas que la 373 se negó, y cada pasada de hoy
escribe más que las de la era 298 (+31 % de completación
por llamada), de ahí el techo de la banda. El freno por PR
(US$6,50) sigue siendo el techo duro de gasto por PR: el
riesgo asentado en la adenda (§5) es que un PR caliente
cierre en falso a mitad de plan en vez de degradar —
mitigado por la línea (6.144 > máximo observado), no
eliminado. **Dato para la decisión:** el saldo tras la
373 quedó en US$17,65 (asentado en
`PREREGISTRO-CORRIDA-20261027.md`) — por debajo de la
banda esperada: correr la medición probablemente exija
cargar ~US$3–9 más. La decisión y la carga son de
Alejandro, con el juicio del 29/10 de por medio.

## 5. Costo de esta corrección

**US$0** — lectura, código y cómputo locales; ninguna
llamada a modelos, ninguna corrida, ningún empuje, ninguna
imagen publicada.
