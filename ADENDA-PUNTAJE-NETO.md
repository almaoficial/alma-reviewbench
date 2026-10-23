# Adenda — el puntaje neto (regla Breken) como métrica secundaria de la línea

**Fecha:** 2026-10-23 (EDT). **Costo de esta tarea: US$0** — sin
llamadas a modelos, sin portal, sin cargas, sin publicación, sin
push. **Autorización:** Alejandro, 23/10/2026 («Lo hagamos»),
sobre la propuesta de adoptar el puntaje del benchmark ESCAPES
v1 de Breken como segunda vara de la línea. **Relación con los
papeles vigentes:** esta adenda NO modifica ningún papel. Cita
como diseño rector el `PREREGISTRO-PRODUCTOR-EVIDENCIA.md`
(validación paga diseñada en su §4, declarada ESTACIONADA) y el
tercer brazo diseñado en la §5 del
`PREREGISTRO-MEMORIA-LECCIONES.md` (revisor v2.5), y se les
anexa: donde esos papeles fijan la vara principal (precisión y
recall grounded, por separado), esta adenda suma una métrica
secundaria obligatoria de reporte. Ninguna puerta, ningún
revisor y ningún papel anterior se toca.

## 1. Por qué una segunda vara

La vara de adopción de la línea mira precisión y recall por
separado. Con esa vara, un brazo que casi no emite puede
disfrazarse de prudente: el brazo ALMA de la nº 311 (puerta
1.4.1) emitió 1 solo reclamo de 169 candidatos y cerró con
precisión grounded 0 % y recall grounded 0 % — números que, sin
el denominador, no distinguen «casi no habló» de «habló bien».
El benchmark ESCAPES v1 (Breken) puntúa distinto: **+1 por
acierto probado, −1 por falsa alarma**. Bajo esa regla el
silencio suma 0, el ruido resta, y ningún brazo se declara
bueno por callar. Esta adenda adopta esa cuenta como métrica
secundaria pre-registrada de la línea, con la definición
operativa exacta de la §2 — escrita, como manda la disciplina
de la casa, ANTES de computar un solo número bajo ella.

## 2. Definición operativa (exacta, sobre adjudicaciones grounded)

- **Unidad de cuenta: la emisión.** Cada hallazgo emitido por
  el brazo cuenta una vez, con el veredicto grounded que la
  adjudicación de su corrida le asignó. El conteo es por
  emisión, consistente con cómo la línea mide precisión (89
  emisiones TP sobre 66 TP gold distintos en la nº 298: las
  emisiones duplicadas sobre un mismo TP cuentan cada una).
- **+1 — acierto probado:** emisión con veredicto grounded
  **TP** (grounded en un TP gold, con el criterio de matching
  de la adjudicación: mismo archivo + región + mismo
  defecto/mecanismo).
- **−1 — falsa alarma probada:** emisión con veredicto
  grounded **FPG** (coincide en archivo y reclamo con un FP
  gold: el gold juzgó ese reclamo falso). Es la única clase
  que resta, porque es la única falsedad *probada* contra el
  oro. Si una adjudicación futura separa subclases dentro de
  las falsas probadas, todas restan −1 y el desglose las
  nombra por separado.
- **0 — ni suma ni resta:** emisiones **GREY** (zona gris: el
  gold ni confirma ni refuta — mismo territorio, mecanismo no
  cerrable con el estándar; incluye los casos que rozan un FP
  gold sin ser el mismo reclamo, que la adjudicación
  explícitamente NO clasifica FPG) y emisiones **NOVEL** (sin
  contraparte en el gold: la adjudicación grounded no las
  juzga; pertenecen a la familia augmented del portal).
  Razón de la clase cero: Breken resta por falsa alarma
  *probada*. GREY y NOVEL son no-verificadas o no-juzgadas, no
  refutadas; cobrarlas −1 confundiría inverificabilidad con
  falsedad y castigaría dos veces lo que la fracción en
  `needs_validation` ya mide por su lado.
- **Alternativa considerada y NO adoptada:** cobrar −1 también
  por NOVEL («todo lo no acreditado resta»). Se rechaza por la
  razón anterior y por una de diseño: el gold de ReviewBench
  es la cosecha de reclamos de OTROS agentes, no el universo de
  defectos; un reclamo NOVEL puede ser un defecto real que el
  gold no cosechó, y esta línea ya decidió — en la
  adjudicación de la nº 298 — no juzgarlos en la familia
  grounded. Queda asentada para que nadie la reintroduzca en
  silencio.
- **Expresión del puntaje, dos números siempre juntos:**
  - **Neto crudo** = TP − FPG (entero, con signo).
  - **Neto por 100 emisiones** = neto crudo / emisiones × 100,
    con un decimal. Si el brazo emitió 0, el neto crudo es 0 y
    el normalizado se reporta **n/d** (no definido: no hay
    emisiones contra las que normalizar).
  El crudo castiga el silencio en términos absolutos (no
  emitir suma 0, contra los aciertos que la base sí sumó); el
  normalizado mide pureza por emisión. Ninguno de los dos,
  solo, es la lectura: se reportan juntos y con el desglose
  completo (+TP, −FPG, 0 GREY, 0 NOVEL, emisiones).

## 3. Regla de lectura (vinculante para los papeles futuros)

1. El puntaje neto es **secundario**: nunca adopta ni rechaza
   una versión por sí solo. La vara principal sigue siendo la
   de cada pre-registro (precisión y recall grounded, con sus
   umbrales declarados).
2. Se **reporta al lado de precisión y recall** en todo papel
   futuro de la línea que adjudique emisiones — empezando por
   el resultado de la validación paga estacionada (§4) — con
   el desglose completo de la §2.
3. **Un brazo con neto crudo ≤ 0 no puede declararse mejora**
   aunque gane en precisión. (Un brazo que emite 1 reclamo no
   probado y nada más tiene neto 0: no es una mejora, es una
   ausencia con buena prensa.)
4. El neto **no mide cobertura**: un brazo puede tener neto
   normalizado alto emitiendo poco sobre un corpus enorme. Por
   eso acompaña a P/R y jamás los reemplaza; el recall sigue
   siendo el número que cobra la ausencia.

## 4. Su lugar en el diseño estacionado

La validación paga diseñada en la §4 del
`PREREGISTRO-PRODUCTOR-EVIDENCIA.md` (A/B sobre los mismos 25
PRs: base v2.3.2 contra v2.4 con puerta 1.5.0, adjudicación
completa) y el tercer brazo de la §5 del
`PREREGISTRO-MEMORIA-LECCIONES.md` (v2.5 con el contexto de
lecciones) quedan **citados, no modificados**: esta adenda no
toca su vara, sus brazos ni su presupuesto. Lo único que suma
es una obligación de reporte: el papel de resultado de esa
validación, cuando corra, publicará para cada brazo — junto a
precisión y recall grounded — el neto crudo, el neto por 100
emisiones y el desglose (+, −, 0 GREY, 0 NOVEL), computados
con el módulo de la §5 sobre la adjudicación de esa corrida.
La regla §3.3 aplica a cualquier declaración de mejora que
salga de esa validación.

## 5. Cómputo de esta adenda (alcance declarado)

El resultado que acompaña a esta adenda
(`RESULTADO-PUNTAJE-NETO-20261023.md`) computa el neto, con la
definición de la §2 y por programa desde las fuentes primarias
(nunca a mano), sobre todo brazo de la línea que tenga
adjudicación grounded asentada:

- **Base nº 298** (corrida real, 166 emisiones): desde
  `adjwork298/decisions.json`.
- **Brazo ALMA nº 311** (corrida real con puerta 1.4.1, 1
  emisión): desde su adjudicación
  (`ADJUDICACION-COMPLETA-311-20261022.md`, §2: 0 TP / 0 FPG /
  1 GREY / 0 NOVEL). No existe `decisions.json` por reclamo
  para la 311 — es su defecto de observabilidad ya asentado —;
  el brazo entra a la tabla como registro asentado con su
  fuente nombrada, no como cómputo.
- **Replays sobre el corpus A** (los 166 de la base, con la
  misma adjudicación): la autopsia de la 1.4.1 (0 aceptados),
  la puerta 1.5.0 sola (32 emitidos), el pipeline del contrato
  (49 emitidos) y el pipeline del formador al nacer (79
  emitidos) — re-derivados por programa con la fórmula de
  replay de la línea y cruzados contra `decisions.json`, con
  sanidad obligatoria: cada cruce debe cerrar exacto contra el
  papel publicado de su medición (base 89/8/17/52; 1.5.0
  19/2/2/9 de 32; contrato 26/2/3/18 de 49; formador 44 TP y
  4 FPG de 79) antes de que su neto se asiente.

El cálculo queda como módulo reutilizable de la línea,
`agent/net_score.py` (`alma-net-score/1.0`), con tests
sintéticos contra conteos a mano y tests de cierre contra las
adjudicaciones reales — para que la validación paga futura lo
importe en vez de reimplementarlo.

## 6. Qué esta adenda NO afirma

- No re-juzga ningún brazo: la vara principal de cada papel
  sigue diciendo lo que dijo (la 1.5.0 no adoptada, el formador
  no adoptado, la 311 NO PASA — nada de eso cambia).
- No compara contra Breken ni contra ningún sistema externo:
  la regla se toma prestada; los números son solo de esta
  línea, sobre su gold y su estándar grounded.
- No afirma efecto alguno de los brazos v2.4/v2.5: su neto se
  computará cuando exista su adjudicación, ni un día antes.
