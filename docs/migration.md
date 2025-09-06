# Migration Notes

InfiniGPT evolved from a single‑file script (`legacy/infinigpt.py`) to a modular package under `infinigpt/`. The new CLI runs the modern implementation and supports config overrides.

## What Changed

- Installed command is `infinigpt-matrix`; module entry `python -m infinigpt` remains available
- Clear separation of concerns: config, Matrix wrapper, handlers, history, LLM client, tools
- Tests and documentation are first‑class

## How To Run (now)

- Start the bot: `infinigpt-matrix --config config.json`

