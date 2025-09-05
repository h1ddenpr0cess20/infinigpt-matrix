from __future__ import annotations

from typing import Any


async def handle_mymodel(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Show or set a per-user model for the current room.

    Args:
        ctx: App context.
        room_id: Matrix room ID.
        sender_id: Matrix user ID.
        sender_display: Sender display name.
        args: Argument string; if present, desired model name.
    """
    model = (args or "").strip()
    if not model:
        # Show current and available
        user_model = ctx.user_models.get(room_id, {}).get(sender_id, ctx.model)
        models = ", ".join([m for v in ctx.models.values() for m in v])
        body = f"**Your current model**: {user_model}\n**Available models**: {models}"
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return
    # Restrict Ollama per-user
    ollama_models = ctx.models.get("ollama", [])
    if model in ollama_models and not (ctx.model in ollama_models and model == ctx.model):
        body = "You cannot set an Ollama model unless it matches the current global model. Please ask an admin to change the global model first."
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return
    # Restrict LM Studio per-user (same rule as Ollama)
    lmstudio_models = ctx.models.get("lmstudio", [])
    if model in lmstudio_models and not (ctx.model in lmstudio_models and model == ctx.model):
        body = "You cannot set an LM Studio model unless it matches the current global model. Please ask an admin to change the global model first."
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return
    for models in ctx.models.values():
        if model in models:
            if room_id not in ctx.user_models:
                ctx.user_models[room_id] = {}
            ctx.user_models[room_id][sender_id] = model
            ctx.log(f"Model for {sender_display} ({sender_id}) in {room_id} set to {model}")
            body = f"Model for {sender_display} set to {model}"
            await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
            return
    models = ", ".join([m for v in ctx.models.values() for m in v])
    body = f"Model '{model}' not found. Available: {models}"
    await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
