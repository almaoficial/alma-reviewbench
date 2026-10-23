# Pre-registro — Lecciones de ausencia: lo que el revisor nunca reclamó

**Fecha:** 2026-10-22 · **Costo: US$0** — análisis local sobre
archivos ya medidos; sin llamadas a modelos, sin portal, sin
cargas, sin publicación. **Autorización:** Alejandro, 22/10/2026
(«Hagamos las 3») — primera de las tres piezas aprobadas esa
noche. Este papel se escribe ANTES del código que lo ejecuta.

## 1. El hueco que esta pieza llena

El compilador de lecciones (`agent/lessons_compiler.py`, papel
`PREREGISTRO-MEMORIA-LECCIONES`) destila la historia adjudicada
del revisor desde sus **166 reclamos nacidos**: cómo murieron, qué
los dejó vivir. Pero el recall grounded de esa misma corrida base
(nº 298, adjudicación completa) fue **66/352 = 18,75 %**: hay
**286 defectos verdaderos del oro que el revisor nunca reclamó**,
y de esos el compilador no aprendió nada, porque nunca existieron
como reclamos. La memoria de lecciones cubre el error de
*comisión* (reclamar mal); esta pieza compila el error de
*omisión*: **qué se le escapó al revisor y dónde vivía lo que se
le escapó.**

## 2. Fuentes (todas locales, todas ya medidas)

- El oro público de ReviewBench: `adjwork298/gold/golden/*.json`,
  restringido a los **25 PRs de la corrida nº 298** (los que
  tienen emisiones en `adjwork298/run298/prs/`). Cada entrada del
  oro trae: `file`, `start_line`, `end_line`, `message`,
  `tp_fp`, `severity`, `category`, `scope`, `difficulty`,
  `context_required` y justificaciones.
- Las emisiones de la base: `adjwork298/run298/prs/*/findings.json`
  (166 emisiones con `file`, `start_line`, `end_line`, `message`).
- La adjudicación grounded: `adjwork298/decisions.json` (su sha256
  queda declarado en el artefacto compilado, como en el contexto
  de lecciones).

## 3. Definición operativa de «ausencia» (el criterio NO se reinventa)

Es exactamente el criterio de la adjudicación grounded que la
línea ya publicó (`adjwork298/aggregate298.py`):

- Una entrada del oro se identifica por `(pr, g)`, donde `g` es su
  índice (base 0) en la lista `findings` del archivo del oro de
  su PR — el mismo índice que las decisiones usan en el campo
  `g` y en los `ref` tipo `G<n>`.
- Una entrada con `tp_fp == "tp"` está **tocada** si y solo si
  existe una decisión de emisión con `v == "TP"` y `g` igual a su
  índice. Está **ausente** en caso contrario.
- Cierre obligatorio: **352 TP = 66 tocados + 286 ausencias**.
  Si el cómputo no cierra contra la adjudicación, la tarea se
  detiene y reporta — la definición no se ajusta para que cierre.

Dato descriptivo secundario, que **no** altera el criterio: una
emisión con veredicto `GREY` cuyo `ref` (`G<n>`, parseable) apunta
a un TP ausente se reporta como «rozado, no tocado» — el revisor
circuló por el defecto y la adjudicación no lo contó como el
mismo. Se cuentan solo los `ref` que parsean limpios, y se
declara cuántos parsearon.

## 4. Dimensiones del análisis (declaradas antes de computar)

Para cada TP ausente, con datos que el oro y las emisiones ya
traen:

1. **Por PR**: ausencias y tasa de ausencia (ausencias / TP del PR).
2. **Por archivo visitado**: ¿la base emitió *algo* en el mismo
   archivo dentro de ese PR? Dos familias de ausencia:
   - **A1 — archivo nunca visitado**: ninguna emisión de la base
     en ese archivo en ese PR.
   - **A2 — archivo visitado, defecto no reclamado**: hay
     emisiones en el archivo, ninguna lo tocó. Subdato: si alguna
     emisión en el archivo **solapa** el rango de líneas del TP.
3. **Por `category` del oro** (correctness, reliability, testing,
   maintainability, security, documentation, api-architecture,
   performance, accessibility): conteos y tasa de ausencia.
4. **Por `context_required`** (diff-only, diff-plus-related-files,
   broader-project-context): conteos y tasa de ausencia.
5. **Por `scope`** (introduced-by-pr, pre-existing,
   exacerbated-by-pr): conteos y tasa de ausencia.
6. **Por `severity` y por `difficulty`**: conteos y tasa de
   ausencia (reportadas; sin prometer patrón).

Ninguna dimensión se agrega después de ver los números; si una
dimensión no soporta conteo (campo ausente), se declara y se omite.

## 5. El artefacto

`CONTEXTO-AUSENCIAS.md` + `CONTEXTO-AUSENCIAS.provenance.json`,
hermanos de `CONTEXTO-LECCIONES`: un bloque de contexto acotado
(≤ **9.600 caracteres**, entre marcadores propios) que contiene:

- Los conteos crudos de §4 (totales y por dimensión, con tasas).
- **Ejemplos trazables** de TP perdidos: el mensaje del oro
  *verbatim*, su ubicación (`file:start-end`), su metadata
  (category / context_required / scope) y **qué miró la base en
  ese PR en cambio**: cuántas emisiones hizo en el PR, cuántas en
  ese archivo, y — si las hay — una emisión suya en el mismo
  archivo, *verbatim*.
  Selección mecánica declarada: elegibles los TP ausentes cuya
  cita del oro abarca ≤ 12 líneas; orden determinista por
  (familia, PR, índice del oro); hasta **3 por familia** (A1, A2).
  Si el bloque excede el tope, achique mecánico: salen primero
  los ejemplos A2 más allá de 2, luego los A1 más allá de 2; los
  conteos y las reglas nunca se recortan; si aun así no entra,
  el compilador **falla** en vez de cortar.
- **Reglas destiladas** en imperativo corto, derivadas solo de
  los conteos de §4 y citándolos (cada regla lleva su número).

El texto del bloque va en inglés, como el de lecciones, porque es
contexto inyectable a los prompts de producción del revisor; los
nombres de las dimensiones del oro se conservan tal cual.

**Auditoría de procedencia**, con el mismo estándar que el
compilador de lecciones: recompilación determinista idéntica al
bloque + hash declarado + por ejemplo, el mensaje del oro y la
emisión citada verificados *verbatim* contra sus fuentes y por
hash en el manifiesto. Cero ejemplos inventados: todo ejemplo
rastrea a una entrada del oro `(pr, g)` declarada en el
manifiesto.

## 6. La vara honesta (vinculante)

Esto es **descriptivo sobre datos ya medidos**. Este papel y su
resultado **no afirman** que leer las lecciones de ausencia
mejore el recall, ni en un punto: el efecto de un contexto sobre
la producción es propiedad de un modelo real y solo lo mide la
corrida paga, que sigue **estacionada** a la espera de ingresos y
del tope de línea de Alejandro. Tampoco es parte de esta tarea
inyectar el artefacto en ningún revisor: la pieza compila la
memoria; montarla es decisión posterior, con su propio papel.

## 7. Lo que no se toca

Byte-idénticos al cierre (verificado por sha256 y por la suite):
todas las puertas (`alma_gate*.py`), `claim_contract.py`,
`birth_shaper.py`, los revisores v2.3/v2.4/v2.5,
`lessons_compiler.py`, `CONTEXTO-LECCIONES.md` y su provenance.
El código nuevo vive en un módulo compañero
(`agent/absence_compiler.py`) que **importa** del compilador de
lecciones lo que reuse (hash, disciplina) sin modificarlo.
Cierre: suite completa verde, commit LOCAL (sin push) y asiento
en el REGISTRO.
