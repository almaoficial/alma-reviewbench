# Guion — publicación v2.3: workflow, digest y configuración base del portal

**Estado: PREPARADO, SIN EJECUTAR.** El código v2.3 ya está publicado
(commit `a6838e60df8d754f361eb10e38eff815ae60708b` en `main` de
`almaoficial/alma-reviewbench`, verificado por relectura del repo el
2026-10-21). Lo que queda son pasos de navegador — el disparo del
workflow es por la UI de GitHub (la API de esta VM no puede: el token
guardado no tiene permiso de Actions, 403 «Resource not accessible by
personal access token», confirmado el 2026-10-21 en la v2.1 y la v2.2)
y la edición de la configuración es en el portal de ReviewBench, sobre
el agente registrado `alma-reviewer`, con la sesión de Alejandro.

**Alcance de esta publicación: SOLO el brazo base.** La configuración
ALMA del portal **NO se toca** — el brazo ALMA de la v2.3 está bloqueado
por pre-registro (puerta 1.4.0 no adoptada; papel v2.3 §4; declaración
completa en `MANIFIESTO-V23.md`). Queda con la imagen y los labels de
la v2.2.

---

## 0. Disparo del workflow (UI de GitHub Actions)

1. GitHub → repo `almaoficial/alma-reviewbench` → Actions → workflow
   **`reviewbench-image`** → «Run workflow».
2. Rama: `main` (debe estar en el commit `a6838e6`). Inputs: `tag` =
   `dev`, `package_dir` = `.` (los defaults).
3. Esperar el cierre en éxito (la v2.2 tardó ~31 s). El resumen del
   workflow («ReviewBench image published») imprime el digest completo
   `ghcr.io/almaoficial/alma-reviewbench@sha256:<64 caracteres>`.
4. **Verificación contra GHCR (primaria, no alcanza con el resumen):**
   con token anónimo de GHCR, el tag `dev` debe resolver a ese mismo
   digest, y el contenido de la imagen debe incluir
   `app/agent/llm_reviewer_v23.py`. Es la misma verificación que cerró
   la v2.1 (`4d1cf01`) y la v2.2 (`cc4dbc8`).
5. Asentar el digest verificado en el campo «Imagen (digest)» de
   `MANIFIESTO-V23.md` y cerrar la publicación con el commit de cierre
   (manifiesto + asiento en `REGISTRO-REVIEWBENCH.md`), como en la
   v2.2. **Sin digest verificado, las secciones siguientes no arrancan.**

## 1. Configuración base-v23 (portal)

1. Portal → agente `alma-reviewer` → configuración **base** (la que hoy
   lleva los labels `reviewer=v22` y la imagen v2.2).
2. **Imagen:** reemplazar el digest v2.2
   (`ghcr.io/almaoficial/alma-reviewbench@sha256:577bc2ec6780c5af4d3260caad74d3bd06b73dedf5b4e616ddbe03e44880206a`)
   por el digest v2.3 completo verificado en el paso 0 — pegar el string
   entero y verificar visualmente que termina en el último carácter del
   manifiesto (la v2 sufrió un digest truncado a 56 caracteres; el
   portal lo cazó, pero la verificación es de este guion).
3. **Labels — dejar EXACTAMENTE estos seis:**
   `backend=llm` · `governance=base` · `model=gpt-5.6-sol` ·
   `effort=medium` · `reviewer=v23` · `gate=v13`
   - El cambio contra la v2.2 es solo `reviewer=v22` → `reviewer=v23`.
   - **Sin `reviewer=v23`, `main.py` cae a su default `v1`** y la
     práctica mediría el revisor viejo con la imagen nueva.
     Sin `gate=v13`, el universo de clases no es el de 19.
4. **Credentials: NO TOCAR `RB_MAX_SPEND_USD`.** El campo se muestra
   totalmente enmascarado y **no se puede leer** (nunca se pudo
   confirmar si el valor guardado es 5,00 o 6,50). Se deja exactamente
   como está: el peor caso por PR queda acotado por construcción
   (plan ancla ≈US$5,43 < US$6,50; saturado, la regla de degradación
   corre 4 profundas y declara la 5ª) y la práctica esperada es
   US$10–25 bajo el tope de US$30. Ningún otro campo de Credentials se
   modifica tampoco.
5. Guardar. **Releer la configuración guardada** y cotejar campo por
   campo contra este guion (imagen y seis labels) — la v2.1 y la v2.2
   se verificaron igual, por relectura.

## 2. Configuración ALMA — NO SE TOCA

Sin cambios de imagen ni de labels en esta publicación. El brazo ALMA
solo podrá correr cuando un papel nuevo (la 1.4.1, ya pre-registrada y
sin construir) repare la frontera de la 1.4.0, su medición de adopción
pase, y una adenda firmada al papel v2.3 declare la etiqueta
`gate=v141` — todo antes de cualquier corrida ALMA. Nada de eso es
parte de este guion.

## 3. Cierre del guion (sin lanzar)

- La configuración base releída y coincidente con el manifiesto.
- **NO** se pulsa «Submit» (eso es la final de 219 PRs; no se toca
  jamás).
- El lanzamiento de la práctica («Test run», 25 PRs, **solo brazo
  base**; la linterna — recall base grounded > 0,7 % sobre 352 TP —
  se lee sobre su resultado) espera el «Corre» expreso de Alejandro,
  como mandan el papel v2.3 y el manifiesto.
- Asentar en `REGISTRO-REVIEWBENCH.md`: fecha/hora del disparo del
  workflow y de la actualización del portal, digest asentado en la
  configuración base, la constancia de que la configuración ALMA no
  fue modificada y de que `RB_MAX_SPEND_USD` no fue leído ni modificado,
  verbatim de la relectura.
