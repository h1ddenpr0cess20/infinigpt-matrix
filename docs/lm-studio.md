# LM Studio Setup (Optional)

InfiniGPT can use local models served by LM Studio via its built‑in OpenAI‑compatible local server. This page covers enabling the server, choosing models, and configuring InfiniGPT.

## Install and Enable the Local Server

- Download and install LM Studio from https://lmstudio.ai/ (macOS/Windows/Linux).
- Open the app, go to the Developer or API section, and enable the OpenAI‑compatible Local Server.
  - Default address: `http://localhost:1234`
  - The API path is OpenAI‑compatible: `/v1/*` (e.g., `/v1/chat/completions`).
  - API key: typically not required for local use. InfiniGPT sends a placeholder token.

## Choose and Download Models

Within LM Studio, search and download one or more chat models. Examples used in this repo:

- `openai/gpt-oss-20b`
- `qwen/qwen3-8b`

The exact model IDs must match what LM Studio exposes via its server.

## Configure InfiniGPT

Add an `lmstudio` entry to your models and set the URL in `config.json`:

```json
{
  "llm": {
    "models": {
      "lmstudio": ["openai/gpt-oss-20b", "qwen/qwen3-8b"]
    },
    "default_model": "openai/gpt-oss-20b",
    "lmstudio_url": "localhost:1234"
  }
}
```

You can also override the URL at launch:

```bash
infinigpt-matrix --config config.json --lmstudio-url localhost:1234
```

## Notes

- Authentication: if you enable API‑key requirement in LM Studio, InfiniGPT currently sends a generic Bearer value; most setups accept this. If yours enforces a specific key, you may need to disable that option or adjust the client.
- Port conflicts: if port `1234` is busy, change LM Studio’s port and update `lmstudio_url` accordingly.
- Model availability: ensure the model you set as `default_model` is present in `llm.models.*` across all providers and actually downloaded in LM Studio.

## Quick Test

Use curl to verify the server responds (replace model as needed):

```bash
curl -s http://localhost:1234/v1/models | jq .
```

If this succeeds, start InfiniGPT and try `.ai hello` in a Matrix room.
