# Pre-registro — Productor con disciplina de evidencia: el revisor v2.4

**Fecha:** 2026-10-22 · **Autorización:** Alejandro, 22/10/2026
(«Lo hagamos») tras el resultado del formador al nacer.
**Costo de este papel y de la construcción que pre-registra:
US$0** — diseño y construcción en seco; sin llamadas a
modelos, sin portal, sin cargar plata, sin publicación.
**Orden obligatorio de este papel: este documento se escribe
ANTES que el código** (`agent/llm_reviewer_v24.py`), y lo que
la §5 declara verificable en seco queda fijado antes de
construir.

## 1. El antecedente medido (por qué existe este papel)

La cadena gratis cerró su diagnóstico en tres pasos y el
último señaló fuera de la capa de formación:

- La **puerta 1.5.0** emite por la vía general, pero su vara
  **NO PASA**: 133/166 en espera, con dos blockers que son
  propiedades del nacimiento — 71 `sin_patron_concreto` y
  62 `tokens_afirmados_ausentes`.
- El **contrato de reclamos** midió el techo a posteriori:
  **49/166** conformables sin inventar evidencia; los 49
  pasaron la puerta enteros (49/49). El cuello quedó en el
  nacimiento.
- El **formador al nacer** (`PREREGISTRO-REVISOR-CONTRATO.md`,
  `RESULTADO-REVISOR-CONTRATO-20261022.md`) llevó la
  conformidad a **80/166** y la precisión entre emitidos a
  **55,7 %**, pero la vara global **NO PASA** (espera
  compuesta 51,8 % contra < 50 %), y su §6 asienta la
  lectura final: el cuello ya no es la **forma** sino la
  **materia** — **86 reclamos nacen sin nada citable que
  afirmar** (54 sin patrón en la prosa, 32 afirmando solo
  tokens que su cita no contiene), entre ellos **44 de los
  89 TP** del corpus. El revisor afirma cosas ciertas sin
  citar evidencia verificable, y ninguna capa determinista
  posterior puede crear esa evidencia sin inventarla.

Este papel construye el paso que el §6 del papel del
formador dejó nombrado: **cambiar la producción del revisor
para que los candidatos nazcan citando** — disciplina de
evidencia en el esquema de emisión y en el prompt, con la
capa de formación al nacer como última etapa de producción.

## 2. El diseño del revisor v2.4

**Identidad:** `REVIEWER_VERSION = "llm-reviewer/2.4.0"`,
`name = "alma-llm-reviewer-v24"`, módulo nuevo
`agent/llm_reviewer_v24.py`. El revisor v2.3.2
(`agent/llm_reviewer_v23.py`) queda **intacto y
byte-idéntico**: todas las corridas medidas de la línea
siguen reproducibles. Lo que NO cambia contra el v2.3 es
todo lo demás: la selección generalizada (su prompt se
importa sin modificar — marcar no afirma, y la disciplina
de evidencia no aplica a la etapa que solo marca), el tope
compartido `MAX_DEEP_PASSES`, la guardia de dos etapas y la
regla de degradación, el chequeo acumulativo de costo que
falla cerrado, la resolución de puerta
(`_resolve_gate_v23`, importada: v1…v141, las 19 clases y
su guía como familia de especialidad), el contrato de
payload (sin `temperature`, sin `max_tokens`,
`max_completion_tokens`, `response_format` JSON) y el
**freno por PR** (`RB_MAX_SPEND_USD`, configuraciones
existentes sin cambios).

### (a) El esquema de emisión evidence-first

Cada pasada profunda (de clase o de categoría) y la pasada
mixta del caso degenerado responden un único objeto JSON
con DOS arreglos:

```json
{"findings": [{"file": "path/in/repo.py", "start_line": 12,
               "end_line": 12, "claim_type": "sql_injection",
               "message": "what is wrong and why; the asserted
                           tokens stand in `backticks`",
               "pattern": ["token_copied_from_line_12"],
               "evidence": ["the exact text of line 12"]}],
 "unverifiable": [{"file": "path/in/repo.py", "start_line": 30,
                   "end_line": 30, "claim_type": "sql_injection",
                   "message": "what is suspected and why",
                   "reason": "why no citable lines support it"}]}
```

- `findings` es el esquema del v2/v2.3 (file, rango,
  claim_type, message, evidence con las líneas exactas del
  head) **más un campo nuevo, `pattern`**: la lista de
  tokens de código que el reclamo afirma, **copiados
  verbatim de las líneas citadas** en `evidence`. El
  `message` envuelve cada token del patrón en backticks y
  no afirma ningún otro token entre backticks (el patrón
  afirmado del mensaje — el que el contrato C1 lee — es
  exactamente el declarado).
- `unverifiable` es la vía de declaración del modelo: un
  defecto que cree real pero que **no puede sostener con
  líneas citables** se lista ahí, con los campos que pueda
  dar y un `reason`. Nunca entra en `findings` disfrazado.

### (b) Los cambios de prompt

La plantilla de pasada profunda es nueva
(`_SYSTEM_PROMPT_TEMPLATE_V24`; la del v2 queda para el
v2) y la pasada mixta tiene su versión v2.4; ambas llevan,
con el mismo texto, la disciplina de evidencia:

1. **Primero las líneas, después el reclamo:** elegir las
   líneas exactas que prueban el defecto y escribir el
   reclamo solo desde esas líneas.
2. **Afirmar solo lo visible en las líneas citadas:** el
   patrón se copia verbatim de la cita; el mensaje no
   afirma ningún token, comportamiento ni hecho que no
   aparezca en las líneas citadas.
3. **Lo no citable se declara, no se disfraza:** si el
   patrón no aparece en ninguna línea citable, el defecto
   va en `unverifiable` con su razón — una declaración,
   nunca un hallazgo.

La guía de clase/categoría es la heredada sin cambios (la
de las 19 clases, byte-idéntica a la del v2 vía el v2.3; la
de categorías, la pública del v2.3 con su «Report only
defects of this category.»). La selección no lleva cambios:
su prompt sale byte-idéntico al del v2.3 para los mismos
insumos (verificable por test).

### (c) La mecánica del revisor y el ledger de producción

La conversión de cada emisión cruda sigue la disciplina
heredada y agrega los caminos del esquema nuevo, en este
orden declarado:

1. **Forma y ancla (heredado, sin cambios):** tipos y
   rangos válidos, `claim_type` igual a la marca de la
   pasada (o dentro de las marcas, en la mixta), y la
   evidencia exactamente igual a las líneas del head —
   los incumplimientos cuentan como `malformed_findings` /
   `unanchored_findings` y se descartan, como en el v2.3.
2. **Sin patrón declarado:** `pattern` ausente, no lista, o
   vacío tras la normalización de la 1.5.0 (la tokenización
   es la de la línea, importada sin modificar) → el
   hallazgo **nace marcado no verificable en origen**: se
   asienta en el **ledger de producción** con el código
   `sin_patron_concreto_en_el_reclamo`. No se emite, no
   cuenta como malformed, no desaparece.
3. **Patrón declarado ≠ patrón afirmado:** el conjunto
   normalizado declarado difiere del conjunto de tokens
   entre backticks del mensaje → ledger de producción,
   código `patron_declarado_distinto_del_mensaje`. No se
   emite: el revisor no elige en silencio cuál de las dos
   afirmaciones del modelo vale.
4. **Declarado por el modelo:** cada entrada de
   `unverifiable` con forma identificable (dict con
   `claim_type` y `message` strings) → ledger de
   producción, código
   `declarado_no_verificable_en_origen`, con el `reason`
   del modelo asentado. Las entradas sin forma identificable
   cuentan como `malformed_findings` (fallan la forma del
   esquema, como en la disciplina heredada).
5. **El resto nace candidato** (`rule_id`
   `llm_v24_<tipo>`, productor `alma-llm-reviewer-v24`),
   con la deduplicación heredada del v2.3. Que un token
   declarado esté ausente de la cita NO se juzga acá: es el
   paso siguiente.

**La capa de formación al nacer corre como última etapa de
producción** — `birth_shaper.shape_candidates` (SIN
MODIFICAR) sobre todos los candidatos recolectados, con el
diff a la vista, antes de que el revisor devuelva nada y
antes de cualquier puerta:

- Lo que el formador entrega en forma de contrato **es** la
  producción del v2.4 (con su recorte en origen asentado:
  los tokens recortados se cuentan en el run info).
- Lo que el formador **declara no verificable en origen**
  se asienta en el ledger de producción con el código del
  propio formador (`tokens_afirmados_ausentes_en_la_evidencia`
  o `sin_patron_concreto_en_el_reclamo`): la producción
  completa — modelo más formador — declara al nacer todo
  lo que no puede citar, con su razón, y nada de eso llega
  a una puerta disfrazado.
- Declarado: **no hay deduplicación posterior a la
  formación** en este papel (la disciplina de duplicados
  del pipeline vive en la puerta, como siempre).

El run info (`LLMRunInfoV24`) extiende el del v2.3 con el
ledger de producción (`production_ledger`: pasada, tipo,
archivo, rango, código, razón) y el asiento de la etapa de
formación (`shaping`: emitidos, retenidos en origen, tokens
recortados, orígenes). Todo lo asentado viaja en `to_dict`.

### (d) Qué no se monta en este papel

`agent/main.py` **no se toca**: el v2.4 no entra al ruteo
del montaje ni a ninguna imagen o config. Montarlo es
decisión del papel de corrida (§4), como lo fue integrar
el formador. Este papel deja el revisor construido, con su
arnés de medición listo y su batería en seco verde (§5).

## 3. LA SALVEDAD HONESTA (escrita antes de construir)

**El efecto de la disciplina de evidencia sobre la tasa de
reclamos citables NO se puede medir en seco.** Esa tasa es
una propiedad de lo que un modelo real hace con el prompt
nuevo — cuántos de sus reclamos nacen con patrón copiado
de su cita, cuántos declara no verificables, cuántos
siguen afirmando fuera de su cita — y ningún transporte
guionado la mide: la guionaría el propio arnés. Lo que
este papel SÍ mide en seco, y es todo lo que reclama:

- la **corrección mecánica del esquema**: que un hallazgo
  con cita válida y patrón declarado nace candidato y sale
  de la etapa de formación **conforme al contrato**
  (verificado con `claim_contract` y la puerta 1.5.0, sin
  modificar), y que cada camino de no-citabilidad nace
  **marcado y asentado**, nunca emitido ni perdido;
- que el **prompt armado contiene** las instrucciones de
  evidencia (verificable por inspección del string, sin
  llamar a ningún modelo);
- la **batería semáforo en seco** (§5) y la suite completa
  sin regresiones;
- que el **arnés de medición queda listo** para la
  validación paga (§4): mismos corpus, misma adjudicación,
  misma vara declarada de antemano.

**Ningún número de efecto se reclama en este papel** —
ninguna conformidad esperada, ninguna precisión proyectada.
Si alguien lee en este diseño una promesa de que la espera
baja del 50 %, está leyendo lo que el papel no dice.

## 4. La validación paga futura — SOLO diseño, no se ejecuta

Cuando Alejandro lo decida, con papel de corrida nuevo:

- **A/B sobre los mismos 25 PRs** de la práctica: brazo base
  = revisor v2.3.2 sin puerta (la base medida de la nº 298);
  brazo nuevo = revisor v2.4 con la puerta 1.5.0. La
  comparación histórica contra la nº 298 es la referencia;
  si el papel de corrida prefiere re-correr la base, lo
  declara ahí.
- **Vara declarada desde ya para esa corrida:**
  (1) conformidad al nacer de la producción del v2.4
  (emitidos en forma de contrato / candidatos producidos,
  con el ledger de producción completo como recibo);
  (2) precisión y recall grounded por **adjudicación
  completa** contra el gold público, con el mismo
  procedimiento de las adjudicaciones de las nº 298/311;
  (3) la fracción en `needs_validation` del pipeline
  compuesto (producción + puerta), contra la misma vara de
  la línea (< 50 %); (4) discriminación reportada sin
  umbral (muerte de FP gold vs muerte de TP); (5) integridad:
  cero evidencia inventada, auditada como en los papeles
  anteriores.
- **Costo estimado:** a los precios medidos hoy
  (~US$20–21 por corrida completa de 25 PRs por brazo), el
  brazo nuevo cuesta ~US$20–21; el freno por PR queda el de
  siempre y el tope de línea lo fija Alejandro en el papel
  de corrida.
- **Estado: ESTACIONADA.** Hoy el saldo de la cuenta es
  **US$5,31** y la prioridad declarada de Alejandro es
  **deuda + pasaje**. Se ejecuta solo con papel de corrida
  nuevo y tope de línea fijado por él. Este papel no la
  arma, no la anuncia y no gasta un centavo en ella.

## 5. La verificación en seco de este papel (declarada antes)

1. **Tests unitarios del esquema de emisión**
   (`tests/test_llm_reviewer_v24.py`), sobre transportes
   guionados, US$0:
   - hallazgo con cita válida y patrón declarado que está
     en su cita → nace candidato, y tras la etapa de
     formación es **conforme** según `claim_contract`
     (sin modificar) y **aceptado** por la puerta 1.5.0
     (sin modificar);
   - hallazgo con un token declarado ausente de su cita →
     el formador lo recorta en origen, el recorte queda
     asentado en el run info, y el reclamo se emite con el
     patrón sobreviviente;
   - hallazgo con todos sus tokens ausentes → no se emite;
     el ledger de producción lo asienta con
     `tokens_afirmados_ausentes_en_la_evidencia`;
   - hallazgo sin patrón declarado (ausente o vacío) → no
     se emite; ledger con `sin_patron_concreto_en_el_reclamo`;
   - patrón declarado distinto del afirmado en el mensaje →
     no se emite; ledger con
     `patron_declarado_distinto_del_mensaje`;
   - entrada `unverifiable` del modelo → ledger con
     `declarado_no_verificable_en_origen` y la razón del
     modelo; no es candidato ni malformed;
   - hallazgo de clase (19 clases) con cita válida → pasa
     la formación intacto (Caso C) y se emite;
   - el prompt profundo armado (clase y categoría) y el de
     la pasada mixta **contienen** las instrucciones de
     evidencia (patrón copiado de las líneas citadas,
     afirmar solo lo visible, la vía `unverifiable`); el
     prompt de selección es **byte-idéntico** al del v2.3;
   - la disciplina heredada no se mueve: ancla que no
     coincide → `unanchored`; `claim_type` distinto de la
     marca → `malformed`; la guardia y la degradación
     conservan sus formas.
2. **Batería semáforo 16/16 en modo dry con el v2.4**
   (equivalente declarado de `BatteryDryRunTests`): los 8
   casos congelados de `fixtures_semaforo` × 2
   configuraciones de puerta (v13 y v14), conduciendo
   `LLMReviewerV24.review()` directo con transporte
   guionado que marca la clase plantada y la devuelve en el
   esquema v2.4 (patrón copiado de la línea plantada). Por
   corrida: sin negativas, 2 llamadas, la especialidad de
   la selección es la clase plantada, sin degradación,
   exactamente 1 candidato emitido, ledger de producción
   vacío, y el candidato conforme al contrato. Son 16
   corridas: **16/16**. El drive es directo, no vía
   `agent/main.py`, porque el montaje queda fuera de este
   papel (§2d) — la batería mide la producción, que es lo
   que el v2.4 cambia.
3. **Suite completa verde** y **hashes congelados**:
   puertas 1.0.0–1.5.0, `claim_contract.py`,
   `birth_shaper.py` y `llm_reviewer_v23.py`
   byte-idénticos antes y después (sha256 de archivo,
   asentados en el resultado).

Si alguna verificación de esta §5 falla, el resultado lo
asienta tal cual: este papel no remedía en silencio ni
ajusta lo declarado tras ver un número.

## 6. Qué NO cambia

- Las puertas 1.0.0–1.5.0, `claim_contract.py` y
  `birth_shaper.py`: byte-idénticas; el v2.4 las consume
  importándolas.
- El revisor v2.3.2: intacto. El v1, v2, v2.1 y v2.2:
  intactos.
- `agent/main.py`, imágenes, configs de portal y montajes:
  sin tocar.
- Ninguna adopción se decide acá: el v2.4 queda construido
  y verificado en seco, **no adoptado**, y su efecto queda
  explícitamente sin medir hasta la validación de la §4.

— Pre-registro del productor con disciplina de evidencia,
2026-10-22. Insumos: `RESULTADO-REVISOR-CONTRATO-20261022.md`,
`PREREGISTRO-REVISOR-CONTRATO.md`,
`PREREGISTRO-CONTRATO-RECLAMOS.md`,
`RESULTADO-CONTRATO-RECLAMOS-20261022.md`. Gasto: **US$0**.
