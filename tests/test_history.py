from infinigpt.history import HistoryStore


def test_history_prompt_and_trim():
    hs = HistoryStore("you are ", ".", "helper", max_items=5)
    room = "!r:server"
    user = "@u:server"
    msgs = hs.get(room, user)
    assert msgs[0]["role"] == "system"
    for i in range(10):
        hs.add(room, user, "user", f"m{i}")
    msgs = hs.get(room, user)
    assert len(msgs) <= 5
    assert msgs[0]["role"] in ("system", "user")

