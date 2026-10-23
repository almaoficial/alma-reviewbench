# Pre-registro — Censo de ejecutabilidad de la sala de espera de la 1.4.1

**Fecha:** 2026-10-22 · **Aprobación:** Alejandro, 22/10/2026
(«Hagamos las 3»). **Costo: US$0** — análisis sobre archivos
locales; sin llamadas a modelos, sin portal, sin cargas, sin
publicación. La taxonomía de este papel se escribió ANTES de
clasificar un solo reclamo del corpus: las clases se definen desde
lo que un oráculo de ejecución necesita para decidir, no desde los
149 casos concretos.

## 1. La pregunta

El replay offline de la puerta 1.4.1 (`REPLAY-PUERTA-141-20261022.md`)
dejó **149 de los 166** hallazgos de la base nº 298 en
`needs_validation`, todos con el mismo blocker:
`sin_regla_de_verificacion_en_puerta`. La puerta verifica por
**citación** — que el patrón afirmado aparezca en la evidencia — y
para las categorías generales no tiene regla. La pregunta de este
censo, inspirada en la verificación por ejecución (un hallazgo vale
si su falla **reproduce**, contra un control que nunca falla):

> De esos 149 reclamos en espera, ¿cuántos serían DECIDIBLES
> ejecutando algo — un test existente, un comando, una reproducción
> determinista anclada en el propio reclamo — y cuántos no tienen
> vía de ejecución ni en principio?

El resultado decide si una «tercera vía» de verificación por
ejecución tiene materia prima o si la sala de espera es
estructural. **La vara es descriptiva: no hay umbral de aprobación.
El entregable es el mapa, no un veredicto de adopción.**

## 2. Fuentes y arnés (sanidad obligatoria antes de clasificar)

- Corpus: los 166 hallazgos de `adjwork298/run298/prs/*/findings.json`
  reconstruidos con la fórmula publicada de la línea
  (`agent/lessons_compiler.py::load_corpus` + `born_candidate`:
  evidencia desde `git show <head>:<archivo>` sobre los clones
  parciales locales, categoría `correctness` con la invarianza ya
  probada del replay).
- La sala de espera se re-deriva ejecutando la puerta CONGELADA
  1.4.1 (`agent/alma_gate_v141.py`, POLICY `73a403d8…`, sin
  modificar) sobre los 166 candidatos reconstruidos.
- **Sanidad vinculante:** antes de clasificar nada, la
  reconstrucción debe reproducir EXACTO el replay publicado:
  0 aceptados / **149 retenidos** / 17 rechazados, y el cruce de
  gold de los retenidos **80 TP / 8 FPG / 16 GREY / 45 NOVEL**
  (adjudicación completa de la 298, `adjwork298/decisions.json`).
  Si la sanidad no cierra, el censo se detiene y se reporta: no se
  clasifica sobre un corpus equivocado.
- Gold: el veredicto de la adjudicación por emisión (`v` en
  `decisions.json`): TP (verdadero), FPG (falso confirmado), GREY
  (zona gris), NOVEL (sin veredicto en el gold).

## 3. Qué significa «decidible por ejecución» (definición operativa)

Un reclamo es decidible por ejecución cuando existe un procedimiento
observable cuyo resultado **difiere** entre el mundo en que el
reclamo es verdadero y el mundo en que es falso, y ese procedimiento
es **determinista**: corrido dos veces sobre el mismo estado da el
mismo veredicto (el estándar de la reproducción contra control:
reproduce siempre o no cuenta). Una reproducción flaky, una
inspección visual o un juicio de un lector no son oráculos de
ejecución.

La clasificación se hace **sobre el reclamo tal como fue escrito**
— su mensaje, su evidencia citada y el diff de su PR — porque una
vía de verificación tiene que anclarse en el propio reclamo. Si
decidir el reclamo exige primero arqueología en el repo para
descubrir qué correr, eso ya no es «directo»: es construcción (si
el reclamo alcanza como especificación) o no-ejecutable (si la
especificación habría que inventarla).

## 4. Taxonomía CERRADA (definida antes de mirar los datos)

### E1 — Ejecutable directo (oráculo existente e identificable)

El reclamo, tal como está escrito, señala un oráculo que **ya
existe** y cuya corrida, tal cual, lo decide:

- la evidencia citada es un archivo de test y el reclamo predice el
  resultado observable de correr ese test tal como está (pasa,
  falla, tira error, se saltea, depende de estado externo real);
- o el reclamo nombra un comando/herramienta con salida determinista
  (compilador, parser, linter, CLI) cuya ejecución decide la
  afirmación;
- o afirma una igualdad/desigualdad concreta entre artefactos
  decidible por ejecución directa de lo nombrado.

### E2 — Ejecutable con construcción (el reclamo alcanza como spec)

No hay oráculo existente identificado, pero el reclamo define
**entrada y salida/efecto esperado** con la concreción suficiente
para escribir la reproducción sin inventar la especificación:
nombra la entrada o el estado inicial y el observable esperado
(excepción, valor de retorno, efecto, salida) — incluidos los
reclamos contrafácticos sobre tests («las aserciones pasan aun si
la implementación estuviera rota»: la construcción es la corrida
con mutación) y los que predicen el resultado de correr el test
**modificado** (sin el doble, con otra entrada).

### E3 — No ejecutable en principio (sin oráculo ni spec construible)

La afirmación no tiene oráculo ejecutable ni reproducción
construible sin inventar la especificación:

- juicios de diseño, legibilidad, mantenibilidad, estilo o
  intención («debería», «es confuso», «duplica lógica» sin
  observable afirmado);
- afirmaciones de ausencia sobre el código («nunca se llama», «no
  se usa») cuya decisión es estática, no de ejecución, cuando el
  reclamo no plantea ninguna corrida que la decida;
- corrección lógica sobre caminos sin entrada ni observable
  definidos; afirmaciones sobre prosa/documentación como contenido;
- afirmaciones cuya verdad depende de semántica externa no
  ejecutable (una especificación en lenguaje natural no citada, el
  comportamiento de un servicio de terceros);
- reclamos de concurrencia/tiempos sin interleaving concreto y
  determinista afirmado (una reproducción no determinista no es
  oráculo).

### E4 — Inclasificable con la información del reclamo

Ni el mensaje ni la evidencia contienen la materia mínima para
asignarlo: referencias truncas, dependencia de contexto fuera de
la cita, o ambigüedad real entre una lectura ejecutable y una no
ejecutable sin señal que desempate. **E4 se declara, no se fuerza**
a otra clase.

### Reglas de borde (declaradas)

- **Gobierna la aserción central:** se clasifica por la afirmación
  que porta el defecto, no por menciones incidentales. Un reclamo
  con vocabulario de diseño Y una aserción ejecutable concreta se
  clasifica por la ejecutable; uno con vocabulario ejecutable de
  adorno y aserción central de juicio, por la de juicio.
- **Precedencia:** oráculo existente (E1) > construcción (E2) >
  no-ejecutable (E3). E2 exige AMBOS: entrada/estado y observable
  esperado nombrados; si falta uno, no es E2.
- **Tests como sujeto:** si el reclamo predice el resultado de
  correr el test tal como está → E1; si predice el resultado bajo
  una modificación (mutación, sin doble, otra entrada) → E2.
- **Performance:** vocabulario de performance sin workload y
  observable concretos → no es E2 (cae a duda, §5); con workload y
  observable nombrados → E2.
- **Ausencia:** afirmación de ausencia que el propio reclamo
  plantea como decidible por una corrida identificable (p. ej.
  cobertura sobre la suite existente) → E1/E2 según el oráculo;
  ausencia a secas → E3 o duda, nunca E1 por defecto.

## 5. El clasificador (script primero, revisión solo ante duda)

`agent/executability_census.py`, determinista. Por reclamo calcula
señales sobre (mensaje, evidencia, archivo, diff):

- archivo es test / es documentación; el mensaje nombra comando o
  herramienta; afirma resultado de runtime con literal concreto
  (excepción/error nombrado, «raises/throws», retorno esperado,
  «fails with», código de salida, estado HTTP); su sujeto es el
  comportamiento de un test; marcadores contrafácticos («even
  if», «still pass», «would»); vocabulario de diseño/juicio;
  vocabulario de concurrencia sin interleaving; vocabulario de
  performance; afirmación de ausencia.

**Regla de decisión del script:** un reclamo sale clasificado por
script SOLO si las reglas de exactamente una clase disparan y
ninguna regla de otra clase dispara en contra. En cualquier otro
caso — conflicto entre clases, ninguna señal, ambigüedad
contrafáctica — el script declara **DUDA** y el reclamo pasa a
**revisión asistida**: el agente ejecutor lo lee y lo asigna a
E1–E4 con una razón de una línea, asentada por reclamo. La revisión
asistida no llama modelos: es lectura del agente sobre el texto
del reclamo, con la misma taxonomía y las mismas reglas de borde.

**Se asienta por reclamo:** clase final, vía (script/revisión),
regla(s) que dispararon y, si fue revisión, la razón de una línea.
**Se reporta:** la fracción clasificada por cada vía y la
distribución de clases dentro de la revisión asistida. Ninguna
fracción objetivo se declara: el split es un resultado, no una
meta.

## 6. El cruce que importa

Por clase (E1, E2, E3, E4) × gold (TP, FPG, GREY, NOVEL), con la
tasa de TP por clase, y el titular en tres lecturas posibles,
declaradas de antemano:

- si E1+E2 **concentran TP** por encima de la tasa base de la sala
  (80/149), la vía de ejecución **rescata verdad**: su materia
  prima son justamente los verdaderos que la citación no pudo
  verificar;
- si E1+E2 concentran **FPG**, la vía sirve sobre todo para
  **descartar rápido**;
- si la distribución de gold por clase ≈ las tasas base, la
  ejecutabilidad es **ortogonal a la verdad** — y la espera es
  estructural en otro sentido: ni siquiera cambiar de instrumento
  separa verdaderos de falsos dentro de la sala.

También se reporta E1 separado de E2 (oráculo existente contra
construcción: el costo de la vía no es el mismo) y el cruce dentro
de la revisión asistida vs el script, por si la vía de
clasificación correla con la clase.

## 7. Salvedades (vinculantes para el resultado)

- **Clasificar no es verificar:** la clase afirma decidibilidad
  EN PRINCIPIO desde el reclamo escrito. No afirma que ejecutar el
  oráculo sea barato, ni que el veredicto de la ejecución vaya a
  coincidir con el gold, ni que la reproducción sea portable entre
  entornos. El censo mide la FORMA de los reclamos contra un
  instrumento posible; no corre ninguna reproducción.
- La clasificación de un reclamo NOVEL o GREY no dice nada sobre
  su verdad: dice si un oráculo podría decidirla.
- Ninguna puerta se modifica, ninguna adopción se decide, ninguna
  corrida se propone en este papel: el entregable es el mapa
  (PREREGISTRO + clasificador + RESULTADO con conteos y cruce).

## 8. Verificación y cierre

- La sanidad del §2 cierra exacta (149 y su cruce 80/8/16/45)
  ANTES de clasificar.
- Los conteos por clase suman 149; el cruce por clase suma, por
  columna, el gold de la sala (80/8/16/45).
- Suite completa verde; hashes de artefactos congelados
  byte-idénticos (puertas 1.0.0–1.5.0, `claim_contract.py`,
  `birth_shaper.py`, revisores v2.3/v2.4/v2.5).
- Commit LOCAL solamente (sin push); asiento en
  `REGISTRO-REVIEWBENCH.md`.

— Pre-registro del censo de ejecutabilidad, 2026-10-22. Gasto: **US$0**.
