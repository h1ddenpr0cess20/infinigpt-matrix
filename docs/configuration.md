# Configuration

InfiniGPT reads a JSON configuration file (default `./config.json`). You can override the path with `--config`. CLI flags and environment variables merge on top of the file.

## Schema

- matrix:
  - server (url)
  - username, password
  - channels: list of room aliases/ids (e.g., `"#room:server"`, `"!roomid:server"`)
  - admins: list of Matrix user IDs with admin privileges
  - device_id: optional; persisted after first login
  - store_path: directory for Matrix store (default: `store`)
  - e2e: boolean, enable end‑to‑end encryption (default: true)
- llm:
  - models: mapping of provider → list of model IDs
    - Providers supported: `openai`, `xai`, `google`, `mistral`, `anthropic`, `deepseek`,`qwen`,`ollama`, `lmstudio`
  - api_keys: mapping of provider → API key (used when env var is not set)
  - default_model: selected model (must exist in the union of all provider lists)
  - prompt: two strings `[prefix, suffix]` used around personality; optionally a third string for a brevity clause `[prefix, suffix, brevity]`
  - personality: non‑empty default personality text
  - history_size: 1–1000 messages retained per user per room
  - options: advanced generation options (provider‑specific fields are ignored by providers that don’t use them)
  - ollama_url: base host:port for a local Ollama instance (e.g., `localhost:11434`)
  - lmstudio_url: base host:port for a local LM Studio server (default: `localhost:1234`)
  - mcp_servers: mapping of names to MCP server specs for tool calling (optional)
- markdown: render replies as Markdown (default: true)

## Environment Variables

Tools prefer environment variables for provider auth. If not set, values in `llm.api_keys` are used.

- `OPENAI_API_KEY`, `XAI_API_KEY`, `GOOGLE_API_KEY`, `MISTRAL_API_KEY`, `ANTHROPIC_API_KEY`,`DEEPSEEK_API_KEY`,`QWEN_API_KEY`
- `INFINIGPT_LOG_LEVEL` — default CLI log level
- The CLI also exports `INFINIGPT_CONFIG` (path to the active config) so tools can read consistent settings.

## Overrides via CLI

- `--e2e` / `--no-e2e`
- `--model`
- `--store-path`
- `--ollama-url`
 - `--ollama-url`
 - `--lmstudio-url`

## Validation

The application validates configuration on startup; on errors it prints messages and exits with code `2`.

Validation checks:

- `matrix.server` is a valid http(s) URL
- Credentials and channels are present and well‑formed
- `llm.default_model` is non‑empty and present across providers
- `llm.prompt` is a list of 2 or 3 strings
- `llm.mcp_servers` must be a mapping if provided
