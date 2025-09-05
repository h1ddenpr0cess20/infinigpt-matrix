# Tools and MCP

InfiniGPT supports two kinds of tool calling so models can look up information or act on the user’s behalf during a chat:

- Built‑in tools bundled with the bot
- External tools exposed by MCP (Model Context Protocol) servers

Both kinds are presented to the model via an OpenAI‑style `tools` schema. The bot automatically merges built‑in and MCP tools at startup and lets the model decide when to call them.

## How It Works

When a user chats (`.ai` or `BotName: …`), the bot calls the selected provider’s Chat Completions API with a combined tools schema. If the model returns tool calls, the bot executes each call, appends the tool results to the conversation, and asks the model to continue. This loop runs up to 8 iterations.

Key details:

- Tool precedence: if an MCP tool name matches a built‑in tool name, the MCP tool takes precedence.
- Logging: tool calls are logged as `Tool (MCP|builtin): <name> args=<json>` with concise, truncated arguments.
- Safety: tool results are coerced to JSON strings before being sent back to the model.

## Built‑in Tools

Built‑in tools live under `infinigpt/tools/` and are described in a JSON schema file that the bot loads at startup.

Schema file:

- `infinigpt/tools/schema.json` — array of tool definitions (OpenAI‑style function schema)

Included built‑in tools (summary):

| Name | Description |
|------|-------------|
| `get_weather` | Get current weather for a city via Open‑Meteo. |
| `calculate_expression` | Safely evaluate a basic arithmetic expression. |
| `get_time` | Get the current time in UTC, local, or a named timezone. |
| `text_stats` | Return counts of words, characters, and sentences. |
| `fetch_url` | Fetch text content from an HTTP(S) URL with truncation. |
| `crypto_prices` | Get Coinbase product price details. |
| `openai_image` | Generate an image with OpenAI Images. |
| `grok_image` | Generate an image with xAI (Grok). |
| `gemini_image` | Generate an image with Google Gemini. |
| `openai_search` | Use OpenAI search preview model.

Implementation notes:

- Functions are defined in modules under `infinigpt/tools/` (e.g., `weather.py`, `math.py`, `utils.py`, `text.py`, `web.py`, `crypto.py`, `images.py`).
- Return values should be JSON‑serializable. Non‑serializable values are stringified.
- The schema’s `function.name` must match the Python function name.

### Adding a Built‑in Tool

1) Implement a function under `infinigpt/tools/` and export it by name.
2) Add a matching tool definition to `infinigpt/tools/schema.json`.

## MCP Tools

Define MCP servers under `llm.mcp_servers` in `config.json`. You can use a URL or a command (with optional `args`) to launch a local server. Examples:

```json
{
  "llm": {
    "mcp_servers": {
      "notes": {"command": "notes-mcp", "args": ["--port", "8765"]},
      "browser": "http://127.0.0.1:9000"
    }
  }
}
```

Behavior notes:

- On startup, the bot probes each server, logs how many tools were found, and builds a consolidated client.
- If a server is defined with `command`/`args`, stderr is silenced; stdout is preserved for MCP stdio.
- Duplicate names: MCP tools override built‑in tools with the same name.

## Troubleshooting

- Model never calls tools: ensure your model supports tool/function calling and that tools appear in logs at startup (use `-L DEBUG`).
- HTTP/network errors from tools: check your environment’s network and any proxies/firewalls. MCP servers must be reachable.
- Built‑in tool not found: confirm the function name in `schema.json` matches the Python function name and module is importable.

