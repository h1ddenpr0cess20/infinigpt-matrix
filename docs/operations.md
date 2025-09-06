# Operations & Security

## Encryption (E2E)

- E2E requires `matrix-nio[e2e]` and `libolm`. When unavailable, run without E2E.
- Toggle with CLI flags `--e2e` / `--no-e2e` or via `matrix.e2e` in config.
- Persist the `store/` directory between runs to retain device keys; treat it as sensitive.
- See also: device verification details in `docs/verification.md`.

## Running the Bot

- Start: `infinigpt-matrix --config config.json`
- Log level: `--log-level DEBUG` or env `INFINIGPT_LOG_LEVEL=DEBUG`

### Logging

- Uses Rich for colorful logs and rich tracebacks by default.
- A Matrix‑aware highlighter emphasizes display names, room IDs, and response sections.

### Graceful Exit

- Stop the bot with Ctrl‑C (SIGINT) or send SIGTERM.
- The bot cancels the sync loop, logs out, closes the Matrix client, and shuts down worker threads.

## Health & Model

- Use `.model` to check current/available models and to change or reset.
- Optional: set `--ollama-url` if your Ollama API is remote.
- The `-S/--server-models` flag exists for parity but is currently a no‑op in InfiniGPT.

## Security Guidelines

- Do not commit secrets. Keep `config.json` local and redacted in tickets.
- Validate inputs; never echo credentials.
- Restrict bot admin to trusted Matrix IDs via `matrix.admins`.

## Troubleshooting

- No replies: verify the bot joined the room and providers are reachable.
- E2E issues: ensure `libolm` is installed; try running without E2E to isolate.
- Model errors: confirm the model exists for the selected provider and any required keys are set.
- Markdown rendering problems: set `"markdown": false` to isolate.

