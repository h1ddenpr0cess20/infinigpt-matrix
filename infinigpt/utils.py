from __future__ import annotations

from typing import Any, Dict, List


def message_content_to_str(message: Dict[str, Any]) -> str:
    """Extract a text string from an LLM message content field.

    Providers like Google may return content as a list of parts instead of a
    plain string. This helper normalizes those variants into a single string
    so that callers can treat responses uniformly.
    """
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text") or part.get("content")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    if isinstance(content, dict):
        parts = content.get("parts")
        if isinstance(parts, list):
            return "".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in parts
            )
    return str(content) if content is not None else ""
