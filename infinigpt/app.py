from __future__ import annotations

import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from .config import AppConfig
from .history import HistoryStore
from .matrix_client import MatrixClientWrapper
from .llm_client import LLMClient
from .handlers.router import Router
from .handlers.cmd_ai import handle_ai
from .handlers.cmd_model import handle_model
from .handlers.cmd_reset import handle_reset, handle_clear
from .handlers.cmd_help import handle_help
from .handlers.cmd_prompt import handle_persona, handle_custom
from .handlers.cmd_x import handle_x
from .handlers.cmd_tools import handle_tools
from .handlers.cmd_mymodel import handle_mymodel
from .security import Security
from .fastmcp_client import FastMCPClient
from .tools import execute_tool, load_schema


class AppContext:
    def __init__(self, cfg: AppConfig, executor: Optional[ThreadPoolExecutor] = None) -> None:
        self.cfg = cfg
        self.executor = executor or ThreadPoolExecutor(max_workers=4, thread_name_prefix="infinigpt")
        self.logger = logging.getLogger(__name__)
        self.log = self.logger.info

        self.matrix = MatrixClientWrapper(
            server=cfg.matrix.server,
            username=cfg.matrix.username,
            password=cfg.matrix.password,
            device_id=cfg.matrix.device_id,
            store_path=cfg.matrix.store_path,
            encryption_enabled=bool(getattr(cfg.matrix, "e2e", True)),
        )
        # History: match reference behavior using prefix/suffix/personality
        prompt = list(cfg.llm.prompt or ["you are ", "."])
        prefix = prompt[0] if len(prompt) >= 1 else "you are "
        suffix = prompt[1] if len(prompt) >= 2 else "."
        extra = prompt[2] if len(prompt) >= 3 else ""
        self.history = HistoryStore(
            prompt_prefix=prefix,
            prompt_suffix=suffix,
            personality=cfg.llm.personality,
            prompt_suffix_extra=extra,
            max_items=cfg.llm.history_size,
        )
        # Model and options
        self.models = cfg.llm.models
        self.default_model = cfg.llm.default_model
        self.model = cfg.llm.default_model
        self.default_personality = cfg.llm.personality
        self.personality = cfg.llm.personality
        self.options = cfg.llm.options
        self.timeout = cfg.llm.timeout
        try:
            self.admins = list(getattr(cfg.matrix, "admins", []))
        except Exception:
            self.admins = []
        self.bot_id = "InfiniGPT"
        self.user_models: Dict[str, Dict[str, str]] = {}

        # LLM client
        self.llm = LLMClient(cfg)

        # Tools
        self.tools_enabled: bool = True
        self.mcp_client: FastMCPClient | None = None
        self._mcp_tool_names: set[str] = set()
        try:
            builtin_schema = load_schema()
        except Exception:
            self.logger.exception("Failed to load builtin tools schema")
            builtin_schema = []
        mcp_schema: List[Dict[str, Any]] = []
        if cfg.llm.mcp_servers:
            self.logger.info("MCP servers configured: %s", list(cfg.llm.mcp_servers.keys()))
            successful: Dict[str, Any] = {}
            for name, spec in cfg.llm.mcp_servers.items():
                if not spec:
                    continue
                try:
                    client = FastMCPClient({name: spec})
                    tools = client.list_tools()
                    self.logger.info("MCP server '%s' returned %d tool(s)", name, len(tools))
                    successful[name] = spec
                    mcp_schema.extend(tools)
                    for tool in tools:
                        fn = (tool.get("function") or {}).get("name")
                        if isinstance(fn, str):
                            self._mcp_tool_names.add(fn)
                except Exception:
                    self.logger.exception("Failed to list tools from MCP server '%s'", name)
                    continue
            if successful:
                try:
                    self.mcp_client = FastMCPClient(successful)
                    _ = self.mcp_client.list_tools()
                except Exception:
                    self.logger.exception("Failed to initialize consolidated MCP client")
                    self.mcp_client = None
        combined: List[Dict[str, Any]] = list(mcp_schema)
        for tool in builtin_schema:
            fn = (tool.get("function") or {}).get("name")
            if isinstance(fn, str) and fn not in self._mcp_tool_names:
                combined.append(tool)
        self.tools_schema = combined
        if not self.tools_schema:
            self.tools_enabled = False
            self.logger.info("Tool calling disabled: no tools available")
        else:
            self.logger.info(
                "Tool calling enabled with %d tools (%d MCP, %d builtin)",
                len(self.tools_schema),
                len(mcp_schema),
                len(self.tools_schema) - len(mcp_schema),
            )

    async def to_thread(self, fn, *args, **kwargs) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, lambda: fn(*args, **kwargs))

    def render(self, body: str) -> Optional[str]:
        if not self.cfg.markdown:
            return None
        try:
            import markdown as _md
            return _md.markdown(body, extensions=["extra", "fenced_code", "nl2br", "sane_lists", "tables", "codehilite"])
        except Exception:
            return None

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        try:
            _args_str = json.dumps(arguments or {}, ensure_ascii=False, default=str)
        except Exception:
            _args_str = str(arguments)
        if len(_args_str) > 800:
            _args_str = _args_str[:800] + "…"
        if self.mcp_client is not None and name in self._mcp_tool_names:
            self.logger.info("Tool (MCP): %s args=%s", name, _args_str)
            return self.mcp_client.call_tool(name, arguments)
        self.logger.info("Tool (builtin): %s args=%s", name, _args_str)
        return execute_tool(name, arguments)

    async def respond_with_tools(self, messages: List[Dict[str, Any]], *, model: Optional[str] = None, room_id: Optional[str] = None, tool_choice: str | None = "auto") -> str:
        use_model = model or self.model
        data: Dict[str, Any] = {
            "model": use_model,
            "messages": messages,
            "tools": self.tools_schema,
            "tool_choice": tool_choice,
        }
        # if use_model not in self.cfg.llm.models.get("google", []):
        #     data.update(self.options)
        try:
            result = await self.llm.chat(data)
        except Exception:
            self.logger.exception("Initial chat with tools failed")
            return ""
        max_iterations = 8
        iterations = 0
        while iterations < max_iterations:
            msg = (result.get("choices", [{}])[0].get("message") or {})
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                break
            try:
                self.logger.info("Model requested %d tool call(s)", len(tool_calls))
            except Exception:
                pass
            messages.append(msg)
            for call in tool_calls:
                func = (call.get("function") or {})
                name = func.get("name") or ""
                raw_args = func.get("arguments")
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) and raw_args.strip() else (raw_args or {})
                except Exception:
                    self.logger.exception("Failed to parse tool arguments for '%s'", name)
                    args = {}
                tool_result = self._execute_tool(name, args)
                # Attempt to detect file-returning tools (.png) and upload
                try:
                    parsed = json.loads(tool_result)
                    path_value = None
                    if isinstance(parsed, dict):
                        path_value = parsed.get("result") or parsed.get("path")
                    if isinstance(path_value, str) and path_value.lower().endswith(".png"):
                        if room_id:
                            try:
                                await self.matrix.send_image(room_id=room_id, path=path_value, filename=None, log=self.logger.info)  # type: ignore
                            except Exception:
                                pass
                except Exception:
                    pass
                tool_msg: Dict[str, Any] = {"role": "tool", "content": str(tool_result)}
                if call.get("id"):
                    tool_msg["tool_call_id"] = call["id"]
                messages.append(tool_msg)
            try:
                data = {"model": use_model, "messages": messages, "tools": self.tools_schema, "tool_choice": tool_choice}
                if (
                    use_model not in self.cfg.llm.models.get("google", [])
                    and use_model != "grok-4"
                    and not (isinstance(use_model, str) and use_model.startswith("gpt-5-"))
                    and not (isinstance(use_model, str) and use_model.startswith("o"))
                ):
                    data.update(self.options)
                result = await self.llm.chat(data)
            except Exception:
                self.logger.exception("Follow-up chat with tools failed")
                return ""
            iterations += 1
        final_msg = (result.get("choices", [{}])[0].get("message") or {})
        content = (final_msg.get("content") or "").strip()
        messages.append({"role": "assistant", "content": content})
        messages[:] = [m for m in messages if not (m.get("role") == "tool" or (isinstance(m, dict) and m.get("tool_calls")))]
        if len(messages) > self.cfg.llm.history_size:
            if messages and messages[0].get("role") == "system":
                messages.pop(1)
            else:
                messages.pop(0)
        return content


async def run(cfg: AppConfig, config_path: Optional[str] = None) -> None:
    ctx = AppContext(cfg)

    router = Router()
    router.register(".ai", handle_ai)
    router.register(".x", handle_x)
    router.register(".persona", handle_persona)
    router.register(".custom", handle_custom)
    router.register(".reset", handle_reset)
    router.register(".stock", lambda c, r, s, d, a: handle_reset(c, r, s, d, "stock"))
    router.register(".help", handle_help)
    router.register(".mymodel", handle_mymodel)
    router.register(".tools", handle_tools, admin=True)
    try:
        from .handlers.cmd_verbose import handle_verbose
        router.register(".verbose", handle_verbose, admin=True)
    except Exception:
        pass
    router.register(".model", handle_model, admin=True)
    router.register(".clear", handle_clear, admin=True)

    ctx.log(f"Model set to {ctx.model}")

    await ctx.matrix.load_store()
    login_resp = await ctx.matrix.login()
    try:
        ctx.log(login_resp)
    except Exception:
        pass
    await ctx.matrix.ensure_keys()
    await ctx.matrix.initial_sync()

    try:
        ctx.bot_id = await ctx.matrix.display_name(cfg.matrix.username)
    except Exception:
        ctx.bot_id = cfg.matrix.username

    try:
        device_id = getattr(ctx.matrix.client, "device_id", None)
        if device_id and hasattr(cfg.matrix, "device_id") and not cfg.matrix.device_id and config_path:
            with open(config_path, "r+") as f:
                data = json.load(f)
                data.setdefault("matrix", {})["device_id"] = device_id
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            ctx.log(f"Persisted device_id to {config_path}")
    except Exception:
        pass

    for room in cfg.matrix.channels:
        try:
            await ctx.matrix.join(room)
            ctx.log(f"{ctx.bot_id} joined {room}")
        except Exception:
            ctx.log(f"Couldn't join {room}")

    import datetime as _dt
    security = Security(ctx.matrix, logger=ctx.logger)
    try:
        from nio import KeyVerificationEvent  # type: ignore
    except Exception:
        KeyVerificationEvent = None  # type: ignore
    try:
        if KeyVerificationEvent:
            ctx.matrix.add_to_device_callback(security.emoji_verification_callback, (KeyVerificationEvent,))
        ctx.matrix.add_to_device_callback(security.log_to_device_event, None)
    except Exception:
        pass

    join_time = _dt.datetime.now()

    async def on_text(room, event) -> None:
        try:
            message_time = getattr(event, "server_timestamp", 0) / 1000.0
            message_time = _dt.datetime.fromtimestamp(message_time)
            if message_time <= join_time:
                return
            text = getattr(event, "body", "")
            sender = getattr(event, "sender", "")
            if sender == cfg.matrix.username:
                return
            sender_display = await ctx.matrix.display_name(sender)
            is_admin = sender_display in ctx.admins or sender in ctx.admins
            handler, args = router.dispatch(ctx, room.room_id, sender, sender_display, text, is_admin, bot_name=ctx.bot_id, timestamp=message_time)  # type: ignore
            if handler is None:
                return
            try:
                ctx.log(f"{sender_display} ({sender}) sent {text} in {room.room_id}")  # type: ignore
            except Exception:
                pass
            try:
                await security.allow_devices(sender)
            except Exception:
                pass
            res = handler(*args)
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            ctx.log(e)

    ctx.matrix.add_text_handler(on_text)

    import signal as _signal
    stop = asyncio.Event()
    try:
        loop = asyncio.get_running_loop()
        for sig in (_signal.SIGINT, _signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except Exception:
                pass
    except Exception:
        pass
    sync_task = asyncio.create_task(ctx.matrix.sync_forever())
    stop_task = asyncio.create_task(stop.wait())
    try:
        await asyncio.wait({sync_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
    except KeyboardInterrupt:
        pass
    finally:
        for t in (sync_task, stop_task):
            if not t.done():
                t.cancel()
        try:
            if hasattr(ctx.matrix, "shutdown"):
                await ctx.matrix.shutdown()
        except Exception:
            pass
        try:
            if getattr(ctx, "mcp_client", None) and hasattr(ctx.mcp_client, "close"):
                ctx.mcp_client.close()
        except Exception:
            pass
        try:
            ctx.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
