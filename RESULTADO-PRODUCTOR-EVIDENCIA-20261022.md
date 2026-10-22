# Resultado — Productor con disciplina de evidencia: el revisor v2.4 construido en seco

**Fecha:** 2026-10-22 · **Papel:** `PREREGISTRO-PRODUCTOR-EVIDENCIA.md`
(escrito ANTES que el código, con la verificación de su §5
declarada de antemano). **Costo: US$0** — construcción y
verificación local sobre transportes guionados; sin llamadas
a modelos, sin portal, sin cargar plata, sin publicación,
sin push.

## Veredicto en una línea

**El revisor v2.4 quedó construido y verificado en seco, y
ningún efecto suyo quedó medido** — porque ningún efecto es
medible en seco, como la §3 del pre-registro declaró antes de
construir. Lo que este resultado asienta es exactamente lo
que la §5 declaró verificable: la corrección mecánica del
esquema de emisión evidence-first, el contenido de los
prompts armados, la batería semáforo 16/16 en su equivalente
declarado, la suite completa sin regresiones y los hashes
congelados byte-idénticos. La disciplina de evidencia queda
lista para la validación paga de la §4 del pre-registro —
**estacionada**: saldo US$5,31, prioridad declarada de
Alejandro deuda + pasaje, y su ejecución exige papel de
corrida nuevo con tope de línea fijado por él.

## 1. Qué quedó construido

**`agent/llm_reviewer_v24.py`** (`llm-reviewer/2.4.0`,
sha256 `ae378c2e…`, 45.435 B), espejo etapa por etapa del
v2.3.2 — que queda **intacto** (`a78bdd6d…`, verificado) —
con solo los cambios declarados en la §2 del pre-registro:

- **Esquema de emisión evidence-first (§2a):** las pasadas
  profundas y la mixta responden un objeto con dos arreglos.
  `findings` lleva el campo nuevo `pattern` — los tokens que
  el reclamo afirma, copiados verbatim de las líneas citadas
  — y el mensaje envuelve en backticks exactamente ese
  patrón (el que el contrato C1 lee). `unverifiable` es la
  vía de declaración del modelo: lo que cree real y no
  puede sostener con líneas citables, con su `reason`.
- **Prompts (§2b):** plantilla profunda nueva
  (`_SYSTEM_PROMPT_TEMPLATE_V24`) y pasada mixta v2.4, con
  el texto de disciplina compartido (`_EVIDENCE_DISCIPLINE`):
  primero las líneas que prueban, después el reclamo desde
  esas líneas; afirmar solo lo visible en la cita; lo no
  citable se declara en `unverifiable`, nunca se disfraza.
  La guía de clases/categorías es la heredada sin cambios y
  el prompt de **selección es byte-idéntico al del v2.3**
  (importado; verificado por test).
- **Ledger de producción (§2c):** la conversión conserva la
  disciplina heredada de forma y ancla (malformed /
  unanchored, sin cambios) y asienta cada nacimiento no
  citable en `production_ledger` del run info, con código y
  razón: sin patrón declarado
  (`sin_patron_concreto_en_el_reclamo`), patrón declarado
  distinto del afirmado en el mensaje
  (`patron_declarado_distinto_del_mensaje`), declarado por
  el modelo (`declarado_no_verificable_en_origen`, con su
  razón), y lo que el formador retiene en la etapa de
  formación (con los códigos del propio formador). Nada no
  citable se emite disfrazado y nada desaparece en silencio.
- **El formador al nacer es la última etapa de producción:**
  `review()` corre `birth_shaper.shape_candidates` (SIN
  MODIFICAR) sobre todo lo recolectado, con el diff a la
  vista, antes de devolver nada y antes de cualquier
  puerta. Lo entregado en forma de contrato ES la producción
  del v2.4; los recortes en origen se cuentan en el run info
  (`shaping`: emitidos, retenidos en origen, tokens
  recortados, orígenes). Sin deduplicación posterior a la
  formación, como se declaró.
- **Sin cambios (§2, §6):** selección, tope compartido de 5
  pasadas, guardia de dos etapas, degradación, chequeo
  acumulativo de costo, freno por PR y configuraciones,
  resolución de puerta importada del v2.3 (v1…v141),
  contrato de payload. `agent/main.py` **no se tocó**: el
  v2.4 no está montado en ninguna imagen ni config.

## 2. Qué quedó medido en seco (§5 del pre-registro)

**Tests del esquema — `tests/test_llm_reviewer_v24.py`**
(sha256 `7447ef8b…`), 15 tests, todos en verde:

- **Nace conforme:** hallazgo con cita válida y patrón que
  está en su cita → candidato; tras la etapa de formación,
  `claim_contract` (sin modificar) lo confirma conforme
  (origen `born`) y la puerta 1.5.0 (sin modificar) lo
  **acepta** de punta a punta.
- **Recorte en origen asentado:** un token declarado ausente
  de la cita (`pickle.loads`) sale des-declarado por el
  formador; el run info cuenta 1 token recortado, el ledger
  queda vacío (el recorte no es una retención) y el reclamo
  se emite con su patrón sobreviviente y su cita achicada al
  rango mínimo (3,3).
- **Todos los tokens ausentes:** no se emite; el ledger de
  producción lo asienta en la etapa `production_shaping` con
  `tokens_afirmados_ausentes_en_la_evidencia`.
- **Sin patrón declarado** (campo ausente y campo vacío, en
  la misma pasada que un hallazgo válido que sí se emite):
  ledger con `sin_patron_concreto_en_el_reclamo` ×2,
  `malformed_findings` en 0 — nace marcado, no se cuenta
  como roto.
- **Patrón ≠ mensaje:** ledger con
  `patron_declarado_distinto_del_mensaje`; no se emite.
- **Declarado por el modelo:** la entrada `unverifiable`
  queda asentada con `declarado_no_verificable_en_origen`
  y la razón del modelo verbatim; no es candidato ni
  malformed. Una segunda entrada sin forma identificable
  cuenta como malformed, como declara el papel.
- **Clase intacta:** un hallazgo `sql_injection` con cita
  válida pasa la formación como Caso C (mensaje y rango
  byte-idénticos) y el chequeo de contrato lo confirma con
  origen `class`.
- **Disciplina heredada:** evidencia que no coincide con el
  head → `unanchored` (1); `claim_type` distinto de la
  marca → `malformed` (1); con el freno en US$0,0001 la
  guardia **rehúsa antes de llamar** (0 llamadas al
  transporte).
- **Prompts por inspección:** las plantillas profunda (de
  clase y de categoría) y la mixta contienen el texto de
  disciplina (`EVIDENCE DISCIPLINE (binding)`, patrón
  copiado verbatim, afirmar solo lo visible, la vía
  `unverifiable` como declaración); el payload conserva el
  contrato (sin `temperature`, sin `max_tokens`); el prompt
  de selección es **igual byte a byte** al del v2.3 para los
  mismos insumos.

**Batería semáforo — 16/16 en el equivalente declarado:**
los 8 casos congelados × 2 configuraciones de puerta (v13
y v14), conduciendo `LLMReviewerV24.review()` directo con
transporte guionado que marca la clase plantada y la
devuelve en el esquema v2.4 (patrón copiado de la línea
plantada por el propio test: el primer token snake_case,
punteado o de asignación de esa línea). Por corrida: sin
negativas, 2 llamadas, especialidad de la selección = la
clase plantada, sin degradación, ledger de producción
vacío, exactamente 1 candidato emitido y conforme al
contrato. El drive es directo y no vía `agent/main.py`
porque el montaje quedó fuera del papel (§2d del
pre-registro): la batería mide la producción, que es lo que
el v2.4 cambia.

**Suite completa: 295/295 OK** (280 previas + 15 nuevas),
sin regresiones.

**Hashes congelados — byte-idénticos antes y después**
(sha256 de archivo): puertas 1.0.0 `4223cb05…`, 1.1.0
`fdd974f1…`, 1.2.0 `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0
`b16c5a79…`, 1.4.1 `08d813e9…`, 1.5.0 `71b1996b…`;
`claim_contract.py` `7df8abc7…`; `birth_shaper.py`
`2b127b23…`; `llm_reviewer_v23.py` `a78bdd6d…`.

## 3. Qué queda explícitamente SIN medir

- **La tasa de reclamos citables bajo el prompt nuevo.**
  Es una propiedad de un modelo real frente a la disciplina
  de evidencia — cuántos reclamos nacen con el patrón
  copiado de su cita, cuántos se declaran no verificables,
  cuántos siguen afirmando fuera de su cita — y en seco
  solo podría medirla el propio arnés guionándola. Ningún
  número de este papel habla de ella.
- **Conformidad al nacer, precisión/recall grounded y
  espera del pipeline en producción.** Son la vara de la
  validación paga (§4 del pre-registro: A/B sobre los mismos
  25 PRs, v2.3.2 sin puerta contra v2.4 con puerta 1.5.0,
  adjudicación completa), no de este papel.
- **Toda proyección.** Si la espera bajaría del 50 %, si la
  discriminación se movería, si los 44 TP hoy incitables se
  volverían citables: este papel no lo afirma en ninguna
  dirección. El arnés para responderlo quedó listo; la
  respuesta exige producción real.

## 4. Custodia

Commit **local** en el repo del workspace
(`~/workspace/alma-prototype`, donde el árbol `reviewbench/`
vive sin trackear): el commit agrega exactamente los cinco
archivos de esta tarea (este resultado, el pre-registro, el
módulo, sus tests y el asiento del REGISTRO). **Sin push** —
la publicación es decisión de Alejandro, como en toda la
línea. El v2.4 queda construido y verificado en seco, **no
adoptado** y no montado.

— Resultado del productor con disciplina de evidencia,
2026-10-22. Gasto: **US$0**.
