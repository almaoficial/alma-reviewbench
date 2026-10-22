# Guion — actualización de las configuraciones del portal a la v2.1

**Estado: PREPARADO, SIN EJECUTAR.** La edición del portal y el lanzamiento
de la práctica quedan para la orden siguiente (la de lanzar), como en la
v2. Este guion se ejecuta en el navegador, sobre el agente registrado
`alma-reviewer` de ReviewBench, con la sesión de Alejandro.

**Precondición:** el campo «Imagen (digest)» del
[`MANIFIESTO-V21.md`](MANIFIESTO-V21.md) ya completado con el digest del
run nº 4 del workflow (64 caracteres hex tras `sha256:`, verificado contra
GHCR por pull fresco). Sin ese digest, este guion no arranca.

---

## 1. Configuración base-v21

1. Portal → agente `alma-reviewer` → configuración **base** (la que hoy
   lleva los labels `reviewer=v2`).
2. **Imagen:** reemplazar el digest v2
   (`ghcr.io/almaoficial/alma-reviewbench@sha256:f2da937c2fa4a0e3cbdf3dae09c821419f34920cf4ab3394fc2cc226e695d5e6`)
   por el digest v2.1 completo del manifiesto — pegar el string entero,
   verificar visualmente que termina en el último carácter del manifiesto
   (la v2 sufrió un digest truncado a 56 caracteres; el portal lo cazó,
   pero la verificación es de este guion).
3. **Labels — dejar EXACTAMENTE estos seis:**
   `backend=llm` · `governance=base` · `model=gpt-5.6-sol` ·
   `effort=medium` · `reviewer=v21` · `gate=v13`
   - El cambio contra la v2 es solo `reviewer=v2` → `reviewer=v21`.
   - **Sin `reviewer=v21`, `main.py` cae a su default `v1`** y la
     práctica mediría el revisor viejo con la imagen nueva.
     Sin `gate=v13`, el universo de clases no es el de 19.
4. **Credentials:** verificar `RB_MAX_SPEND_USD` = **6.50**.
   En las corridas #282/#287 el log mostró el valor enmascarado como
   `US$***00`: el 6,50 de la Adenda 4 **no consta efectivamente cargado**.
   Si el campo muestra 5.00 (o cualquier otro valor), corregirlo a 6.50
   ANTES de guardar. Con la v2.1 el peor caso por PR es ~US$1,31: el
   freno no debería gatillar, pero queda como está firmado.
5. Guardar. **Releer la configuración guardada** y cotejar campo por
   campo contra este guion (imagen, seis labels, freno) — la v2 se
   verificó igual, por relectura.

## 2. Configuración ALMA-v21

Idéntica a la §1, con **un solo campo distinto**:

- Labels: `backend=llm` · `governance=alma` · `model=gpt-5.6-sol` ·
  `effort=medium` · `reviewer=v21` · `gate=v13`
- Misma imagen (digest v2.1), mismo freno `RB_MAX_SPEND_USD` = **6.50**
  en su panel Credentials (el freno vive en CADA configuración).
- Guardar y releer completa.

## 3. Cierre del guion (sin lanzar)

- Las dos configuraciones releídas y coincidentes con el manifiesto.
- **NO** se pulsa «Submit» (eso es la final de 219 PRs; no se toca).
- El lanzamiento de la práctica («Test run», 25 PRs, base primero y
  ALMA después de verificar el puntaje de la base) espera la orden
  expresa de Alejandro, como mandan el papel v2.1 §6 y el manifiesto.
- Asentar en `REGISTRO-REVIEWBENCH.md`: fecha/hora de la actualización,
  digest asentado en cada configuración y confirmación del freno 6.50
  en ambas, verbatim de la relectura.
