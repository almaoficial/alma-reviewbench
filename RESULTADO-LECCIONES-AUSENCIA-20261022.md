# Resultado — Lecciones de ausencia: los 286 defectos que el revisor nunca reclamó

**Fecha:** 2026-10-22 · **Papel:** `PREREGISTRO-LECCIONES-AUSENCIA.md`
(definición, dimensiones y vara declaradas ANTES de computar).
**Costo: US$0** — análisis local sobre el oro público, las
emisiones y la adjudicación de la corrida nº 298; sin modelos,
sin portal, sin publicación.

## Veredicto en una línea

El cierre es exacto — **352 TP del oro = 66 tocados + 286
ausencias** — y el patrón dominante no es el que la intuición
sugería: **la mayoría de lo perdido (182 de 286, 63,6 %) vivía en
archivos que el revisor SÍ miró** y aun así no reclamó; solo el
36,4 % (104) estaba en archivos que nunca tocó. La ausencia es,
en su mayor parte, un problema de *reconocimiento sobre lo ya
mirado*, no de cobertura de archivos. Todo lo demás es
descriptivo: **ningún efecto sobre el recall se afirma** — eso
solo lo mide la corrida paga estacionada.

## 1. El cierre y las familias

| | n | % |
|---|---:|---:|
| TP del oro (25 PRs de la nº 298) | 352 | 100 |
| Tocados (recall grounded 66/352 = 18,75 %) | 66 | 18,8 |
| **Ausencias** | **286** | **81,3** |
| A1 — archivo nunca visitado por la base en ese PR | 104 | 36,4 de las ausencias |
| A2 — archivo visitado, defecto no reclamado | 182 | 63,6 de las ausencias |
| A2 con alguna emisión solapando las líneas del defecto | 54 | 29,7 de A2 |
| Ausencias «rozadas» por un GREY (ref parseable) | 11 | 3,8 de las ausencias |

Refs GREY: 17 decisiones; **16 parsean** con la regla declarada
(`G<n>` simple) y 1 no — el ref doble `G13/G6` de
konturio_disaster-ninja-fe E1 — que por la regla declarada no
cuenta como roze. Los 11 rozados son ausencias plenas según el
criterio grounded: el revisor circuló por el defecto y la
adjudicación lo archivó como zona gris, no como ese defecto.

Por PR: los peores son cmik_apilix (29 ausencias de 36 TP),
DisciplinedSoftware_Codebase-Conversion (26 de 31),
scotthamilton77_agents-config (24 de 25), PROTRIDER (19 de 21) y
Mcp-Docker (16 de 22). Dos PRs tuvieron recall cero —
allan-mobley-jr_gimmes y simnaut_emdash, todos sus TP ausentes —
y el mejor PR (brianc_node-postgres) aun así perdió 7 de 11.

## 2. Por dimensión (ausencias / TP del oro, con tasa)

**Por category** — dos categorías con ceguera total:

| Categoría | Ausentes | Tasa |
|---|---:|---:|
| maintainability | 44/44 | 100 % |
| api-architecture | 12/12 | 100 % |
| documentation | 18/21 | 85,7 % |
| security | 23/27 | 85,2 % |
| reliability | 49/58 | 84,5 % |
| correctness | 100/133 | 75,2 % |
| testing | 26/35 | 74,3 % |
| accessibility | 7/10 | 70,0 % |
| performance | 7/12 | 58,3 % |

Correctness domina por *volumen* (100 de las 286 ausencias) pero
tiene la segunda tasa más baja entre las categorías grandes: el
revisor pierde de todo, y pierde *todo* lo de mantenibilidad y
arquitectura de API que el oro marcó.

**Por scope** — el defecto preexistente es invisible para esta
base: **pre-existing 23/23 (100 %)**, exacerbated-by-pr 12/14
(85,7 %), introduced-by-pr 251/315 (79,7 %). Nada de lo que el
PR no introdujo fue reclamado jamás.

**Por context_required** — **plano**: diff-plus-related-files
178/220 (80,9 %), diff-only 94/115 (81,7 %),
broader-project-context 14/17 (82,4 %). La clase de contexto NO
discrimina la ausencia: se pierde lo mismo necesite el defecto
el diff solo o el proyecto entero. (La regla 3 del artefacto
cita al líder por volumen, como manda su plantilla; la lectura
honesta es esta planitud, y queda asentada acá para que nadie
extraiga del bloque una lección de contexto que el dato no
sostiene.)

**Por difficulty** — invertido contra la intuición: los
«fáciles» se pierden *más* — easy 148/174 (85,1 %), medium
125/159 (78,6 %), hard 13/19 (68,4 %).

**Por severity**: low 165/182 (90,7 %), high 28/36 (77,8 %),
medium 93/134 (69,4 %).

## 3. El artefacto compilado

`CONTEXTO-AUSENCIAS.md` (9.282 B) + provenance (3.424 B):
bloque inyectable de **8.427 caracteres** (tope declarado
9.600), block-sha256 `be712a35…`, corpus fijado por el sha256
de `decisions.json` (`feebdc6e…`, el mismo del contexto de
lecciones). Contiene los conteos por dimensión, **4 ejemplos**
verbatim (A1-1, A1-2, A2-1, A2-2) y 5 reglas imperativas que
citan sus conteos.

La selección mecánica eligió 6 ejemplos (3 por familia) y el
bloque sin achicar midió **10.960** caracteres: se aplicó
exactamente el achique declarado en el pre-registro (salen los
A2 más allá de 2, luego los A1 más allá de 2) y quedaron 4 —
los dos A1 de AY2526 y los dos A2 de AA-Factory, por el orden
determinista (familia, PR, índice del oro). Elegibles había de
sobra (88 A1 y 147 A2 con cita ≤ 12 líneas): el límite fue el
tamaño del bloque, no el material. **Auditoría de procedencia:
0 violaciones** (recompilación determinista idéntica + hash +
verbatim por ejemplo, incluido el reclamo citado de la base;
los tests prueban que la auditoría detecta adulteraciones
nombrando la violación — conteo cambiado, hash corrupto,
ejemplo apuntando a un TP tocado).

## 4. Salvedades (vinculantes)

- **Efecto sobre el recall: NO medido.** Este papel es
  descriptivo sobre datos ya medidos, como declaró el
  pre-registro. Que un revisor lea estas ausencias y reclame
  más de lo verdadero es una hipótesis cuya única medición
  posible es la corrida paga estacionada.
- **El artefacto no está montado en ningún revisor.** El v2.5
  sigue inyectando solo el contexto de lecciones; montar el de
  ausencias (junto, en vez, en otra pasada) es decisión
  posterior con su propio papel — no se hizo en esta tarea.
- La familia A1/A2 se asigna por igualdad exacta de la cadena
  de archivo entre el oro y las emisiones (la convención de los
  propios datos de la corrida); un mismo archivo con rutas
  escritas distinto contaría como «nunca visitado». En este
  corpus ambas fuentes comparten convención.
- Los conteos por PR mezclan tamaño con ceguera (un PR con 36
  TP aporta más ausencias que uno con 6); las tasas por PR
  están en el manifiesto para quien quiera la lectura fina.

## 5. Verificación de cierre

- Cierre de la adjudicación re-derivado por programa:
  **352 = 66 + 286**, sin errores de consistencia (toda
  decisión TP apunta a un TP del oro; toda FPG, a un FP).
- Suite completa: **324/324** tests en verde (314 previos + 10
  nuevos de `tests/test_absence_compiler.py`).
- Congelados byte-idénticos por sha256 al cierre: puertas
  1.0.0–1.5.0, `claim_contract.py` `7df8abc7…`,
  `birth_shaper.py` `2b127b23…`, revisores v2.3 `a78bdd6d…`,
  v2.4 `ae378c2e…`, v2.5 `7546d7d9…`,
  `lessons_compiler.py` `482fce85…`, `CONTEXTO-LECCIONES.md`
  `92895d85…` y su provenance `d56e6104…`.
- Nuevos: `PREREGISTRO-LECCIONES-AUSENCIA.md`,
  `agent/absence_compiler.py`, `tests/test_absence_compiler.py`,
  `CONTEXTO-AUSENCIAS.md`, `CONTEXTO-AUSENCIAS.provenance.json`
  y este resultado. Commit local; sin push.

— Resultado de lecciones de ausencia, 2026-10-22. Gasto: **US$0**.
