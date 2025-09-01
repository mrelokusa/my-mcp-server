# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install build essentials required by some wheels (kept small)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use the PORT env Render provides; default to 10000 for local dev consistency
ENV PORT 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000", "--proxy-headers"]
