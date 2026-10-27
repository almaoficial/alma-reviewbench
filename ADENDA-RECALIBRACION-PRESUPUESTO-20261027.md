# Adenda — Recalibración del presupuesto de planificación por PR (la degradación de la nº 373)

**Fecha:** 2026-10-27 (EDT). **Costo de esta tarea: US$0** — sin
llamadas a modelos, sin portal, sin publicación, sin empuje
al repo. **Autorización:** Alejandro, 27/10/2026 («Ok lo
hagamos»), sobre la autopsia de la corrida nº 373
(`AUTOPSIA-373-20261027.md`). **Relación con los papeles
vigentes:** esta adenda se anexa a
`ADENDA-ARREGLO-TOPE-20261024.md` y la enmienda en UN punto
— la proyección de costo con la que el pre-flight 2 decide
qué pasadas profundas entran bajo el freno — sin tocar su
tope de salida (16.384), su reintento a 32.768, su freno
(`RB_MAX_SPEND_USD` = US$6,50 por PR, intocable), su vara ni
la puerta 1.5.0. **El piso 2 de la autopsia (los descartes
por forma de la puerta) queda expresamente FUERA de esta
adenda**: es otra corrección, y mezclarlas en una misma
corrida volvería imposible atribuir el efecto.

## 1. La falla que esta adenda repara (piso 1 de la autopsia)

En la nº 373, el pre-flight 2 admitió las pasadas profundas
preciando cada payload armado a su **peor caso**: entrada
estimada + la salida completa del tope, 16.384 tokens. A los
precios de planificación de la línea (US$15/US$75 por Mtók),
el componente de salida por pasada pasó de US$0,3072 (era
4.096) a **US$1,2288**. Con el mismo freno por PR (US$6,50),
el mismo diseño compró menos pasadas: degradación por
`spend_cap` en **19 de 25 PRs** (base 298: 9 de 25) y
**54 pasadas profundas caídas** (298: 26); los candidatos
generados cayeron de 168 a 108. El sistema se frenó por
precio *supuesto*, no por gasto real: la 373 terminó costando
**US$14,40**, menos que los US$20,41 de la 298, justamente
porque no corrió las pasadas.

Uso real observado en la 373 (computado de las líneas
`llm_run` de los 25 `agent.log` descargados, con la salvedad
de que la completación de la pasada de selección varía por
PR — el estimador resta la selección del único PR con una
sola llamada, 1.545 tokens): completación por pasada
profunda **media ≈ 2.336, mediana ≈ 2.134, máximo por
promedio de PR ≈ 5.164 tokens**. Ninguna pasada profunda
observada se acerca a 16.384: el peor caso que la
planificación supone es ~3× el uso máximo observado y ~7×
el uso medio.

## 2. El arreglo, declarado antes del código

En la capa compartida que heredan los tres brazos
(`agent/llm_reviewer_v24.py`; el v2.5 y el v2.6 son subclases
que heredan la planificación entera):

**(a) La admisión de pasadas profundas deja de preciar la
salida al tope y pasa a preciarla a una línea de
planificación propia de la familia**: nace
`DEFAULT_DEEP_PLANNING_OUTPUT_TOKENS = 6144`, resuelto por
`_resolve_deep_planning_output_tokens(env, config)` con la
misma precedencia y el mismo fail-closed que los resolvers
hermanos — config `deep_planning_output_tokens`
(`RB_CONFIG_DEEP_PLANNING_OUTPUT_TOKENS`) → entorno
`RB_LLM_V24_DEEP_PLANNING_OUTPUT_TOKENS` → default; valor no
entero o no positivo rehúsa en construcción. Un método
nuevo, `planning_estimate(payload)`, precia la entrada como
hoy y la salida a `min(tope del payload, línea de
planificación)`. Lo usa **solo** la decisión de admisión
del pre-flight 2 y el chequeo de asequibilidad de la pasada
mixta degenerada (que es la misma decisión: qué producción
cabe planificar bajo el freno).

*Justificación del valor — del uso medido, no de la era
vieja.* (i) 6.144 queda **por encima del máximo observado**
por promedio de PR (5.164) con ~19 % de aire, y a ~2,6× la
media observada (2.336): la proyección sigue cubriendo la
pasada más cara vista, sin suponer el techo. (ii) **No es
4.096**: las pasadas de hoy escriben más que las de la era
del tope chico (el esquema de evidencia es verboso y el
razonamiento cuenta como completación; +31 % de
completación por llamada entre la 298 y la 373, y promedios
por PR de hasta 5.164): planificar a 4.096 subpreciaría el
uso real sistemáticamente y trasladaría la protección al
chequeo acumulativo de costo real a mitad de plan —
convirtiendo una degradación declarada (sobrevivible) en
muertes totales de PR por cierre en falso (peor desenlace).
(iii) El componente de salida por pasada queda en
US$0,4608: entre el US$0,3072 con el que el diseño original
compraba sus pasadas y el US$1,2288 que estranguló la 373;
en los contextos grandes típicos de la 373 (mediana
≈ 44.400 tokens entre los PRs degradados) eso repone la
admisión cercana a la del diseño — sin prometerla idéntica
(ver §4).

**(b) El run info declara la línea en vigor**: campo nuevo
`deep_planning_output_tokens` junto a
`deep_max_output_tokens` (espejo de
`triage_max_output_tokens`), asentado por corrida y
atravesando las reconstrucciones del v2.5 y del v2.6, para
que cualquier degradación o muerte futura sea atribuible a
la línea exacta que rigió su planificación.

**Qué sigue preciando a peor caso verdadero, sin tocar:**
el pre-flight 1 (la selección sola debe caber — su payload
es el de triaje, línea distinta), la **guardia del reintento
por `length`** (custodia una llamada real extra contra el
freno: ahí lo conservador es lo correcto) y, sobre todo, el
**chequeo acumulativo de costo real** (`_account`, sin
modificar), que sigue cerrando en falso contra
`RB_MAX_SPEND_USD` con el costo **real** reportado por el
endpoint. La planificación decide qué se intenta; el freno
sigue decidiendo cuánto se gasta de verdad.

## 3. Qué NO cambia

La puerta **1.5.0** y todas las puertas 1.0.0–1.5.0,
`claim_contract.py` y `birth_shaper.py`, byte-idénticos —
**el piso 2 no se toca**. `RB_MAX_SPEND_USD` — ni su valor
(US$6,50 por PR), ni su custodia, ni su chequeo acumulativo.
El tope profundo (16.384), el reintento por `length` a
32.768 y su guardia. La pasada de selección y su techo de
triaje. Los prompts (ni una palabra). `agent/llm_reviewer.py`
(la base v1) y los revisores v2/v2.1/v2.2/v2.3 —
byte-idénticos. Los `REVIEWER_VERSION` quedan
(`2.4.0`/`2.5.0`/`2.6.0`): identidad del revisor, no de sus
bytes; la identidad exacta del código la fijan los hashes de
cierre de esta adenda y el digest de la imagen futura, como
en toda la línea. **Re-fijado declarado** (mismo precedente
que la adenda anterior, §3): las tablas de congelados de
`tests/test_llm_reviewer_v24.py` (`FROZEN_FILE_SHA256`, que
importan los tests del v2.5 y del v2.6 sobreescribiendo su
entrada) y las entradas propias de
`tests/test_llm_reviewer_v25.py` (`FROZEN_V25`) y
`tests/test_llm_reviewer_v26.py` (`FROZEN_V26`) fijan los
sha256 de `llm_reviewer_v24.py` (y el del v2.5 en la del
v2.6); esta adenda re-fija esos valores a los hashes nuevos
y ningún otro valor de esas tablas se toca.

## 4. Lo que el arreglo NO afirma

No afirma que el alcance vuelva al nivel de la 298: ataca
solo el piso 1 (generación, −60 candidatos); con la
generación restaurada, la puerta 1.5.0 seguiría descartando
en origen ~1 de cada 3 reclamos por falta de patrón
declarado (piso 2, fuera de alcance) — la recuperación
esperada es **parcial**. No afirma degradación cero: la 298
ya degradaba en 9 de 25 PRs con su economía; en los
contextos más grandes seguirá habiendo degradación
**declarada**, que es el desenlace sobrevivible del diseño.
Y no afirma ningún efecto sobre P/R/F1: la medición sigue
siendo la corrida paga, que esta adenda no autoriza.

## 5. El riesgo, asentado antes del código

Subir la admisión sube el gasto real por corrida hacia —o
por encima de— los US$20,41 de la base (es el costo de
correr las pasadas que la 373 se negó). El freno global no
se ajusta en conjunto, y ese es el riesgo declarado por la
autopsia (§4): si una corrida planificada con la línea
nueva gasta más rápido que lo proyectado, el chequeo
acumulativo cierra en falso **a mitad de corrida** y ese PR
muere entero (la corrida quedaría inválida en ese PR, no
solo cara). La mitigación es la propia línea: 6.144 cubre
con aire el máximo observado por llamada, así que el gasto
real por pasada debería quedar, en lo típico, por debajo
de lo planificado. La mitigación **no elimina** el riesgo:
una pasada patológica (o un reintento a 32.768) puede
comer el resto de un PR grande. Por eso la línea se
declara por corrida en el run info (§2b) y por eso el
freno queda exactamente donde estaba: es el techo duro de
plata real por PR, y ninguna proyección lo mueve.

## 6. Verificación en seco (declarada antes, US$0)

1. **Tests de regresión nuevos** en
   `tests/test_llm_reviewer_v24.py`, por transporte
   guionado: (i) la línea por defecto es 6.144, el resolver
   (config/entorno/inválido) se comporta como sus hermanos
   y el payload profundo conserva su tope de 16.384 (la
   planificación no toca el payload); (ii) en un PR de
   contexto grande sintético donde la planificación a peor
   caso (línea forzada a 16.384 vía entorno — la aritmética
   vieja) degrada pasadas planificadas, la línea por
   defecto las admite todas y corren; (iii) el freno sigue
   cortando ante gasto real excesivo: con transporte que
   reporta uso real por encima del freno, el chequeo
   acumulativo cierra en falso igual que hoy, aunque la
   planificación hubiera admitido el plan.
2. **Suite completa** corriendo entera, en verde, con el
   conteo asentado en el informe de cierre.
3. **Semáforo congelado:** la batería `fixtures_semaforo/`
   íntegra contra su `MANIFIESTO-BATERIA.json` (32
   archivos, bytes y sha256) y la batería en seco 16/16 por
   cada portador (v2.4, v2.5, v2.6) dentro de la suite.
4. **Congelados:** foto sha256 antes/después del resto de
   la línea — puertas, contrato, formador, revisores
   previos, compiladores, contextos — byte-idénticos; los
   únicos archivos de código que difieren son los
   declarados en la §2–§3.

## 7. Corridas futuras bajo esta enmienda

Toda corrida que use el arreglo lleva un **`RB_RUN_ID`
nuevo** y corre sobre una imagen nueva que lo contenga,
con esta enmienda citada en su papel. **Esta adenda no
publica imagen ni empuja el repo** (la tarea que la encarga
lo prohíbe expresamente): el arreglo queda validado en el
repo local, y la publicación — sincronización, disparo del
workflow `reviewbench-image` y digest verificado en dos
fuentes — es el paso siguiente por el pipeline asentado,
cuando Alejandro lo decida junto con la corrida. Si un
papel de corrida quisiera otra línea de planificación, la
fija por `RB_CONFIG_DEEP_PLANNING_OUTPUT_TOKENS` (o su
config) y la declara antes.

## 8. Asiento de cierre (ejecutado el 2026-10-27)

- **El código:** `agent/llm_reviewer_v24.py` →
  `3b33238f…` (línea de planificación 6.144 + resolver +
  `planning_estimate` + campo del run info);
  `agent/llm_reviewer_v25.py` → `47ae82e6…` y
  `agent/llm_reviewer_v26.py` → `a2452372…` (solo el pase
  del campo nuevo en sus reconstrucciones). Re-fijados
  ejecutados según la §3 en `tests/test_llm_reviewer_v25.py`
  y `tests/test_llm_reviewer_v26.py`; 3 tests nuevos en
  `tests/test_llm_reviewer_v24.py` (clase
  `PlanningBudgetTests`).
- **La suite: 397/397 OK** (394 de apertura + 3 nuevos).
  **Semáforo VERDE 3/3:** batería `fixtures_semaforo/`
  íntegra contra su manifiesto (32/32) y batería en seco
  16/16 por portador dentro de la suite; puertas 1.0.0–1.5.0,
  contrato y formador byte-idénticos (tablas de la suite +
  git sin modificaciones en esos archivos).
- **Efecto esperado, sin replay de la 373 real** (la
  descarga no trae diffs/contextos; declarado en el
  informe): demostración guionada 3/5 → 5/5 pasadas en el
  PR grande sintético, y simulación sobre los agregados de
  la 373 con supuestos declarados: caídas 24 → 4, PRs
  degradados 14 → 4. Informe completo:
  `CORRECCION-PRESUPUESTO-20261027.md`.
- **La imagen: NO publicada** (la tarea lo prohíbe): el
  arreglo queda validado en el repo local; la publicación
  por el pipeline asentado y la corrida de medición se
  deciden con Alejandro (costo esperado ESTIMADO
  US$20–26; saldo US$17,65).

— Adenda a la adenda del arreglo del tope del 24/10/2026,
escrita el 2026-10-27 ANTES del código de la
recalibración, sobre la autopsia asentada de la nº 373.
