from __future__ import annotations

import datetime as _dt
from typing import Callable, Dict, Optional, Tuple


class Router:
    """Command router mapping message prefixes to handlers.

    Handlers are callables with signature:
        handler(ctx, room_id: str, sender_id: str, sender_display: str, args: str) -> None|Awaitable

    The router itself is framework-agnostic; the surrounding code is expected to
    await handlers if they are coroutines.
    """

    def __init__(self) -> None:
        """Create a new, empty command router."""
        self._handlers: Dict[str, Callable] = {}
        self._admin_handlers: Dict[str, Callable] = {}

    def register(self, cmd: str, fn: Callable, admin: bool = False) -> None:
        """Register a handler for a command prefix.

        Args:
            cmd: Command token (e.g., ".ai").
            fn: Callable to invoke when dispatched.
            admin: If True, only dispatch for admin users.
        """
        if admin:
            self._admin_handlers[cmd] = fn
        else:
            self._handlers[cmd] = fn

    def dispatch(
        self,
        ctx: object,
        room_id: str,
        sender_id: str,
        sender_display: str,
        text: str,
        is_admin: bool,
        bot_name: Optional[str] = None,
        timestamp: Optional[_dt.datetime] = None,
    ) -> Tuple[Optional[Callable], Tuple]:
        """Resolve an incoming message to a handler and arg tuple.

        Args:
            ctx: Application context object passed to handlers.
            room_id: Matrix room ID.
            sender_id: Matrix sender user ID.
            sender_display: Display name for the sender.
            text: Raw message text.
            is_admin: Whether the sender is an admin.
            bot_name: Optional bot name prefix to address without a dot command.
            timestamp: Optional message timestamp.

        Returns:
            Tuple of (callable or None, args tuple) suitable for ``handler(*args)``.
        """
        parts = text.strip().split()
        if not parts:
            return None, tuple()
        cmd = parts[0]
        args = " ".join(parts[1:])
        if bot_name and cmd == f"{bot_name}:":
            return self._handlers.get(".ai"), (ctx, room_id, sender_id, sender_display, args)
        if cmd in self._handlers:
            return self._handlers[cmd], (ctx, room_id, sender_id, sender_display, args)
        if is_admin and cmd in self._admin_handlers:
            return self._admin_handlers[cmd], (ctx, room_id, sender_id, sender_display, args)
        return None, tuple()
