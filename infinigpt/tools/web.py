import httpx
import json
import os


def openai_search(query: str) -> str:
    """Perform an OpenAI web search and return the raw JSON response.

    Args:
        query: Search query.

    Returns:
        JSON string response or a JSON-encoded error.
    """
    url = "https://api.openai.com/v1/chat/completions"
    # Prefer env var, else read from config file path
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        try:
            from pathlib import Path
            cfg_path = os.environ.get("INFINIGPT_CONFIG") or os.environ.get("INFINIGPT_CONFIG_PATH") or "config.json"
            import json as _json
            cfg = _json.loads(Path(cfg_path).read_text())
            openai_key = cfg.get("llm", {}).get("api_keys", {}).get("openai", "")
        except Exception:
            openai_key = ""
    if not openai_key:
        return json.dumps({"error": "Missing OpenAI API key (OPENAI_API_KEY or llm.api_keys.openai)"})
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {openai_key}"}
    data = {
        "model": "gpt-4o-mini-search-preview",
        "messages": [{"role": "user", "content": query}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "search_results",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "total_results": {"type": "number"},
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "snippet": {"type": "string"},
                                },
                                "required": ["title", "url", "snippet"],
                                "additionalProperties": False,
                            },
                        },
                        "timestamp": {"type": "string"},
                    },
                    "required": ["query", "total_results", "results", "timestamp"],
                    "additionalProperties": False,
                },
            },
        },
        "web_search_options": {
            "search_context_size": "medium",
            "user_location": {"type": "approximate", "approximate": {"country": "", "timezone": "America/New_York"}},
        },
        "store": False,
    }
    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=data, timeout=60)
        try:
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"HTTP error: {e.response.status_code} - {e.response.text}"})
        except Exception as e:
            return json.dumps({"error": f"Unexpected: {str(e)}"})


def fetch_url(url: str, max_bytes: int = 65536) -> dict:
    """Fetch a URL and return text content with truncation.

    Args:
        url: HTTP/HTTPS URL to fetch.
        max_bytes: Maximum number of UTF-8 bytes to return.

    Returns:
        Dict with url, status, content, truncated flag; or error.
    """
    try:
        with httpx.Client() as client:
            resp = client.get(url, timeout=20)
            resp.raise_for_status()
            text = resp.text
            encoded = text.encode("utf-8")
            truncated = False
            if len(encoded) > max_bytes:
                text = encoded[:max_bytes].decode("utf-8", errors="ignore")
                truncated = True
            return {
                "url": url,
                "status": resp.status_code,
                "content": text,
                "truncated": truncated,
            }
    except httpx.HTTPError as e:
        return {"error": f"Request failed: {e}"}
