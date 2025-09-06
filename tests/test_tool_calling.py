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

