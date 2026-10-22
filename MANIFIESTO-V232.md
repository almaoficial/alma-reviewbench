# Manifiesto de publicación v2.3.2 — ReviewBench (imagen reparada: admisión `v141`)

**Versión del manifiesto:** run-manifest/2.3.2 · **Preparado:** 2026-10-22 ·
Pre-registro: [`PREREGISTRO-REVIEWBENCH-V23.md`](PREREGISTRO-REVIEWBENCH-V23.md)
(cuerpo congelado 2026-10-21 + **Adenda 4**, firmada por Alejandro el
2026-10-22 a las 07:37 EDT — «Lo hagamos» — que pre-registra esta
reparación, su falsador y el relanzamiento del brazo ALMA)

**Estado de este manifiesto: CERRADO** (con la enmienda de cierre al
final: imagen construida y verificada en dos fuentes, y corrida
nº 311 corrida con esa imagen). *Texto original al abrirlo:* El
commit del paquete v2.3.2 está
en `main` (ver el sobre) y los 10 archivos quedaron verificados
byte a byte contra el remoto (sha256 y SHA de blob, 10/10). El
workflow `reviewbench-image` es solo disparo manual
(`workflow_dispatch`, «compuerta humana» por diseño) y su disparo
requiere el navegador con la sesión de Alejandro: **queda pendiente
de disparo sobre el commit del sobre**. Cuando la corrida cierre, el
digest se verifica en dos fuentes (resumen de la corrida de Actions
y página del paquete GHCR) y se asienta acá con una enmienda de
cierre, con el mismo procedimiento de la v2.3 (corrida nº 6), la
v2.3.1 (corrida nº 7) y las anteriores. **Este manifiesto cierra la
PUBLICACIÓN del código; no lanza nada:** la secuencia de la Adenda 4
sigue con el disparo del workflow, la actualización de SOLO el campo
de imagen de la config ALMA del portal y, tras la compuerta de saldo
(≥ US$25 verificado en el acto; US$25,58 al 22/10 07:33 EDT), el
relanzamiento del brazo ALMA — el último acto del papel v2.3.

## Sobre

- **Commit:** `8ae47d402b8300d02ad427c0cc2fdd68cc6eb9ae` (main de
  `almaoficial/alma-reviewbench`, sobre la cabeza previa `cc56817`).
- **Imagen (digest):** `ghcr.io/almaoficial/alma-reviewbench@sha256:fbf1fe48364f915fed703a0a618bea48e0e7b379f7afaa645b8b4bf712850498`
  (construida por el workflow `reviewbench-image`, corrida nº 8, y
  verificada en dos fuentes — detalle en la enmienda de cierre).
  Reemplazó a la v2.3.1 (`sha256:144756cea49ee33e8b16ddb0204556adb0f1c2430ea885ec6a206bbaa6964544`).
- **Revisor:** `llm-reviewer/2.3.2` (constante `REVIEWER_VERSION` en
  `agent/llm_reviewer_v23.py`, sha256 del archivo `a78bdd6d…`).
- **Puerta del brazo ALMA:** 1.4.1, POLICY_SHA256
  `73a403d853fca843f06d289e90b5dd7e93dde8b469ad3da7b06bb8448c64db46`
  — archivo `agent/alma_gate_v141.py` byte-idéntico (sha256
  `08d813e9…`), recomputada y verificada en el arreglo.

## Qué es la v2.3.2

La v2.3.1 con UNA reparación de cableado y nada más (Adenda 4 §3):
la imagen trae dos resolvedores de `RB_CONFIG_GATE` que no se
espejan — el selector de `agent/main.py` admite `v141` desde la
Adenda 1 y cargó la puerta 1.4.1 en la práctica nº 310, pero el
resolvedor interno del revisor, `_resolve_gate_v23`, tenía su
propia lista que terminaba en `v14` y rechazó `v141` fail-closed
antes de cualquier llamada al modelo (la nº 310: FAILED en
run-agent, costo real US$0,00, cero emisiones; diagnóstico con
recibos en `DIAGNOSTICO-PRACTICA-ALMA-310-20261022.md`). El arreglo,
en `agent/llm_reviewer_v23.py` y en ningún otro archivo de código:
la rama espejo `v141` (las 19 clases y la guía de la 1.3.0 con la
identidad `GATE_V141_VERSION`), la importación de esa identidad, el
mensaje de error con `'v141'` en la lista, y el bump de versión.
Mismos prompts, mismas clases, mismo techo de 4.096, misma puerta:
es completar la tabla de admisión del revisor, no un cambio de
comportamiento.

## Archivos del commit `8ae47d4` (10, verificados 10/10 byte a byte)

| Archivo | Estado | sha256 |
|---|---|---|
| `agent/llm_reviewer_v23.py` | modificado (el arreglo) | `a78bdd6d…` |
| `tests/test_llm_reviewer_v232.py` | nuevo (4 tests de la resolución `v141`) | `00adef18…` |
| `tests/test_llm_reviewer_v23.py` | modificado (2 pins de versión → 2.3.2) | `6fc14181…` |
| `tests/test_llm_reviewer_v231.py` | modificado (1 pin de versión → 2.3.2) | `4bbc269e…` |
| `PREREGISTRO-REVIEWBENCH-V23.md` | modificado (Adenda 4; 59.330 → 65.828 B) | `bfd85f12…` |
| `REGISTRO-REVIEWBENCH.md` | modificado (completo; 77.649 → 80.761 B) | `3d1091a8…` |
| `DIAGNOSTICO-PRACTICA-ALMA-310-20261022.md` | nuevo (la causa, con recibos) | `19ce3531…` |
| `RESULTADO-ARREGLO-V232-20261022.md` | nuevo (arreglo en seco y verificaciones) | `3a0061b9…` |
| `RESULTADO-PRACTICA-ALMA-V231-20261022.md` | nuevo (cierre formal de la nº 310) | `21d03b2a…` |
| `MANIFIESTO-V231.md` | nuevo en el remoto (cierre v2.3.1 pendiente; 11.962 B) | `02024d64…` |

No viajan, como siempre: `fixtures_semaforo/` (Push Protection) ni
`runs/`. Este manifiesto y su asiento en el REGISTRO viajan en un
commit posterior al del sobre (el manifiesto no puede contener su
propio commit).

## Verificaciones asentadas

- **Suite completa en seco: 249/249 OK** (245 previas + 4 nuevas);
  batería semáforo **16/16** dentro de la suite, sin regresiones.
- **Puertas congeladas byte-idénticas** antes y después del arreglo
  (sha256 de archivo): 1.0.0 `4223cb05…`, 1.1.0 `fdd974f1…`, 1.2.0
  `c5c32bfc…`, 1.3.0 `d3b993d4…`, 1.4.0 `b16c5a79…`, 1.4.1
  `08d813e9…`; POLICY de la 1.4.1 recomputada: `73a403d8…`.
  `agent/main.py` sin cambios (`9ac76b6f…`).
- **Remoto verificado tras el push:** cabeza de main =
  `8ae47d402b8300d02ad427c0cc2fdd68cc6eb9ae`; los 10 archivos
  releídos del remoto coinciden byte a byte (sha256 y SHA de blob
  de Git, 10/10).
- **Pendiente (declarado):** el disparo del workflow
  `reviewbench-image` sobre `8ae47d4` (manual, por navegador) y, con
  su digest, la enmienda de cierre de este manifiesto. Hasta ese
  cierre, la config ALMA del portal NO se toca: sigue apuntando a
  la imagen v2.3.1.

## Enmienda de cierre — imagen construida y corrida nº 311 (2026-10-22)

- **Imagen construida:** el workflow `reviewbench-image` se disparó
  manualmente (`workflow_dispatch`, la compuerta humana de diseño) y
  su **corrida nº 8 cerró SUCCESS**:
  https://github.com/almaoficial/alma-reviewbench/actions/runs/39775599211
- **Digest verificado en dos fuentes** (idéntico en ambas):
  `ghcr.io/almaoficial/alma-reviewbench@sha256:fbf1fe48364f915fed703a0a618bea48e0e7b379f7afaa645b8b4bf712850498`
  — resumen de la corrida nº 8 de Actions y página del paquete GHCR
  (versión `1428141056`, tag `dev`).
- **Cabeza de main al disparo: `276051e`** — incluye el commit del
  sobre (`8ae47d4`) más los asientos documentales posteriores; la
  imagen se construyó desde esa cabeza, no desde `8ae47d4` pelado.
- **Corrida nº 311 con esta imagen:** el relanzamiento del brazo
  ALMA autorizado por la Adenda 4 corrió con esta imagen exacta
  (config ALMA del portal actualizada **solo** en el campo de
  imagen y releída campo por campo: «llm · alma · gpt-5.6-sol ·
  medium · v23 · v141»). Compuerta de saldo verificada en el acto:
  **US$25,58** previos (≥ US$25). Resultado: **SUCCEEDED**, titular
  augmented del portal P 0 % · R 0 % con 1 hallazgo, **costo real
  US$20,27** por diferencia de saldo (cierre formal:
  `RESULTADO-PRACTICA-ALMA-V232-20261022.md`; efecto de la puerta
  adjudicado en `ADJUDICACION-COMPLETA-311-20261022.md` — regla de
  avance variante (ii): **NO PASA**).
- **Estado de este manifiesto: CERRADO.** La publicación v2.3.2
  queda completa: código verificado (sobre), imagen verificada
  (esta enmienda) y corrida del último acto del papel v2.3 corrida
  y adjudicada. Este cierre es documental y local; su asiento en el
  REGISTRO acompaña esta enmienda.
