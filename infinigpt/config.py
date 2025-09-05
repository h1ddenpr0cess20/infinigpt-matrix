from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Tuple, Optional


@dataclass
class MatrixConfig:
    server: str
    username: str
    password: str
    channels: List[str]
    admins: List[str] = field(default_factory=list)
    device_id: str = ""
    store_path: str = "store"
    e2e: bool = True


@dataclass
class OpenAIConfig:
    api_url: str = "http://localhost:11434/api/chat"
    options: Dict[str, Any] = field(default_factory=dict)
    models: Dict[str, str] = field(default_factory=dict)
    default_model: str = ""
    prompt: List[str] = field(default_factory=lambda: ["you are ", "."]) 
    personality: str = ""
    history_size: int = 24
    timeout: int = 180
    mcp_servers: Dict[str, Any] = field(default_factory=dict)
    # When True, omit the optional brevity clause (third prompt element) from new conversations
    verbose: bool = False


@dataclass
class AppConfig:
    matrix: MatrixConfig
    openai: OpenAIConfig
    markdown: bool = True


def _deep_update(base: dict, updates: dict) -> dict:
    """Recursively update a mapping.

    For keys present in both mappings, nested dictionaries are merged
    recursively; other values are overwritten.

    Args:
        base: Original dictionary to update.
        updates: Dictionary of updates to apply.

    Returns:
        The updated dictionary (same object as `base`).
    """
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _deep_update(dict(base[k]), v)
        else:
            base[k] = v
    return base


def _asdict_redacted(cfg: AppConfig) -> dict:
    """Convert config to a dictionary with sensitive fields redacted.

    Args:
        cfg: Application configuration.

    Returns:
        A dictionary representation with credentials masked.
    """
    d = asdict(cfg)
    # Redact sensitive values
    if "matrix" in d:
        d["matrix"]["password"] = "***"
        # Username can be sensitive too; keep domain for context
        user = d["matrix"].get("username", "")
        if isinstance(user, str) and ":" in user:
            name, domain = user.split(":", 1)
            d["matrix"]["username"] = f"***:{domain}"
        else:
            d["matrix"]["username"] = "***"
    return d


def load_config(
    path: Optional[str],
    env: Optional[Dict[str, str]] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> AppConfig:
    """Load configuration from JSON and apply overrides.

    Reads `path` (or `INFINIGPT_CONFIG`/`config.json`), applies selected
    environment overrides and explicit overrides, and returns a structured
    `AppConfig`.

    Args:
        path: Path to a JSON config file. If `None`, uses environment/defaults.
        env: Environment variables mapping; defaults to `os.environ`.
        overrides: Explicit overrides to merge into the loaded config.

    Returns:
        Parsed application configuration.
    """
    env = env or os.environ
    cfg_path = path or env.get("INFINIGPT_CONFIG", "config.json")

    with open(cfg_path, "r") as f:
        raw = json.load(f)

    # Apply ENV overrides (selected keys only to avoid surprises)
    env_over = {}
    if env.get("INFINIGPT_OPENAI_URL"):
        env_over.setdefault("openai", {})["api_url"] = env["INFINIGPT_OPENAI_URL"]
    if env.get("INFINIGPT_MODEL"):
        env_over.setdefault("openai", {})["default_model"] = env["INFINIGPT_MODEL"]
    if env.get("INFINIGPT_STORE_PATH"):
        env_over.setdefault("matrix", {})["store_path"] = env["INFINIGPT_STORE_PATH"]
    if env.get("INFINIGPT_MATRIX_SERVER"):
        env_over.setdefault("matrix", {})["server"] = env["INFINIGPT_MATRIX_SERVER"]

    raw = _deep_update(raw, env_over)
    if overrides:
        raw = _deep_update(raw, overrides)

    # Back-compat: allow top-level "mcp_servers" and merge into openai section
    try:
        if isinstance(raw.get("mcp_servers"), dict):
            raw.setdefault("openai", {})
            existing = raw["openai"].get("mcp_servers")
            if not isinstance(existing, dict):
                raw["openai"]["mcp_servers"] = dict(raw["mcp_servers"])  # copy
            else:
                merged = dict(existing)
                merged.update(raw["mcp_servers"])  # top-level wins
                raw["openai"]["mcp_servers"] = merged
    except Exception:
        # Non-fatal; validation will surface bad types later
        pass

    matrix = raw.get("matrix", {})
    openai = raw.get("openai", {})

    app_cfg = AppConfig(
        matrix=MatrixConfig(
            server=matrix.get("server", ""),
            username=matrix.get("username", ""),
            password=matrix.get("password", ""),
            channels=list(matrix.get("channels", [])),
            admins=list(matrix.get("admins", [])),
            device_id=matrix.get("device_id", ""),
            store_path=matrix.get("store_path", "store"),
            e2e=bool(matrix.get("e2e", True)),
        ),
        openai=OpenAIConfig(
            api_url=openai.get("api_url", "http://localhost:11434/api/chat"),
            options=dict(openai.get("options", {})),
            models=dict(openai.get("models", {})),
            default_model=openai.get("default_model", ""),
            prompt=list(openai.get("prompt", ["you are ", "."])) ,
            personality=openai.get("personality", ""),
            history_size=int(openai.get("history_size", 24)),
            timeout=360,
            mcp_servers=dict(openai.get("mcp_servers", {})),
            verbose=bool(openai.get("verbose", False)),
        ),
        markdown=bool(raw.get("markdown", True)),
    )
    return app_cfg


_URL_RE = re.compile(r"^https?://", re.I)


def validate_config(cfg: AppConfig) -> Tuple[bool, List[str]]:
    """Validate configuration values and return errors, if any.

    Args:
        cfg: Application configuration to validate.

    Returns:
        A tuple of `(ok, errors)` where `ok` is `True` if the configuration is
        valid, and `errors` is a list of human-readable error messages.
    """
    errors: List[str] = []

    # Matrix
    if not cfg.matrix.server or not _URL_RE.search(cfg.matrix.server):
        errors.append("matrix.server must be a valid http(s) URL")
    if not cfg.matrix.username:
        errors.append("matrix.username is required")
    if not cfg.matrix.password:
        errors.append("matrix.password is required")
    if not cfg.matrix.channels or not isinstance(cfg.matrix.channels, list):
        errors.append("matrix.channels must be a non-empty list")
    else:
        bad = [c for c in cfg.matrix.channels if not isinstance(c, str) or not (c.startswith("#") or c.startswith("!"))]
        if bad:
            errors.append(f"matrix.channels entries must start with '#' or '!': {bad}")
    if not isinstance(cfg.matrix.admins, list):
        errors.append("matrix.admins must be a list")
    if not isinstance(cfg.matrix.store_path, str) or not cfg.matrix.store_path:
        errors.append("matrix.store_path must be a non-empty string path")
    if not isinstance(cfg.matrix.e2e, bool):
        errors.append("matrix.e2e must be a boolean")

    # OpenAI
    if not cfg.openai.api_url or not _URL_RE.search(cfg.openai.api_url):
        errors.append("openai.api_url must be a valid http(s) URL")
    if not isinstance(cfg.openai.models, dict):
        errors.append("openai.models must be a mapping of name→id")
    if not isinstance(cfg.openai.default_model, str) or not cfg.openai.default_model:
        errors.append("openai.default_model must be a non-empty string")
    else:
        # If models mapping is provided, ensure default is present (by key or id)
        try:
            models = cfg.openai.models or {}
            if isinstance(models, dict) and (
                cfg.openai.default_model not in models
                and cfg.openai.default_model not in set(models.values())
            ):
                errors.append("openai.default_model must match a key or id in openai.models")
        except Exception:
            pass
    # Allow 2-element [prefix, suffix] or 3-element with optional brevity clause as [prefix, suffix, brevity]
    if (
        not isinstance(cfg.openai.prompt, list)
        or len(cfg.openai.prompt) not in (2, 3)
        or not all(isinstance(p, str) for p in cfg.openai.prompt)
    ):
        errors.append("openai.prompt must be a list of 2 or 3 strings [prefix, suffix, (optional brevity clause)]")
    if not isinstance(cfg.openai.personality, str) or not cfg.openai.personality:
        errors.append("openai.personality must be a non-empty string")
    if not (1 <= cfg.openai.history_size <= 1000):
        errors.append("openai.history_size must be between 1 and 1000")

    # Options ranges (if present)
    opts = cfg.openai.options or {}
    temp = opts.get("temperature")
    if temp is not None and not (0 <= float(temp) <= 2):
        errors.append("openai.options.temperature must be between 0 and 2")
    top_p = opts.get("top_p")
    if top_p is not None and not (0 < float(top_p) <= 1):
        errors.append("openai.options.top_p must be between >0 and ≤1")
    rp = opts.get("repeat_penalty")
    if rp is not None and not (0.5 <= float(rp) <= 2):
        errors.append("openai.options.repeat_penalty must be between 0.5 and 2")
    if not isinstance(cfg.openai.mcp_servers, dict):
        errors.append("openai.mcp_servers must be a mapping if provided")

    ok = len(errors) == 0
    return ok, errors


def summarize(cfg: AppConfig) -> Dict[str, Any]:
    """Return a redacted summary dict suitable for printing.

    Args:
        cfg: Application configuration to summarize.

    Returns:
        A redacted dictionary intended for user display or logs.
    """
    return _asdict_redacted(cfg)
