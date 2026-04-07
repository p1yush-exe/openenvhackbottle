FROM python:3.11-slim

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for layer caching
COPY requirements.txt ./requirements.txt
COPY server/requirements.txt ./server/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r server/requirements.txt

# Copy application source
COPY . .

# Install the package itself (provides server entry-point)
RUN pip install --no-cache-dir -e .

# Seed the SQLite database so it exists at runtime
RUN python server/seed_db.py

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
