from __future__ import annotations

from typing import Any


async def handle_x(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Speak as the target user by addressing them explicitly.

    Args:
        ctx: App context.
        room_id: Matrix room ID.
        sender_id: Matrix user ID.
        sender_display: Sender display name.
        args: "<display|@user:server> <message>".
    """
    raw = (args or "").strip()
    if not raw:
        return

    target_user = None
    message = ""

    # Explicit mxid target: ``.x @user:server message``
    if raw.startswith("@"):
        parts = raw.split(maxsplit=1)
        if len(parts) < 2:
            return
        possible_user, rest = parts
        if ":" in possible_user:
            target_user = possible_user
            message = rest

    # Display-name target (supports spaces): choose the longest matching name
    if not target_user:
        candidates = []
        for user in list(ctx.history.messages.get(room_id, {}).keys()):  # type: ignore[attr-defined]
            name = await ctx.matrix.display_name(user)
            if not name:
                continue
            if raw == name:
                candidates.append((len(name), user, name, ""))
            elif raw.startswith(f"{name} "):
                candidates.append((len(name), user, name, raw[len(name) + 1 :]))

        if not candidates:
            return
        _, target_user, _, message = max(candidates, key=lambda c: c[0])
        if not message:
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
            response_text = (result.get("choices", [{}])[0].get("message") or {}).get("content", "")
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
