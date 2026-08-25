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
COPY checks-consumer/requirements.txt ./
RUN python -m pip install --upgrade pip && pip install --prefix=/install -r requirements.txt

FROM base AS runtime
RUN useradd --create-home --shell /bin/bash consumer
WORKDIR /app
COPY --from=builder /install /usr/local
COPY checks-consumer/ ./checks-consumer
COPY checks-consumer/.env.example ./checks-consumer/.env
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /app/checks-consumer
USER consumer
CMD ["/usr/local/bin/python", "consumer.py"]
