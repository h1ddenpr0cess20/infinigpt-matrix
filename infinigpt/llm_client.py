from __future__ import annotations

import json
from typing import Dict, Any, Tuple

import httpx

from .config import AppConfig


def resolve_provider(model: str, cfg: AppConfig) -> Tuple[str, str]:
    """Return (base_url, bearer) for the selected model based on provider lists."""
    llm = cfg.llm
    if model in llm.models.get("openai", []):
        return ("https://api.openai.com/v1", llm.api_keys.get("openai", ""))
    if model in llm.models.get("xai", []):
        return ("https://api.x.ai/v1", llm.api_keys.get("xai", ""))
    if model in llm.models.get("google", []):
        # Google OpenAI-compatible
        return ("https://generativelanguage.googleapis.com/v1beta/openai", llm.api_keys.get("google", ""))
    if model in llm.models.get("mistral", []):
        return ("https://api.mistral.ai/v1", llm.api_keys.get("mistral", ""))
    if model in llm.models.get("anthropic", []):
        return ("https://api.anthropic.com/v1", llm.api_keys.get("anthropic", ""))
    if model in llm.models.get("ollama", []):
        return (f"http://{llm.ollama_url}/v1", "hello_friend")
    if model in llm.models.get("lmstudio", []):
        return (f"http://{llm.lmstudio_url}/v1", "hello_friend")
    # Fallback: treat as OpenAI-compatible if unknown
    return ("https://api.openai.com/v1", llm.api_keys.get("openai", ""))


class LLMClient:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    async def chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a chat.completions call with standardized provider routing.

        Expects keys: model, messages, tools (optional), options (already merged for non-Google).
        """
        model = payload["model"]
        base_url, bearer = resolve_provider(model, self.cfg)
        url = f"{base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.cfg.llm.timeout)) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            return res.json()
