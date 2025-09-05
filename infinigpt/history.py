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
        return self._messages

    def set_verbose(self, verbose: bool) -> None:
        self._include_extra = not bool(verbose)

    def _full_suffix(self) -> str:
        return f"{self.prompt_suffix}{self.prompt_suffix_extra if self._include_extra and self.prompt_suffix_extra else ''}"

    def _system_for(self, room: str, user: str) -> str:
        if self._fixed_system_prompt is not None:
            return self._fixed_system_prompt
        return f"{self.prompt_prefix}{self.personality}{self._full_suffix()}"

    def _ensure(self, room: str, user: str) -> None:
        if room not in self._messages:
            self._messages[room] = {}
        if user not in self._messages[room]:
            self._messages[room][user] = [{"role": "system", "content": self._system_for(room, user)}]

    def init_prompt(self, room: str, user: str, persona: Optional[str] = None, custom: Optional[str] = None) -> None:
        self._ensure(room, user)
        if custom:
            self._messages[room][user] = [{"role": "system", "content": custom}]
        else:
            p = persona if (persona is not None and persona != "") else self.personality
            self._messages[room][user] = [
                {"role": "system", "content": f"{self.prompt_prefix}{p}{self._full_suffix()}"}
            ]

    def add(self, room: str, user: str, role: str, content: str) -> None:
        self._ensure(room, user)
        self._messages[room][user].append({"role": role, "content": content})
        self._trim(room, user)

    def get(self, room: str, user: str) -> List[Dict[str, str]]:
        self._ensure(room, user)
        return list(self._messages[room][user])

    def reset(self, room: str, user: str, stock: bool = False) -> None:
        if room not in self._messages:
            self._messages[room] = {}
        self._messages[room][user] = []
        if not stock:
            self.init_prompt(room, user, persona=self.personality)

    # alias used by our handlers
    def clear(self, room: str, user: str) -> None:
        self.reset(room, user, stock=True)

    def clear_all(self) -> None:
        self._messages.clear()

    def _trim(self, room: str, user: str) -> None:
        msgs = self._messages[room][user]
        while len(msgs) > self.max_items:
            if msgs and msgs[0].get("role") == "system":
                if len(msgs) > 1:
                    msgs.pop(1)
                else:
                    break
            else:
                msgs.pop(0)
