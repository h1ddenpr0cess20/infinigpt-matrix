from __future__ import annotations

from typing import Any


async def handle_ai(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Primary chat command: add user text and reply with model output.

    Args:
        ctx: App context.
        room_id: Matrix room ID.
        sender_id: Matrix user ID.
        sender_display: Sender display name.
        args: Optional text to add before generating a reply.
    """
    history = ctx.history
    matrix = ctx.matrix
    if args:
        history.add(room_id, sender_id, "user", args)
    messages = history.get(room_id, sender_id)
    # Per-user model override
    model = ctx.user_models.get(room_id, {}).get(sender_id, ctx.model)
    try:
        if getattr(ctx, "tools_enabled", False):
            response_text = await ctx.respond_with_tools(messages, model=model, room_id=room_id)
        else:
            data = {"model": model, "messages": messages}
            if model not in ctx.cfg.llm.models.get("google", []):
                data.update(ctx.options)
            result = await ctx.llm.chat(data)
            response_text = (result.get("choices", [{}])[0].get("message") or {}).get("content", "")
    except Exception as e:
        try:
            await matrix.send_text(room_id, "Something went wrong", html=ctx.render("Something went wrong"))
            ctx.log(e)
        except Exception:
            pass
        return
    # Strip think tags
    text = response_text or ""
    if "</think>" in text and "<think>" in text:
        try:
            thinking, rest = text.split("</think>", 1)
            thinking = thinking.replace("<think>", "").strip()
            ctx.log(f"Model thinking for {sender_display} ({sender_id}): {thinking}")
            text = rest
        except Exception:
            pass
    if "<|begin_of_thought|>" in text and "<|end_of_thought|>" in text:
        try:
            parts = text.split("<|end_of_thought|>")
            if len(parts) > 1:
                thinking = parts[0].replace("<|begin_of_thought|>", "").replace("<|end_of_thought|>", "").strip()
                ctx.log(f"Model thinking for {sender_display} ({sender_id}): {thinking}")
                text = parts[1]
        except Exception:
            pass
    if "<|begin_of_solution|>" in text and "<|end_of_solution|>" in text:
        try:
            text = text.split("<|begin_of_solution|>", 1)[1].split("<|end_of_solution|>", 1)[0].strip()
        except Exception:
            pass
    text = text.strip()
    history.add(room_id, sender_id, "assistant", text)
    body = f"**{sender_display}**:\n{text}"
    html = ctx.render(body)
    try:
        ctx.log(f"Sending response to {sender_display} in {room_id}: {body}")
    except Exception:
        pass
    await matrix.send_text(room_id, body, html=html)
