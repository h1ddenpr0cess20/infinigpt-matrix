import pytest

from infinigpt.handlers.cmd_reset import handle_reset
from infinigpt.history import HistoryStore


class Ctx:
    def __init__(self):
        # Mirror reference prompt handling
        self.history = HistoryStore(prompt_prefix="you are ", prompt_suffix=".", personality="helper", max_items=8)
        self.bot_id = "Bot"
        self._sent = []

    def render(self, body):
        return None

    async def matrix_send(self, room_id, body, html=None):
        self._sent.append(body)

    @property
    def matrix(self):
        class M:
            def __init__(self, outer):
                self._o = outer

            async def send_text(self, room_id, body, html=None):
                await self._o.matrix_send(room_id, body, html)

        return M(self)

    def log(self, *a, **k):
        pass


@pytest.mark.asyncio
async def test_reset_seeds_default_persona():
    ctx = Ctx()
    room = "!r"
    user = "@u"
    # Call reset without stock
    await handle_reset(ctx, room, user, "User", "")
    msgs = ctx.history.get(room, user)
    assert msgs and msgs[0]["role"] == "system"
    assert msgs[0]["content"].startswith("you are ")

