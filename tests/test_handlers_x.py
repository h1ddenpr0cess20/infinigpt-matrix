from types import SimpleNamespace

import pytest

from infinigpt.handlers.cmd_x import handle_x
from infinigpt.history import HistoryStore


class FakeMatrix:
    def __init__(self):
        self.sent = []
        self.names = {}

    async def send_text(self, room_id, body, html=None):
        self.sent.append((room_id, body, html))

    async def display_name(self, user_id):
        return self.names.get(user_id)


class FakeLLM:
    async def chat(self, payload):
        return {"choices": [{"message": {"content": "got it"}}]}


@pytest.mark.asyncio
async def test_x_supports_display_names_with_spaces():
    matrix = FakeMatrix()
    matrix.names = {
        "@john:hs": "John Doe",
        "@jane:hs": "Jane",
    }
    history = HistoryStore("you are ", ".", "helper")
    # Seed both users in room so handle_x can resolve against known participants
    history.init_prompt("!r", "@john:hs")
    history.init_prompt("!r", "@jane:hs")

    ctx = SimpleNamespace(
        history=history,
        matrix=matrix,
        llm=FakeLLM(),
        render=lambda s: None,
        model="gpt-4o",
        cfg=SimpleNamespace(llm=SimpleNamespace(models={"google": []})),
        options={},
        log=lambda *a, **k: None,
        user_models={},
        tools_enabled=False,
    )

    await handle_x(ctx, "!r", "@sender:hs", "Sender", "John Doe hello there")

    assert matrix.sent
    assert matrix.sent[-1][1] == "**Sender**:\ngot it"
    # message should be recorded under John Doe's user thread
    assert history.get("!r", "@john:hs")[-2] == {"role": "user", "content": "hello there"}


@pytest.mark.asyncio
async def test_x_keeps_matrix_id_targeting():
    matrix = FakeMatrix()
    history = HistoryStore("you are ", ".", "helper")
    ctx = SimpleNamespace(
        history=history,
        matrix=matrix,
        llm=FakeLLM(),
        render=lambda s: None,
        model="gpt-4o",
        cfg=SimpleNamespace(llm=SimpleNamespace(models={"google": []})),
        options={},
        log=lambda *a, **k: None,
        user_models={},
        tools_enabled=False,
    )

    await handle_x(ctx, "!r", "@sender:hs", "Sender", "@target:hs hello")

    assert matrix.sent
    assert history.get("!r", "@target:hs")[-2] == {"role": "user", "content": "hello"}
