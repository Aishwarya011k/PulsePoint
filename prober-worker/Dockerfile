FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

FROM base AS builder
WORKDIR /app
COPY prober-worker/requirements.txt ./
RUN python -m pip install --upgrade pip && pip install --prefix=/install -r requirements.txt

FROM base AS runtime
RUN useradd --create-home --shell /bin/bash worker
WORKDIR /app
COPY --from=builder /install /usr/local
COPY prober-worker/ ./prober-worker
COPY prober-worker/.env.example ./prober-worker/.env
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /app/prober-worker
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD python -c "import sys,requests; sys.exit(0)" || exit 1

USER worker
CMD ["/usr/local/bin/python", "worker.py"]
