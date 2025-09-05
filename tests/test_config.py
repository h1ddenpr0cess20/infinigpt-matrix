import json
from pathlib import Path

import pytest

from infinigpt.config import load_config, validate_config, AppConfig, LLMConfig, MatrixConfig


def test_load_config_and_validate(tmp_path: Path):
    cfg_data = {
        "llm": {
            "models": {"openai": ["gpt-4o"]},
            "api_keys": {"openai": "X"},
            "default_model": "gpt-4o",
            "personality": "helper",
            "prompt": ["you are ", "."],
            "options": {},
            "history_size": 8,
            "ollama_url": "localhost:11434"
        },
        "matrix": {
            "server": "https://example.org",
            "username": "@bot:example.org",
            "password": "pw",
            "channels": ["!r:example.org"],
            "admin": "@admin:example.org",
            "device_id": "",
            "store_path": "store"
        }
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg_data))
    cfg = load_config(str(p))
    ok, errs = validate_config(cfg)
    assert ok and not errs


def test_validate_config_default_model_missing():
    llm = LLMConfig(models={"openai": []}, api_keys={}, default_model="x", personality="p", prompt=["you are ", "."])
    matrix = MatrixConfig(server="s", username="u", password="p", channels=["!r"], admin="a")
    cfg = AppConfig(llm=llm, matrix=matrix)
    ok, errs = validate_config(cfg)
    assert not ok and errs

