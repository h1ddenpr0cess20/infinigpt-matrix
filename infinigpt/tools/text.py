from __future__ import annotations

import re
from typing import Dict, Any


def text_stats(text: str) -> Dict[str, Any]:
    """Return basic statistics for a block of text.

    Args:
        text: Input text.

    Returns:
        Dict with counts for words, characters, and sentences.
    """
    if not isinstance(text, str) or not text.strip():
        return {"words": 0, "characters": 0, "sentences": 0}
    words = re.findall(r"\b\w+\b", text)
    sentences = re.findall(r"[.!?]+", text)
    return {
        "words": len(words),
        "characters": len(text),
        "sentences": len(sentences),
    }
