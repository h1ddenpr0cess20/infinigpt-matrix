from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests

from .exceptions import NetworkError, RuntimeFailure


class OpenAIClient:
    """HTTP client for the OpenAI Chat Completions API.

    This client is synchronous; when used from async code run calls in a thread
    executor (e.g. ``asyncio.to_thread``) to avoid blocking the event loop.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 180,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = int(timeout)
        self._session = session or requests.Session()
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"
        self._session.headers.setdefault("Content-Type", "application/json")

    # ---- Public API ----
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Send a chat request and return the parsed JSON response."""
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if options:
            payload.update(options)
        if stream:
            payload["stream"] = True
        try:
            resp = self._session.post(url, json=payload, timeout=(self.timeout if timeout is None else int(timeout)))
            resp.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e))
        try:
            data = resp.json()
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from OpenAI: {e}")
        return data

    def chat_with_tools(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: str,
        options: Optional[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: Optional[str] = "auto",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"model": model, "messages": messages, "tools": tools}
        if options:
            payload.update(options)
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        url = f"{self.base_url}/chat/completions"
        try:
            resp = self._session.post(url, json=payload, timeout=(self.timeout if timeout is None else int(timeout)))
            resp.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e))
        try:
            return resp.json()
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from OpenAI: {e}")

    def health(self) -> bool:
        """Best-effort health check against the OpenAI API."""
        try:
            r = self._session.get(f"{self.base_url}/models", timeout=5)
            return r.ok
        except requests.RequestException:
            return False

    def list_models(self) -> Dict[str, str]:
        """Return a mapping of available model names from the server."""
        url = f"{self.base_url}/models"
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise NetworkError(str(e))
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from OpenAI: {e}")
        models: Dict[str, str] = {}
        items = data.get("data", []) if isinstance(data, dict) else []
        for item in items:
            name = item.get("id") if isinstance(item, dict) else None
            if isinstance(name, str):
                models[name] = name
        return models
