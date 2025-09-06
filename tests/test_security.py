import asyncio
from types import SimpleNamespace

import pytest

from infinigpt.security import Security


class FakeMatrix:
    def __init__(self):
        self.client = SimpleNamespace()


@pytest.mark.asyncio
async def test_security_allows_devices_noop():
    sec = Security(FakeMatrix())
    await sec.allow_devices("@u:example.org")

