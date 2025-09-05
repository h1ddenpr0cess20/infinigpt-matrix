from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import List, Optional

from .logging_conf import setup_logging
from .config import load_config
from .app import run as run_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="infinigpt-matrix", description="InfiniGPT Matrix bot (modular)", add_help=True)
    parser.add_argument("-L", "--log-level", default=os.getenv("INFINIGPT_LOG_LEVEL", "INFO"), choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    parser.add_argument("-c", "--config", help="Path to config.json (default: ./config.json)")
    parser.add_argument("-E", "--e2e", action="store_true", help="Enable end-to-end encryption (overrides config)")
    parser.add_argument("-N", "--no-e2e", action="store_true", help="Disable end-to-end encryption (overrides config)")
    parser.add_argument("-m", "--model", help="Override default model")
    parser.add_argument("-s", "--store-path", help="Override store path")
    parser.add_argument("-u", "--ollama-url", help="Override Ollama base URL (llm.ollama_url)")
    parser.add_argument("--lmstudio-url", help="Override LM Studio base URL (llm.lmstudio_url)")
    parser.add_argument("-S", "--server-models", action="store_true", help="(noop) present for parity; ignored")
    parser.add_argument("-v", "--verbose", dest="verbose_mode", action="store_true", help="Enable verbose mode (omit brevity clause)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(args.log_level)
    # Export config path so tools can discover API keys without direct cfg wiring
    os.environ["INFINIGPT_CONFIG"] = args.config or "config.json"
    cfg = load_config(args.config)
    # Apply overrides
    if args.model:
        try:
            cfg.llm.default_model = args.model
        except Exception:
            pass
    if args.store_path:
        try:
            cfg.matrix.store_path = args.store_path
        except Exception:
            pass
    if args.ollama_url:
        try:
            cfg.llm.ollama_url = args.ollama_url
        except Exception:
            pass
    if args.lmstudio_url:
        try:
            cfg.llm.lmstudio_url = args.lmstudio_url
        except Exception:
            pass
    if args.e2e:
        try:
            cfg.matrix.e2e = True
        except Exception:
            pass
    if args.no_e2e:
        try:
            cfg.matrix.e2e = False
        except Exception:
            pass
    logging.getLogger(__name__).info(
        "Loaded config. Providers: %s; Default model: %s",
        ", ".join([k for k, v in cfg.llm.models.items() if v]),
        cfg.llm.default_model,
    )
    asyncio.run(run_app(cfg, config_path=args.config or "config.json"))
    return 0
