**Refactor Plan: Mirror ollamarama-matrix Structure (Reuse-As-Much-As-Possible)**

- **Goal:** Restructure this repository to mirror the modular layout of `/home/vagabond/projects/ollamarama-matrix/ollamarama`, reusing its code wherever possible, while adapting for this project’s differences (multi-provider LLMs, existing tools/schema, commands, and config).
- **Scope:** Code structure, configuration, command handling, Matrix client/security, history, tools, logging, packaging/CLI, docs, and optional Docker/test scaffolding.

**High-Level Mapping**
- **From (this repo):** `infinigpt.py`, `tools.py`, `verification.py`, `config.json`, `schema.json`, `help.txt`.
- **To (mirroring ollamarama-matrix):**
  - `infinigpt/` package with modules paralleling `ollamarama/`:
    - `app.py`, `cli.py`, `config.py`, `logging_conf.py`, `matrix_client.py`, `security.py`, `history.py`, `interfaces.py`
    - `llm_client.py` (adapted from `ollama_client.py`, generalized to OpenAI/xAI/Google/Mistral/Anthropic/Ollama)
    - `handlers/` (`cmd_ai.py`, `cmd_x.py`, `cmd_model.py`, `cmd_mymodel.py`, `cmd_prompt.py`, `cmd_reset.py`, `cmd_help.py`, `cmd_tools.py`, `router.py`, `__init__.py`)
    - `tools/` (`__init__.py`, `utils.py`, plus concrete tools split from current `tools.py`; reuse `schema.json`)
  - Root-level: `pyproject.toml`, `README.md` updates, `help.md` (rename from `help.txt`), optional `Dockerfile`/`docker-compose.yml`, `docs/`.

**Project-Specific Differences (Must-Haves)**
- **Multi-provider LLM support:** Unlike ollamarama (Ollama-only), this bot supports OpenAI, xAI, Google, Mistral, Anthropic, and Ollama. Implement a generalized `LLMClient` with per-provider routing, auth, and base URLs.
- **Config format is different:** Current `config.json` uses a top-level `llm` with `models` grouped by provider and `api_keys` for all providers. The new `config.py` must preserve this format and validation, not ollamarama’s `ollama.*` structure.
- **Combined tool system with MCP:** Replace the current ad-hoc tool flow with the ollamarama combined tool system. Merge built-in tools (from this repo’s toolset, including image generators) with tools discovered from configured MCP servers. Execute MCP tools via MCP client, and built-ins locally. Dedupe by function name.
- **Tool schema and tools set:** Keep using this repo’s tools (`crypto_prices`, `openai_image`, `grok_image`, `gemini_image`, `openai_search`) by migrating them into `infinigpt/tools/` and exposing them through the combined tool system. Retain `schema.json` format; augment with MCP-provided schemas.
- **Commands parity/differences:** Support `.mymodel` (per-user model) and `.tools` (toggle tools) in addition to `.ai`, `.x`, `.persona`, `.custom`, `.reset`, `.stock`, `.model`, `.help`.
- **Reasoning content handling:** Preserve `<think>…</think>` stripping before sending replies.
- **Per-user model mapping:** Maintain `user_models` per-channel per-user selection in `history`/context logic.
- **Matrix encryption callbacks:** Port existing emoji verification and to-device handlers (from `verification.py`) into `security.py` and wire them via `matrix_client`.

**Step-by-Step Tasks**

1) Create Package Skeleton (mirror structure)
- Create `infinigpt/` package mirroring `ollamarama/` layout.
- Add `__init__.py`, `__main__.py` (delegates to CLI main), and `logging_conf.py` (copy from ollamarama, keep levels consistent).
- Add `interfaces.py` and `exceptions.py` (reuse from ollamarama where applicable).

2) Config System (preserve current config model)
- Implement `infinigpt/config.py`:
  - Dataclasses: `MatrixConfig`, `LLMConfig` (mirrors current `llm` schema: `models` as provider→list, `api_keys`, `default_model`, `personality`, `prompt`, `options`, `history_size`, `ollama_url`, and `mcp_servers` mapping for MCP integration).
  - `AppConfig` wraps `matrix: MatrixConfig` and `llm: LLMConfig`, plus `markdown: bool` (default True).
  - `load_config(path: Optional[str]) -> AppConfig` reads this repo’s `config.json` format (do NOT adopt ollamarama’s `ollama.*`).
  - `validate_config(cfg) -> (ok, errors)` validates: required fields, provider models presence, default model exists in any provider, API keys present for used providers, ranges for options, and `mcp_servers` shape (mapping of name→server spec/url/env).
  - `summarize(cfg)` returns a redacted dict for logs.
- Keep environment overrides minimal (optional): e.g., `INFINIGPT_MATRIX_SERVER`, `INFINIGPT_STORE_PATH`, etc.

3) Matrix Client Wrapper (extract IO)
- Add `infinigpt/matrix_client.py` (copy `ollamarama/matrix_client.py`):
  - Keep `send_text` with optional HTML; mapping `markdown` rendering will live in `app.py`.
  - Keep `add_text_handler`, `add_to_device_callback`, `load_store`, `login`, `ensure_keys`, `initial_sync`, `sync_forever`, `shutdown`.
- Ensure `display_name` mirrors current behavior and falls back gracefully.

4) Security / Verification (port from this repo)
- Add `infinigpt/security.py` using logic from this repo’s `verification.py`:
  - `allow_devices(user_id)` unblacklist/ignore devices to allow sending.
  - `emoji_verification_callback` and `log_to_device_event` exactly as in current code.
- Wire these callbacks via `matrix_client.add_to_device_callback` in `app.py` at startup (as ollamarama does).

5) Conversation History and State
- Add `infinigpt/history.py` modeled after `ollamarama/history.py` but adapted to this project’s behavior:
  - Keep per-channel, per-user message lists.
  - Insert system prompt: `prompt_prefix + personality + prompt_suffix` from config at start of history.
  - Honor `history_size` and prune, while removing tool/tool_call messages when trimming (match current `infinigpt.py`).
  - Maintain `user_models: Dict[channel, Dict[user, model]]` and helpers to set/get.
  - Optional: support `verbose` flag similar to ollamarama if desired; default False.

6) LLM Client (multi-provider; tools)
- Create `infinigpt/llm_client.py` adapted from `ollamarama/ollama_client.py` but generalized:
  - Implement `chat_with_tools(model, messages, options, tools, tool_choice, timeout)` that:
    - Maps `model` to a provider based on `cfg.llm.models` (OpenAI, xAI, Google, Mistral, Anthropic, Ollama).
    - All providers are OpenAI-compatible: use `POST {base}/chat/completions` with a single unified request/response shape.
    - Build base URL and Authorization for each provider (Bearer per provider):
      - OpenAI: `https://api.openai.com/v1`
      - xAI: `https://api.x.ai/v1`
      - Google: `https://generativelanguage.googleapis.com/v1beta/openai`
      - Mistral: `https://api.mistral.ai/v1`
      - Anthropic: `https://api.anthropic.com/v1`
      - Ollama: `http://{ollama_url}/v1`
    - JSON body: `{model, messages, tools, tool_choice?, options?}`
      - Maintain current behavior to omit `options` for Google provider unless confirmed otherwise.
  - Return OpenAI-style response (`choices[0].message`).
  - Optionally expose `chat` alias if needed by handlers.

7) Tool Execution (combined built-ins + MCP)
- Create `infinigpt/tools/`:
  - Move existing tool functions out of `tools.py` into separate modules (e.g., `images.py`, `web.py`, `crypto.py`) with unchanged signatures/names.
  - Add `__init__.py` that provides:
    - `load_builtin_schema()` to read local `schema.json`.
    - `load_mcp_schema(mcp_client)` to ask MCP servers for tool schemas.
    - `merge_schemas(builtin, mcp)` that dedupes by `function.name` (prefer MCP definitions when name conflicts, unless configured otherwise).
    - `execute_tool(name, args)` that dispatches to built-ins; MCP tool execution resides in app context via MCP client when the name is in MCP tool set.
  - Preserve saving images to `./images/...` and ensure directory existence.
- Keep the tool names/signatures stable to match `schema.json` and compatible with MCP tool-call JSON.

8) Command Handlers (split per-command)
- Create `infinigpt/handlers/` and port logic from `infinigpt.py`:
  - `router.py`: copy from ollamarama.
  - `cmd_ai.py`: adds user message to history, calls response with tools loop, sends reply.
  - `cmd_x.py`: cross-user interaction with named target display; resolve to user ID if present.
  - `cmd_model.py`: admin `.model` – list/set global model (ensure it exists in any provider list).
  - `cmd_mymodel.py`: user `.mymodel` – list/set per-user model; enforce Ollama constraint: if selecting an Ollama model, it must match global model as in current logic.
  - `cmd_prompt.py`: `.persona` and `.custom`; set system prompt and optionally trigger an intro reply.
  - `cmd_reset.py`: `.reset` and `.stock` (clear history and repopulate based on defaults or stock).
  - `cmd_help.py`: render `help.md` (converted from `help.txt`) to Matrix, with optional Markdown->HTML.
  - `cmd_tools.py`: `.tools` toggle tools on/off.
- Align handler signatures with ollamarama router: `(ctx, room_id, sender_id, sender_display, args)`.

9) Application Orchestrator
- Implement `infinigpt/app.py` (mirror ollamarama/app.py) with adaptations:
  - Build `AppContext` with: config, logger, `MatrixClientWrapper`, `LLMClient`, `HistoryStore`, tools schema, default model/personality, options, timeout, admins, bot_id from Matrix display name when available.
  - Add Markdown renderer guard like ollamarama.
  - Build combined tool schema:
    - Initialize MCP client from `llm.mcp_servers` using `fastmcp_client.py` (reused from ollamarama).
    - Query MCP servers for tools and merge with builtin schema from `infinigpt/tools/schema.json` via `merge_schemas`.
    - Track which tool names are MCP-backed vs built-in; enable/disable tools with `.tools` command.
  - Implement `respond_with_tools(messages, tool_choice="auto")`:
    - Use `LLMClient.chat_with_tools`.
    - Loop tool calls up to a max (use current repo’s 10 or ollamarama’s 8; keep 10 to preserve behavior).
    - Append tool results and prune `tool`/`tool_calls` messages between iterations.
    - For each tool call, route to MCP client if name is MCP-provided; otherwise, call built-in `execute_tool`.
    - Strip `<think>...</think>` from final content (preserve current repo behavior).
  - Register handlers via `Router` (include `.mymodel` and `.tools`).
  - Wire `Security` to-device callbacks and allow_devices before handling.
  - Load store, login, ensure keys, initial sync, join rooms, sync_forever with graceful shutdown (copy ollamarama flow).

10) CLI and Entry Points
- Add `infinigpt/cli.py` (mirror ollamarama):
  - Parse `--config` path, optional overrides (e.g., `--model`, `--markdown`), and a `--no-e2e` switch if desired.
  - Load and validate config; print redacted summary on start; run `app.run(cfg, config_path)`.
- Add `__main__.py` to call CLI.
- Add `pyproject.toml` with a console script, e.g., `infinigpt-matrix = infinigpt.cli:main`.

11) Docs and Help
- Convert `help.txt` to `help.md` (format already Markdown-like). Update handler to use it.
- Update `README.md` to explain modular structure, multi-provider support, and commands (include `.mymodel` and `.tools`).
- Add `docs/` (optional) with configuration examples and provider-specific notes.

12) Packaging and Runtime
- Add `requirements.txt` or rely on `pyproject.toml`:
  - `matrix-nio[e2e]`, `httpx`, `markdown`, and any tool dependencies.
- Optional Docker: copy `Dockerfile` and `docker-compose.yml` from ollamarama and adapt env/config variable names.
- Create `store/` in `.gitignore` if not present.

13) Tests and Validation (optional but recommended)
- Mirror lightweight tests from `ollamarama/tests/` where feasible for router, config validation, and history trimming.
- Add minimal smoke test for `LLMClient` provider routing (mock HTTP).

14) Migration and Cutover
- Move/rename files:
  - Keep current files for reference during refactor; create new modular package in parallel, then remove old monoliths when verified.
  - Migrate `schema.json` as is; relocate to `infinigpt/tools/schema.json` or keep at repo root and reference consistently.
  - Migrate `tools.py` functions into `infinigpt/tools/` modules; keep names stable to match schema.
  - Migrate verification logic into `security.py` and wire in `app.py`.
  - Replace `infinigpt.py` runtime with `python -m infinigpt` CLI entry.
- Verify parity:
  - Commands: `.ai`, `.x`, `.persona`, `.custom`, `.reset`, `.stock`, `.model`, `.mymodel`, `.help`, `.tools`.
  - Behavior: per-user history, per-channel isolation, per-user model override, `<think>` stripping, tool loop up to 10, Google options omission, image upload via Matrix for file-returning tools.

15) Provider-Specific Notes
- All configured providers are OpenAI-compatible; use the unified `/chat/completions` path and payload.
- Google path remains `v1beta/openai` per current project; continue omitting `options` unless confirmed otherwise.
- Ollama tool-calling compatibility: maintain `tool_choice="auto"` behavior and schema format identical to Ollama expectations.
- Timeouts: use 120–360s as today; make configurable via `llm.timeout`.

16) Logging and Observability
- Use `logging_conf.py` from ollamarama; set module loggers for `infinigpt.*`.
- Ensure tool calls are logged with truncated, safe args (as in ollamarama `AppContext._execute_tool`).

17) Backward Compatibility Notes
- Keep `config.json` structure unchanged to avoid user migration friction.
- Maintain existing tool names and signatures; keep `schema.json` identical unless adding new tools.
- Retain per-user model restriction for Ollama models (must match global model) per current implementation.

18) MCP Tool Support (required when configured)
- Reuse `fastmcp_client.py` from ollamarama to connect to multiple MCP servers, list tools, and call tools.
- Enable by providing `llm.mcp_servers` mapping in `config.json`. If none are configured, the bot runs with built-in tools only.
- Merge MCP tools with built-ins; prefer MCP tool definitions on name conflicts unless explicitly overridden.

**File/Module Creation Checklist**
- `infinigpt/__init__.py`, `infinigpt/__main__.py`
- `infinigpt/app.py` (orchestrator)
- `infinigpt/cli.py` (entry point)
- `infinigpt/config.py` (current repo’s config model, not ollamarama’s)
- `infinigpt/history.py` (per-channel/user store + user_models)
- `infinigpt/matrix_client.py` (copied/adapted)
- `infinigpt/security.py` (from `verification.py`)
- `infinigpt/llm_client.py` (new, multi-provider)
- `infinigpt/handlers/` (`router.py`, `cmd_*.py` including `.mymodel` and `.tools`)
- `infinigpt/tools/` (`__init__.py`, modules for current tools, `schema.json` or loader to root schema, merge helpers)
- `infinigpt/fastmcp_client.py` (reused from ollamarama)
- `logging_conf.py`
- `pyproject.toml` (console script `infinigpt-matrix`)
- `help.md` (converted from `help.txt`)

**Explicit Reuse From ollamarama-matrix**
- Reuse directly (with minimal edits): `matrix_client.py`, `logging_conf.py`, `handlers/router.py`, handler patterns, history trimming logic, CLI scaffolding, graceful shutdown, and Markdown rendering pattern.
- Adapt: `ollama_client.py` → `llm_client.py` (provider routing and OpenAI-compatible responses), `app.py` tool-call loop and Markdown toggle.
- Include: `fastmcp_client.py` and the AppContext combined-tool logic (schema merging, tool routing). This project will enable MCP if configured.

**Delivery Order (recommended)**
- Skeleton and config → Matrix/security → History → LLM client → Tools package → Handlers → App/CLI → Docs/help → Packaging → Optional Docker/tests → Cutover/removal of old files.

**Acceptance Criteria**
- The repository layout mirrors `ollamarama/` structure.
- All commands work, including `.mymodel` and `.tools`.
- Multi-provider selection works; response/tool-call loop matches current behavior (including `<think>` stripping and Google options handling).
- E2E callbacks function as before; per-user history and model behavior preserved.
- Existing `schema.json` tools are loaded and executed correctly; MCP tools are discovered, merged, and callable when `llm.mcp_servers` is provided.
