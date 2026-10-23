# Adenda — Revisor v2.6: el v2.5 más el contexto de ausencias montado

**Fecha:** 2026-10-23 (EDT). **Costo de esta tarea: US$0** — sin
llamadas a modelos, sin portal, sin cargas, sin publicación, sin
push. **Autorización:** Alejandro, 23/10/2026 («Hacela
funcionar», en la secuencia «hacerla fundacional»), sobre el
último lever diagnosticado que seguía sin montar en ningún
revisor: el compilador de ausencias cerró el 22/10 con el
artefacto explícitamente *sin montar*
(`RESULTADO-LECCIONES-AUSENCIA-20261022.md` §4: «El artefacto
no está montado en ningún revisor… montar el de ausencias
(junto, en vez, en otra pasada) es decisión posterior con su
propio papel»). Este es ese papel. **Relación con los papeles
vigentes:** esta adenda NO modifica ningún papel. Cita el
diseño rector de la validación paga
(`PREREGISTRO-PRODUCTOR-EVIDENCIA.md` §4), el tercer brazo del
`PREREGISTRO-MEMORIA-LECCIONES.md` §5 (v2.5) y la obligación de
reporte de la `ADENDA-PUNTAJE-NETO.md` (§3–§4), y se les anexa:
suma un brazo candidato (v2.6) y su disciplina de construcción;
no toca la vara, los brazos ya diseñados ni el presupuesto de
la validación, que sigue **ESTACIONADA**.

## 1. Qué es el v2.6

**Identidad:** `REVIEWER_VERSION = "llm-reviewer/2.6.0"`,
`name = "alma-llm-reviewer-v26"`, módulo
`agent/llm_reviewer_v26.py`. Es el **v2.5 heredado entero**
(subclase de `LLMReviewerV25`, que queda intacto y
byte-idéntico) más exactamente un delta: el bloque compilado
de ausencias (`CONTEXTO-AUSENCIAS.md`,
`alma-absence-context/1.0`, compilador
`alma-absence-compiler/1.0`) entra en producción junto al
bloque de lecciones que el v2.5 ya inyecta.

El fundamento medido de este brazo, asentado en su papel: de
los 352 TP del oro de la nº 298, la base tocó 66 y **nunca
reclamó 286 (81,3 %)**; el patrón dominante de la ausencia no
es cobertura de archivos sino **reconocimiento sobre lo ya
mirado** (A2 = 182/286, 63,6 %; A1 = 104/286). Las lecciones
del v2.5 gobiernan cómo *nacen* los reclamos (su forma
citable); las ausencias apuntan a qué *mirar dos veces* antes
de que el reclamo exista. Son las dos mitades de la memoria
que se lee: la de la comisión y la de la omisión.

## 2. Qué hereda intacto del v2.5 (y por herencia del v2.4/v2.3)

El esquema de emisión evidence-first con su vía
`unverifiable`; los prompts de disciplina del v2.4 (ningún
prompt se reescribe: los bloques se **agregan**); el ledger de
producción; el formador al nacer como última etapa de
producción, sin modificar; la selección generalizada y su
tope compartido `MAX_DEEP_PASSES`; la guardia de dos etapas y
la regla de degradación; el chequeo acumulativo de costo que
falla cerrado; el freno por PR; la resolución de puerta
(v1…v141, importada); el contrato de payload (sin
`temperature`, sin `max_tokens`; `max_completion_tokens`);
las puertas 1.0.0–1.5.0, `claim_contract.py` y
`birth_shaper.py` consumidos sin modificar; y `agent/main.py`
— **el v2.6 no se monta en ninguna imagen ni config**, como el
v2.4 y el v2.5: montarlo es decisión del papel de corrida.

## 3. El delta, declarado antes de construir

- **Inyección doble, en las mismas pasadas.** El bloque de
  ausencias entra **verbatim**, precedido por su propio
  encabezado fijo de una línea —
  `ABSENCE_INJECTION_HEADER`: *"The following absence lessons
  were compiled deterministically from the same adjudicated
  run: the true defects this reviewer never claimed. Look for
  what you would otherwise walk past:"* — al final del
  contenido de sistema de las **pasadas profundas**
  (`build_deep_payload`) y de la **pasada mixta degenerada**
  (`build_fallback_payload`), **después** del encabezado y el
  bloque de lecciones del v2.5 (orden fijo declarado: disciplina
  de nacimiento primero, memoria de omisión después). La
  **selección no se sobrescribe**: su payload queda
  byte-idéntico al del v2.5/v2.4/v2.3 (marcar no afirma; ningún
  contexto de memoria gobierna el marcado). El contenido de
  usuario no se toca jamás.
- **Carga fail-closed de AMBOS bloques, cada uno por su lado.**
  Sin bloque explícito, el constructor carga cada artefacto
  desde el disco, extrae su bloque entre marcadores, recomputa
  su sha256 y lo compara con el declarado en el encabezado del
  artefacto, y verifica su versión declarada: archivo ausente,
  marcadores ausentes, declaración de hash ausente,
  declaración de versión ausente o hash distinto →
  `RealLLMRefused` en construcción, antes de que exista
  llamada alguna — para el bloque de ausencias exactamente
  como el v2.5 ya hace para el de lecciones (que sigue
  fallando cerrado por su propio lado, heredado). Un bloque
  puede inyectarse directo (`absence_block=`, como
  `lessons_block=`) para tests.
- **Procedencia:** entre la producción y la etapa de
  formación, cada candidato se re-etiqueta
  `producer="alma-llm-reviewer-v26"`,
  `rule_id="llm_v26_<claim_type>"` (el formador preserva
  ambas). `LLMRunInfoV26` extiende el del v2.5 con
  `absence_sha256`, `absence_version`
  (`alma-absence-context/1.0`) y `absence_block_chars`
  (8.427), junto a los `lessons_*` heredados — cada corrida
  futura declara qué memorias leyó, con sus dos hashes.

## 4. El presupuesto combinado de contexto (verificado ANTES de construir)

El presupuesto de contexto de la línea es de **60.000 tokens**
(`PREREGISTRO-MEMORIA-LECCIONES.md` §2: «el presupuesto de
contexto de la línea es de 60.000 tokens y el bloque se repite
en cada pasada profunda»), y de él deriva el tope por bloque
de **9.600 caracteres** («tiene que caber en el prompt de
producción sin desplazar al diff»). La verificación de esta
adenda usa el estimador de la propia línea
(`_estimate_tokens`: ⌈caracteres / 3,5⌉):

| Pieza | Caracteres | Tokens estimados |
|---|---:|---:|
| Bloque de lecciones (v2.5) | 9.052 | 2.587 |
| Bloque de ausencias (nuevo) | 8.427 | 2.408 |
| **Bloques combinados** | **17.479** | **4.994** |
| Encabezados fijos + separadores (×2) | 324 | 93 |
| **Inyección total por pasada** | **17.803** | **5.087** |

(La estimación combinada se computa sobre la cadena completa;
la suma de las estimaciones por bloque da 4.995 por el
redondeo hacia arriba de cada ⌈·⌉ — la diferencia es de
redondeo, no de contenido.)

**Criterios de encaje declarados (ambos se cumplen):**
(1) bloques combinados ≤ 19.200 caracteres — la suma de los
dos topes por bloque vigentes (9.600 + 9.600): 17.479 ✓;
(2) inyección total estimada ≤ 6.000 tokens — el 10 % del
presupuesto de contexto de la línea: 5.087 ✓. El contexto
combinado **entra con holgura** (8,5 % del presupuesto): **no
se aplica ningún achique** — ninguno de los dos artefactos se
toca, se recompila ni se recorta en esta tarea.

**Regla de precedencia, declarada ahora para el futuro** (si
una recompilación posterior de cualquiera de los dos bloques
rompiera alguno de los dos criterios): precede el bloque de
**lecciones** (es la capa cuyo brazo ya está diseñado en la
validación estacionada) y el que cede es el de **ausencias**,
siguiendo el orden de achique mecánico ya declarado en su
propio pre-registro (salen los ejemplos más allá de los
primeros 2 por familia, A2 antes que A1; taxonomía y reglas
nunca se recortan); si aun achicado no entrara, la
construcción del v2.6 **falla cerrada** — ningún recorte en
silencio, ninguna inyección parcial no declarada.

**Precio de la inyección, declarado y no escondido:** los
bloques viajan en el contenido de sistema, por encima del
presupuesto de archivos de contexto (que queda en 60.000
tokens para los archivos); la guardia heredada precia el
payload armado tal como se construye — ambos bloques
incluidos — de modo que el freno por PR sigue atando con la
misma aritmética de siempre. La inyección suma ~5.000 tokens
estimados de entrada por llamada de producción, dentro del
peor caso que la guardia ya cobra.

## 5. LA SALVEDAD HONESTA (vinculante, la de siempre)

**El efecto de las ausencias sobre la producción NO está
medido** y este papel no afirma ninguno: ni recall esperado,
ni que el bloque «le haría muy bien» a la base en magnitud
alguna. Lo que se verifica en seco es lo de siempre:
**procedencia** (el bloque inyectado es byte-igual al
artefacto auditado con 0 violaciones, hash declarado y
recomputado coincidentes), **inyección fiel** (ambos bloques
verbatim, en las pasadas declaradas y en el orden declarado;
selección byte-idéntica; usuario intacto), **disciplina
heredada intacta** y la **batería semáforo en seco**. La
única afirmación es que el brazo existe, es fiel a sus dos
fuentes y está listo para medirse.

## 6. Su lugar en la validación paga estacionada

El diseño estacionado tiene tres brazos sobre los mismos 25
PRs (base v2.3.2 de referencia · v2.4 con puerta 1.5.0 · v2.5
con puerta 1.5.0). Esta adenda **no lo modifica**: registra el
v2.6 como **el brazo candidato completo de la línea** — el
único que lleva montadas las dos memorias — de modo que,
cuando Alejandro escriba el papel de corrida con su tope
sobre la línea entera, la comparación **v2.5 ↔ v2.6** aísla el
efecto del contexto de ausencias exactamente como la
v2.4 ↔ v2.5 aísla el de las lecciones. Por la
`ADENDA-PUNTAJE-NETO.md` (§3–§4), la adjudicación de este
brazo — como la de todo brazo futuro — reportará junto a
precisión y recall el **neto crudo, el neto por 100 emisiones
y su desglose** (+TP, −FPG, 0 GREY, 0 NOVEL), y **un neto
crudo ≤ 0 no podrá declararse mejora** aunque gane en
precisión. **Nada corre sin papel de corrida y aprobación**:
esta adenda no arma la validación, no la anuncia y no gasta
un centavo en ella. El v2.6 queda **construido, no montado,
no adoptado**.

## 7. La verificación en seco de esta adenda (declarada antes)

`tests/test_llm_reviewer_v26.py`, sobre transportes guionados,
US$0:

1. **Identidad y congelados:** versión y nombre; byte-idénticos
   por sha256 (foto antes = después) las puertas 1.0.0–1.5.0,
   `claim_contract.py`, `birth_shaper.py`, los revisores
   v2.3/v2.4/**v2.5**, ambos compiladores y ambos artefactos de
   contexto con su provenance.
2. **Carga fail-closed por bloque:** el artefacto de ausencias
   comprometido carga y verifica (bloque = el extraído por
   `absence_compiler.extract_block`; sha256 = el declarado
   `be712a35…`; versión `alma-absence-context/1.0`; 8.427
   caracteres); el revisor carga ambas memorias por defecto;
   artefacto de ausencias adulterado, ausente o sin marcadores
   → `RealLLMRefused`; artefacto de lecciones adulterado →
   `RealLLMRefused` (el fail-closed heredado sigue atando);
   inyección directa de ambos bloques.
3. **Inyección doble fiel:** payload profundo y mixto = el
   sistema del v2.5 + encabezado de ausencias + bloque de
   ausencias, verbatim y en ese orden (lecciones exactamente
   una vez, ausencias exactamente una vez, lecciones antes que
   ausencias); usuario byte-idéntico; selección byte-idéntica
   a la del v2.4 y a la del v2.5.
4. **Presupuesto combinado:** los caracteres y tokens
   estimados de la inyección, computados por programa con el
   estimador de la línea, coinciden con la tabla de la §4 y
   cumplen los dos criterios declarados.
5. **Extremo a extremo:** un reclamo citable nace con las
   marcas v2.6, conforme y aceptado por la 1.5.0 sin
   modificar; el run info asienta `lessons_*` y `absence_*`
   con los valores del artefacto; ambos bloques presentes en
   el prompt de sistema de la llamada profunda real; sin
   patrón → ledger `sin_patron_concreto_en_el_reclamo`; la
   guardia rehúsa antes de llamar (0 llamadas).
6. **Batería semáforo en seco:** 16/16 conduciendo
   `LLMReviewerV26.review()`, con ambos bloques presentes en
   cada payload profundo.
7. **Suite completa** corriendo entera, sin regresiones.
