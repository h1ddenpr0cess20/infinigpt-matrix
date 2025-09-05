import json
import pytest
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from infinigpt.fastmcp_client import FastMCPClient


class FakeTool:
    def __init__(self):
        self.name = "echo"
        self.description = "Echo text"
        self.inputSchema = {"type": "object", "properties": {"text": {"type": "string"}}}


class FakeMCPClient:
    def __init__(self, cfg):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def list_tools(self):
        return [FakeTool()]

    async def call_tool(self, name, arguments):
        class Res:
            def __init__(self, data):
                self.data = data
                self.structured_content = None
                self.content = []
        return Res({"echo": arguments.get("text", "")})


def fake_client(cfg):
    return FakeMCPClient(cfg)


def test_fastmcp_client(monkeypatch):
    monkeypatch.setattr("infinigpt.fastmcp_client.Client", fake_client)
    client = FastMCPClient({"s": {"command": "none"}})
    tools = client.list_tools()
    assert tools[0]["function"]["name"] == "echo"
    data = json.loads(client.call_tool("echo", {"text": "hi"}))
    assert data["echo"] == "hi"


@pytest.mark.asyncio
async def test_fastmcp_client_inside_loop(monkeypatch):
    monkeypatch.setattr("infinigpt.fastmcp_client.Client", fake_client)
    client = FastMCPClient({"s": {"command": "none"}})
    tools = client.list_tools()
    assert tools[0]["function"]["name"] == "echo"
