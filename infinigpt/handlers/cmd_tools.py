from __future__ import annotations

from typing import Any


async def handle_tools(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    arg = (args or "").strip().lower()
    if arg in ("", "status"):
        state = "enabled" if getattr(ctx, "tools_enabled", False) else "disabled"
        body = f"Tools are currently {state}"
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return
    if arg in ("on", "enable", "enabled"):
        ctx.tools_enabled = True
    elif arg in ("off", "disable", "disabled"):
        ctx.tools_enabled = False
    else:
        ctx.tools_enabled = not bool(getattr(ctx, "tools_enabled", False))
    state = "enabled" if ctx.tools_enabled else "disabled"
    body = f"Tools are now {state}"
    await ctx.matrix.send_text(room_id, body, html=ctx.render(body))

