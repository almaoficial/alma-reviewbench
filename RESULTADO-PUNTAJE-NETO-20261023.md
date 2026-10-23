# Resultado — la línea completa bajo el puntaje neto (regla Breken)

**Fecha:** 2026-10-23 (EDT). **Papel:** `ADENDA-PUNTAJE-NETO.md`
(la definición operativa y la regla de lectura se declararon
ANTES de computar). **Costo: US$0** — cómputo local por programa
desde las fuentes primarias; sin llamadas a modelos, sin
portal, sin publicación, sin push.

## 0. La tabla

| Brazo | Emisiones | +TP | −FPG | 0 GREY | 0 NOVEL | Neto crudo | Neto/100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base nº 298 (sin puerta, corrida real) | 166 | 89 | 8 | 17 | 52 | **+81** | **+48,8** |
| Replay autopsia 1.4.1 (sobre el corpus A) | 0 | 0 | 0 | 0 | 0 | **0** | n/d |
| Replay puerta 1.5.0 sola | 32 | 19 | 2 | 2 | 9 | **+17** | **+53,1** |
| Replay pipeline del contrato (+1.5.0) | 49 | 26 | 2 | 3 | 18 | **+24** | **+49,0** |
| Replay pipeline del formador al nacer (+1.5.0) | 79 | 44 | 4 | 8 | 23 | **+40** | **+50,6** |
| ALMA nº 311 (puerta 1.4.1, corrida real) | 1 | 0 | 0 | 1 | 0 | **0** | **0,0** |

**Sanidad (condición de validez):** cada cruce computado cerró
**exacto** contra el papel publicado de su medición antes de
asentar su neto — base 89/8/17/52
(`ADJUDICACION-COMPLETA-298`), 1.5.0 sola 19/2/2/9 de 32
(`RESULTADO-REPLAY-150` §3), contrato 26/2/3/18 de 49
(`RESULTADO-CONTRATO-RECLAMOS` §3), y del formador los totales
publicados (79 emitidos, 44 TP, 4 FPG; `RESULTADO-REVISOR-
CONTRATO` §§3–4). El desglose GREY/NOVEL del formador (8/23) no
estaba publicado: es salida derivada de este cómputo, con su
suma (31) fijada por los totales asentados. El brazo 311 entra
como registro citado de su adjudicación (§3), no como cómputo.

## 1. La precisión que esta tabla obliga a hacer sobre la 311

La única emisión de la nº 311 **no es una falsa alarma
probada**: su adjudicación (§2) la clasifica **zona gris** —
0 emisiones sobre FP gold / 1 gris / 0 novedosas — y declina
explícitamente el FPG con el estándar de la casa (el reclamo no
es el mismo que el FP juzgado en ese territorio; el gold ni
confirma ni refuta). Bajo la definición pre-registrada, GREY
cuenta **0**: el neto de la 311 es **0, no −1**. Cualquier cita
del brazo como «−1 en puntaje neto» estaría reclasificando la
emisión contra su adjudicación asentada.

El veredicto no cambia por eso: con la regla de lectura §3.3
(neto crudo ≤ 0 no puede declararse mejora aunque gane en
precisión), la 311 queda bloqueada como mejora por la métrica
nueva igual que lo estaba por la vara principal (P 0 % / R 0 %,
NO PASA). La métrica llega al mismo lugar por otro camino — y
de paso deja de ser un adjetivo: «la puerta suprimió» ahora es
un 0 con desglose (1 emisión, 0 probadas, 0 falsas probadas, 1
gris).

## 2. Qué dice la tabla (y qué no)

- **Ningún brazo con puerta supera a la base en neto crudo.**
  La base suma +81 emitiendo todo, aciertos y ruido juntos; el
  mejor pipeline (formador) suma +40 — la mitad — porque 87 de
  las 166 emisiones nunca salen, y entre ellas van 45 TP. En
  unidades Breken: filtrar, en toda la línea medida, *destruyó*
  más aciertos probados de los que ahorró en falsas alarmas
  probadas (la base solo tenía 8 FPG que ahorrar).
- **El neto por 100 ordena igual que la precisión** (1.5.0
  +53,1 > formador +50,6 > contrato +49,0 > base +48,8): es la
  misma pureza por emisión que P ya decía, con otra unidad. Lo
  que la métrica suma no es un ranking nuevo: es la **escala
  absoluta** (el crudo) y el **cero exigible** (la regla §3.3).
- **El silencio puntúa 0 en las dos expresiones** — crudo 0
  para la autopsia de la 1.4.1 (0 emisiones, normalizado n/d) y
  0,0 para la 311. Ninguna vara anterior le ponía número a no
  emitir; esta sí, y es el mismo número que obtiene un brazo
  que emite solo reclamos grises.
- **Lo que la métrica NO hace** (adenda §6): no re-juzga a
  nadie — la 1.5.0 y el formador siguen no adoptados por su
  vara (la sala de espera), la 311 sigue NO PASA — y no mide
  cobertura: el +53,1 de la 1.5.0 sola convive con un recall de
  TP distintos de 3,12 %. Neto y recall se leen juntos o no se
  lee ninguno.

## 3. El módulo y lo que queda

`agent/net_score.py` (`alma-net-score/1.0`) deja el cálculo
importable: `compute_arms()` re-deriva los brazos desde
`decisions.json` con la fórmula de replay de la línea y
**rehúsa asentar** cualquier neto cuyo cruce no cierre contra
lo publicado (`SANITY`); `counts_from_verdicts()` sirve para
la adjudicación futura. Cuando la validación paga estacionada
corra y se adjudique, su papel reportará el neto de cada brazo
(base / v2.4 / v2.5) con esta misma definición, al lado de
precisión y recall, por la obligación de reporte de la adenda
§4. Hasta ese día, los brazos v2.4 y v2.5 **no tienen neto**:
no tienen emisiones adjudicadas, y esta métrica — como todas
las de la línea — no computa sobre intenciones.

## 4. Verificación de cierre

- Suite completa: **351/351 OK** (337 previas + 14 nuevas de
  `tests/test_net_score.py`: mezcla sintética contra conteos a
  mano, GREY/NOVEL = 0 y no −1, cero emisiones → normalizado
  n/d, neto negativo, veredicto desconocido rehúsa, cruce que
  no cierra rehúsa, la constante 311 es GREY y no FPG, y el
  cierre de cada brazo real contra su papel).
- El CLI del módulo (`python3 -m agent.net_score`) reproduce
  la tabla de la §0 y su `--json` deja el desglose auditable
  por brazo.
- Congelados byte-idénticos (sha256 antes = después): puertas
  1.0.0–1.5.0, `claim_contract.py`, `birth_shaper.py`,
  revisores v2.3/v2.4/v2.5, compiladores de lecciones, de
  ausencias y del censo, `decisions.json` y los dos
  pre-registros citados (productor y memoria) — esta adenda
  los cita, no los modifica.
- Commit local con exactamente los cinco archivos de la tarea
  (adenda, resultado, módulo, tests y el asiento del REGISTRO);
  **sin push**.

— Resultado del puntaje neto, 2026-10-23. Gasto: **US$0**.
