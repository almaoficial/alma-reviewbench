# ReviewBench requires linux/amd64. Build with:
#   docker build --platform linux/amd64 -t alma-reviewbench:dev .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY agent /app/agent

# The benchmark starts the image with no arguments and provides RB_* env vars.
ENTRYPOINT ["python", "-m", "agent"]
