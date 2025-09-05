from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FastMCPClient:
    def __init__(self, servers: Dict[str, Any]) -> None:
        try:
            from fastmcp import Client  # type: ignore
            import mcp.types  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("fastmcp is required for MCP integration") from e
        self._Client = Client
        self._servers = dict(servers or {})
        self._tool_servers: Dict[str, str] = {}
        for name, cfg in list(self._servers.items()):
            if isinstance(cfg, str):
                if cfg.lower() in os.environ:
                    env_cfg = os.environ[cfg]
                    try:
                        self._servers[name] = json.loads(env_cfg)
                    except Exception:
                        self._servers[name] = env_cfg
                else:
                    self._servers[name] = cfg
            elif isinstance(cfg, dict):
                continue
        for name, spec in list(self._servers.items()):
            if isinstance(spec, str) and "://" in spec:
                continue
            if isinstance(spec, dict):
                cmd = spec.get("command")
                args = spec.get("args", [])
                if isinstance(cmd, str):
                    argv = [cmd] + ([str(a) for a in args] if isinstance(args, (list, tuple)) else [])
                    cmdline = " ".join(shlex.quote(p) for p in argv)
                    wrapped = {"command": "bash", "args": ["-lc", f"{cmdline} 2>/dev/null"]}
                    self._servers[name] = wrapped

    async def _list_tools_async(self) -> List[Dict[str, Any]]:
        schema: List[Dict[str, Any]] = []
        Client = self._Client
        for name, cfg in self._servers.items():
            logger.debug("Listing tools from MCP server '%s'", name)
            client = Client({name: cfg})
            try:
                async with client:
                    tools = await client.list_tools()
            except Exception as e:
                logger.error("Failed to list tools from MCP server '%s': %s", name, e)
                continue
            for tool in tools:
                self._tool_servers[tool.name] = name
                schema.append({"type": "function", "function": {"name": tool.name, "description": tool.description or "", "parameters": tool.inputSchema or {"type": "object", "properties": {}, "additionalProperties": False}}})
        return schema

    def _run(self, coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        result: Dict[str, Any] = {}

        def runner() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result["value"] = loop.run_until_complete(coro)
            except Exception as e:
                result["exc"] = e
            finally:
                loop.close()

        import threading

        t = threading.Thread(target=runner)
        t.start()
        t.join()
        if "exc" in result:
            raise result["exc"]
        return result.get("value")

    def list_tools(self) -> List[Dict[str, Any]]:
        return self._run(self._list_tools_async())

    async def _call_tool_async(self, server_name: str, spec: Any, name: str, arguments: Dict[str, Any]) -> Any:
        Client = self._Client
        client = Client({server_name: spec})
        async with client:
            result = await client.call_tool(name, arguments)
        if result.data is not None:
            return result.data
        if result.structured_content is not None:
            return result.structured_content
        texts: List[str] = []
        import mcp.types  # type: ignore
        for block in result.content:
            if isinstance(block, mcp.types.TextContent):
                texts.append(block.text)
        return {"result": "\n".join(texts)}

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        server_name = self._tool_servers.get(name)
        if server_name is None:
            return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
        cfg = self._servers.get(server_name)
        try:
            data = self._run(self._call_tool_async(server_name, cfg, name, arguments))
        except Exception as e:
            return json.dumps({"error": f"Tool execution error for {name}: {e}"}, ensure_ascii=False)
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return json.dumps({"result": str(data)}, ensure_ascii=False)

    def close(self) -> None:
        """No-op close for symmetry; kept for future compatibility."""
        return None

__all__ = ["FastMCPClient"]
