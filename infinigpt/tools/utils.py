from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any


def get_time(timezone_name: str = "UTC") -> Dict[str, Any]:
    """Return the current time for a given timezone.

    Args:
        timezone_name: "UTC", "local", or an IANA tz database name.

    Returns:
        Dict with ISO datetime and a timezone label, or an error message.
    """
    tz = (timezone_name or "UTC").strip()
    if tz.upper() == "UTC":
        return {"datetime": datetime.now(timezone.utc).isoformat(), "timezone": "UTC"}
    if tz.lower() == "local":
        return {"datetime": datetime.now().isoformat(), "timezone": "local"}
    try:
        from zoneinfo import ZoneInfo  # type: ignore

        return {"datetime": datetime.now(ZoneInfo(tz)).isoformat(), "timezone": tz}
    except Exception:
        return {"error": f"Unsupported timezone '{tz}'. Use 'UTC' or 'local'."}
