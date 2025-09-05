from types import SimpleNamespace

from infinigpt.llm_client import resolve_provider
from infinigpt.config import AppConfig, LLMConfig, MatrixConfig


def _cfg():
    llm = LLMConfig(
        models={"openai": ["gpt-4o"], "google": ["gemini-2.0-flash"], "ollama": ["llama3.2"]},
        api_keys={"openai": "X", "google": "Y"},
        default_model="gpt-4o",
        personality="p",
        prompt=["you are ", "."],
    )
    matrix = MatrixConfig(server="s", username="u", password="p", channels=["!r"], admin="a")
    return AppConfig(llm=llm, matrix=matrix)


def test_resolve_provider_urls():
    cfg = _cfg()
    url, _ = resolve_provider("gpt-4o", cfg)
    assert url.endswith("/v1")
    url, _ = resolve_provider("gemini-2.0-flash", cfg)
    assert "v1beta/openai" in url
    url, _ = resolve_provider("llama3.2", cfg)
    assert "http://" in url and ":11434" in url

