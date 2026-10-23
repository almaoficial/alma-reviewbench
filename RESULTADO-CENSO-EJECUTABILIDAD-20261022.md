# Resultado — Censo de ejecutabilidad de la sala de espera de la 1.4.1

**Fecha:** 2026-10-22 · **Papel:** `PREREGISTRO-CENSO-EJECUTABILIDAD.md`
(la taxonomía cerrada y las reglas de borde se escribieron ANTES de
clasificar un solo reclamo). **Costo: US$0** — archivos locales y la
puerta congelada; sin modelos, sin portal, sin publicación.

## Veredicto en una línea

**La sala de espera NO es estructural por falta de materia: el
81,2 % de los 149 reclamos retenidos (121/149) es decidible por
ejecución** — pero casi nada de eso es consulta: solo **4** tienen
un oráculo existente identificado en el propio reclamo (E1); los
otros **117** exigen CONSTRUIR la reproducción (E2), con el reclamo
como especificación. Y la ejecutabilidad apenas concentra verdad:
la tasa de TP entre los ejecutables es 56,2 % contra 53,7 % de
base en la sala. Lo que la vía de ejecución ofrece no es
discriminación gratis — es **cobertura**: podría decidir 68 de los
80 verdaderos (85,0 %) que la citación no pudo verificar en
absoluto, al precio de correr también sobre 53 no-verdaderos que
solo la ejecución, al fallar, descartaría.

## 1. Arnés y sanidad (vinculante, cerró exacta)

Corpus reconstruido con la fórmula publicada de la línea
(`lessons_compiler.load_corpus` + `born_candidate`), sala de
espera re-derivada ejecutando la puerta CONGELADA 1.4.1 (POLICY
`73a403d8…`, sin modificar) sobre los 166 candidatos. Antes de
clasificar, la reconstrucción reprodujo **exacto** el replay
publicado: **0 aceptados / 149 retenidos / 17 rechazados**, y el
gold de los retenidos **80 TP / 8 FPG / 16 GREY / 45 NOVEL**
(`adjwork298/decisions.json`). Ningún reclamo se clasificó sobre
una lista a mano: los 149 salen de la puerta, por programa.

## 2. El mapa — conteos por clase

| Clase | n | % de la sala | Qué es |
|---|---:|---:|---|
| **E1** ejecutable directo | **4** | 2,7 % | Oráculo existente identificado en el reclamo (test o comando cuya corrida, tal cual, decide) |
| **E2** ejecutable con construcción | **117** | 78,5 % | Sin oráculo citado, pero el reclamo define entrada y observable: alcanza como spec de la reproducción |
| **E3** no ejecutable en principio | **28** | 18,8 % | Juicio de diseño, ausencia estática, semántica externa, aritmética sobre constantes declaradas |
| **E4** inclasificable | **0** | 0,0 % | Ningún reclamo quedó sin materia para clasificarlo |
| **Total** | **149** | 100 % | |

## 3. El cruce con gold — el número que importaba

| Clase | TP | FPG | GREY | NOVEL | Tasa TP |
|---|---:|---:|---:|---:|---:|
| E1 (n=4) | 4 | 0 | 0 | 0 | 100 % (n=4, anecdótico) |
| E2 (n=117) | 64 | 7 | 13 | 33 | 54,7 % |
| E3 (n=28) | 12 | 1 | 3 | 12 | 42,9 % |
| **Sala (n=149)** | **80** | **8** | **16** | **45** | **53,7 %** |

Las tres lecturas declaradas en el pre-registro, contra el número:

- **¿Concentra TP? Apenas.** Ejecutables (E1+E2): 68 TP / 121 =
  56,2 %, solo +2,5 pp sobre la tasa base de la sala (53,7 %). La
  ejecutabilidad no es un detector de verdad.
- **¿Concentra FPG para descartar rápido? Tampoco en especial:**
  7 de los 8 falsos confirmados son ejecutables (87,5 %) — casi la
  misma proporción que los TP (85,0 %). La ejecución los decidiría
  a *ellos también*, en cualquier dirección.
- **La lectura que el número sostiene es la de cobertura:** de los
  80 TP que la puerta retuvo sin poder verificar ninguno, **68
  (85,0 %) tienen una vía de ejecución que los decidiría**. La
  sala no está llena de reclamos indecidibles: está llena de
  reclamos decidibles por OTRO instrumento. Y el residuo es real:
  **12 TP (15,0 %) son E3** — verdaderos cuya verdad es de diseño
  o estática, inalcanzables también para la ejecución.

**Decidibilidad ≠ discriminación:** 53 de los 121 ejecutables son
no-TP (7 FPG + 46 GREY/NOVEL). La vía no separa nada por sí sola:
habría que correr las 121 reproducciones y pagar sus veredictos
uno por uno. Lo que el censo prueba es que el material para
hacerlo EXISTE dentro de la sala; no que el resultado sería
limpio.

## 4. El costo de la vía: construcción, no consulta

La descomposición E1/E2 es el dato operativo del censo. Un oráculo
**existente** e identificado en el propio reclamo aparece 4 veces
en 149 (2,7 %). Todo el resto de la materia ejecutable (117) exige
escribir la reproducción caso por caso — un test, un fixture, un
arnés — usando el reclamo como especificación. Una «tercera vía»
no sería una regla más de la puerta: sería una **capacidad de
construcción de reproducciones** (o un humano haciéndolo), con su
costo por reclamo. La sala de espera es estructural *para la
citación*; para la ejecución es una cola de trabajo de
construcción con 121 ítems, no un muro.

## 5. Cómo se clasificó (vías y criterios de borde aplicados)

- **Script determinista** (`agent/executability_census.py`):
  clasificó **28/149 (18,8 %)** — solo cuando las reglas de
  exactamente una clase dispararon sin oposición (E1: 4, E2: 5,
  E3: 19). Declaró DUDA en 121.
- **Revisión asistida** (lectura del agente ejecutor, sin modelos,
  con razón de una línea asentada por reclamo): **121/149
  (81,2 %)** → E2: 112, E3: 9, E1: 0, E4: 0. Que la revisión no
  haya asignado ningún E1 confirma el §4 desde el otro lado: los
  reclamos casi nunca nombran su oráculo.
- Criterios de borde que la revisión aplicó, lecturas fieles de
  las definiciones pre-registradas (se declaran porque gobiernan
  familias enteras):
  - **Reclamos sobre tests** (test tautológico, aserción omitida,
    «no hay test para X»): decidibles por **mutación** — introducir
    la regresión nombrada y observar que la suite pasa — cuando el
    reclamo nombra la regresión concreta → E2. Es la familia más
    numerosa de la sala después de los defectos de comportamiento.
  - **«Correr el propio artefacto bajo una condición»** (el
    instalador bajo Bash 3, el endpoint con un POST, la sonda en
    Node 18) contó como **construcción (E2)**, no como oráculo
    existente: el oráculo de E1 es un artefacto de verificación ya
    existente (test/comando) identificado en el reclamo.
  - **Exposición a tecnología asistiva** (qué anuncia VoiceOver,
    qué traits expone la vista): propiedad de **runtime**,
    auditable corriendo la vista y leyendo el árbol de
    accesibilidad → E2. En contraste, los reclamos de **contraste
    WCAG** traen ambos valores hex y la razón ya computada: es
    aritmética sobre constantes declaradas, ninguna corrida del
    producto la decide → E3.
  - **Desajustes de contrato esquema↔runtime** (el esquema omite
    el `maxLength` que el parser impone): la verdad es la
    comparación estática de dos textos → E3.
  - **Concurrencia**: E2 solo cuando el reclamo nombra una
    secuencia/interleaving forzable en un arnés (dos pushes que
    leen el mismo estado; interrumpir en espera y el runnable
    encolado); la concurrencia genérica sin interleaving quedó
    E3 (la que el script ya había marcado).

## 6. Qué NO afirma este censo (salvedades del pre-registro)

- **Clasificar no es verificar.** Ninguna reproducción se corrió:
  la clase afirma decidibilidad EN PRINCIPIO desde el reclamo
  escrito. No afirma que la ejecución sea barata, portable entre
  entornos, ni que su veredicto coincida con el gold — un reclamo
  E2 puede ejecutarse y resultar falso, y uno E3 puede ser
  verdadero (12 lo son).
- La fracción alta de revisión asistida (81,2 %) es un resultado,
  no una meta: las señales textuales del script separan limpio
  solo los casos extremos; el centro del corpus — reclamos de
  comportamiento concretos, sin vocabulario de oráculo — es
  exactamente lo que un lector decide y una regex no.
- Ninguna puerta se modificó, ninguna vía se adopta, ninguna
  corrida se propone en este papel: el entregable es el mapa.

## 7. Verificación de cierre

- Sanidad del §1 reproducida por programa antes de clasificar
  (0/149/17; gold de la sala 80/8/16/45) y re-aseverada en los
  tests de integración.
- Conteos por clase suman **149**; el cruce por clase suma, por
  columna, el gold de la sala (80/8/16/45) — aserción automática
  en `run_census` al cerrar la clasificación.
- Suite completa: **337/337** tests en verde (13 nuevos de
  `tests/test_executability_census.py`: una por familia de regla,
  conflicto→duda, sin-señal→duda, sanidad e integración con
  revisión).
- Artefactos congelados byte-idénticos (sha256 verificados al
  cierre): puertas 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`, 1.2.0
  `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0 `b16c5a79…`, 1.4.1
  `08d813e9…`, 1.5.0 `71b1996b…`, `claim_contract.py`
  `7df8abc7…`, `birth_shaper.py` `2b127b23…`, revisores v2.3
  `a78bdd6d…` y v2.4 `ae378c2e…` — idénticos a los asentados en
  los papeles anteriores.
- Nuevos: `agent/executability_census.py`
  (`alma-executability-census/1.0`) y
  `tests/test_executability_census.py`.

— Resultado del censo de ejecutabilidad, 2026-10-22. Gasto: **US$0**.
