from __future__ import annotations

from typing import Dict, List, Optional


class HistoryStore:
    """In-memory history per room and user with system prompt support."""

    def __init__(
        self,
        prompt_prefix: str = "you are ",
        prompt_suffix: str = ".",
        personality: str = "",
        *,
        prompt_suffix_extra: str = "",
        max_items: int = 24,
        history_size: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        # Back-compat: allow alternate constructor via system_prompt/history_size
        if system_prompt is not None:
            self.prompt_prefix = ""
            self.prompt_suffix = ""
            self.prompt_suffix_extra = ""
            self.personality = ""
            self._fixed_system_prompt = system_prompt
        else:
            self.prompt_prefix = prompt_prefix
            self.prompt_suffix = prompt_suffix
            self.prompt_suffix_extra = prompt_suffix_extra
            self.personality = personality
            self._fixed_system_prompt = None
        self.max_items = history_size or max_items
        self._include_extra = True
        self._messages: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
        # For per-user model override parity with app
        self.user_models: Dict[str, Dict[str, str]] = {}

    @property
    def messages(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        """Expose the raw history mapping for inspection/testing."""
        return self._messages

    def set_verbose(self, verbose: bool) -> None:
        """Enable or disable verbose mode for system prompt suffix.

        When verbose is True, omit the extra suffix in the system prompt.

        Args:
            verbose: Verbosity flag.
        """
        self._include_extra = not bool(verbose)

    def _full_suffix(self) -> str:
        """Compute the current suffix including optional extra parts."""
        return f"{self.prompt_suffix}{self.prompt_suffix_extra if self._include_extra and self.prompt_suffix_extra else ''}"

    def _system_for(self, room: str, user: str) -> str:
        """Build the system prompt for a specific room/user thread."""
        if self._fixed_system_prompt is not None:
            return self._fixed_system_prompt
        return f"{self.prompt_prefix}{self.personality}{self._full_suffix()}"

    def _ensure(self, room: str, user: str) -> None:
        """Ensure a history thread exists, seeding with a system message."""
        if room not in self._messages:
            self._messages[room] = {}
        if user not in self._messages[room]:
            self._messages[room][user] = [{"role": "system", "content": self._system_for(room, user)}]

    def init_prompt(self, room: str, user: str, persona: Optional[str] = None, custom: Optional[str] = None) -> None:
        """Initialize or replace the system prompt for a thread.

        Args:
            room: Matrix room ID.
            user: Matrix user ID.
            persona: Optional persona to apply using configured prefix/suffix.
            custom: Optional custom system prompt string to use instead.
        """
        self._ensure(room, user)
        if custom:
            self._messages[room][user] = [{"role": "system", "content": custom}]
        else:
            p = persona if (persona is not None and persona != "") else self.personality
            self._messages[room][user] = [
                {"role": "system", "content": f"{self.prompt_prefix}{p}{self._full_suffix()}"}
            ]

    def add(self, room: str, user: str, role: str, content: str) -> None:
        """Append a message and trim to max history length.

        Args:
            room: Matrix room ID.
            user: Matrix user ID.
            role: Message role ("user"/"assistant"/"system").
            content: Message content.
        """
        self._ensure(room, user)
        self._messages[room][user].append({"role": role, "content": content})
        self._trim(room, user)

    def get(self, room: str, user: str) -> List[Dict[str, str]]:
        """Return a copy of the message list for a thread."""
        self._ensure(room, user)
        return list(self._messages[room][user])

    def reset(self, room: str, user: str, stock: bool = False) -> None:
        """Reset a user's history for a room.

        Args:
            room: Matrix room ID.
            user: Matrix user ID.
            stock: When True, leave history empty; otherwise seed default prompt.
        """
        if room not in self._messages:
            self._messages[room] = {}
        self._messages[room][user] = []
        if not stock:
            self.init_prompt(room, user, persona=self.personality)

    # alias used by our handlers
    def clear(self, room: str, user: str) -> None:
        """Alias for ``reset(..., stock=True)`` for handler parity."""
        self.reset(room, user, stock=True)

    def clear_all(self) -> None:
        """Clear all histories across rooms and users."""
        self._messages.clear()

    def _trim(self, room: str, user: str) -> None:
        """Trim a thread's messages to the configured max length."""
        msgs = self._messages[room][user]
        while len(msgs) > self.max_items:
            if msgs and msgs[0].get("role") == "system":
                if len(msgs) > 1:
                    msgs.pop(1)
                else:
                    break
            else:
                msgs.pop(0)
