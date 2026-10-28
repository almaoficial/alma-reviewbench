# Corrección de la puerta — el descarte por forma (27/10/2026)

Diseño e implementación en seco (US$0), bajo
ADENDA-PUERTA-FORMA-20261027.md (declarada antes del código).
Sin imagen publicada, sin corridas, sin portal: la corrida que
mida esta corrección se decide después.

## 1. Diseño elegido y porqué

Criterio rector: ningún reclamo muere en origen solo por su
forma — antes de descartarlo por falta de patrón, el sistema
intenta extraer el patrón del propio reclamo contra su cita
(ruta (b); la (a) reclasifica la muerte sin juzgar nada y la
(c) no tiene juez determinista al que entregar la marca).

La lectura del código fijó el punto exacto de muerte: NO es
la puerta 1.5.0 por dentro, es la conversión del revisor
(`_to_candidate_v24`), que asentaba el hallazgo cuando el
campo `pattern` de la emisión venía ausente/no-lista/vacío —
después de verificar forma, tipo y evidencia idéntica al HEAD,
y ANTES de que el formador al nacer pudiera minar la prosa
(su Caso B, construido exactamente para esto). En las dos
corridas medidas, el 100 % de los descartes por
`sin_patron_concreto_en_el_reclamo` lleva nombre de pasada
profunda como origen y 0 llevan `production_shaping`: el
rescate existía y era inalcanzable.

La corrección, una sola variable de comportamiento, en dos
piezas que componen:

- **Puerta nueva `alma-evidence-gate/1.5.1`** (módulo nuevo
  `agent/alma_gate_v151.py`, sha256 `23b370ad…`): la 1.5.0 por
  delegación, con un pre-paso sobre los reclamos generales que
  no afirman ningún token — extracción determinista del
  patrón desde la prosa del propio reclamo contra su cita
  (el minado cerrado del contrato de reclamos, importado sin
  modificar). Con patrón extraído, el reclamo se juzga sobre
  él y la aceptación asienta que el patrón fue extraído, no
  declarado. Sin nada extraíble, lo retiene la 1.5.0 con el
  código histórico. Registrada en `agent/main.py` como
  `v151` (sha256 del archivo `64ccaf10…`).
- **Enmienda de conversión** en la capa compartida de la
  familia v2.4 (`agent/llm_reviewer_v24.py`, sha256 nuevo
  `a771ae72…`, declarada en el docstring del módulo como las
  dos enmiendas anteriores): el hallazgo sin patrón declarado
  ya no se asienta en la conversión; se construye el candidato
  tal como nació y decide el formado (minado) y, en su caso,
  la puerta 1.5.1 — cuya resolución también quedó admitida
  (`gate=v151`, misma familia de clases que la 1.5.0). La
  identidad del revisor no cambia: `llm-reviewer/2.4.0`.

Lo que no se movió: presupuesto 6.144, tope 16.384, freno,
prompts, anclaje, formador, contrato, y todas las puertas
congeladas 1.0.0–1.5.0 byte a byte. Los descartes no-forma
siguen muriendo igual: patrón declarado contradictorio con el
mensaje (se sigue asentando en la conversión), declarado no
verificable por el propio modelo, tokens afirmados ausentes
de la cita (la extracción nunca sustituye un patrón
afirmado), contradicción afirmativa y cita que no resuelve
(rechazos firmes de la puerta, intactos).

## 2. Replay US$0 sobre las descargas de la 373 y la 374

Población reencauzable (descartes `sin_patron` asentados en
la conversión — la población que la corrección deja de matar
antes de la extracción), computada de los `agent.log` de
ambas descargas:

| | 373 | 374 |
|---|---|---|
| Descartes en origen (todos los códigos) | 34 | 49 |
| Reencauzables (`sin_patron`, en conversión) | **29** | **36** |
| De ellos, sobre territorio de un gold TP | 25 (recomputo) | 22 (asentado por código) |
| De ellos, fuera de territorio gold | 4 (recomputo) | 14 (asentado por código) |

(Criterio del recomputo, declarado: mismo archivo y solape
de rango contra el gold de la adjudicación de la nº 298; para
la 374 da 25 entradas sobre gold contra las 22 asentadas por
la autopsia con su cotejo — misma magnitud, diferencia de
criterio de borde. La autopsia de la 373 asentó 26/34 para el
total de descartes, sin desglose por código.)

**Rescate exacto por corrida: SIN DATO.** Las descargas no
traen los mensajes de los descartados (el ledger asienta
pasada, archivo y líneas, no el texto), así que ningún replay
puede correr el minado sobre ellos sin inventar el material.
Lo que sí puede afirmarse es la población que gana el derecho
a la extracción (29 y 36) y dónde estaba concentrada.

**Estimación declarada (no medición):** con la única tasa de
rescate medida sobre un corpus con mensajes — el minado
rescató 17/71 reclamos sin patrón del corpus de la nº 298
(23,9 %; RESULTADO-REVISOR-CONTRATO-20261022) — los
reencauzables que sobrevivirían a juzgado serían ≈7 (373) y
≈9 (374), de los cuales ≈5 (374) sobre territorio gold. La
carga extra de juzgado es esa: ≈7–9 reclamos más por corrida
entran a la validación determinista de la puerta (US$0; ni la
conversión, ni el formado, ni la puerta hacen llamadas de
modelo), y es carga con riesgo declarado: en el corpus de la
298 los minados emitieron con precisión 41,2 % (7/17 TP)
contra 59,7 % de los declarados — la corrección compra
alcance pagando precisión potencial, y la vara de la corrida
futura lo juzgará en F1, no en intenciones. Los descartes
no-forma de ambas corridas (373: 5; 374: 13) quedan fuera del
reencauce por diseño.

## 3. Suite y semáforo

- **Suite completa: 397/397 → 410/410 OK.** Nuevos: 9 de la
  puerta 1.5.1 (`tests/test_gate_v151.py`: extracción acepta
  y declara, nada extraíble retiene con el código histórico,
  contradicción afirmativa sigue rechazada en firme, tokens
  afirmados ausentes no se rescatan, clases equivalentes a la
  1.5.0, determinismo, congelados) y 4 de la enmienda
  (`GateFormAmendmentTests` en `tests/test_llm_reviewer_v24.py`:
  sin patrón con contenido juzgable sobrevive y nace minado;
  `pattern=[]` también fluye; sin contenido se sigue
  asentando, ahora en `production_shaping`; resolución
  `gate=v151`). Actualizados con declaración: el test de la
  2.4 que fijaba el asentamiento en conversión (mismos
  códigos, etapa nueva) y los de la 2.5/2.6 (su fixture por
  defecto ahora sobrevive por extracción: el asentamiento se
  afirma sobre un reclamo sin contenido). Re-fijadas SOLO las
  entradas de `llm_reviewer_v24.py` en las tablas
  `FROZEN_V25`/`FROZEN_V26`, como en la corrección anterior.
- **Semáforo en seco, 3/3 VERDE:** (1) batería congelada
  íntegra contra su manifiesto — 32/32 archivos, bytes y
  sha256, sin extras ni faltantes; (2) puertas congeladas
  1.0.0–1.5.0, `claim_contract.py` y `birth_shaper.py`
  byte-idénticos — verificados por las tablas de congelados
  de la propia suite, en verde, incluida la tabla nueva de
  `test_gate_v151.py`; (3) suite entera en verde, con la
  batería en seco de cada portador (v2.4, v2.5, v2.6).

## 4. Costo

Esta corrección (adenda, código, tests, replay, este
informe): **US$0**. La corrida futura que la mida costará lo
que cuesta la configuración actual — **ESTIMADO US$20–26**,
anclado en el costo real de la nº 374 (US$20,33) — porque la
corrección no agrega llamadas de modelo: conversión, formado
y puerta son etapas deterministas posteriores a la
generación. Publicarla y correrla espera el pre-registro y
el «corre» de Alejandro.
