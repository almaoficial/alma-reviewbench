# Guion — actualización de las configuraciones del portal a la v2.2

**Estado: PREPARADO, SIN EJECUTAR.** La edición del portal y el lanzamiento
de la práctica quedan para la orden de lanzar (el «Corre» de Alejandro),
como en la v2.1. Este guion se ejecuta en el navegador, sobre el agente
registrado `alma-reviewer` de ReviewBench, con la sesión de Alejandro.

**Precondición:** el workflow `reviewbench-image` corrido sobre `main`
@ `031dd0f` (el commit del paquete v2.2) completó con éxito y el campo
«Imagen (digest)» del [`MANIFIESTO-V22.md`](MANIFIESTO-V22.md) quedó
asentado con el digest completo, **verificado contra GHCR** (el tag
`dev` resuelve a ese digest; el digest anterior, v2.1, era
`sha256:32da7c01…`). Sin ese digest verificado, este guion no arranca.
Nota de procedimiento: el disparo del workflow es por la UI de GitHub —
la API de esta VM no puede (el token guardado no tiene permiso de
Actions: 403 «Resource not accessible by personal access token»,
confirmado el 2026-10-21, igual que en la v2.1).

---

## 1. Configuración base-v22

1. Portal → agente `alma-reviewer` → configuración **base** (la que hoy
   lleva los labels `reviewer=v21`).
2. **Imagen:** reemplazar el digest v2.1
   (`ghcr.io/almaoficial/alma-reviewbench@sha256:32da7c01181c3ebae61d6cb9d5d31590858ad328c7f292d56d153a5b0523a0bc`)
   por el digest v2.2 completo del manifiesto — pegar el string entero,
   verificar visualmente que termina en el último carácter del
   manifiesto (la v2 sufrió un digest truncado a 56 caracteres; el
   portal lo cazó, pero la verificación es de este guion).
3. **Labels — dejar EXACTAMENTE estos seis:**
   `backend=llm` · `governance=base` · `model=gpt-5.6-sol` ·
   `effort=medium` · `reviewer=v22` · `gate=v13`
   - El cambio contra la v2.1 es solo `reviewer=v21` → `reviewer=v22`.
   - **Sin `reviewer=v22`, `main.py` cae a su default `v1`** y la
     práctica mediría el revisor viejo con la imagen nueva.
     Sin `gate=v13`, el universo de clases no es el de 19.
4. **Credentials: NO TOCAR `RB_MAX_SPEND_USD`.** El campo se muestra
   totalmente enmascarado y **no se puede leer** (nunca se pudo
   confirmar si el valor guardado es 5,00 o 6,50). Se deja exactamente
   como está: con la v2.2 ningún PR puede superar el freno por
   construcción (planificación por peor caso + regla de degradación
   declarada del diseño C2; el peor caso saturado del ancla es
   ≈US$6,49 y la práctica esperada es US$10–25 bajo el tope de US$30).
   Ningún otro campo de Credentials se modifica tampoco.
5. Guardar. **Releer la configuración guardada** y cotejar campo por
   campo contra este guion (imagen y seis labels) — la v2.1 se
   verificó igual, por relectura.

## 2. Configuración ALMA-v22

Idéntica a la §1, con **un solo campo distinto**:

- Labels: `backend=llm` · `governance=alma` · `model=gpt-5.6-sol` ·
  `effort=medium` · `reviewer=v22` · `gate=v13`
- Misma imagen (digest v2.2). Credentials sin tocar, igual que en la
  base (el freno vive en CADA configuración y en ninguna se edita).
- Guardar y releer completa.

## 3. Cierre del guion (sin lanzar)

- Las dos configuraciones releídas y coincidentes con el manifiesto.
- **NO** se pulsa «Submit» (eso es la final de 219 PRs; no se toca
  jamás).
- El lanzamiento de la práctica («Test run», 25 PRs, base primero y
  ALMA solo si la base supera la prueba de la linterna — recall base
  > 0,7 %) espera el «Corre» expreso de Alejandro, como mandan el
  papel v2.2 §7 y el manifiesto.
- Asentar en `REGISTRO-REVIEWBENCH.md`: fecha/hora de la actualización,
  digest asentado en cada configuración y la constancia de que
  `RB_MAX_SPEND_USD` no fue leído ni modificado en ninguna de las dos,
  verbatim de la relectura.
