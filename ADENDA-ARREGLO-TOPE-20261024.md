# Adenda — Arreglo del tope de salida de las pasadas profundas (la muerte de la nº 344)

**Fecha:** 2026-10-24 (EDT). **Costo de esta tarea: US$0** — sin
llamadas a modelos, sin portal, sin cargas, sin publicación por
esta vía si la compuerta lo impide (ver §7). **Autorización:**
Alejandro, 24/10/2026 («Hacé el arreglo en seco (US$0)»),
sobre el diagnóstico de la corrida nº 344
(`RESULTADO-V24-20261024.md`, causa clasificada **(a) propia
del brazo**). **Relación con los papeles vigentes:** esta
adenda se anexa a `PREREGISTRO-VALIDACION-20261024.md` y lo
enmienda en UN punto — la configuración de salida de las
pasadas profundas de los brazos v2.4/v2.5/v2.6 — sin tocar su
vara (§2), su regla de adjudicación (§6), su economía (§7) ni
sus altos (§8): **la nº 344 no se relanza** y ninguna corrida
futura con este arreglo es la nº 344 corregida — es una
corrida nueva, con otro `RB_RUN_ID` (§6 de esta adenda).

## 1. La falla que esta adenda repara

Asentada en el diagnóstico: en la nº 344 el agente arrancó en
los 4 shards, produjo findings parseables con la puerta 1.5.0
activa en 18 de 20 PRs intentados, y murió por PR en la
llamada al modelo — la respuesta volvió bien formada pero
**vacía**: `finish_reason='length'`, `content_length=0`. El
razonamiento (gpt-5.6-sol, esfuerzo medium) agotó el tope de
salida antes de emitir el primer token de contenido; sin JSON,
el revisor cerró en falso por diseño y el portal reintentó
con el mismo presupuesto, con el mismo resultado (3 intentos
idénticos por PR; 4 de 20 PRs pegados, 2 sin recuperación). El
presupuesto en cuestión: las pasadas profundas llaman con
`max_completion_tokens = settings.max_output_tokens`, default
**4096** heredado de la base compartida
(`agent/llm_reviewer.py`: `RB_LLM_MAX_OUTPUT_TOKENS`). En la
nº 298 (v2.3.1, mismo modelo y esfuerzo) el parseo fue 25/25
limpio: lo que cambió es el productor v2.4, que razona más por
pasada — y su esquema de emisión (arreglos de evidencia con
líneas citadas verbatim) hace que el contenido legítimo de una
pasada también sea más largo.

## 2. El arreglo, declarado antes del código

Dos piezas, en la capa compartida que heredan los tres brazos
(`agent/llm_reviewer_v24.py` — el v2.5 y el v2.6 son subclases
que solo sobrescriben el contenido de los payloads y las
marcas de procedencia, nunca los presupuestos ni el bucle de
llamadas):

**(a) El presupuesto de salida de las pasadas profundas pasa a
ser una configuración propia de la familia v2.4, con default
16384.** Hoy las pasadas profundas (y la mixta degenerada)
leen `settings.max_output_tokens` — un default de la era v1
que ningún papel de la familia eligió para ellas. El arreglo
sigue el precedente exacto de la línea para este mismo modo
de muerte (fix v2.3.1: la nº 296 murió bajo un techo de
triaje de 1024 y el techo se subió al presupuesto hermano,
fijado como configuración resoluble propia): nace
`DEFAULT_DEEP_MAX_OUTPUT_TOKENS = 16384`, resuelto por
`_resolve_deep_max_output_tokens(env, config)` con la misma
precedencia y el mismo fail-closed que el resolver de triaje
— config `deep_max_output_tokens`
(`RB_CONFIG_DEEP_MAX_OUTPUT_TOKENS`) → entorno
`RB_LLM_V24_DEEP_MAX_OUTPUT_TOKENS` → default; valor no
entero o no positivo rehúsa en construcción.
`build_deep_payload` y `build_fallback_payload` usan ese
presupuesto; la pasada de selección **no se toca** (su techo
de triaje es otra línea de configuración, con su propio
arreglo histórico).

*Justificación del valor.* (i) **Del código:** 4096 nunca fue
una elección para las pasadas profundas de esta familia — es
el default compartido de la base v1, pensado para una única
pasada sobre el diff solo; la familia v2.4 corre pasadas
profundas con el contexto completo de los archivos y un
esquema de dos arreglos con evidencia verbatim. (ii) **De lo
medido:** en la nº 344, los PRs exitosos agregan hasta
**14.132 tokens de completion por PR** (≤6 llamadas); los dos
PRs muertos quemaron ≥4096 **solo en razonamiento**, con cero
contenido. Un presupuesto de 16384 pone a disposición de UNA
pasada más que el mayor total de completion observado en un
PR entero: 4× el techo que falló. (iii) **Del modelo:** la
familia GPT-5 admite `max_completion_tokens` hasta 128.000;
16384 (y los 32768 del reintento) quedan muy adentro de lo
que el modelo admite — la restricción que ata sigue siendo el
freno de gasto, no el modelo. (iv) **Del freno:** a los
precios de planificación de la línea (US$15/US$75 por Mtók),
el peor caso de salida por pasada profunda pasa de US$0,3072
a US$1,2288; la guardia de dos etapas precia el payload armado
tal como se construye, así que en los contextos más grandes
se admitirán menos pasadas y la degradación quedará
**declarada** en el run info — una degradación asentada es
sobrevivible; una muerte por `length` es total (el portal
marca la corrida FAILED). El chequeo acumulativo de costo
real que falla cerrado no cambia.

**(b) Un reintento interno ante la respuesta vacía por
`length`.** Si una pasada profunda o la mixta devuelve
`finish_reason='length'` con contenido vacío (cadena vacía o
solo espacios, o contenido ausente), el agente reintenta **una
sola vez dentro de la misma pasada**, con presupuesto de
salida = **2× el presupuesto de la pasada** (32768 con el
default), antes de cerrar en falso. El reintento está
custodiado por el freno: se dispara solo si el costo real
acumulado más el peor caso del payload reintentado sigue
≤ `RB_MAX_SPEND_USD`; si no, no hay reintento y el camino de
cierre en falso es exactamente el de hoy. El costo real del
reintento entra en el mismo chequeo acumulativo que falla
cerrado (`_account`, sin modificar). Cada evento queda
asentado en el run info (`length_retries`: pasada,
presupuestos, desenlace — `recovered` / `still_empty` /
`refused_spend_cap`), junto al nuevo campo
`deep_max_output_tokens` que declara el presupuesto en vigor,
espejo de `triage_max_output_tokens`. Si el reintento también
vuelve vacío por `length`, la pasada cierra en falso como
hoy: el parseo fallido se asienta con su `finish_reason` y su
extracto, y el PR muere — el arreglo no convierte ninguna
muerte en silencio. **Ningún otro error cambia de
comportamiento:** HTTP ≠ 200, JSON inválido con contenido,
`finish_reason` distinto de `length`, contenido no vacío —
todos siguen el camino actual, sin reintento.

## 3. Qué NO cambia

La puerta **1.5.0** y todas las puertas 1.0.0–1.5.0,
`claim_contract.py` y `birth_shaper.py`, byte-idénticos.
`RB_MAX_SPEND_USD` — ni su valor ni su custodia. La pasada de
selección y su techo de triaje. Los prompts (ni una palabra).
`agent/llm_reviewer.py` (la base v1) y los revisores
v2/v2.1/v2.2/v2.3 — byte-idénticos: el default 4096 de la base
sigue rigiendo a la v1; el presupuesto profundo nuevo es
configuración de la familia v2.4, no un cambio global. Los
`REVIEWER_VERSION` quedan (`2.4.0`/`2.5.0`/`2.6.0`): identidad
del revisor, no de sus bytes — la identidad exacta del código
la fijan los hashes asentados en el cierre de esta adenda y el
digest de la imagen nueva, como en toda la línea (precedente:
§3 del pre-registro de la corrida). **Re-fijado declarado**
(mismo precedente): las tablas de congelados de
`tests/test_llm_reviewer_v25.py` y `tests/test_llm_reviewer_v26.py`
fijan el sha256 de `llm_reviewer_v24.py` (`f9d3578e…`), y la
del v2.6 fija además el de `llm_reviewer_v25.py` (`7546d7d9…`,
que cambia solo en el pase de los dos campos nuevos del run
info a través de su reconstrucción); esta adenda re-fija esos
valores a los hashes nuevos y ningún otro valor de esas
tablas se toca.

## 4. Lo que el arreglo NO afirma

El arreglo repara el **mecanismo** de la muerte (techo
agotado + reintentos con el mismo presupuesto), verificado en
seco contra el modo reproducido por transporte guionado. No
afirma que el v2.4 vaya a pasar la vara, ni que ninguna pasada
real deje de morir por `length` en algún diff futuro: afirma
que el techo sube 4×, que existe un segundo intento con el
doble de presupuesto dentro del mismo freno, y que ambos
hechos quedan asentados por corrida en el run info. La
medición sigue siendo la corrida paga — que esta adenda no
autoriza.

## 5. Verificación en seco (declarada antes, US$0)

1. **Test de regresión del modo** en
   `tests/test_llm_reviewer_v24.py`, por transporte guionado:
   la pasada profunda responde vacío con `finish_reason =
   'length'` → el reintento sale con 32768 → responde findings
   parseables → los candidatos se producen y el run info
   asienta el evento (`recovered`); segundo escenario: el
   reintento también vuelve vacío por `length` → cierre en
   falso con el parseo asentado, como hoy; tercer escenario:
   freno sin resto → no hay segunda llamada y el cierre es el
   de hoy (`refused_spend_cap` asentado). Más: el payload
   profundo por defecto lleva 16384 y el resolver
   (config/entorno/inválido) se comporta como el de triaje.
2. **Suite completa** corriendo entera, en verde, con el
   conteo asentado en el cierre.
3. **Semáforo congelado:** la batería `fixtures_semaforo/`
   íntegra contra su `MANIFIESTO-BATERIA.json` (32 archivos,
   bytes y sha256) y la batería en seco 16/16 por cada
   portador (v2.4, v2.5, v2.6) dentro de la suite.
4. **Congelados:** foto sha256 antes/después del resto de la
   línea — puertas, contrato, formador, revisores previos,
   compiladores, contextos — byte-idénticos; los únicos
   archivos de código que difieren son los declarados en la
   §2–§3.

## 6. Corridas futuras bajo esta enmienda

Toda corrida que use el arreglo lleva un **`RB_RUN_ID`
nuevo** (nunca `validacion-20261024-v24`) y corre sobre la
imagen nueva de la §7, con la enmienda citada en su papel. La
config de portal no cambia: el presupuesto profundo nuevo
rige por default dentro del revisor; si un papel de corrida
quisiera otro valor, lo fija por
`RB_CONFIG_DEEP_MAX_OUTPUT_TOKENS` y lo declara antes. La
economía de cualquier corrida nueva se presenta en un solo
número antes de cargar, como manda la regla de la línea.

## 7. La imagen nueva

Una sola imagen, por el pipeline asentado (sincronización del
paquete a `main` de `almaoficial/alma-reviewbench` →
`workflow_dispatch` de `reviewbench-image` → digest verificado
en **dos fuentes**: el resumen de la corrida de Actions y la
página del paquete en GHCR), llevando el arreglo en la capa
compartida — los tres brazos lo heredan de la misma imagen y
difieren solo en config, como siempre. El digest se asienta
en el asiento de cierre de esta adenda y en el REGISTRO, y es
el `RB_IMAGE_SHA256` de cualquier corrida futura bajo esta
enmienda. Si la publicación no puede ejecutarse desde el
entorno de esta tarea (la compuerta del pipeline es la sesión
de Alejandro / el mecanismo de sincronización del agente
principal), el arreglo queda validado en el repo local, el
bloqueo se reporta con su causa exacta y **no se improvisa
otra vía**.

## 8. Asiento de cierre (ejecutado el 2026-10-24)

- **El código:** `agent/llm_reviewer_v24.py`
  `f9d3578e…` → **`3e01b4743bfcdfb6e0dc74e082097eb43cdd8f06e1532ec30d5bc49f8f0240d1`**
  (presupuesto profundo propio + resolver + reintento +
  campos del run info); `agent/llm_reviewer_v25.py`
  `7546d7d9…` → **`75460ac3b877a201a941696590ed49e2024e06844ea3642bb57a3d3bd8e5ab9a`**
  y `agent/llm_reviewer_v26.py` `16cca0a4…` →
  **`0081b9853b8b430d1fa57452fbd6d2d306e5b39a527b3a0838dc9c42ff0183ec`**
  (solo el pase de `deep_max_output_tokens` y `length_retries`
  en sus reconstrucciones del run info). Re-fijados ejecutados
  según la §3: el hash del v2.4 en las tablas de
  `tests/test_llm_reviewer_v25.py` y `tests/test_llm_reviewer_v26.py`,
  y el del v2.5 en la del v2.6; ningún otro valor tocado.
- **La suite: 394/394 OK** (388 de apertura + 6 nuevas del
  test de regresión del modo, en
  `tests/test_llm_reviewer_v24.py`: presupuesto
  default/resolución/inválido; vacío por `length` → reintento
  a 32768 → findings producidos, con el evento asentado;
  doble vacío → cierre en falso de siempre con el parseo
  asentado; freno sin resto → sin segunda llamada,
  `refused_spend_cap`; error HTTP y contenido no vacío no
  reintentan). **Semáforo congelado VERDE en su forma seca:**
  la batería `fixtures_semaforo/` íntegra contra su
  manifiesto (32/32 archivos, bytes y sha256, sin extras ni
  faltantes) y la batería en seco 16/16 por cada portador
  (v2.4, v2.5, v2.6) dentro de la suite. **Herencia
  verificada extremo a extremo:** con el modo reproducido por
  transporte guionado, el v2.5 y el v2.6 se recuperan por el
  mismo reintento, emiten con sus marcas de procedencia y su
  run info asienta el presupuesto (16384) y el evento
  (`recovered`).
- **Congelados byte-idénticos** (foto sha256 antes = después):
  puertas 1.0.0–1.5.0 (`4223cb05…`, `fdd974f1…`, `c5c32bfc…`,
  `d3b993d4…`, `b16c5a79…`, `08d813e9…`, `71b1996b…`),
  `claim_contract.py` (`7df8abc7…`), `birth_shaper.py`
  (`2b127b23…`), `llm_reviewer.py` (`2fead048…`), revisores
  v2/v2.1/v2.2/v2.3 (`ff7204ed…`, `bedd9a8a…`, `6874f22c…`,
  `a78bdd6d…`), compiladores (`482fce85…`, `567c67d9…`,
  `ce465502…`), `net_score.py` (`2444bd01…`),
  `run_ledger.py` (`5094e8ff…`), `main.py` (`228e5de5…`),
  contextos (`92895d85…`, `530ad952…`) y `Dockerfile`
  (`048175dd…`).
- **La imagen — BLOQUEO asentado al cierre:** la publicación
  no se completó desde el entorno de esta tarea, en dos
  escalones verificados. (1) **Sincronización:** se intentó
  por el flujo asentado (conector de GitHub, `push_files`,
  delta de 10 rutas computado contra la cabeza remota
  verificada `49d56fd9…` y las bases por ruta del registro de
  snapshots); la escritura quedó colgada ~30 minutos —
  la aprobación de escritura del conector no se completa en
  este contexto — y el proceso fue terminado sin resultado
  confirmado. Releído el remoto después del intento: **la
  cabeza sigue en `49d56fd9…` — nada se escribió**, y el
  registro de snapshots no avanzó. No se reintentó: el delta
  queda listo para el mecanismo del agente principal o la
  sesión de Alejandro, que es la compuerta asentada del
  pipeline (la misma que la preparación del 23/10 asentó y el
  paso siguiente ejecutó). (2) **Disparo:** aun con el sync
  hecho, el servidor MCP de GitHub conectado no ofrece
  herramientas de Actions (catálogo verificado: sin disparo
  de `workflow_dispatch` ni lectura de corridas); el disparo
  corre por el navegador con la sesión de Alejandro, como en
  la publicación de la corrida nº 9. **Digest: pendiente de
  esa publicación.** Cuando se publique, el digest verificado
  en dos fuentes se asienta en el REGISTRO y pasa a ser el
  `RB_IMAGE_SHA256` de cualquier corrida futura bajo esta
  enmienda; hasta entonces, ninguna corrida puede usar el
  arreglo. El arreglo queda **validado en el repo local**;
  el bloqueo es del pipeline de publicación, no del código.

— Adenda al pre-registro de validación del 24/10/2026,
escrita el 2026-10-24 ANTES del código del arreglo, sobre el
diagnóstico asentado de la nº 344.
