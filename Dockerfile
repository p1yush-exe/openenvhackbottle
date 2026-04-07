FROM node:22-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json /app/frontend/
RUN npm ci --no-audit --no-fund

COPY frontend/ /app/frontend/
RUN npm run build

FROM python:3.11-slim

# ------------------------------------------------------------------
# System packages
# ------------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libhts-dev \
        libbz2-dev \
        liblzma-dev \
        libcurl4-gnutls-dev && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------
# Python dependencies
# ------------------------------------------------------------------
WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Install all deps; pysam has manylinux wheels so no source build needed
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------
# Application code + data
# ------------------------------------------------------------------
COPY clinical_bench/ /app/clinical_bench/
COPY server/ /app/server/
COPY openenv.yaml /app/openenv.yaml
COPY pyproject.toml /app/pyproject.toml
COPY inference.py /app/inference.py
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Data files live at /app/data so DATA_PATH=/app/data works out of the box
RUN cp -r /app/clinical_bench/data /app/data

# ------------------------------------------------------------------
# Environment variables
# ------------------------------------------------------------------
ENV PYTHONPATH=/app
ENV DATA_PATH=/app/data
ENV MAX_STEPS=8
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ------------------------------------------------------------------
# Start the server
# ------------------------------------------------------------------
EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn clinical_bench.server.app:app --host 0.0.0.0 --port ${PORT} --workers 1 --timeout-keep-alive 75"]
