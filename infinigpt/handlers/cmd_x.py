from __future__ import annotations

from typing import Any

from ..utils import message_content_to_str


async def handle_x(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    parts = (args or "").split()
    if len(parts) < 2:
        return
    target_display = parts[0]
    message = " ".join(parts[1:])

    target_user = None
    if target_display.startswith("@") and ":" in target_display:
        target_user = target_display
    else:
        for user in list(ctx.history.messages.get(room_id, {}).keys()):  # type: ignore[attr-defined]
            name = await ctx.matrix.display_name(user)
            if name == target_display:
                target_user = user
                break
    if not target_user:
        return
    ctx.history.add(room_id, target_user, "user", message)
    messages = ctx.history.get(room_id, target_user)
    # Per-target model override
    model = ctx.user_models.get(room_id, {}).get(target_user, ctx.model)
    try:
        if getattr(ctx, "tools_enabled", False):
            response_text = await ctx.respond_with_tools(messages, model=model, room_id=room_id)
        else:
            data = {"model": model, "messages": messages}
            if model not in ctx.cfg.llm.models.get("google", []):
                data.update(ctx.options)
            result = await ctx.llm.chat(data)
            response_text = message_content_to_str((result.get("choices", [{}])[0].get("message") or {}))
    except Exception as e:
        try:
            await ctx.matrix.send_text(room_id, "Something went wrong", html=ctx.render("Something went wrong"))
            ctx.log(e)
        except Exception:
            pass
        return
    text = (response_text or "").strip()
    ctx.history.add(room_id, target_user, "assistant", text)
    body = f"**{sender_display}**:\n{text}"
    html = ctx.render(body)
    await ctx.matrix.send_text(room_id, body, html=html)
