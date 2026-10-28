# Adenda — corrección de la puerta: el descarte por forma (27/10/2026)

Declarada ANTES del código, como las correcciones anteriores de
esta línea (tope, 24/10; presupuesto, 27/10). Aprobada por
Alejandro el 27/10/2026: diseño e implementación en seco (US$0);
la corrida que la mida se decide después.

## 1. El defecto, medido dos veces

La puerta 1.5.0 exige que todo reclamo de categoría general
declare un patrón concreto — tokens de código entre backticks —
contrastable con su cita (regla G4). El reclamo que no declara
patrón muere **en origen**, antes de ser juzgado, con el código
`sin_patron_concreto_en_el_reclamo`. Dos corridas lo midieron:

- nº 373 (autopsia del 27/10): 34 descartes en origen, **29 por
  ese código**; 26 de los 34 caen sobre territorio de un gold TP.
- nº 374 (autopsia del 27/10): 49 descartes, **36 por ese
  código**; 32 de los 49 sobre territorio gold y, asentado por
  código, 22 de los 36 de forma sobre gold; los descartes por
  forma solos solapan 34 gold TP distintos.

Resultado en ambas: precisión ~72 %, alcance 9,4–9,8 % contra
18,75 % de la base nº 298. La corrección de presupuesto ya
quedó absuelta como causa (autopsia 374, veredicto a): con las
pasadas restauradas, el alcance no volvió. El piso que queda es
este.

## 2. Dónde muere exactamente (lectura del código, 27/10)

El descarte NO ocurre dentro de `AlmaGateV150`: ocurre una
etapa antes, en la conversión del revisor
(`llm_reviewer_v24._to_candidate_v24`). El hallazgo crudo ya
pasó ahí la disciplina heredada — forma válida, tipo acorde a
la pasada, líneas citadas existentes y evidencia citada
idéntica byte a byte al archivo HEAD — y muere solo si el
campo `pattern` de la emisión viene ausente, no-lista o sin
ningún token sobreviviente (`_declared_pattern` → vacío). Las
49 entradas del `production_ledger` de la 374 llevan el nombre
de una pasada profunda como origen; **cero** llevan
`production_shaping`.

La ironía medible: la etapa siguiente del pipeline, el
formador al nacer (`birth_shaper`, Caso B), YA implementa el
rescate para reclamos sin patrón declarado — minado cerrado de
la prosa contra la cita, importado del contrato de reclamos —
y su Caso A/Caso B decidía el destino de cada reclamo sin
patrón. Pero en la familia v2.4 ese mecanismo es inalcanzable
para esta población: la conversión mata antes de que exista un
candidato que formar. El minado no perdió contra los datos;
nunca fue invocado sobre ellos.

## 3. La corrección (variable única)

Criterio rector: **ningún reclamo muere en origen solo por su
forma: antes de descartarlo por falta de patrón, el sistema
intenta extraer el patrón del propio reclamo contra su cita**
(ruta (b) de las evaluadas; las rutas (a) y (c) se descartan
abajo). La corrección tiene dos piezas que componen una sola
variable de comportamiento:

**(i) Puerta nueva `alma-evidence-gate/1.5.1`** (módulo nuevo
`agent/alma_gate_v151.py`; las congeladas 1.0.0–1.5.0 no se
editan). Delega todo en la 1.5.0 — las 19 clases por su
delegación, y de la vía general G0–G3 y G5 idénticos — con UN
cambio en G4: cuando el reclamo no afirma ningún token, la
puerta corre primero la extracción determinista de patrón
(minado cerrado de la prosa del propio reclamo contra sus
líneas citadas, el del contrato de reclamos, importado sin
modificar). Si la extracción produce ≥1 token, el reclamo se
juzga sobre ese patrón extraído (duplicado y aceptación como
en la 1.5.0, con la razón asentando que el patrón fue
extraído, no declarado). Si no produce ninguno, el reclamo
queda retenido con el mismo código y la misma razón que hoy:
sin patrón *extraíble*, no sin patrón *declarado*. La puerta
no reescribe el mensaje ni inventa evidencia: extrae solo
tokens que están a la vez en la prosa del reclamo y en su
cita, con veto a los tokens gobernados por marcadores de
ausencia (la maquinaria cerrada existente).

**(ii) Enmienda de conversión en la capa compartida de la
familia v2.4** (`llm_reviewer_v24.py`, declarada aquí, como
las enmiendas del tope y del presupuesto en este mismo
archivo): si el campo `pattern` viene ausente/no-lista/vacío,
el hallazgo ya NO se asienta ni muere en la conversión: se
construye el candidato tal como nació (mensaje intacto) y
fluye a las etapas que ya saben decidir — el formador al nacer
mina su prosa (Caso B, sin modificar) y lo declara no
verificable en origen solo si nada es extraíble; la puerta
1.5.1 aplica la misma política a todo candidato que le llegue
sin patrón desde cualquier productor. Lo que la conversión
sigue asentando igual que hoy: `patron_declarado_distinto_del_mensaje`
(declaró un patrón y su mensaje afirma otro: no es ausencia de
forma, es autocontradicción) y `declarado_no_verificable_en_origen`
(declaración del propio modelo). La identidad del revisor no
cambia (`llm-reviewer/2.4.0`); la identidad del código la lleva
el digest de la imagen futura y esta adenda, como en toda la
línea.

Por qué no las otras rutas: (a) pasar los descartes por forma
a `needs_validation` sin extracción no cambia ningún destino
en producción (la emisión estricta ya trata lo retenido como
no emitido) y no juzga nada: es reclasificar la muerte, no
evitarla. (c) degradar el motivo a una marca que «el juez
pondera» no tiene juez determinista al que entregarla en esta
arquitectura y convierte una regla en una sugerencia. La
extracción (b) es además la ruta que el propio código ya
había construido dos veces (contrato y formador): la
corrección la conecta, no la inventa.

## 4. Qué NO cambia

- Presupuesto por PR (línea de planificación 6.144), tope de
  salida 16.384 y su reintento, freno de gasto
  (`RB_MAX_SPEND_USD`) y chequeo acumulativo: intactos.
- El revisor: prompts, selección, pasadas, disciplina de
  anclaje (malformed/unanchored), formador al nacer y contrato
  de reclamos: sin modificar. La única rama que se mueve es la
  de patrón declarado vacío en la conversión.
- La puerta 1.5.1 conserva TODOS los rechazos firmes de la
  1.5.0 (rango inválido, cita que no resuelve contra HEAD,
  evidencia que contradice el diff, contradicción afirmativa
  G3, duplicado G5) y la retención por
  `tokens_afirmados_ausentes_en_la_evidencia`. Las 19 clases
  quedan byte a byte en la delegación de la 1.4.1.
- Los descartes que no son de forma siguen muriendo igual:
  declarado no verificable por el propio modelo, patrón
  declarado distinto del afirmado, y el reclamo sin patrón del
  que nada puede extraerse de su prosa contra su cita (ese
  último muere por materia — no hay nada contrastable — no por
  forma; el código y la razón del asentamiento lo declaran).

## 5. Criterios de aceptación medibles en seco

1. **Regresión de origen**: un hallazgo sin campo `pattern`
   (o vacío) cuyo mensaje contiene un token con forma de
   código presente en su evidencia citada sobrevive a la
   conversión y nace en forma de contrato (origen `mined`);
   antes de la corrección moría asentado en la conversión.
2. **La muerte no-forma sigue**: un hallazgo sin patrón y sin
   nada extraíble se sigue asentando con
   `sin_patron_concreto_en_el_reclamo` (ahora en la etapa de
   formado, con el intento de extracción registrado); el
   declarado no verificable y el patrón contradictorio se
   siguen asentando en la conversión, igual que hoy.
3. **Puerta 1.5.1**: un candidato general sin tokens afirmados
   pero con patrón extraíble de su prosa contra su cita es
   ACEPTADO con razón que declara la extracción; uno sin nada
   extraíble queda retenido con el código histórico; una
   contradicción afirmativa (G3) y una cita que no resuelve
   (G1) siguen siendo rechazo firme; la vía de clases es la de
   la 1.5.0 por delegación.
4. **Congelados intactos**: sha256 de las puertas 1.0.0–1.5.0,
   `claim_contract.py` y `birth_shaper.py` idénticos antes y
   después; suite completa en verde y semáforo en seco 3/3.
5. **Replay US$0 declarado**: sobre las descargas de la 373 y
   la 374 se computa la población reencauzable (descartes por
   `sin_patron` en conversión: 29 y 36) y su solape con gold;
   el rescate exacto por corrida queda **sin dato** si las
   descargas no traen los mensajes (no los traen: el ledger
   asienta archivo y líneas, no el texto), y se estima con la
   única tasa medida sobre un corpus con mensajes: el minado
   rescató 17/71 reclamos sin patrón del corpus de la nº 298
   (RESULTADO-REVISOR-CONTRATO-20261022), con precisión de
   emisión de los minados de 41,2 % (7/17) — el costo honesto
   de la corrección: lo rescatado emite más sucio que lo
   declarado (59,7 % en ese corpus).

## 6. Costo

Diseño, implementación, replay y verificación: **US$0**
(trabajo local determinista; ninguna corrida, ninguna llamada
paga). La corrida futura que mida esta corrección costará lo
que cuesta la configuración actual — estimado US$20–26 por
corrida, anclado en el costo real de la nº 374 (US$20,33) — y
se corre solo con pre-registro y «corre» de Alejandro.
