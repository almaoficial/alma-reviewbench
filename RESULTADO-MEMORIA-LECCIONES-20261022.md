# RESULTADO — Memoria que se lee: compilador de lecciones + revisor v2.5 (22/10/2026)

Papel: `PREREGISTRO-MEMORIA-LECCIONES.md` (18.069 B, escrito ANTES que
cualquier código, como manda la orden). Autorizado por Alejandro el
22/10/2026 («Si lo hagamos») tras identificar la capa faltante: ALMA
tenía registro (memoria que se guarda) pero no memoria que se lee.
**Gasto US$0 estricto:** sin llamadas a modelos, sin portal, sin
cargas, sin push, sin publicación. Solo archivos locales.

## 0. Veredicto seco

Construido y verificado en seco: el **compilador de lecciones**
(`agent/lessons_compiler.py`, `alma-lessons-compiler/1.0`) destila el
corpus adjudicado de la corrida nº 298 en un artefacto de contexto
acotado y auditable (`CONTEXTO-LECCIONES.md`, `alma-lessons-context/1.0`),
y el **revisor v2.5** (`agent/llm_reviewer_v25.py`, `llm-reviewer/2.5.0`)
lo inyecta verbatim en sus prompts de producción. La auditoría de
procedencia da **0 violaciones** y la suite completa queda **314/314**.
**El efecto de las lecciones sobre la producción NO está medido** —
es la salvedad vinculante del pre-registro (§4): en seco se audita
procedencia, inyección fiel y disciplina heredada, nada más. El v2.5
no está montado en `main.py` ni adoptado.

## 1. Sanidad obligatoria: la reconstrucción reproduce los números publicados

Antes de compilar, el arnés reconstruyó el corpus desde las fuentes
primarias (findings + `decisions.json` + contenido del head vía clones
parciales locales, caché de construcción) y repitió la cadena
determinista de la línea (formador → contrato → puerta 1.5.0, con la
fórmula de replay publicada y las dos asignaciones de tipo de reclamo
P1/P2, con invarianza verificada). Resultado: **166/166 reclamos
reconstruidos, 0 errores**, y cada número declarado en §2.1 del
pre-registro reproducido **exacto**:

- Puerta 1.5.0 sola: **32 aceptados / 133 en espera / 1 rechazado**;
  blockers primarios **71** `sin_patron_concreto_en_el_reclamo` +
  **62** `tokens_afirmados_ausentes_en_la_evidencia`.
- Contrato: **49 conformes** (32 nacidos + 17 minados); 117 no
  conformes (**63** tokens + **54** patrón); de los 133 en espera,
  conforman 17.
- Formador: **80 formados** (63 declarados + 17 minados); **86 en
  origen** (54 sin patrón + 32 tokens).
- Compuesto: **79 emitidos / 86 en espera / 1 rechazado** (el TP de
  Mcp-Docker, gold 33, por (G3)); TP emitidos **44**; muerte FP
  **4/8 = 50,0 %** vs TP **45/89 = 50,6 %** (paridad).

**Una diferencia asentada, sin elegir bando:** el papel del formador
(`RESULTADO-REVISOR-CONTRATO` §3) imprime «17 TP gold distintos»
para este pipeline; el conteo por pares (PR, entrada gold) da **32**,
y ese mismo conteo reproduce exacto el 18 del papel del contrato
para su pipeline — la cifra 17 parece responder a otra convención
(crédito por gemelas de la adjudicación) o a un error aritmético de
ese papel. Este trabajo no usa esa cifra en ningún lado: la taxonomía
del artefacto cuenta **reclamos**, no gold cubierto. Queda registrada
para que la corrija quien toque ese papel, con los recibos de ambos
conteos.

## 2. Qué se compiló

`CONTEXTO-LECCIONES.md` (9.834 B) + sidecar
`CONTEXTO-LECCIONES.provenance.json` (3.188 B). El bloque inyectable
(entre `<!-- LESSONS-BLOCK-BEGIN -->` y `<!-- LESSONS-BLOCK-END -->`)
mide **9.052 caracteres** (tope declarado: 9.600), con
**block-sha256 `2cdb32ced88785164491bda5f9cda72121b2be048ec18c7b3f236fa17a5bae6b`**
declarado en el encabezado; el corpus queda fijado por el sha256 de
`decisions.json`: `feebdc6e0aecf073dd81b7e1dabde670449932fbdef2d9e073a15174ea74651c`.

**Taxonomía compilada** (conteos crudos, cruzados con gold):

| Disposición | n | TP | FPG | GREY | NOVEL |
|---|---|---|---|---|---|
| Muerto en origen — tokens ausentes | 32 | 15 | 3 | 4 | 10 |
| Muerto en origen — sin patrón | 54 | 29 | 1 | 5 | 19 |
| Rechazado por la puerta (G3) | 1 | 1 | 0 | 0 | 0 |
| Emitido (62 declarados + 17 minados) | 79 | 44 | 4 | 8 | 23 |
| **Total** | **166** | **89** | **8** | **17** | **52** |

**Ejemplos:** la selección declarada daba 11 (3+3 muertes por
familia, el rechazado, 2+2 vividos) y el bloque sin achicar medía
12.770 caracteres — por encima del tope. Se aplicó **exactamente el
achique mecánico declarado** en §2.4 del pre-registro: salieron
primero los vividos más allá de los primeros 2 (los dos minados:
AY2526 e=5 y DisciplinedSoftware e=5) y después el tercer muerto de
cada familia (tokens: PaulStSmith e=5; sin patrón: Marvell e=0).
Quedan **7 ejemplos** (D1–D5, L1–L2), todos verbatim y trazables.
Consecuencia honesta, asentada: la sección de vividos quedó solo con
ejemplos de origen *declarado*; la regla 6 del bloque cita el conteo
de rescates minados (17 emitidos, 7 de ellos TP), no un ejemplo —
porque el orden de achique fue declarado antes de ver los tamaños y
no se renegoció después.

**Reglas destiladas:** 6, imperativas y cortas, cada una cerrando con
la familia y el conteo que la sostiene (los números dentro de las
reglas los computa el programa, no una mano).

## 3. La cifra de tokens, con sus dos definiciones

El pre-registro (§2.1) hablaba de «42 tokens afirmados ausentes»,
fundiendo dos conteos que la medición separa: sobre las 32 muertes
por tokens, los tokens **afirmados al nacer son 42** (la cifra del
papel del contrato) y los **ausentes de la cita son 40**. Los 2 que
están presentes pero no salvaron a su reclamo son `Plugin.pull` y
`Plugin.push` (jadx-collaboration, e=3 y e=4): figuran en la
evidencia como menciones en prosa, sin tramo de código que los haga
declarables al nacer. El artefacto usa **40** con la etiqueta exacta
(«asserted tokens with no backing») y cada ejemplo D de la familia
lista sus tokens ausentes computados. La redacción del pre-registro
queda corregida acá, con ambos números y su recibo.

## 4. Auditoría de procedencia: 0 violaciones

`audit_artifact` re-deriva todo desde el corpus y verifica, por
programa: (1) el sha256 declarado en el encabezado coincide con el
del bloque extraído; (2) una **recompilación determinista completa**
desde el corpus produce un bloque idéntico al del artefacto; (3) por
cada ejemplo: su tag de fuente (PR, índice, gold, disposición)
coincide con la disposición recomputada, los hashes de mensaje y de
evidencia del manifiesto coinciden con el reclamo adjudicado real, y
el mensaje y la evidencia aparecen **verbatim** dentro del bloque.
Corrida por CLI (`--verify`) y por test sobre el corpus real:
**0 violaciones**. Los tests prueban además que la auditoría
**falla nombrando la violación** ante un artefacto adulterado (un
conteo cambiado dentro del bloque) y ante un manifiesto con un hash
corrompido. Cero ejemplos inventados, cero conteos a mano: es una
propiedad del programa, no una promesa.

## 5. El revisor v2.5

Subclase de `LLMReviewerV24` (que queda byte-idéntico); hereda
emisión evidence-first, vía `unverifiable`, ledger de producción,
formador como última etapa, selección generalizada, guardia de dos
etapas, degradación, freno por PR y resolución de puerta. Cambios,
solo los declarados en §3 del pre-registro:

- **Inyección:** encabezado fijo de una línea + el bloque
  **verbatim**, al final del contenido de sistema de
  `build_deep_payload` y `build_fallback_payload` — solamente.
  `build_selection_payload` no se sobrescribe: el payload de
  selección es **idéntico en dict** al del v2.4 (probado). El
  contenido de usuario no se toca (probado). La guardia heredada
  precia el payload armado tal como se construye — lecciones
  incluidas.
- **Carga fail-closed:** sin bloque explícito, el constructor carga
  el artefacto, extrae el bloque entre marcadores, recomputa su
  sha256 y lo compara con el declarado: archivo ausente, marcadores
  ausentes, declaración ausente o hash distinto →
  `RealLLMRefused` en construcción, antes de que exista llamada
  alguna (las cuatro anomalías, probadas).
- **Procedencia:** entre `_produce` y la etapa de formación, cada
  candidato se re-etiqueta `producer="alma-llm-reviewer-v25"`,
  `rule_id="llm_v25_<claim_type>"` (el formador preserva ambas);
  `LLMRunInfoV25.to_dict()` suma `lessons_sha256`,
  `lessons_version` (`alma-lessons-context/1.0`) y
  `lessons_block_chars` (9.052).

## 6. Verificación en seco

- **19 tests nuevos, todos verdes:** `tests/test_lessons_compiler.py`
  (5: disposiciones sintéticas contra conteos a mano — taxonomía
  3/2/2/1 sobre 8 reclamos, orden de selección exacto, nota GREY
  verbatim en el bloque —; auditoría limpia y adulteraciones
  detectadas; achique declarado y núcleo irrecortable con cap
  imposible → el compilador falla; auditoría del artefacto real
  contra el corpus real) y `tests/test_llm_reviewer_v25.py` (14:
  identidad, congelados, carga fail-closed ×4, inyección verbatim en
  profunda y mixta, selección byte-idéntica, extremo a extremo con
  transporte guionado — reclamo citable nace **conforme** y la 1.5.0
  lo **acepta**, con tags v2.5 y el bloque presente en la llamada
  real —, sin patrón → ledger `sin_patron_concreto_en_el_reclamo`,
  guardia que rehúsa antes de llamar con 0 llamadas, y **batería
  semáforo 16/16** conduciendo `review()` del v2.5 con el bloque en
  cada payload profundo).
- **Suite completa: 314/314 OK** (295 previas + 19 nuevas), sin
  regresiones.
- **Congelados byte-idénticos** (sha256 antes = después, verificados
  por test): puertas 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`, 1.2.0
  `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0 `b16c5a79…`, 1.4.1
  `08d813e9…`, 1.5.0 `71b1996b…` (POLICY `16befdd1…`), 
  `claim_contract.py` `7df8abc7…`, `birth_shaper.py` `2b127b23…`,
  `llm_reviewer_v23.py` `a78bdd6d…`, `llm_reviewer_v24.py`
  `ae378c2e…`. `agent/main.py` sin tocar.

## 7. Qué queda sin medir

El efecto de las lecciones sobre la producción real: si un modelo,
con su propia historia adjudicada en el prompt, nace con más
reclamos citables (la materia, el cuello que dejó la cadena gratis)
o si el bloque es peso muerto que desplaza diff. Ningún número de
este documento habla de eso y ninguno debe citarse como si lo
hiciera. La medición está **diseñada** en §5 del pre-registro —
tercer brazo del A/B estacionado del papel del v2.4: v2.4 contra
v2.5, mismos 25 PRs, misma vara, adjudicación completa, ~US$20 más
por el brazo a los precios medidos — y **ESTACIONADA**: se ejecuta
solo con papel de corrida nuevo y tope sobre la línea entera fijado
por Alejandro (saldo OpenAI US$5,31; prioridad declarada: deuda
cero + pasaje). La adjudicación de la nº 311 **no se compiló** —
declarado en §2.3 del pre-registro: el montaje de esa corrida no
persistió disposiciones por reclamo recuperables; compilarla sería
inventar procedencia.

## 8. Archivos de la tarea

- `PREREGISTRO-MEMORIA-LECCIONES.md` — 18.069 B (antes que el código).
- `CONTEXTO-LECCIONES.md` — 9.834 B; bloque 9.052 caracteres,
  sha256 `2cdb32ce…`.
- `CONTEXTO-LECCIONES.provenance.json` — 3.188 B.
- `agent/lessons_compiler.py` — 30.440 B.
- `agent/llm_reviewer_v25.py` — 10.212 B.
- `tests/test_lessons_compiler.py` — 10.319 B;
  `tests/test_llm_reviewer_v25.py` — 13.829 B.
- Asiento en `REGISTRO-REVIEWBENCH.md`; commit **local** con
  exactamente estos archivos (los clones de `adjwork298/repos/` son
  caché de construcción y no se commitean). **Sin push**, sin
  publicar, sin montar.
