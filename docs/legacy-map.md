# Legacy → New Mapping

This page maps parts of the archived legacy implementation to their equivalents in the refactored codebase.

## Startup & Runtime

- Legacy `legacy/infinigpt.py: main()` → New `infinigpt/__main__.py` (entry), `infinigpt/cli.py` (flags), `infinigpt/app.py: run()` (compose, login/join/sync).
- Legacy direct `config.json` read → New `infinigpt/config.py` (`load_config`, validation, summarization).
- Legacy logging via `logging.basicConfig` → New `infinigpt/logging_conf.py: setup_logging()`.

## Matrix I/O

- Legacy direct `nio.AsyncClient` usage → New `infinigpt/matrix_client.py: MatrixClientWrapper` (`login`, `join`, `send_text`, `display_name`, `sync_forever`).

## Routing & Commands

- Legacy inline command router → New `infinigpt/handlers/router.py: Router` with `register()` and `dispatch()`.
- Legacy “BotName:” mention handled inline → New router mention path dispatches to `.ai`.

## AI Interaction

- Legacy direct HTTP calls → New `infinigpt/llm_client.py: LLMClient`.

## History & Personas

- Legacy message dict + trim → New `infinigpt/history.py: HistoryStore` (`add`, `get`, `reset`, `init_prompt`, trim).

## User Commands

- Legacy `.ai` / `BotName:` → New `handlers/cmd_ai.py`.
- Legacy `.x` → New `handlers/cmd_x.py`.
- Legacy `.reset` and `.stock` → New `handlers/cmd_reset.py`.
- Legacy `.help` (split by `~~~`) → New `handlers/cmd_help.py`.

## Admin Commands

- Legacy `.model` → New `handlers/cmd_model.py`.
- Legacy `.clear` → New `handlers/cmd_reset.py`.

## Security & E2E

- Legacy verification mixins → New `infinigpt/security.py` (to‑device logging and verification helpers).

## Markdown Rendering

- Legacy inline Markdown → New renderer in application context; wrappers send body+html.

