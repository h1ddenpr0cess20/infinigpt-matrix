import asyncio
from types import SimpleNamespace

import pytest

from infinigpt.app import AppContext
from infinigpt.config import AppConfig, LLMConfig, MatrixConfig


class FakeLLM:
    def __init__(self):
        self.calls = 0

    async def chat(self, payload):
        self.calls += 1
        if self.calls == 1:
            # Return one tool call to calculate 2+2
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "t1",
                                    "function": {"name": "calculate_expression", "arguments": "{\"expression\": \"2+2\"}"},
                                }
                            ]
                        }
                    }
                ]
            }
        # Final message
        return {"choices": [{"message": {"content": "Result is 4"}}]}


class CaptureLLM:
    def __init__(self, response):
        self.response = response
        self.payloads = []

    async def chat(self, payload):
        self.payloads.append(payload)
        return self.response


@pytest.mark.asyncio
async def test_tool_loop_executes_and_completes(monkeypatch):
    cfg = AppConfig(
        llm=LLMConfig(models={"openai": ["gpt-4o"]}, api_keys={}, default_model="gpt-4o", personality="p", prompt=["you are ", "."]),
        matrix=MatrixConfig(server="s", username="u", password="p", channels=["!r"], admins=[]),
    )
    ctx = AppContext(cfg)
    # Replace LLM with fake
    ctx.llm = FakeLLM()
    messages = [{"role": "system", "content": "you are p."}]
    out = await ctx.respond_with_tools(messages, room_id="!r")
    assert "Result is 4" in out


@pytest.mark.asyncio
async def test_google_list_content(monkeypatch):
    cfg = AppConfig(
        llm=LLMConfig(
            models={"google": ["gemini-2.0-flash"]},
            api_keys={},
            default_model="gemini-2.0-flash",
            personality="p",
            prompt=["you are ", "."],
        ),
        matrix=MatrixConfig(server="s", username="u", password="p", channels=["!r"], admins=[]),
    )
    ctx = AppContext(cfg)
    fake_llm = CaptureLLM({"choices": [{"message": {"content": [{"type": "text", "text": "ok"}]}}]})
    ctx.llm = fake_llm
    messages = [{"role": "system", "content": "you are p."}]
    out = await ctx.respond_with_tools(messages, room_id="!r")
    assert out == "ok"

