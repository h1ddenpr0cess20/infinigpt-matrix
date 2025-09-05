from __future__ import annotations

from typing import Any


async def handle_verbose(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Toggle or display the bot's verbose mode setting.

    Args:
        ctx: App context.
        room_id: Matrix room ID.
        sender_id: Matrix user ID.
        sender_display: Sender display name.
        args: Command argument: on/off/toggle/status.
    """
    arg = (args or "").strip().lower()
    if arg in ("", "status"):
        state = "ON" if getattr(ctx, "verbose", False) else "OFF"
        body = f"Verbose mode is **{state}**"
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return

    new_state: bool | None = None
    if arg in ("on", "true", "1", "enable", "enabled"):
        new_state = True
    elif arg in ("off", "false", "0", "disable", "disabled"):
        new_state = False
    elif arg in ("toggle", "switch"):
        new_state = not bool(getattr(ctx, "verbose", False))
    else:
        body = "Usage: .verbose [on|off|toggle]"
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return

    ctx.verbose = bool(new_state)
    # Optional: if your history store supports verbosity, update it here
    try:
        if hasattr(ctx.history, "set_verbose"):
            ctx.history.set_verbose(ctx.verbose)
    except Exception:
        pass
    state = "ON" if ctx.verbose else "OFF"
    body = f"Verbose mode set to **{state}**"
    await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
