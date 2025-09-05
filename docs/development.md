# Development Guide

## Project Structure

- Core bot: `infinigpt/` package (Matrix client wrapper, handlers, router, LLM client).
- Config: `config.json` (Matrix creds, providers, models).
- Help text: `help.md` (user/admin commands shown in chat; split by `~~~`).
- Runtime data: `store/` (Matrix E2E state/keys), created automatically.
- Docs: `docs/` (overview, guides, references).

## Local Setup

- Install: `pip install -r requirements.txt`
- Run: `python -m infinigpt --config config.json`
- Optional linters: `ruff check .` and `black .`

## Coding Style

- PEP 8; 4‑space indentation; line length ≈ 100–120 chars.
- Names: functions/vars `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- Prefer small async functions and pure helpers.
- Public functions should have docstrings and types where practical.
- Avoid wildcard imports; use the provided logger.

## Testing

- Framework: `pytest`. Tests live under `tests/` and follow `test_*.py`.
- Mock external I/O (`nio.AsyncClient`, HTTP calls to providers).
- Target unit tests around:
  - Message parsing and router behavior
  - History trim/initialization
  - Model switching and prompt handling

## Security & Configuration

- Do not commit secrets. Keep `config.json` out of version control.
- Keep provider URLs configurable; default to sane local values where applicable.
- Treat `store/` contents as sensitive if E2E is enabled.

## Contributing

- Use scoped, imperative commit messages (e.g., `fix: handle .x mentions`).
- Describe user impact and update docs/help when commands/flags change.

