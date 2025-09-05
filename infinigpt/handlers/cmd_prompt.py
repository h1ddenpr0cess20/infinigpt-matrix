from __future__ import annotations

from typing import Any

from ..utils import message_content_to_str


async def handle_persona(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    persona = args.strip()
    # Initialize a fresh system prompt using persona
    try:
        ctx.history.init_prompt(room_id, sender_id, persona=persona or ctx.default_personality)
        ctx.log(
            f"System prompt for {sender_display} ({sender_id}) set to '{(ctx.cfg.llm.prompt[0] if ctx.cfg.llm.prompt else 'you are ')}{persona or ctx.default_personality}{(ctx.cfg.llm.prompt[1] if len(ctx.cfg.llm.prompt) > 1 else '.')}"  # noqa: E501
        )
    except Exception:
        pass
    ctx.history.add(room_id, sender_id, "user", "introduce yourself")
    await _respond(ctx, room_id, sender_id, sender_display)


async def handle_custom(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    custom = args.strip()
    if not custom:
        return
    # Replace system prompt with custom text
    try:
        ctx.history.init_prompt(room_id, sender_id, custom=custom)
        ctx.log(f"System prompt for {sender_display} ({sender_id}) set to '{custom}'")
    except Exception:
        pass
    ctx.history.add(room_id, sender_id, "user", "introduce yourself")
    await _respond(ctx, room_id, sender_id, sender_display)


async def _respond(ctx: Any, room_id: str, user_id: str, header_display: str) -> None:
    messages = ctx.history.get(room_id, user_id)
    try:
        data = {"model": ctx.model, "messages": messages}
        if ctx.model not in ctx.cfg.llm.models.get("google", []):
            data.update(ctx.options)
        result = await ctx.llm.chat(data)
    except Exception as e:
        try:
            await ctx.matrix.send_text(room_id, "Something went wrong", html=ctx.render("Something went wrong"))
            ctx.log(e)
        except Exception:
            pass
        return
    response_text = message_content_to_str((result.get("choices", [{}])[0].get("message") or {}))
    # Think markers
    if "</think>" in response_text and "<think>" in response_text:
        try:
            thinking, rest = response_text.split("</think>", 1)
            thinking = thinking.replace("<think>", "").strip()
            response_text = rest
            try:
                ctx.log(f"Model thinking for {header_display} ({user_id}): {thinking}")
            except Exception:
                pass
        except Exception:
            pass
    if "<|begin_of_thought|>" in response_text and "<|end_of_thought|>" in response_text:
        try:
            parts = response_text.split("<|end_of_thought|>")
            if len(parts) > 1:
                thinking = parts[0].replace("<|begin_of_thought|>", "").replace("<|end_of_thought|>", "").strip()
                response_text = parts[1]
                try:
                    ctx.log(f"Model thinking for {header_display} ({user_id}): {thinking}")
                except Exception:
                    pass
        except Exception:
            pass
    if "<|begin_of_solution|>" in response_text and "<|end_of_solution|>" in response_text:
        try:
            response_text = response_text.split("<|begin_of_solution|>", 1)[1].split("<|end_of_solution|>", 1)[0].strip()
        except Exception:
            pass
    response_text = (response_text or "").strip()
    ctx.history.add(room_id, user_id, "assistant", response_text)
    body = f"**{header_display}**:\n{response_text}"
    html = ctx.render(body)
    try:
        ctx.log(f"Sending response to {header_display} in {room_id}: {body}")
    except Exception:
        pass
    await ctx.matrix.send_text(room_id, body, html=html)
