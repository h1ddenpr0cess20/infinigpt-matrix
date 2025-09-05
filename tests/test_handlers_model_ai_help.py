import asyncio
from types import SimpleNamespace

import pytest

from infinigpt.handlers.cmd_model import handle_model
from infinigpt.handlers.cmd_ai import handle_ai
from infinigpt.handlers.cmd_help import handle_help
from infinigpt.history import HistoryStore


class FakeMatrix:
    def __init__(self):
        self.sent = []

    async def send_text(self, room_id, body, html=None):
        self.sent.append((room_id, body, html))


class FakeLLM:
    def __init__(self, text: str):
        self.text = text

    async def chat(self, payload):
        return {"choices": [{"message": {"content": self.text}}]}


@pytest.mark.asyncio
async def test_handle_model_show_set_reset():
    ctx = SimpleNamespace(
        model="gpt-4o",
        default_model="gpt-4o",
        models={"openai": ["gpt-4o", "gpt-4o-mini"], "ollama": ["llama3.2"]},
        render=lambda s: None,
        matrix=FakeMatrix(),
        log=lambda *a, **k: None,
    )
    await handle_model(ctx, "!r", "@u", "Admin", "")
    assert "Current model" in ctx.matrix.sent[-1][1]
    await handle_model(ctx, "!r", "@u", "Admin", "gpt-4o-mini")
    assert ctx.model == "gpt-4o-mini"
    await handle_model(ctx, "!r", "@u", "Admin", "reset")
    assert ctx.model == ctx.default_model


@pytest.mark.asyncio
async def test_handle_ai_strips_think_markers_and_trims():
    content = "<think>plan</think>  Hello  \n"
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=8),
        matrix=FakeMatrix(),
        llm=FakeLLM(content),
        render=lambda s: None,
        model="gpt-4o",
        cfg=SimpleNamespace(llm=SimpleNamespace(models={"google": []})),
        options={},
        log=lambda *a, **k: None,
        user_models={},
        tools_enabled=False,
    )
    await handle_ai(ctx, "!r", "@u", "User", "hello")
    sent_body = ctx.matrix.sent[-1][1]
    assert "<think>" not in sent_body
    assert sent_body.endswith("Hello")


@pytest.mark.asyncio
async def test_handle_help_with_admin_split(monkeypatch, tmp_path):
    help_file = tmp_path / "help.md"
    help_file.write_text("User Help~~~Admin Help")
    monkeypatch.chdir(tmp_path)
    ctx = SimpleNamespace(render=lambda s: None, matrix=FakeMatrix(), admins=["AdminUser"]) 
    # Non-admin receives only first part
    await handle_help(ctx, "!r", "@u", "User", "")
    assert ctx.matrix.sent[-1][1].strip() == "User Help"
    # Admin receives second section too
    ctx.matrix.sent.clear()
    await handle_help(ctx, "!r", "@admin", "AdminUser", "")
    assert len(ctx.matrix.sent) == 2
    assert ctx.matrix.sent[0][1].strip() == "User Help"
    assert ctx.matrix.sent[1][1].strip() == "Admin Help"
