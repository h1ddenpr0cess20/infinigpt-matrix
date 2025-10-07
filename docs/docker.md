# Docker

This guide covers building and running the InfiniGPT Matrix bot with Docker and Docker Compose. The image includes `libolm` for E2E, runs as a non‑root user, and persists sensitive state under `/data`.

## Prerequisites

- Docker 20.10+
- Optional: Docker Compose v2 (`docker compose`)
- A Matrix account for the bot and a `config.json` (see Configuration)

## Build the Image

Build from the repo root:

```bash
docker build -t infinigpt-matrix:latest .
```

What the image does:

- Installs the package from the repo (`pip install .`)
- Runs `infinigpt-matrix` by default with `--config /data/config.json --store-path /data/store`

## Run with Docker

1) Prepare configuration and store directories on the host:

```bash
mkdir -p store
cp config.json ./config.json  # ensure it contains Matrix creds, rooms, models
```

2) Run the container:

```bash
docker run --rm -it \
  --name infinigpt \
  -v "$(pwd)/config.json":/data/config.json:ro \
  -v "$(pwd)/store":/data/store \
  -v "$(pwd)/images":/data/images \
  -e OPENAI_API_KEY \
  -e XAI_API_KEY \
  -e GOOGLE_API_KEY \
  -e MISTRAL_API_KEY \
  -e ANTHROPIC_API_KEY \
  -e DEEPSEEK_API_KEY \
  -e QWEN_API_KEY \
  infinigpt-matrix:latest
```

Notes:

- The bot does not expose ports; it connects out to Matrix and any providers you configure.
- Persist `/data/store` to retain device keys for E2E rooms.

## Run with Docker Compose

An example compose service:

```yaml
services:
  infinigpt:
    build: .
    environment:
      - OPENAI_API_KEY
      - XAI_API_KEY
      - GOOGLE_API_KEY
      - MISTRAL_API_KEY
      - ANTHROPIC_API_KEY
      - DEEPSEEK_API_KEY
      - QWEN_API_KEY
    volumes:
      - ./config.json:/data/config.json:ro
      - ./store:/data/store
      - ./images:/data/images
    command: ["infinigpt-matrix", "--config", "/data/config.json", "--store-path", "/data/store", "--log-level", "INFO"]
```

Ensure your `store/` directory is writable by the container user.

## Configuration

- File: mount your `config.json` at `/data/config.json` (read‑only recommended).
- Environment: export API keys for the providers you enable.

See [Configuration](configuration.md) for the full schema and validation rules.

## Security Notes

- Treat `store/` as sensitive; back it up securely and do not commit it.
