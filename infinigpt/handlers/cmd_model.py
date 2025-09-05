from __future__ import annotations

from typing import Any


async def handle_model(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Admin: set or display the global model.

    Args:
        ctx: App context.
        room_id: Matrix room ID.
        sender_id: Matrix user ID.
        sender_display: Sender display name.
        args: Desired model or "reset" to default; blank to show.
    """
    arg = (args or "").strip()
    if not arg:
        keys = []
        try:
            keys = sorted([m for v in ctx.models.values() for m in v])
        except Exception:
            pass
        body = f"**Current model**: {ctx.model}\n**Available models**: {', '.join(keys)}"
        html = ctx.render(body)
        await ctx.matrix.send_text(room_id, body, html=html)
        return
    if arg == "reset":
        ctx.model = ctx.default_model
        ctx.log(f"Model set to {ctx.model}")
    else:
        # verify exists in any provider list
        for models in ctx.models.values():
            if arg in models:
                ctx.model = arg
                break
    body = f"Model set to **{ctx.model}**"
    ctx.log(body)
    html = ctx.render(body)
    await ctx.matrix.send_text(room_id, body, html=html)
