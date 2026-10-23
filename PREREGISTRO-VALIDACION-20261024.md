# Pre-registro — Validación paga del 24/10/2026: base nº 298 contra v2.4, v2.5 y v2.6

**Fecha de este papel:** 2026-10-23 (preparación). **Corrida:**
2026-10-24. **Autorización:** Alejandro, 23/10/2026 — decisión
«No va a ser en enero, va a ser mañana la corrida» y su sí sobre
el total de la línea (~US$131) presentado en un solo número.
**Costo de esta preparación: US$0** — sin prácticas, sin cargas
de saldo, sin llamadas a modelos. La corrida misma es mañana y
la ejecuta otro paso.
**Orden obligatorio: este papel se escribe ANTES que cualquier
código de montaje** (la §3 declara ese delta antes de tocarlo).

## 1. Los brazos (finales, nombrados)

El examen es el mismo de siempre: la práctica «Test run» de
**25 PRs** del portal. **«Submit» JAMÁS** — en ningún brazo,
bajo ninguna circunstancia.

- **Base (referencia, NO se re-corre):** la corrida nº 298
  congelada — revisor `llm-reviewer/2.3.1`, sin puerta.
  Medido y adjudicado: **P grounded 53,6 % (89/166),
  R 18,75 % (66/352 TP del gold), neto crudo +81**
  (`RESULTADO-PUNTAJE-NETO-20261023.md`). Todo brazo nuevo se
  compara contra estos números, con el mismo procedimiento de
  adjudicación de las nº 298/311.
- **Brazo v2.4:** revisor `llm-reviewer/2.4.0` (productor con
  disciplina de evidencia, `PREREGISTRO-PRODUCTOR-EVIDENCIA.md`)
  **con puerta 1.5.0** (`alma-evidence-gate/1.5.0`).
- **Brazo v2.5:** revisor `llm-reviewer/2.5.0` (el v2.4 + el
  contexto de lecciones leído en producción,
  `PREREGISTRO-MEMORIA-LECCIONES.md`) **con puerta 1.5.0**.
  La comparación v2.4↔v2.5 aísla el efecto de las lecciones.
- **Brazo v2.6:** revisor `llm-reviewer/2.6.0` (el v2.5 + el
  contexto de ausencias, `ADENDA-V26.md`) **con puerta 1.5.0**.
  La comparación v2.5↔v2.6 aísla el efecto de las ausencias.

**Config de portal por brazo** (idéntica a la de la nº 298 en
todo lo que no es el brazo): backend `llm`, modelo
**gpt-5.6-sol**, esfuerzo **medium**, modo `alma`,
`RB_CONFIG_REVIEWER` = `v24`/`v25`/`v26` según el brazo,
`RB_CONFIG_GATE` = `v150`, y el freno por PR
**`RB_MAX_SPEND_USD` = US$6,50 — intocable**, el de siempre.

## 2. La vara por brazo (la del diseño estacionado + la adenda del neto)

La de `PREREGISTRO-PRODUCTOR-EVIDENCIA.md` §4, sin mover un
número: (1) **conformidad al nacer** de la producción (emitidos
en forma de contrato / candidatos producidos, con el ledger de
producción completo como recibo); (2) **precisión y recall
grounded por adjudicación completa** contra el gold público,
con el mismo procedimiento de las adjudicaciones de las
nº 298/311; (3) la **fracción en `needs_validation`** del
pipeline compuesto (producción + puerta) contra la vara de la
línea: **< 50 %**; (4) **discriminación reportada sin umbral**
(muerte de FP gold contra muerte de TP); (5) **integridad**:
cero evidencia inventada, auditada como en los papeles
anteriores.

**Más la adenda del neto** (`ADENDA-PUNTAJE-NETO.md`, vigente):
el neto (crudo y por 100 emisiones, computado con
`agent/net_score.py`) se reporta junto a P/R en todo papel de
la corrida, y **un brazo con neto crudo ≤ 0 no puede declararse
mejora aunque gane en precisión**. El neto es métrica
secundaria: nunca adopta ni rechaza solo.

## 3. El delta de montaje (declarado antes del código)

Hecho verificado hoy: los brazos están **diseñados pero no
montados** — `agent/main.py` selecciona revisores solo hasta
`v23` y su `_select_gate` admite puertas solo hasta `v141`;
el resolvedor del lado del revisor (`_resolve_gate_v23`)
también termina en `v141`. Sin este delta, ninguna config de
la §1 corre: moriría fail-closed antes de la primera llamada,
como la nº 310. El delta es de **admisión**, del mismo tipo
que el de la Adenda 4 (que reparó la admisión `v141`), y es
exactamente este, ni un archivo más:

1. **`agent/main.py`** (el runner; no es un archivo congelado
   y ya fue extendido por papeles declarados: el registro de
   sesión): la selección de revisor gana las ramas `v24`,
   `v25` y `v26` espejando la de `v23`; `_select_gate` gana la
   rama `v150` (`AlmaGateV150`); `_selected_gate_identity`
   gana la identidad `v150`; mensajes de error actualizados.
2. **`agent/llm_reviewer_v24.py`**: un resolvedor propio
   `_resolve_gate_v24` — la rama `v150` devuelve las 19 clases
   de la familia (`KNOWN_CLAIM_TYPES_V13` = el conjunto de la
   1.5.0, verificado por programa) con su guía y la versión
   `alma-evidence-gate/1.5.0`; todo lo demás **delega** en
   `_resolve_gate_v23` sin tocarlo. `LLMReviewerV24.from_env`
   pasa a usarlo; el v2.5 y el v2.6 lo heredan (ninguno define
   `from_env` propio).
3. **Tests nuevos** que fijan las tres admisiones y el
   extremo a extremo en seco (transporte guionado, US$0):
   selección de revisor, puerta e identidad; el resolvedor
   nuevo; y una corrida `run_agent` completa (modo `alma`,
   revisor v2.6, puerta v150) con el registro de sesión
   activo. Suite completa corriendo entera.

**Lo que NO cambia:** `llm_reviewer_v23.py` y todas las
puertas 1.0.0–1.5.0, `claim_contract.py`, `birth_shaper.py`,
los revisores v2.5/v2.6, los compiladores y los contextos —
byte-idénticos, verificados por sha256 antes y después.
**Declaración adicional del mismo delta:** las tablas de
congelados de `tests/test_llm_reviewer_v25.py` y
`tests/test_llm_reviewer_v26.py` fijan el hash de
`llm_reviewer_v24.py` de su construcción (`ae378c2e…`); como
este montaje cambia ese archivo, **este papel re-fija ese
único valor en ambas tablas al hash nuevo**, asentado en el
resultado de la preparación. Los `RESULTADO` de v2.5 y v2.6
quedan como el registro histórico de los bytes de su
construcción; ningún otro valor de esas tablas se toca. Los
`REVIEWER_VERSION` quedan como están (`2.4.0`/`2.5.0`/`2.6.0`):
el delta agrega la admisión de una config que **nunca pudo
correr** — no altera ningún comportamiento medido — y la
identidad exacta del código la fijan el digest de la imagen
y los hashes asentados en el papel de la corrida, como en
toda la línea.

## 4. La imagen (una sola, tres configs)

El `Dockerfile` copia todo `agent/`: como en toda la línea
(la nº 298 base y la nº 311 ALMA compartieron imagen y
difirieron solo en config), **una sola imagen nueva** lleva
los tres revisores y las tres configs de la §1 la seleccionan.
**Delta de imagen declarado acá, antes de tocarlo:** los
revisores v2.5 y v2.6 resuelven su contexto en
`Path(__file__).parent.parent / "CONTEXTO-*.md"` — en la
imagen, `/app/CONTEXTO-LECCIONES.md` y
`/app/CONTEXTO-AUSENCIAS.md` — y el `Dockerfile` actual solo
copia `agent/`: sin los dos artefactos en la raíz de la
imagen, ambos brazos morirían fail-closed al construirse,
antes de cualquier llamada (la muerte de la nº 310 por otra
vía). El delta es una línea del `Dockerfile` —
`COPY CONTEXTO-LECCIONES.md CONTEXTO-AUSENCIAS.md /app/` —
sin tocar ningún revisor, y su verificación es un test que
construye los tres revisores desde un árbol copiado con el
layout exacto de la imagen.
Publicación por el pipeline asentado: el paquete se sincroniza
a `main` de `almaoficial/alma-reviewbench`, el workflow
`reviewbench-image` se dispara por `workflow_dispatch`
(**compuerta humana por diseño**: la UI de GitHub Actions con
la sesión de Alejandro) y el digest se verifica en **dos
fuentes** — el resumen de la corrida de Actions y la página
del paquete en GHCR — antes de asentarse. Ese digest es el
`RB_IMAGE_SHA256` de las tres configs.

## 5. El procedimiento de mañana, por intento

1. **Compuerta de saldo:** saldo de la cuenta verificado
   **≥ US$25 antes de lanzar cada brazo** (la compuerta de la
   línea desde la Adenda 2). La carga es de Alejandro; sin
   carga verificada no se lanza.
2. **`RB_RUN_ID` único por intento** (p. ej.
   `validacion-20261024-v24`), **`RB_IMAGE_SHA256`** = el
   digest publicado de la §4, en la config de cada brazo.
3. **Un solo lanzamiento por brazo.** Nada de «Submit».
4. **`run-ledger.jsonl` es salida requerida**: se recolecta
   por cada PR de cada brazo (el registro viene prendido por
   defecto en el runner; si no puede abrirse, la corrida lo
   anuncia por stderr y esa ausencia queda asentada).
5. Al cierre de cada brazo: reconciliar el `spend` estimado
   del registro contra el **saldo real** de la cuenta en el
   papel de la corrida.

## 6. La regla de adjudicación (vinculante)

**Ninguna corrida se adjudica si su registro de sesión no
audita completo.** Antes de adjudicar un brazo se corre
`verify_chain` (integridad) y `audit_completeness`
(completitud: una decisión por candidato, sesiones cerradas)
sobre cada `run-ledger.jsonl` recolectado. Si la auditoría
falla, la corrida **se diagnostica, no se adjudica** — la
lección de la nº 311, cuya pureza de retención quedó sin medir
porque el portal no persistió el ledger. Con la auditoría en
verde: adjudicación completa contra el gold con el
procedimiento de las nº 298/311, vara de la §2 y neto por la
adenda.

## 7. La economía (estimada desde lo asentado)

Costo por brazo a los precios medidos de la línea: la nº 298
costó **US$20,41** y la nº 311 **US$20,27** → cada brazo de
mañana se estima en **~US$20–21**; los tres, **~US$61**. La
línea completa, en un solo número como mandó Alejandro:
**~US$70 ya gastados (21–22/10) + US$0,1290 del juez modelo
(ya corrido el 23/10) + ~US$61 de mañana ≈ US$131**. Saldo de
la cuenta al 22/10: **US$5,31** — la carga que falta es de
Alejandro y es el paso (a) de mañana.

## 8. Altos y falsadores

Si un brazo muere por causa propia (admisión, parseo, freno),
se registra igual, con su costo real — y no se relanza «hasta
que salga»: ninguna corrida de esta línea se repite por
resultado (la única excepción histórica es el corte de
infraestructura, declarado en el acto). Si la imagen no está
publicada y verificada, no hay corrida: se corre con lo
publicado o no se corre.

— Pre-registro de la validación del 24/10/2026, escrito el
2026-10-23 antes del código de montaje. La preparación cierra
en `RESULTADO-PREPARACION-20261024.md`.
