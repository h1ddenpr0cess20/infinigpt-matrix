# Docker

This guide covers building and running the InfiniGPT Matrix bot with Docker and Docker Compose.

Note: The provided image is minimal and does not install `libolm`. If you require E2E inside the container, extend the image to include `libolm` and ensure `matrix-nio[e2e]` is available.

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
- Runs `infinigpt-matrix` by default with `--config config.json`

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
  -v "$(pwd)/config.json":/app/config.json:ro \
  -v "$(pwd)/store":/app/store \
  -e OPENAI_API_KEY \
  -e XAI_API_KEY \
  -e GOOGLE_API_KEY \
  -e MISTRAL_API_KEY \
  -e ANTHROPIC_API_KEY \
  infinigpt-matrix:latest
```

Notes:

- The bot does not expose ports; it connects out to Matrix and any providers you configure.
- Persist `/app/store` to retain device keys for E2E rooms.

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
    volumes:
      - ./config.json:/app/config.json:ro
      - ./store:/app/store
    command: ["infinigpt-matrix", "--config", "config.json", "--log-level", "INFO"]
```

Ensure your `store/` directory is writable by the container user.

## Configuration

- File: mount your `config.json` at `/app/config.json` (read‑only recommended).
- Environment: export API keys for the providers you enable.

See [Configuration](configuration.md) for the full schema and validation rules.

## Security Notes

- Treat `store/` as sensitive; back it up securely and do not commit it.

