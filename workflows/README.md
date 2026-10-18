# Workflow de imagen — dónde va y cómo se usa

`reviewbench-image.yml` es el camino de construcción de la imagen cuando no
hay Docker local (esta VM no tiene docker/podman/buildah/nerdctl/kaniko:
verificado el 2026-10-18; no se instalaron paquetes del sistema).

## Dónde va

En el repo de GitHub que contenga este paquete, como:

```text
.github/workflows/reviewbench-image.yml
```

Ese repo debe vivir bajo la cuenta **almaoficial** para que el destino
`ghcr.io/almaoficial/alma-reviewbench` sea correcto y el `GITHUB_TOKEN` del
workflow tenga permiso de publicación (`packages: write`, ya declarado en
el workflow). Si el paquete no está en la raíz del repo, al disparar el
workflow hay que pasar su ruta en el input `package_dir`.

## Cómo se usa

1. Copiar el archivo a `.github/workflows/` del repo elegido y commitear.
   (Nada de esto se subió todavía: es decisión A de
   [REGISTRO-REVIEWBENCH.md](../REGISTRO-REVIEWBENCH.md).)
2. En GitHub: Actions → `reviewbench-image` → **Run workflow** (manual,
   `workflow_dispatch`; no corre por push ni por cron).
3. El job construye `linux/amd64`, publica en GHCR y deja el digest
   `ghcr.io/almaoficial/alma-reviewbench@sha256:<...>` en el resumen del
   run. Ese digest — no el tag — es el que se pega en el formulario de
   registro de ReviewBench.
4. La imagen publicada es código público (GHCR público por defecto, que es
   lo que el portal espera para tirar sin credencial). Publicarla = hacer
   público el código del adaptador; el repo de ALMA ya es público, pero la
   decisión es explícita igual.
