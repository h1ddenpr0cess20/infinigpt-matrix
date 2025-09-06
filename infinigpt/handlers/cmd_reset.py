from __future__ import annotations

from typing import Any


async def handle_reset(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Reset a user's history to stock or default prompt.

    Args:
        ctx: App context.
        room_id: Matrix room ID.
        sender_id: Matrix user ID.
        sender_display: Sender display name.
        args: "stock" to clear, else reset to default persona.
    """
    stock = args.strip().lower() == "stock"
    # Match reference behavior: reset history; if not stock, seed default persona
    try:
        ctx.history.reset(room_id, sender_id, stock=stock)
    except Exception:
        # Fallback to clear if reset not available
        ctx.history.clear(room_id, sender_id)
    if stock:
        body = f"Stock settings applied for {sender_display}"
        try:
            ctx.log(f"Stock settings applied for {sender_display} in {room_id}")
        except Exception:
            pass
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
    else:
        body = f"{ctx.bot_id} reset to default for {sender_display}"
        try:
            ctx.log(f"{ctx.bot_id} reset to default for {sender_display} in {room_id}")
        except Exception:
            pass
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))


async def handle_clear(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Admin: clear all histories and reset bot defaults.

    Clears conversation history for all rooms/users and restores the default
    model and personality.
    """
    try:
        ctx.history.clear_all()
    except Exception:
        pass
    ctx.model = ctx.default_model
    ctx.personality = ctx.default_personality
    body = "Bot has been reset for everyone"
    await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
