# infinigpt-matrix

InfiniGPT is a powerful AI chatbot for the Matrix chat protocol that can roleplay as almost anything you can imagine. It supports multiple providers — OpenAI, xAI, Google, Mistral, Anthropic — and optional local models via Ollama and LM Studio. Each user has a separate conversation history per room, with dynamic personalities and admin controls for models and resets.

Also available for IRC: <https://github.com/h1ddenpr0cess20/infinigpt-irc>  
Ollama-only version at <https://github.com/h1ddenpr0cess20/ollamarama-matrix>

## Documentation

- [Overview](docs/index.md)
- [Getting Started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Commands](docs/commands.md)
- [Tools & MCP](docs/tools-and-mcp.md)
- [Images Directory](docs/images.md)
- [Docker](docs/docker.md)
- [CLI Reference](docs/cli.md)
- [Operations & E2E](docs/operations.md)
- [Architecture](docs/architecture.md)
- [Ollama Setup](docs/ollama.md)
- [LM Studio Setup](docs/lm-studio.md)
- [Development](docs/development.md)
- [Migration](docs/migration.md)
- [Legacy Map](docs/legacy-map.md)
- [Security](docs/security.md)
- [Not a Companion](docs/not-a-companion.md)
- [AI Output Disclaimer](docs/ai-output-disclaimer.md)

## Features

- Dynamic personalities with quick switching
- Per‑user history, isolated per room and user
- Collaborative mode to talk across histories
- Multi‑provider LLMs with unified model selection
- Tool calling (builtin and MCP) for actions and lookups
- Admin controls for model switching and global resets

## Installation

From source (installs CLI):

- `pip install .`
- Or use pipx: `pipx install .`

From source without installing the package:

- `pip install -r requirements.txt`
- Run with: `python -m infinigpt --config config.json`

After installation, use the `infinigpt-matrix` command.

## Quick Start

1) Create a Matrix account for the bot and note the server URL, username, and password.
2) Choose providers. For cloud providers, set API keys via env or `config.json`. For local models, install [Ollama](/docs/ollama.md) or [LM Studio](/docs/lm-studio.md)
3) Create `config.json`. See [Configuration](docs/configuration.md) for full schema
4) Run:

- Installed command: `infinigpt-matrix --config config.json`
- As module: `python -m infinigpt --config config.json`

## Usage

Common commands (see [Commands](docs/commands.md) for the full list):

| Command | Description | Example |
|---------|-------------|---------|
| `.ai <message>` or `BotName: <message>` | Chat with the AI | `.ai Hello there!` |
| `.x <user> <message>` | Continue another user's conversation | `.x Alice What did we discuss?` |
| `.persona <text>` | Change your personality | `.persona helpful librarian` |
| `.custom <prompt>` | Use a custom system prompt | `.custom You are a coding expert` |
| `.reset` / `.stock` | Clear history (default/stock prompt) | `.reset` |
| `.mymodel [name]` | Show/change personal model | `.mymodel gpt-4o-mini` |
| `.model [name|reset]` (admin) | Show/change model | `.model qwen3` |
| `.clear` (admin) | Reset globally for all users | `.clear` |
| `.help` | Show inline help | `.help` |

## Encryption Support

- Works in encrypted Matrix rooms using `matrix-nio[e2e]` with device verification.
- Requires `libolm` available to Python for E2E. If unavailable, you can run without E2E; see [Operations](docs/operations.md) and [Verification](docs/verification.md).
- Persist the `store/` directory to retain device keys and encryption state.

## Community & Policies

- Code of Conduct: [Code of Conduct](CODE_OF_CONDUCT.md)
- Contributing: [Contributing](CONTRIBUTING.md)
- Security Policy: [Security Policy](SECURITY.md)
- Security Guide: [Security Guide](docs/security.md)

## License

AGPL‑3.0 — see [License](LICENSE) for details.
