from types import SimpleNamespace

from infinigpt.cli import build_parser


def test_cli_overrides():
    p = build_parser()
    args = p.parse_args([
        "--config", "cfg.json",
        "--log-level", "DEBUG",
        "--model", "gpt-4o",
        "--store-path", "st",
        "--ollama-url", "http://x:11434",
        "--e2e",
    ])
    assert args.config == "cfg.json"
    assert args.log_level == "DEBUG"
    assert args.model == "gpt-4o"
    assert args.store_path == "st"
    assert args.ollama_url.startswith("http://x")
    assert args.e2e is True

