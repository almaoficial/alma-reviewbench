# Pre-registro — ReviewBench v2: un revisor que habla el idioma de la puerta

**Fecha:** 2026-10-19 · **Autor del «corre»:** Alejandro (19:56 EDT, sobre el diseño aprobado a las 18:01)
**Estado:** CONGELADO al escribirse. Toda corrección posterior es una adenda fechada, nunca una edición silenciosa.
**Antecede:** `PREREGISTRO-REVIEWBENCH.md` (v1) y su veredicto en `REGISTRO-REVIEWBENCH.md`.

## 1. El antecedente medido (v1, cerrado el 2026-10-19)

- Brazo base (#251, primera base válida): **Grounded F1 1,4% · Precision 42,9% · Recall 0,7%**; 14 findings en 25 PRs.
- Brazo ALMA (#253): el agente completó 25/25 PRs; la plataforma falló en su propio paso de puntaje («score / Summarise»), sin nota oficial. Desde las salidas: **1 finding emitido en 25 PRs**.
- Causa estructural, medida en los `agent.log`: el modelo devuelve pocos hallazgos crudos (la mayoría de los PRs en 0) y la puerta congelada `alma-evidence-gate/1.0.0` solo verifica **8 clases** de reclamo (sql_injection, hardcoded_secret, tls_verification_disabled, silenced_bare_except, mutable_default, command_execution, unsafe_deserialization, race_condition), cada una con su evidencia específica. Todo hallazgo del LLM fuera de esas clases se rechaza fail-closed. El único emitido fue un race_condition: una de las 8.
- Veredicto v1: la regla de avance **no se cumplió**; la compuerta D (final 219×3) no se abrió. La puerta hizo lo que su política dice; el revisor y la puerta no hablan el mismo idioma, y el revisor además mira solo el diff (recall 0,7%).

## 2. Hipótesis de la v2 (falsable)

1. **Idioma:** si el revisor produce candidatos *por clase verificable*, citando la evidencia exacta de cada clase, el brazo ALMA deja de perder casi todo en la puerta y su efecto de precisión se vuelve medible por primera vez.
2. **Linterna:** si el revisor ve el archivo cambiado completo (no solo el parche), el recall del brazo base sube materialmente sobre el 0,7% de la v1.

Si ninguna de las dos se cumple en la práctica de la v2, la v2 se registra como nulo y se detiene: no hay v2.1 de ajuste fino sobre la misma práctica.

## 3. Diseño (qué cambia y qué NO cambia)

**No cambia:** la puerta. `alma_gate.py` y su `POLICY_SHA256` quedan intactos — el validador congelado no se toca. Tampoco cambian el modelo (gpt-5.6-sol), el effort (medium), la plataforma ni la estructura A/B: mismo revisor en ambos brazos, único campo distinto = `governance`.

**Cambia el revisor** (`llm_reviewer` v2):
- **Contexto completo:** además del diff, lee en `/work/repo` el contenido completo (versión head) de cada archivo tocado por el PR, con tope de tokens por PR declarado en la corrida.
- **Pasadas por clase:** una pasada por cada una de las 8 clases verificables, con instrucción de citar líneas exactas del archivo como evidencia. Una pasada general adicional queda permitida solo en el brazo base; en el brazo ALMA, todo candidato nace dentro de una clase verificable o no nace.
- **Anclaje verificado:** antes de emitir, cada candidato comprueba que las líneas citadas existen en el archivo head y que el texto citado coincide; el que no ancla, se descarta en el propio revisor (no espera a la puerta).
- **Exploración del repo** (grep de llamadores, tests vecinos): EXCLUIDA de la v2. La falla medida fue idioma + contexto, no exploración; sumarla ahora mezclaría dos cambios en un experimento.

## 4. Medición y regla (congeladas)

- Práctica: el mismo set privado de 25 PRs del portal, **1 corrida por brazo**; la primera corrida que complete en cada brazo es la válida; todas las duplicadas se declaran.
- Métrica primaria: grounded F1 · co-primaria: grounded precision (idénticas a v1).
- **Regla de avance a la final:** F1 ALMA ≥ F1 base-v2, precisión ALMA ≥ precisión base-v2 + 0,05, recall ALMA no cae más de 0,03.
- **Prueba de la linterna (independiente de la regla):** si el recall del brazo base-v2 no supera el 0,7% de la v1, la hipótesis 2 queda falsada aunque el A/B «gane» por precisión.

## 5. Presupuesto (estimaciones desde la muestra medida de la v1)

- Costo observado v1: ≈ US$0,14 por PR (US$5,49 ÷ 39 revisiones, entre #251 y #252; los estimadores internos por PR oscilaron US$0,01–0,81 según tamaño del diff).
- La v2 suma contexto completo y 9 pasadas por PR: se estima 2–3× por PR → práctica completa (2 brazos × 25 PRs) ≈ **US$15–25**. **Tope duro pre-registrado: US$30** para toda la práctica v2, con el freno por PR de US$5,00 sin cambios. Si el tope no alcanza, la práctica se detiene y se registra así; no se amplía en caliente.
- Construcción y pruebas: US$0 (mock primero, fixtures sintéticos, la Lenovo no es requisito).

## 6. Anti-pesca (declaración de lo que se vio y lo que no)

- El set dorado de ReviewBench es privado: **nunca vimos las respuestas correctas**. Lo que se leyó de la v1 son NUESTRAS salidas (conteos de hallazgos por PR y los logs del agente), y este diseño responde solo a hechos estructurales agregados (clases rechazadas, prevalencia de 0 hallazgos, costo por PR), no al contenido de ningún PR puntual.
- Prohibido ajustar prompts contra el detalle por PR de la práctica; prohibido repetir una corrida «hasta que salga»; prohibido tocar la puerta para que el A/B dé mejor.

## 7. Secuencia

1. Construir el revisor v2 con mock (US$0) + tests sobre fixtures, incluida una fixture por clase verificable.
2. Publicar imagen nueva (mismo repo, workflow existente) y manifiesto v2 (mismo formato que v1).
3. Práctica A/B de la v2 (requiere crédito suficiente y el «sí» de Alejandro al momento de lanzar, como en v1).
4. Asentar resultados verbatim en manifiesto y registro; aplicar la regla congelada; la final se decide con Alejandro a la vista del veredicto.

## 8. Falsadores (qué nos haría detenernos)

- El brazo base-v2 no supera el recall de la v1 → la linterna no era (solo) contexto: registrar y detener.
- El brazo ALMA-v2 sigue emitiendo ≈ 0–1 findings con el revisor por clases → el desajuste no era el idioma del revisor: registrar y detener.
- Costo por PR > 3× lo estimado sin mejora de recall → la práctica se detiene por tope y se registra.

## Adenda 1 (2026-10-19, 22:05 EDT — ANTES de cualquier corrida de la v2)

**Decisión de Alejandro:** «mejora la estructura, entonces, para mejorar todo el proyecto» — sobre el diagnóstico de la §1 (el techo de las 8 clases deja al brazo ALMA sin recall posible aunque el revisor hable el idioma).

**Qué cambia respecto del cuerpo de este pre-registro:** la §3 decía «la puerta no cambia». Se enmienda así: la puerta **1.0.0 queda intacta y congelada para siempre** (la v1 sigue reproducible byte a byte), y la v2 usa una puerta nueva, **`alma-evidence-gate/1.1.0`**, que hereda las 8 clases de la 1.0.0 con sus mismas reglas y suma clases nuevas. Cada clase nueva entra solo si su evidencia es **mecánicamente verificable** sobre las líneas citadas — la doctrina de la puerta no se negocia: ninguna clase que exija opinar.

**Clases nuevas de la 1.1.0** (regla de evidencia entre paréntesis):
- `resource_leak` — recurso abierto (`open(`, conexión, socket) en las líneas citadas, sin `with` y sin cierre (`.close(`) dentro del rango citado.
- `swallowed_exception` — manejador `except` tipado cuyo cuerpo es solo `pass` (la 1.0.0 cubría el `except:` pelado; esta cubre el tipado que traga en silencio).
- `unsafe_xml_parsing` — parseo XML con la librería estándar (`ET.parse`/`fromstring`, `xml.dom`, `xml.sax`) sin defusedxml en la evidencia.
- `insecure_tempfile` — `tempfile.mktemp(` (inseguro por diseño, documentado).
- `ssl_context_unverified` — `ssl._create_unverified_context` o `CERT_NONE` en la evidencia (hermana de tls_verification_disabled, evidencia distinta).
- `weak_random_security` — valor asignado a un nombre de seguridad (token, secret, password, otp, session, api_key) generado con el módulo `random` en vez de `secrets`.

**Condiciones de la extensión:** cada clase nueva nace con su fixture y sus casos adversarios (hallazgos que PARECEN de la clase y la puerta debe rechazar: ej. `open(` dentro de un `with`, `random` para un nombre no sensible, XML con defusedxml presente). La `POLICY_SHA256` de la 1.1.0 se asienta en este papel al construirse (adenda de construcción, sin cambiar reglas). El manifiesto v2 declara qué puerta usa cada brazo… — corrección: la puerta solo existe en el brazo ALMA; el base la saltea igual que en v1.

**Qué NO promete esta adenda:** el techo sube, no desaparece. Los hallazgos dorados de ReviewBench incluyen clases no mecanizables (lógica, diseño, rendimiento) que ninguna puerta determinista podrá verificar jamás; eso queda declarado como límite permanente del enfoque, no como deuda.

**Asiento de construcción (2026-10-19, 22:12 EDT):** puerta 1.1.0 construida en `agent/alma_gate_v11.py`, sin tocar `agent/alma_gate.py`. **POLICY_SHA256 de la 1.1.0 = `6a7a7aa462296cbee79f0835262ea24152fdae030dee8b6383ef6c0bd0beccc9`.** La 1.0.0 verificada intacta: `3ad514ede02e6eefc9b2ed0dceed144bdc6aafe21cab57aa6746c44190689f35`. Suite completa: **69/69** (36 previos + 33 nuevos: aceptación y adversarios por clase nueva, equivalencia de las 8 heredadas entre ambas puertas, e2e por clase). Ambigüedades de la adenda resueltas al implementar y documentadas en el módulo: resource_leak con marcadores mecánicos (open/connect/socket/create_connection, exclusión si una línea citada abre un with); weak_random_security exige asignación y llamada `random.` en la MISMA línea citada; swallowed_exception exige citar el cuerpo (el `pass` debe estar en la evidencia); unsafe_xml_parsing se derrota si `defusedxml` aparece en cualquier línea citada. Selección de puerta por configuración: `RB_CONFIG_GATE=v1|v11` (default v1; la práctica v2 usará v11 y así lo declarará el manifiesto v2).

## Adenda 2 (2026-10-20, 00:22 EDT — ANTES de cualquier corrida de la v2)

**Decisión de Alejandro:** «Hacelo ahora» — sobre la recomendación asentada a las 00:09 de no lanzar la v2 con la puerta perforada.

**Motivo (medido, no opinado):** el equipo rojo de la ola de estudio estructural (informe en `~/workspace/alma-prototype/estudio-estructura-20261020/equipo-rojo.md`) corrió 46 ataques bien formados contra la 1.1.0 y 27 contra la 1.0.0: **pasaron el 95,7% y el 96,3%** respectivamente. Los dos únicos rechazados cayeron por formato, no por la regla. Diagnóstico: las clases verifican la PRESENCIA de marcadores en el texto citado, sin distinguir código de comentario/docstring, sin exigir que la cita contenga líneas agregadas por el cambio, y dos clases (hardcoded_secret, race_condition) tienen reglas casi vacías. La puerta caza vaguedad, no mentira bien formada.

**Qué cambia:** nace `alma-evidence-gate/1.2.0` con los arreglos mínimos del informe del equipo rojo, todos mecánicos: (a) tokenización previa — comentarios y docstrings se descartan de la evidencia antes del chequeo (los strings ASIGNADOS quedan, ahí viven SQL y secretos legítimos); (b) hardcoded_secret aplica filtro de nombre sensible; (c) race_condition exige asignación a estado compartido (`self.x =`); (d) las marcas de una clase deben co-ocurrir en líneas relacionadas (no bolsa de líneas sueltas); (e) el antídoto (la forma segura: SafeLoader, .close(), raise, with) se busca en el bloque completo del archivo, no solo en el rango citado; (f) la evidencia debe contener al menos una línea agregada por el cambio.

**Condiciones:** las puertas 1.0.0 y 1.1.0 NO se tocan (v1 y la medición intermedia quedan reproducibles). La batería de ataques del equipo rojo pasa a ser suite de regresión: la 1.2.0 debe RECHAZAR todos los ataques bien formados y seguir ACEPTANDO todos los fixtures legítimos existentes (la suite completa previa debe seguir verde). La POLICY_SHA256 de la 1.2.0 se asienta al construirse (adenda de construcción). La práctica v2 usará la 1.2.0 y el manifiesto v2 lo declara. **Límites declarados sin arreglo mecánico** (del informe, no se tapan): proveniencia del input en unsafe_xml_parsing y código muerto — fronteras honestas del enfoque de patrones sobre líneas citadas.

**Asiento de construcción (2026-10-20, 00:31 EDT):** puerta 1.2.0 construida en `agent/alma_gate_v12.py`, sin tocar las anteriores (hashes 1.0.0 y 1.1.0 reverificados idénticos). **POLICY_SHA256 de la 1.2.0 = `a768afa46136ba1bf542da65006a946d11cb39e8db73fbd484c3f021b7994211`.** Suite completa: **104/104** (69 previas + 35 nuevas, batería roja incluida como regresión). **Tasa de paso de la batería del equipo rojo: 2/46 = 4,3%** (desde 95,7%). Los 2 ataques sobrevivientes son exactamente los residuales declarados en esta adenda (C3: código muerto bajo `if False:`; X2: proveniencia del input en `ET.parse(CONSTANTE)`) y quedaron fijados en la suite como «aceptados con límite declarado». Equivalencia legítima: fixtures v1, fixtures_v2 y fixtures_v11 producen resultados idénticos bajo la 1.2.0 que bajo sus puertas originales. Tensiones documentadas en el módulo: la cita de race_condition debe reunir en una línea la marca de concurrencia y la asignación a estado compartido; el antídoto a grano de bloque puede derrotar un resource_leak genuino si otro recurso del mismo bloque se cierra; SQL multilínea exige citar esqueleto y construcción en la misma línea. Selección: `RB_CONFIG_GATE=v12`; la práctica v2 corre con la 1.2.0.

## Adenda 3 (2026-10-20, 00:37 EDT — ANTES de cualquier corrida de la v2)

**Decisión de Alejandro:** «Lo hagamos» — sobre las palancas propuestas para subir la probabilidad de la regla de avance (estimación asentada: de ~45–50% a ~55–60% con las palancas 1 y 2; la palanca 3, paga, queda como decisión separada de gasto según su regla de aprobaciones de a una).

**Palanca 1 — disciplina de cita del revisor (sin tocar la puerta):** el revisor v2 suma guidance de citación alineada con los chequeos de la 1.2.0: citar en el mismo conjunto la marca y la construcción (SQL: esqueleto y construcción inseguros juntos; race_condition: concurrencia y asignación a estado compartido juntas), y verificar la ausencia del antídoto en el bloque antes de proponer (resource_leak, swallowed_exception, unsafe_deserialization). Fixtures nuevas que prueban que patrones VERDADEROS antes rechazados por forma de cita ahora se aceptan, y que los falsos siguen rechazados.

**Palanca 2 — puerta `alma-evidence-gate/1.3.0`:** hereda las 14 clases y los chequeos endurecidos de la 1.2.0 (sin modificarla) y suma las 5 clases mejor rankeadas del informe del cazador (`~/workspace/alma-prototype/estudio-estructura-20261020/cazador-clases.md`), cada una con su regla mecánica tal como el informe la escribe: `weak_hash`, `tarfile_unsafe_extract`, `hardcoded_password_argument`, `jwt_verification_disabled`, `debug_mode_enabled`. Las 9 candidatas restantes del informe quedan documentadas como candidatas futuras, no entran en esta versión. Condiciones: cada clase nueva con fixture de aceptación y adversarios de rechazo; el equipo rojo extiende su batería a las clases nuevas y la 1.3.0 debe mantener la tasa de paso ≤ 4,3% sobre la batería total; la suite completa previa sigue verde; las puertas 1.0.0/1.1.0/1.2.0 no se tocan. POLICY_SHA256 de la 1.3.0 a asentar al construirse. La práctica v2 corre con la 1.3.0 y el revisor de la palanca 1; el manifiesto v2 lo declara todo.

**Lo que esta adenda NO hace:** no cambia la regla de avance, no cambia el brazo base (su única diferencia con ALMA sigue siendo la gobernanza), no usa ningún dato del set dorado (privado, nunca visto) y no ajusta nada contra resultados de corrida alguna de la v2 (ninguna corrió todavía).

**Palanca 3 — simulacro semáforo (aprobada por Alejandro el 2026-10-20 00:37 EDT, como decisión de gasto separada):** antes de la corrida puntuada v2, un simulacro con modelos REALES sobre una batería sintética fija de 8 códigos con defectos plantados de las clases verificables (la batería se congela antes de correr y se publica con el manifiesto v2). Ambas configuraciones (base-v2 y alma-v2 con puerta 1.3.0), una sola pasada, **tope duro US$20**, freno por PR de US$5 sin cambios. Criterio semáforo, fijado ahora: si algún brazo emite CERO hallazgos sobre códigos con defectos plantados a la vista, NO se lanza la corrida puntuada — se frena, se diagnostica y el diagnóstico se asienta antes de cualquier nuevo intento. Si ambos brazos emiten, se procede sin ajustar NADA del sistema a partir de este simulacro (su función es detectar catástrofes de emparejamiento, no afinar: ajustar contra él convertiría el simulacro en pesca). Corre mañana 20/10 después de Micro1, tras el chequeo de saldo.

**Asiento de construcción de la Adenda 3 (2026-10-20, 00:46 EDT):** puerta 1.3.0 construida en `agent/alma_gate_v13.py` (19 clases: 14 endurecidas heredadas por delegación a la 1.2.0 + 5 del cazador). **POLICY_SHA256 de la 1.3.0 = `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`.** Hashes de 1.0.0/1.1.0/1.2.0 reverificados idénticos tras la construcción. Suite completa: **137/137**. Batería roja extendida (69 ataques: 46 heredados + 23 nuevos): **tasa de paso 2,9%** — únicos aceptados: los residuales declarados C3 y X2. Palanca 1 verificada: la cita de race en dos líneas (def + asignación) y el SQL multilínea citado completo son ACEPTADOS por 1.2.0/1.3.0; los falsos con antídoto fuera de la cita siguen rechazados; la guidance de citación solo se activa bajo gate=v13 (con puertas viejas, prompts byte a byte los anteriores). Tensiones declaradas en el módulo: guardas de weak_hash/tarfile evaluadas en el span de la llamada sobre todo el bloque (disciplina de la Adenda 2(e)); tarfile no distingue un ZipFile en variable de nombre neutro (límite mecánico declarado); JWT con opciones por variable falla cerrado. **Nota operativa para el simulacro semáforo:** la estimación worst-case del revisor con 19 pasadas es ≈US$5,97 por PR, por encima del freno RB_MAX_SPEND_USD=5,00 cargado en el portal — el simulacro medirá el costo real por PR; si el freno corta algún PR, el ajuste del freno en la bóveda es acción de Alejandro y se declara en el manifiesto v2 antes de la práctica.

## Adenda 4 (2026-10-21, 13:24 EDT — firmada ANTES de correr el semáforo)

**Decisión de Alejandro:** «Firmo la adenda: freno por PR de US$5,00 a US$6,50» (su toque en la opción presentada en el chat, 21/10 13:24 EDT), precedida de su «Corre» (autorización de la corrida) y de su «Larga todo lo pendiente».

**Qué cambia:** el freno por PR (`RB_MAX_SPEND_USD`) sube de US$5,00 a **US$6,50** para el semáforo y la práctica v2. Motivo medido, no opinado: el worst-case del revisor con 19 pasadas es ≈US$5,97 por PR (asiento de construcción de la Adenda 3) — con el freno en US$5,00 un PR podía cortarse a mitad de camino y perder hallazgos por corte, no por mérito.

**Lo que NO cambia:** el tope duro del semáforo sigue en **US$20 totales**; la regla de avance queda intacta; las puertas siguen congeladas (la 1.3.0 corre con POLICY_SHA256 `0a711435adb3bc449da5d2b410f6511b7b70de7be5e55604ffca2e1946eddf78`). El techo por PR sube; no desaparece.

**Saldo verificado antes de correr:** US$1,85 en la cuenta correcta (Billing de OpenAI, cuenta «Continue with Apple», verificado en pantalla el 21/10 13:23 EDT; clave activa «Reviewbench») + carga de US$20 confirmada por Alejandro («Tenemos 21 dólares de tokens») → saldo ≈US$21,85, por encima del tope duro del semáforo.

## Adenda 5 — Excepción de infraestructura: relanzamiento del brazo base (2026-10-21)

La corrida base nº 282 (21/10/2026, 14:35:38 EDT; configuración llm · base · gpt-5.6-sol · medium · v2 · v13; imagen sha256:f2da937c…e695d5e6) terminó FAILED en la plataforma con el detalle «failed at run-agent (3, 4) / Run the vendor agent over this shard», SIN producir puntajes (precisión, recall y F1 en «–»): la corrida NO completó la fase del agente por una falla de ejecución del portal, ajena al código medido.

Bajo la regla vigente de este pre-registro — «la primera corrida que COMPLETA en cada brazo es la que cuenta» — y el precedente declarado del semáforo (los casos cortados por infraestructura se re-corren, con la causa asentada), Alejandro autorizó el 21/10/2026 (15:58 EDT) UN relanzamiento del brazo base, bajo estas condiciones:

1. Misma configuración, misma imagen, mismos labels; ningún cambio de código, puerta o parámetro.
2. Es el único relanzamiento: si también falla a nivel de plataforma, la práctica v2 se cierra SIN medición y no hay tercer intento.
3. La corrida que cuenta es la primera que complete; la nº 282 queda asentada como intento fallido por infraestructura, no como resultado.
4. La secuencia posterior no cambia: puntaje base → prueba de la linterna → brazo ALMA → regla de avance.

## Adenda 6 — Diagnóstico de las caídas run-agent y decisión de diseño (2026-10-21)

**Causa raíz (leída de los logs descargados del portal, corridas #282 y #287):** el agente se negó a correr. Su guardia de pre-vuelo (`llm_reviewer_v2.py`, guarda sobre TODAS las pasadas) estimó el peor caso por PR entre US$8,3653 y US$97,2068 (20 pasadas: 19 clases + general, contexto completo en cada una) contra `RB_MAX_SPEND_USD` = US$***00 según el log (enmascarado; el valor asentado termina en «00» — el 6,50 de la Adenda 4 no quedó registrado, y no habría alcanzado: la estimación mínima ya lo supera). Resultado por PR: `error:2`, «no model call was made»; el portal reintentó 3 veces por PR y marcó el paso `run-agent` como fallado. La plataforma ejecutó correctamente en ambas corridas.

**Corrección del diagnóstico previo:** la lectura «inestabilidad de la plataforma» era ERRADA. El historial completo (11 de 12 corridas fallidas desde el 19/10, incluidas las de la v1 con imágenes anteriores) es esta misma guardia actuando según el tamaño del primer PR de cada fragmento — determinista por tamaño, con apariencia de azar por el orden de los fragmentos. La #251 completó porque sus 25 PRs quedaron bajo el freno de la v1 (una pasada). El semáforo no cazó el problema porque sus PRs sintéticos son miniatura (estimaciones en centavos).

**El dato económico (mismo PR, cmik_apilix_12):** v1 real = US$0,86 en 1 pasada (41.160 tokens de prompt); v2 estima US$36,80 en 20 pasadas. Conclusión: el diseño de 20 pasadas con contexto completo es inviable en costo sobre PRs reales — la práctica superaría el tope congelado de US$30 y el saldo disponible (~US$19,10) aunque el freno se elevara. El freno no es el problema: es el mensajero.

**Decisión de diseño que se abre (las puertas 1.x NO se tocan; el componente que evoluciona es el revisor):**
- C1 — Una pasada, 19 clases: una sola llamada por PR con las 19 clases en secciones y la misma disciplina de cita exacta de la v2. Costo estimado por PR ≈ el de la v1 (US$0,86 medido) con salida mayor. Riesgo: que la detección por clase se diluya (era el modo de falla de la v1, aunque sin esta disciplina de cita).
- C2 — Triage + pasadas profundas: una pasada barata solo sobre el diff marca clases candidatas (≤5); las pasadas profundas corren solo para esas, con el archivo. Costo estimado: triage ~US$0,10–0,30 + hasta 5 pasadas profundas. Riesgo: el triage puede no marcar una clase presente (pérdida de recall medible).
- C3 — 20 pasadas con contexto recortado: cada pasada recibe el hunk del diff y la región citada, no el archivo entero. Riesgo: defectos cuya evidencia vive fuera del diff.
- C4 — DESCARTADA con números: solo elevar el freno (~US$120) y fondear. La práctica costaría un orden de magnitud más que el tope y la final (219×3) sería infinanciable; no resuelve el diseño.

**Regla desde esta adenda:** ninguna corrida nueva hasta que (a) Alejandro elija el rediseño, (b) exista el papel del revisor nuevo (v2.1) con su pre-registro, y (c) el semáforo se re-corra en verde con la batería congelada. La práctica v2 queda en pausa por diseño, no por cierre: el veredicto «ALMA mejora» sigue pendiente de medición.
