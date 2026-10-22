# Pre-registro — Puerta 1.4.1: el chequeo (f) vuelve a ser rechazo firme

**Fecha:** 2026-10-21 · **Aprobación:** Alejandro, 21/10/2026
(«Si hacelo» a la propuesta de escribir este papel).
**Estado:** CONGELADO al escribirse. **Este documento es SOLO PAPEL: no
existe código de la 1.4.1, y escribirlo no autoriza implementarla.**
Construirla requiere el «sí» de Alejandro a este papel, como fue con
la 1.4.0. Toda corrección posterior es una adenda fechada, nunca una
edición silenciosa.
**Antecede:** `PREREGISTRO-PUERTA-140.md` (congelado 2026-10-21),
`RESULTADO-MEDICION-PUERTA-140.md` (medición de adopción de la 1.4.0:
**NO ADOPTADA**), `PREREGISTRO-REVIEWBENCH-V23.md` §4 (el brazo ALMA
de la v2.3 está atado a la adopción de la puerta del tercer estado,
sin sustitución silenciosa).

## 1. El antecedente medido (por qué existe este papel)

La puerta 1.4.0 se construyó fiel a su papel y se midió contra su
propio criterio de adopción (§6 de su pre-registro). El resultado,
asentado en `RESULTADO-MEDICION-PUERTA-140.md`:

- **VP recuperados = 4** (el candidato `sql_injection` de sem_01 en
  ambos brazos de ambas corridas asentadas): el tercer estado
  recupera, confirmado, el verdadero que la binaria perdía.
- **Equivalencia de aceptados: exacta en los tres universos.**
- **Falsos en el universo 1 (corridas reales): 0.**
- **Falsos nuevos = 1** — y ese único falso alcanza para la no
  adopción, porque el criterio es conjuntivo.

El falso es **S3**, un ataque de la batería roja de la 1.3.0:
`sql_injection`, «cita una línea de CONTEXTO — el PR no introduce el
defecto». El candidato cita líneas de contexto donde esqueleto y
construcción SQL **sí co-ocurren en la misma línea citada** — el
chequeo de soporte de la 1.3.0 pasa — y el **único** chequeo que
falla es el (f) de la Adenda 2 del papel v2: «sin línea agregada».
La §3(5)(c) del papel de la 1.4.0 incluyó ese chequeo entre los de
**completitud de evidencia** que habilitan `needs_validation`, y la
§6 de ese mismo papel cuenta cualquier movimiento de estado en la
batería roja como falso nuevo. Leídas literalmente, las dos
secciones producen el veredicto: la frontera pre-registrada deja
pasar exactamente un falso a la sala de espera — una inyección real
pero **preexistente**, que el cambio bajo revisión no introduce.

La 1.4.0 no se re-afina contra ese resultado: su papel lo prohíbe
(«cualquier cambio de frontera es papel nuevo y medición nueva»).
Este es ese papel nuevo.

## 2. El cambio exacto (único, mecánico)

**El chequeo (f) «sin línea agregada» SALE del conjunto de chequeos
de completitud que habilitan `needs_validation`.**

En la frontera de la 1.4.1, el enrutamiento del chequeo (f) queda
así, sin opinión y sin excepciones:

- Si la evidencia citada por un candidato **no contiene ninguna
  línea agregada por el cambio** (ninguna línea citada proviene del
  lado agregado del diff), el candidato es **RECHAZO FIRME** en la
  frontera: nunca `needs_validation`, nunca candidato, nunca sala de
  espera.
- El rechazo por (f) **domina**: un candidato que falla (f) y
  también fallaría un chequeo de completitud (a) o (b) de la
  §3(5) del papel 140 queda rechazado — (f) no se asienta como un
  blocker más, porque ya no es un blocker: es una causal de rechazo.
- Los únicos chequeos cuyo fallo habilita `needs_validation`
  quedan siendo los de completitud **(a)** co-ocurrencia y **(b)**
  construcción fuera del span citado, en los términos exactos de la
  §3(5) del papel 140. Todo lo demás de esa frontera — las cinco
  condiciones, el registro sin `severity`, los blockers con su
  requisito de confirmación, la sección separada del ledger, el
  determinismo — se hereda **sin retoques**.

**Fundamento declarado.** `needs_validation` existe para defectos
**del cambio** que el revisor ve pero no puede probar con la
evidencia citada: la prueba existe en principio y falta completarla.
Un defecto que el cambio **no introduce** no admite esa lectura: no
hay evidencia del diff que lo convierta en hallazgo de esta
revisión, porque no es un hallazgo de esta revisión. Retenerlo no
es prudencia — es contaminación: ensucia el ledger del tercer
estado y, aguas abajo, la métrica de **pureza de la retención** del
papel v2.3 (§6, componente 3: de lo que ALMA retenga o rechace, a
lo sumo 1 de cada 3 puede ser un TP grounded), contando como
«retenido» algo que la gobernanza jamás debió considerar.

**Nota de origen (esto no es un ajuste contra un fixture).** El
chequeo (f) nació en la Adenda 2 del papel v2 como causal de
**rechazo** dentro de la línea 1.3.0 — y en la medición de la 1.4.0
es exactamente así como la 1.3.0 trata a S3: rechazado. Fue el
papel de la 1.4.0 el que lo reclasificó como chequeo de completitud
al redactar su §3(5)(c). La 1.4.1 no inventa una regla para tapar
un caso: **revierte una reclasificación** y devuelve el chequeo a
la función que tuvo en toda la línea anterior. La regla subyacente
— un hallazgo de una revisión es un defecto que el cambio bajo
revisión introduce — es un principio general de revisión de código,
se aplica uniformemente a todo candidato, y ninguna parte de este
papel se diseñó contra el detalle de ningún PR, ninguna práctica
ni el set dorado.

**Alcance del cambio.** El cambio opera sobre la frontera de
candidatos **de clase** de la §3 del papel 140, que es donde el
chequeo (f) vivía. La extensión del tercer estado a hallazgos
generales que declara el papel v2.3 §4 (blocker
`sin_regla_de_verificacion_en_puerta`) **no se toca** en este papel:
cualquier cambio ahí es materia de adenda al papel v2.3, no de este
pre-registro.

## 3. Qué NO cambia

- **Las puertas 1.0.0–1.3.0, byte a byte, para siempre** — y también
  **la 1.4.0**, que queda intacta como artefacto construido y medido
  (`POLICY_VERSION: alma-evidence-gate/1.4.0`, `POLICY_SHA256:
  b0c0aa661f644b5229ea3ee1984b3fd2dbb17649d1eeae91e5945fd357fd6d19`).
  Su NO adopción es un resultado asentado, no un borrador que se
  corrige encima. La 1.4.1, si nace, nace al lado — nunca encima de
  ninguna de las anteriores.
- **Las 19 clases** y cada regla de evidencia de la 1.3.0, heredadas
  por delegación sin retoques. Ninguna clase nueva entra por este
  papel, y ningún otro chequeo de la frontera se mueve: el §2 es el
  cambio completo.
- **El tercer estado y su regla de puntuación:** `needs_validation`
  no cuenta como hallazgo emitido ni entra a numerador ni
  denominador en el portal (§5 del papel 140, heredado sin cambios);
  la pasada de validación sigue definida ahí y sigue **inactiva
  hasta medirse aparte**. Este papel no la activa ni la redefine.
- **El productor de candidatos y los frenos:** sin cambios (esto es
  un papel de puerta; juzgar con la puerta es local y cuesta US$0).
- **Las prohibiciones anti-pesca:** nada de afinar ninguna frontera
  contra el detalle por PR de ninguna práctica ni contra el set
  dorado (privado, nunca visto). Y la regla que mató la re-afinación
  de la 1.4.0 rige igual aquí: si la medición del §4 no da adopción,
  este papel no se edita contra su propio resultado — cualquier
  nuevo intento es papel nuevo, medición nueva y decisión nueva.

## 4. La medición de adopción (pre-registrada aquí)

**Pregunta:** ¿recupera el tercer estado, con (f) como rechazo
firme, los mismos verdaderos que recuperó la 1.4.0 sin dejar pasar
ningún falso?

**Universos:** los mismos tres del §6 del papel 140, congelados, y
la medición se corre **completa de nuevo** — no se hereda ningún
conteo de la medición anterior:

1. La batería del semáforo (candidatos asentados del revisor v2.1,
   `runs/semaforo-v21-20261021/`, y muestra secundaria
   `runs/semaforo-intento3/`), re-juzgados offline contra la 1.3.0.
2. La batería roja de la 1.3.0 (69 ataques, Adenda 3 del papel v2).
3. La suite completa vigente, equivalencia sobre fixtures legítimos
   y adversarios.

**Definiciones de conteo:** las del §6 del papel 140 (VP
recuperado, falso nuevo — en el universo 2, cualquier ataque que se
mueva de estado; en el 3, cualquier adversario que se mueva — y
equivalencia de aceptados), con una precisión que este papel
agrega: **los únicos movimientos de estado esperados en toda la
medición son los VP del universo 1** (rechazado → `needs_validation`
por completitud (a)/(b)). En los universos 2 y 3 el mapa de estados
esperado es **idéntico** al de la 1.3.0, candidato por candidato —
en particular, **S3 debe quedar rechazado, sin movimiento**, con el
chequeo (f) asentado como su causal de rechazo firme.

**Criterio de adopción (escrito antes de medir):** la 1.4.1 se
adopta **si y solo si** se cumplen las cuatro, en conjunto:

1. **VP recuperados = 4** — los mismos 4 de la medición de la
   1.4.0, sobre los mismos universos congelados. Perder cualquiera
   es no-adopción: con los universos idénticos, el conteo es
   reproducible, y una reparación de enrutamiento no puede costar
   ni un verdadero.
2. **Falsos nuevos = 0 en los tres universos**, con S3 resuelto
   como rechazo firme (sin movimiento de estado).
3. **Equivalencia exacta de aceptados con la 1.3.0** en los tres
   universos.
4. **Suite completa verde**, incluyendo los tests nuevos del
   enrutamiento (f), por categoría: (i) caso tipo S3 — evidencia
   citada sin línea agregada, soporte presente — → **rechazo
   firme**, sin registro `needs_validation`; (ii) caso tipo VP —
   línea agregada presente en la cita y co-ocurrencia partida entre
   líneas citadas — → sigue `needs_validation` con su blocker de
   completitud; (iii) caso mixto — falla (f) y falla (a) — →
   rechazo firme (dominancia de (f)).

**Costo de la medición:** US$0, offline y determinista, como la
anterior. Este papel no autoriza ningún gasto ni ningún semáforo
con modelos reales.

## 5. Falsadores (qué mata a la 1.4.1)

- **VP recuperados < 4** en la medición del §4 → no se adopta.
- **Cualquier falso nuevo** en cualquier universo → no se adopta:
  la sala de espera sigue filtrando.
- **Equivalencia de aceptados rota** en cualquier universo → no se
  adopta: la neutralidad de puntaje es la garantía central del
  tercer estado.
- **Cualquier movimiento de estado no explicado por el cambio (f)**
  — es decir, cualquier diferencia de veredictos entre la 1.4.1 y
  la 1.3.0 fuera del conjunto exacto que el §2 predice (los VP por
  completitud (a)/(b) en el universo 1, y nada más) → no se adopta,
  aunque los conteos cierren: un efecto no declarado es una frontera
  distinta de la pre-registrada.
- **Suite no verde**, o tests nuevos del enrutamiento (f) no verdes
  → no se adopta.
- La frontera con el cambio del §2 no se puede implementar sin una
  sola decisión de juicio (qué cuenta como «línea agregada» ya está
  definido mecánicamente por el diff y la cita, igual que en la
  Adenda 2(f); si apareciera un caso que exigiera opinar) → muere
  en el papel: la puerta no opina.

## 6. Camino declarado hacia el brazo ALMA (sin sustitución silenciosa)

El papel v2.3 §4 ató su brazo ALMA a la puerta 1.4.0 y a su
criterio de adopción, y declaró: si la 1.4.0 no se adopta, el brazo
no corre y **no hay sustitución silenciosa por la 1.3.0**. Esa
declaración sigue vigente y este papel no la afloja. El camino
desde la 1.4.1 hacia ese brazo es, completo y en orden:

1. **Construcción de la 1.4.1** (solo con el «sí» de Alejandro a
   este papel): módulo nuevo `agent/alma_gate_v141.py`, selección
   `RB_CONFIG_GATE=v141`, `POLICY_VERSION:
   alma-evidence-gate/1.4.1`, su POLICY_SHA256 asentado en la
   adenda de construcción; el default del paquete no cambia y
   ninguna puerta anterior se toca.
2. **Medición de adopción del §4.** Si no adopta, el camino termina
   aquí (ver el párrafo final de esta sección).
3. **Adenda firmada al `PREREGISTRO-REVIEWBENCH-V23.md`**, anterior
   a cualquier corrida ALMA, que declare expresamente: (a) el
   reemplazo de la 1.4.0 por la 1.4.1 como puerta del brazo ALMA de
   la v2.3, con este papel y su resultado de medición citados; y
   (b) la etiqueta `gate` que llevará la config ALMA en el portal.
   **Etiqueta propuesta: `gate=v141`.** Justificación: el historial
   de etiquetas sigue la versión de política — `v13` = puerta
   1.3.0, `v14` = puerta 1.4.0 — y `v14` queda para siempre atada al
   artefacto 1.4.0 tal como fue construido y medido; reusarla para
   la 1.4.1 sería exactamente la sustitución silenciosa que los
   papeles prohíben, porque dos puertas distintas compartirían una
   sola etiqueta en el portal. `v141` codifica la línea de parche
   (familia 1.4.x), es inequívoca y ordena después de `v14`; la
   config ALMA llevaría entonces `reviewer=v23` (sin cambio) y
   `gate=v141`. Sin esa adenda firmada, la 1.4.1 — aun adoptada —
   **no se usa** en el brazo ALMA.

**Si la 1.4.1 no se adopta:** el brazo ALMA de la v2.3 no corre,
igual que con la 1.4.0, y **no hay 1.4.2 automática**. Cualquier
nuevo intento sobre esta frontera es una decisión nueva de
Alejandro, con su papel nuevo: la cadena de reparaciones no se
auto-perpetúa.

## 7. Alcance honesto y orden de ejecución

- **Lo que la 1.4.1 es:** la corrección del enrutamiento de un caso
  de frontera. Nada más.
- **Lo que la 1.4.1 no es:** una mejora de detección. No recupera
  ningún verdadero que la 1.4.0 no recuperara (el criterio del §4
  exige exactamente los mismos 4), no agrega clases, no toca al
  revisor ni sus prompts, y no mueve el puntaje de nadie: adoptada,
  su emisión sigue siendo idéntica a la de la 1.3.0. Su único efecto
  es que la sala de espera deje de admitir defectos que el cambio
  bajo revisión no introduce.
- **Orden de ejecución futuro (compuertas, en orden):** este papel
  → «sí» de Alejandro a este papel → construcción declarada en
  adenda → medición del §4 → decisión de adopción → (solo si
  adopta) adenda al papel v2.3 del §6 → recién ahí, cualquier uso
  en el portal queda habilitado a decidirse. Ningún paso salta al
  siguiente, y ningún paso de esta cadena autoriza gasto: la
  medición es offline y cuesta US$0.
