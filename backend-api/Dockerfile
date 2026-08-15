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
COPY backend-api/requirements.txt ./
RUN python -m pip install --upgrade pip && pip install --prefix=/install -r requirements.txt

FROM base AS runtime
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY backend-api/ ./backend-api
COPY backend-api/.env.example ./backend-api/.env
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /app/backend-api
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

USER appuser
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000}"]
