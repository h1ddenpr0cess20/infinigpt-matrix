# Architecture

The bot is a small, modular async application that wires a Matrix client to one or more LLM providers through a command router and stateless handlers.

## Modules

- `infinigpt/cli.py`: CLI entry; loads config, applies overrides, starts the app.
- `infinigpt/config.py`: Dataclasses, merge, validation, redacted summaries.
- `infinigpt/logging_conf.py`: Central logging setup with Rich handler and tracebacks.
- `infinigpt/llm_client.py`: Provider‑agnostic LLM client (cloud + optional Ollama).
- `infinigpt/fastmcp_client.py`: MCP tool server client/launcher integration.
- `infinigpt/matrix_client.py`: Thin wrapper over `nio.AsyncClient` (login/join/send/sync).
- `infinigpt/history.py`: Per‑room/user histories with prompt injection and trimming.
- `infinigpt/handlers/`: Router and command handlers (`.ai`, `.model`, `.mymodel`, `.reset`, `.help`, `.persona`, `.custom`, `.x`, `.tools`, `.verbose`).
- `infinigpt/security.py`: To‑device callbacks and verification helpers.
- `infinigpt/interfaces.py`: Protocols for testing and typing.
- `infinigpt/tools/`: Built‑in tools and `tools/schema.json`.

## Data Flow

1. CLI loads and validates config; composes dependencies into an application context.
2. Matrix wrapper logs in, joins rooms, and dispatches text events to the router.
3. Router selects a handler by command prefix or `BotName:` mention.
4. Handlers read/write `HistoryStore` and call the LLM client in a background thread when needed.
5. Replies are sent with optional Markdown formatting.

## Async Boundaries

- Matrix I/O is async.
- Most LLM HTTP calls are synchronous; they run in a thread executor via a helper when appropriate.

## Histories and Personas

The `HistoryStore` maintains a per‑user, per‑room transcript. A system prompt is always the first entry, constructed from the configured personality and prompt prefix/suffix. Trim logic ensures history stays within a fixed bound while keeping context fresh.

## Security Notes

- No secrets are committed. `config.json` lives locally.
- E2E is supported when `matrix-nio[e2e]` and libolm are present; store data under `store/` should be treated as sensitive.
- To‑device callbacks are registered to support device verification and logging.
