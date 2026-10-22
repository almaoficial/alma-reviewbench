# Pre-registro — Memoria que se lee: compilador de contexto de lecciones y revisor v2.5

**Fecha:** 2026-10-22 · **Autorización:** Alejandro, 22/10/2026
(«Si lo hagamos») tras identificar la capa faltante en su
propio arnés: ALMA tiene registro — memoria que se guarda —
pero no memoria que se lee. **Costo de este papel y de la
construcción que pre-registra: US$0** — diseño y construcción
en seco; sin llamadas a modelos, sin portal, sin cargar
plata, sin publicación, sin push. **Orden obligatorio de este
papel: este documento se escribe ANTES que el código**
(`agent/lessons_compiler.py`, `agent/llm_reviewer_v25.py`), y
lo que su §5 declara verificable en seco queda fijado antes
de construir.

## 1. El antecedente medido (por qué existe este papel)

Toda la cadena gratis de la línea ReviewBench produjo registro:
papeles, adjudicaciones emisión por emisión, ledgers por PR,
un REGISTRO de 114 KB. Nada de eso entra a la producción del
revisor. Cada corrida rinde como si fuera la primera: el
revisor de la nº 311 no sabía que en la nº 298 el 37,3 % de
sus reclamos había nacido afirmando tokens que su propia cita
no contenía, ni que 54 de 166 habían nacido sin ningún patrón
declarable. Las lecciones existen como documentos que leen
Alejandro y el agente principal; el sistema que produce no
lee ninguna.

Las capas anteriores atacaron la forma y la materia desde
fuera de la producción: el contrato a posteriori topó en
**49/166** conformables sin inventar; el formador al nacer
llegó a **80/166** con precisión entre emitidos del **55,7 %**,
pero la vara global no pasó (espera 51,8 % contra < 50 %) y su
lectura final fue que el cuello es la **materia**: **86
reclamos nacen sin nada citable que afirmar** (54 sin patrón
declarable, 32 afirmando solo tokens ausentes de su cita),
entre ellos **44 de los 89 TP** del corpus. El v2.4 agregó la
disciplina de evidencia al prompt y al esquema — instrucciones
estáticas, escritas por un humano que leyó las adjudicaciones.

Este papel construye la pieza que falta entre el registro y
la producción: **un compilador determinista que destila las
adjudicaciones existentes en un artefacto de contexto acotado
y versionado, y un revisor (v2.5) que lo lee** — el mismo
contexto, verbatim, en cada pasada de producción. Es la
versión mecánica y auditable de lo que el v2.4 hizo a mano en
su prompt: que el sistema entre a producir habiendo leído sus
propias correcciones.

## 2. El diseño del compilador (`agent/lessons_compiler.py`)

**Identidad:** `COMPILER_VERSION = "alma-lessons-compiler/1.0"`.
Determinista, sin modelos. Entrada: el corpus A destilable —
los **166 hallazgos de la base nº 298**
(`adjwork298/run298/prs/*/findings.json`) con su veredicto
adjudicado (`adjwork298/decisions.json`: TP 89, NOVEL 52,
GREY 17, FPG 8) — reconstruidos como candidatos con la fórmula
del propio revisor (evidencia desde el head sobre clones,
diffs regenerados), exactamente como en la autopsia y los tres
replay anteriores. La adjudicación de la nº 311 **no** se
compila: no tiene disposiciones por reclamo recuperables (el
defecto de observabilidad que su propio informe asienta); se
cita como contexto en este papel y en el resultado, no como
fuente del artefacto. Ningún ejemplo y ningún conteo del
artefacto proviene de otra fuente que el corpus A y las
etapas deterministas sin modificar que lo juzgan.

### 2.1 La disposición de cada reclamo (las etapas sin modificar)

Para cada uno de los 166, el compilador corre las etapas de
la línea, todas importadas sin modificar, y asienta su
disposición final en el pipeline de producción medido
(formador → contrato → puerta 1.5.0):

- `emitido` — el formador lo entregó en forma de contrato y
  la puerta 1.5.0 lo aceptó (79 esperados).
- `muerto_en_origen_tokens` — el formador lo declaró no
  verificable en origen con
  `tokens_afirmados_ausentes_en_la_evidencia`: todo token que
  el reclamo afirma entre backticks está ausente de sus
  líneas citadas (32 esperados; sus tokens nacidos: 42).
- `muerto_en_origen_sin_patron` — el formador lo declaró no
  verificable en origen con
  `sin_patron_concreto_en_el_reclamo`: su prosa no declara ni
  deja minar ningún token presente en su cita (54 esperados).
- `rechazado_puerta` — formado en contrato y rechazado en
  firme por la puerta (1 esperado: el TP de Mcp-Docker, por
  contradicción afirmativa (G3)).

**Control de sanidad obligatorio del arnés:** antes de
destilar nada, la reconstrucción debe reproducir exactamente
los números ya publicados de la línea — la 1.5.0 sola
(32/133/1, blockers primarios 71/62), el pipeline del
contrato (49 conformes: 32 nacidos + 17 minados; 117 no
conformes: 63 tokens + 54 patrón) y el pipeline del formador
(80 formados: 63 declarados + 17 minados; 86 en origen:
54 + 32; puerta 79/0/1; TP emitidos 44; FP muertos 4/8;
TP muertos 45/89) — y ser invariante entre las dos
asignaciones extremas de categoría general (todas
`correctness`; rotación por las nueve). Si la sanidad no
cierra exacta, no hay artefacto: el resultado lo asienta.

### 2.2 El artefacto (`CONTEXTO-LECCIONES.md`)

El compilador emite un único artefacto Markdown versionado:

- **Encabezado** (fuera del bloque inyectable): identidad
  (`alma-lessons-context/1.0`), corpus fuente (corrida nº 298,
  166 reclamos, con el sha256 de `decisions.json`), versión
  del compilador, y `block-sha256`: el sha256 del **bloque de
  lecciones** — el texto exacto entre los marcadores
  `<!-- LESSONS-BLOCK-BEGIN -->` y
  `<!-- LESSONS-BLOCK-END -->`, que es lo único que el
  revisor inyecta.
- **(a) Taxonomía de muertes con conteos crudos:** las
  familias de la §2.1 con sus conteos sobre 166 y su cruce
  con el gold (cuántos TP, FPG, GREY, NOVEL murieron en cada
  familia; cuántos vivieron), computados por programa desde
  las disposiciones — ningún conteo a mano.
- **(b) Ejemplos de reclamos que nacieron muertos:**
  trazables, con el texto del reclamo **verbatim**, su cita
  (archivo y rango), sus líneas de evidencia **verbatim**, su
  veredicto gold y su razón de muerte (para la familia de
  tokens: los tokens nacidos ausentes, computados; para la
  familia sin patrón: la ausencia misma y, si el veredicto es
  GREY, la nota de adjudicación verbatim de `decisions.json`).
- **(c) Contraejemplos que vivieron:** reclamos emitidos por
  el pipeline del formador, con el mismo formato: los que
  nacieron declarando y sobrevivieron, y los minados al
  nacer que se emitieron — verdaderos (TP) en ambos casos.
- **(d) Reglas destiladas:** imperativas y cortas, derivadas
  **solo** de (a)–(c): cada regla cierra con la familia y el
  conteo que la sostiene. Ninguna regla afirma nada que la
  taxonomía no cuente.

**Selección de ejemplos (determinista, declarada acá):**
solo reclamos cuya cita nacida tenga **≤ 10 líneas** (para
que el ejemplo entre entero y verbatim). Dentro de cada
familia de muerte, orden por (rango de veredicto: TP, FPG,
GREY, NOVEL; clave de PR; índice de emisión) y se toman los
primeros **3**. La familia `rechazado_puerta` aporta su
único reclamo. De los vividos: los primeros **2** TP
emitidos de origen declarado y los primeros **2** TP
emitidos de origen minado, con el mismo orden. Total
máximo: 3 + 3 + 1 + 4 = **11 ejemplos**.

**Tope de tamaño (declarado):** el bloque inyectable mide
**≤ 9.600 caracteres** — tiene que caber en el prompt de
producción sin desplazar al diff (el presupuesto de contexto
de la línea es de 60.000 tokens y el bloque se repite en
cada pasada profunda). Si el bloque supera el tope, la regla
de achique es mecánica y declarada: se descartan ejemplos
vividos más allá de los primeros 2 (en orden inverso de
selección), luego ejemplos de muerte más allá de los
primeros 2 por familia, hasta entrar; la taxonomía, las
reglas y el ejemplo rechazado **nunca** se recortan. Si aun
así no entra, el compilador falla y el resultado lo asienta.

**Procedencia (la cláusula que gobierna el artefacto):**
cada ejemplo lleva una línea de procedencia legible por
máquina:
`<!-- src: run298 pr=<clave> e=<índice> gold=<veredicto>
disp=<disposición> -->`. El compilador emite además un
manifiesto lateral (`CONTEXTO-LECCIONES.provenance.json`)
con, por ejemplo: clave de PR, índice, veredicto, disposición,
el sha256 del mensaje y el sha256 de la evidencia tal como
entran al artefacto. Y trae una **auditoría**
(`audit_artifact`): re-lee el artefacto, extrae cada
procedencia, re-deriva el ejemplo desde el corpus
reconstruido y compara mensaje, evidencia, tokens ausentes,
nota y disposición — y recomputa cada conteo de la taxonomía
contra las disposiciones. Cero ejemplos inventados, cero
conteos a mano: la auditoría debe dar **0 violaciones** o el
artefacto no vale (§4).

## 3. La integración: el revisor v2.5 (`agent/llm_reviewer_v25.py`)

**Identidad:** `REVIEWER_VERSION = "llm-reviewer/2.5.0"`,
`name = "alma-llm-reviewer-v25"`. Es el v2.4 (que queda
**intacto y byte-idéntico**) más SOLO esto:

- **Carga verificada del artefacto.** El revisor recibe el
  bloque de lecciones por parámetro (`lessons_block`) o lo
  lee del artefacto (`lessons_path`; por defecto
  `CONTEXTO-LECCIONES.md` en la raíz del repo). Al cargar
  desde el artefacto, extrae el bloque entre marcadores,
  recomputa su sha256 y lo compara con el `block-sha256`
  declarado en el encabezado: **si el artefacto falta, no
  tiene marcadores o el hash no coincide, la construcción
  falla cerrada** (`RealLLMRefused`) — el v2.5 nunca produce
  con un contexto de lecciones distinto del compilado y
  auditado.
- **Inyección declarada.** El bloque entra **verbatim**,
  precedido por un encabezado fijo de una línea que lo nombra
  como lecciones de las adjudicaciones previas del propio
  sistema, al final del prompt de sistema de las **pasadas
  profundas** (`build_deep_payload`) y de la **pasada mixta**
  (`build_fallback_payload`) — las dos pasadas que producen
  reclamos. **No** entra en la selección: su prompt queda
  **byte-idéntico** al del v2.3/v2.4 (marcar no afirma; las
  lecciones son sobre cómo nacen los reclamos, no sobre qué
  mirar). El contenido de usuario no se toca.
- **Marca de productor.** Los candidatos del v2.5 llevan
  `producer = "alma-llm-reviewer-v25"` y `rule_id`
  `llm_v25_<tipo>`, aplicados por un reemplazo declarado de
  exactamente esos dos campos sobre la conversión heredada
  del v2.4, antes de la etapa de formación; mensaje, cita,
  patrón y ledger de producción quedan intactos.
- **Run info.** `LLMRunInfoV25` extiende el del v2.4 con el
  asiento de la memoria leída: `lessons_sha256` (el hash del
  bloque efectivamente inyectado), `lessons_version` y
  `lessons_block_chars` — cada corrida futura declara qué
  memoria leyó, con su hash, igual que declara su puerta.

**Qué NO cambia:** el esquema de emisión evidence-first, los
prompts de disciplina del v2.4 (el bloque se **agrega**, no se
reescribe ninguno), la capa de formación al nacer como última
etapa (sin modificar), la selección y su tope compartido, la
guardia de dos etapas y la degradación, el freno por PR, la
resolución de puerta (v1…v141, importada), el contrato de
payload, y `agent/main.py` — **el v2.5 no se monta**, como el
v2.4: montarlo es decisión del papel de corrida (§5).

## 4. LA SALVEDAD HONESTA (escrita antes de construir)

**El efecto de las lecciones sobre la producción NO se
puede medir en seco.** Si el revisor, leyendo sus propias
correcciones, nace citando mejor es una propiedad de lo que
un modelo real hace con ese contexto — y ningún transporte
guionado la mide: la guionaría el propio arnés. Lo que este
papel SÍ audita en seco, y es todo lo que reclama:

- la **procedencia** del artefacto: cada ejemplo y cada
  conteo se rastrea por programa a un hallazgo adjudicado
  real (auditoría de la §2.2 con **0 violaciones**), y el
  arnés de disposiciones reproduce exactos los números ya
  publicados de la línea (§2.1);
- la **inyección fiel**: el bloque aparece **verbatim** en
  los prompts de producción armados (inspección del string,
  sin llamar a ningún modelo), su hash coincide con el
  declarado en el artefacto, y el run info lo asienta;
- la **disciplina heredada intacta** y la batería semáforo
  en seco (§5).

**Ningún número de efecto se reclama en este papel** — ni
conformidad esperada, ni precisión proyectada, ni que las
lecciones «le harían muy bien» a ALMA en magnitud alguna: la
única afirmación es que la capa existe, es fiel a su fuente
y está lista para medirse. Si alguien lee en este diseño una
promesa de mejora, está leyendo lo que el papel no dice.

## 5. La validación paga futura — SOLO diseño, no se ejecuta

Cuando Alejandro lo decida, con papel de corrida nuevo, la
medición se suma como **tercer brazo del A/B ya diseñado**
en `PREREGISTRO-PRODUCTOR-EVIDENCIA.md` §4:

- **Brazos sobre los mismos 25 PRs:** base v2.3.2 sin puerta
  (referencia medida de la nº 298) · v2.4 con puerta 1.5.0 ·
  **v2.5 con puerta 1.5.0** (el único delta contra el brazo
  v2.4 es el contexto de lecciones: la comparación v2.4↔v2.5
  aisla el efecto de la memoria leída).
- **La misma vara de la línea:** (1) conformidad al nacer de
  cada producción, con su ledger completo como recibo;
  (2) precisión y recall grounded por **adjudicación
  completa** contra el gold público, con el procedimiento
  de las adjudicaciones de las nº 298/311; (3) fracción en
  `needs_validation` del pipeline compuesto contra la vara
  < 50 %; (4) discriminación reportada sin umbral; (5)
  integridad: cero evidencia inventada, auditada como en los
  papeles anteriores. El run info del v2.5 asienta además el
  `lessons_sha256`, de modo que la corrida declara qué
  memoria leyó.
- **Costo estimado:** a los precios medidos hoy (~US$20–21
  por corrida completa de 25 PRs por brazo), el tercer brazo
  cuesta **~US$20 más** sobre el A/B estacionado. El freno
  por PR queda el de siempre y el tope de línea lo fija
  Alejandro en el papel de corrida.
- **Estado: ESTACIONADA**, por la misma razón asentada en
  el papel del v2.4: saldo **US$5,31** y prioridad declarada
  de Alejandro **deuda + pasaje**. Este papel no la arma, no
  la anuncia y no gasta un centavo en ella.

## 6. La verificación en seco de este papel (declarada antes)

1. **Compilador** (`tests/test_lessons_compiler.py`), sobre
   un corpus sintético chico construido en el test (sin red,
   sin clones): la taxonomía computada coincide con los
   conteos a mano del fixture; cada ejemplo del artefacto
   sintético pasa la auditoría de procedencia contra el
   fixture (mensaje, evidencia, tokens, nota y disposición
   re-derivados por programa); un artefacto adulterado a
   mano (un ejemplo con el mensaje cambiado) hace fallar la
   auditoría con la violación nombrada; el tope de tamaño
   se respeta y la regla de achique se ejercita.
2. **Auditoría sobre el corpus real:** con los clones
   presentes, la reconstrucción reproduce exactos los
   números publicados (§2.1) y `audit_artifact` sobre el
   `CONTEXTO-LECCIONES.md` compilado da **0 violaciones**,
   con el conteo de ejemplos y el hash del bloque asentados
   en el resultado.
3. **Revisor v2.5** (`tests/test_llm_reviewer_v25.py`),
   sobre transportes guionados, US$0:
   - el bloque de lecciones aparece **verbatim** en el
     prompt de sistema armado de la pasada profunda (clase y
     categoría) y de la mixta, y su sha256 coincide con el
     `block-sha256` del artefacto;
   - el prompt de selección es **byte-idéntico** al del
     v2.4 (y, por herencia, al del v2.3);
   - el run info asienta `lessons_sha256`, `lessons_version`
     y `lessons_block_chars` del bloque inyectado;
   - artefacto adulterado (hash que no coincide) o ausente →
     la construcción **falla cerrada** sin ninguna llamada;
   - la disciplina heredada no se mueve: un hallazgo con
     cita válida nace candidato con la marca del v2.5 y,
     tras la formación, es conforme según `claim_contract`
     y aceptado por la 1.5.0 (ambas sin modificar); sin
     patrón declarado → ledger `sin_patron_concreto_en_el_reclamo`;
     la guardia rehúsa antes de llamar cuando la selección
     sola excede el freno.
4. **Batería semáforo 16/16 en modo dry con el v2.5**
   (equivalente declarado, drive directo de `review()`
   como en el v2.4): 8 casos × 2 configuraciones de puerta
   (v13 y v14); por corrida: sin negativas, 2 llamadas,
   especialidad = clase plantada, sin degradación, ledger
   de producción vacío, exactamente 1 candidato emitido con
   la marca del v2.5 y conforme al contrato.
5. **Suite completa verde** y **hashes congelados**:
   puertas 1.0.0–1.5.0, `claim_contract.py`,
   `birth_shaper.py`, `llm_reviewer_v23.py` y
   `llm_reviewer_v24.py` byte-idénticos antes y después
   (sha256 de archivo, asentados en el resultado).

Si alguna verificación de esta §6 falla, el resultado lo
asienta tal cual: este papel no remedía en silencio ni
ajusta lo declarado tras ver un número.

## 7. Qué NO cambia

- Las puertas 1.0.0–1.5.0, `claim_contract.py`,
  `birth_shaper.py` y los revisores v1–v2.4: byte-idénticos;
  el compilador y el v2.5 los consumen importándolos.
- `agent/main.py`, imágenes, configs de portal y montajes:
  sin tocar. Los clones bajo `adjwork298/repos/` son caché
  de construcción del arnés (la misma fuente pública de los
  replay anteriores), no entregables, y no se commitean.
- Ninguna adopción se decide acá: el v2.5 queda construido
  y verificado en seco, **no adoptado**, y su efecto queda
  explícitamente sin medir hasta la validación de la §5.

— Pre-registro de la memoria que se lee, 2026-10-22.
Insumos: `ADJUDICACION-COMPLETA-298-20261022.md`,
`ADJUDICACION-COMPLETA-311-20261022.md`,
`RESULTADO-CONTRATO-RECLAMOS-20261022.md`,
`RESULTADO-REVISOR-CONTRATO-20261022.md`,
`PREREGISTRO-PRODUCTOR-EVIDENCIA.md`. Gasto: **US$0**.
