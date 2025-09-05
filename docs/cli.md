# CLI Reference

Use the installed command (preferred):

`infinigpt-matrix [flags]`

Or run the module directly:

`python -m infinigpt [flags]`

## Flags

- `-c, --config PATH`: Path to `config.json` (default: `./config.json`).
- `-L, --log-level LEVEL`: `DEBUG|INFO|WARNING|ERROR|CRITICAL` (colored Rich logs). Default comes from `INFINIGPT_LOG_LEVEL` if set.
- `-v, --verbose`: Enable verbose mode (omit brevity clause from system prompt for new conversations).
- Overrides:
  - `-E, --e2e` / `-N, --no-e2e`
  - `-m, --model`
  - `-s, --store-path`
  - `-u, --ollama-url`
  - `--lmstudio-url`
  - `-S, --server-models` (present for parity; currently a no‑op)

## Examples

- Run with a specific config:
  - `infinigpt-matrix --config config.json`
- Increase verbosity:
  - `INFINIGPT_LOG_LEVEL=DEBUG infinigpt-matrix --config config.json`

## Exit Codes

- 0: OK
- 2: Configuration error or file load failure
