# ReviewBench requires linux/amd64. Build with:
#   docker build --platform linux/amd64 -t alma-reviewbench:dev .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY agent /app/agent
# The v2.5/v2.6 reviewers resolve their context artifacts at
# Path(__file__).parent.parent / "CONTEXTO-*.md" — the image
# root.  Without these two files the v25/v26 arms refuse at
# construction (fail-closed), before any model call
# (PREREGISTRO-VALIDACION-20261024.md §4).
COPY CONTEXTO-LECCIONES.md CONTEXTO-AUSENCIAS.md /app/

# The benchmark starts the image with no arguments and provides RB_* env vars.
ENTRYPOINT ["python", "-m", "agent"]
