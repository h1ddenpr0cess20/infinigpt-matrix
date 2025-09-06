import os
import pytest


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    # Ensure tools resolve config from a temp path in tests when needed
    monkeypatch.setenv("INFINIGPT_CONFIG", os.environ.get("INFINIGPT_CONFIG", "config.json"))
    yield

