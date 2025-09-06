# Getting Started

This guide gets you from zero to a running Matrix bot backed by your choice of LLM providers (OpenAI, xAI, Google, Mistral, Anthropic) and/or local models via Ollama.

## Prerequisites

- Python 3.10+
- A Matrix account for the bot (server URL, username, password)
- API keys for any cloud providers you plan to use
- Optional: [Ollama](https://ollama.com/) installed with at least one model pulled

For a deeper Ollama configuration guide, see [Ollama Setup](ollama.md).

Install Ollama and a model (optional):

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3
```

## Install Dependencies

Using the bundled requirements (includes E2E‑capable `matrix-nio[e2e]`):

```bash
pip install -r requirements.txt
```

## Configure

Create or edit `config.json` at the repo root. Minimal example spanning one cloud provider and one local model list:

```json
{
  "matrix": {
    "server": "https://matrix.org",
    "username": "@your_bot:matrix.org",
    "password": "your_password",
    "channels": ["#your-room:matrix.org"],
    "admins": ["@admin:matrix.org"],
    "store_path": "store",
  },
  "llm": {
    "models": {
      "openai": ["gpt-4o", "gpt-4o-mini"],
      "ollama": ["qwen3"]
    },
    "api_keys": {"openai": "YOUR_OPENAI_KEY"},
    "default_model": "gpt-4o",
    "personality": "a helpful assistant",
    "prompt": ["you are ", "."],
    "options": {"temperature": 0.8},
    "history_size": 24,
    "ollama_url": "localhost:11434",
    "mcp_servers": {}
  }
}
```

Environment variables commonly used by tools/providers:

- `OPENAI_API_KEY`, `XAI_API_KEY`, `GOOGLE_API_KEY`, `MISTRAL_API_KEY`, `ANTHROPIC_API_KEY`

See [Configuration](configuration.md) for the full schema and validation rules.

## Run

Preferred (installed command):

```bash
infinigpt-matrix --config config.json
```

Alternatively, run as a module:

```bash
python -m infinigpt --config config.json
```

## Verify

- The bot logs in and joins configured rooms
- Send `.ai hello` or `BotName: hello` in a joined room
- The bot replies and maintains per‑user history
