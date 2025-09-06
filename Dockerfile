# Minimal, secure image for the InfiniGPT Matrix bot
# - Includes libolm runtime for E2E support (matrix-nio[e2e])
# - Runs as non-root and persists sensitive state under /data

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System dependencies: libolm for E2E; certificates for HTTPS
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libolm3 \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project and install as a package to get the console script
COPY pyproject.toml README.md LICENSE ./
COPY infinigpt ./infinigpt
COPY docs ./docs
RUN pip install --no-cache-dir .

# Non-root user for security (default UID 1000 for host bind-mount compatibility)
RUN groupadd -r app && useradd -r -g app -u 1000 app 
RUN mkdir -p /data/images && chown -R app:app /data
RUN ln -s /data/images /app/images

USER app
VOLUME ["/data"]

# Sensible defaults; override at runtime as needed
ENV INFINIGPT_CONFIG=/data/config.json \
    INFINIGPT_LOG_LEVEL=INFO

# No ports need exposure; the bot connects out to Matrix and providers
CMD ["infinigpt-matrix", "--config", "/data/config.json", "--store-path", "/data/store"]
