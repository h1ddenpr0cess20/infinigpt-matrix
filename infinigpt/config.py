from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .exceptions import ConfigError


@dataclass
class MatrixConfig:
    """Matrix client configuration values.

    Attributes:
        server: Homeserver URL.
        username: Bot account user ID (e.g., @bot:server).
        password: Account password.
        channels: Rooms to join on startup.
        admin: Legacy single admin user ID.
        admins: List of admin user IDs.
        device_id: Persisted device ID for E2EE.
        store_path: Path for nio store files.
        e2e: Whether to enable end-to-end encryption.
    """
    server: str
    username: str
    password: str
    channels: List[str]
    # Back-compat: some tests/clients still pass single 'admin' string
    admin: str = ""
    admins: List[str] = field(default_factory=list)
    device_id: str = ""
    store_path: str = "store"
    e2e: bool = True


@dataclass
class LLMConfig:
    """LLM provider, model, and runtime settings.

    Attributes:
        models: Mapping of provider name to list of model IDs.
        api_keys: Mapping of provider to API key.
        default_model: Name of the default model.
        personality: Default persona string joined with system prompt parts.
        prompt: List of system prompt prefix/suffix (and optional extra).
        options: Provider-agnostic chat options to merge when applicable.
        history_size: Max messages kept per history thread.
        ollama_url: Host:port for Ollama OpenAI-compatible API.
        lmstudio_url: Host:port for LM Studio OpenAI-compatible API.
        mcp_servers: Mapping of MCP server names to specs.
        timeout: HTTP client timeout in seconds.
    """
    models: Dict[str, List[str]]
    api_keys: Dict[str, str]
    default_model: str
    personality: str
    prompt: List[str]
    options: Dict[str, Any] = field(default_factory=dict)
    history_size: int = 24
    ollama_url: str = "localhost:11434"
    lmstudio_url: str = "localhost:1234"
    mcp_servers: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 180


@dataclass
class AppConfig:
    """Top-level application configuration container."""
    llm: LLMConfig
    matrix: MatrixConfig
    markdown: bool = True


def _require(obj: dict, key: str, typ):
    """Fetch and type-check a required key from a dict.

    Args:
        obj: Source mapping.
        key: Required key name.
        typ: Expected type or tuple of types.

    Returns:
        The value associated with ``key`` if present and of the right type.

    Raises:
        ConfigError: If the key is missing or of the wrong type.
    """
    if key not in obj:
        raise ConfigError(f"Missing required config key: {key}")
    val = obj[key]
    if not isinstance(val, typ):
        raise ConfigError(f"Config key '{key}' must be of type {typ}")
    return val


def validate_config(cfg: AppConfig) -> Tuple[bool, List[str]]:
    """Validate cross-field constraints and presence of required items.

    Args:
        cfg: Application configuration to validate.

    Returns:
        Tuple of (is_valid, error_messages).
    """
    errors: List[str] = []

    # Validate default model exists among providers
    all_models = {m for models in cfg.llm.models.values() for m in models}
    if cfg.llm.default_model not in all_models:
        errors.append(
            f"llm.default_model '{cfg.llm.default_model}' not found in provided models"
        )

    # Validate essential API keys presence for known providers
    for provider in ["openai", "xai", "google", "mistral", "anthropic"]:
        if provider in cfg.llm.models and cfg.llm.models[provider]:
            if provider not in cfg.llm.api_keys:
                errors.append(f"Missing API key for provider '{provider}'")

    # Validate prompt format of two strings when not custom
    if not (isinstance(cfg.llm.prompt, list) and len(cfg.llm.prompt) >= 1):
        errors.append("llm.prompt must be a list with at least one string")

    return (len(errors) == 0, errors)


def load_config(path: Optional[str] = None) -> AppConfig:
    """Load configuration from disk into an AppConfig.

    Preserves this repository's schema; does not adopt other projects' schemas.

    Args:
        path: Optional JSON path. Defaults to ``./config.json`` if omitted.

    Returns:
        Parsed and validated ``AppConfig`` instance.

    Raises:
        ConfigError: When required fields are missing or invalid.
    """
    config_path = Path(path) if path else Path("config.json")
    raw = json.loads(config_path.read_text())

    llm_raw = _require(raw, "llm", dict)
    matrix_raw = _require(raw, "matrix", dict)

    llm = LLMConfig(
        models=_require(llm_raw, "models", dict),
        api_keys=_require(llm_raw, "api_keys", dict),
        default_model=_require(llm_raw, "default_model", str),
        personality=_require(llm_raw, "personality", str),
        prompt=_require(llm_raw, "prompt", list),
        options=llm_raw.get("options", {}),
        history_size=llm_raw.get("history_size", 24),
        ollama_url=llm_raw.get("ollama_url", "localhost:11434"),
        lmstudio_url=llm_raw.get("lmstudio_url", "localhost:1234"),
        mcp_servers=llm_raw.get("mcp_servers", {}),
        timeout=int(llm_raw.get("timeout", 180)),
    )

    # admins: prefer list, fallback to legacy single 'admin' string
    admins_val: List[str] = []
    if isinstance(matrix_raw.get("admins"), list):
        admins_val = [str(x) for x in matrix_raw.get("admins")]
    elif isinstance(matrix_raw.get("admin"), str) and matrix_raw.get("admin"):
        admins_val = [matrix_raw.get("admin")]  # legacy

    matrix = MatrixConfig(
        server=_require(matrix_raw, "server", str),
        username=_require(matrix_raw, "username", str),
        password=_require(matrix_raw, "password", str),
        channels=_require(matrix_raw, "channels", list),
        admins=admins_val,
        device_id=matrix_raw.get("device_id", ""),
        store_path=matrix_raw.get("store_path", "store"),
        e2e=bool(matrix_raw.get("e2e", True)),
    )

    cfg = AppConfig(llm=llm, matrix=matrix, markdown=True)
    ok, errs = validate_config(cfg)
    if not ok:
        raise ConfigError("Invalid configuration: " + "; ".join(errs))
    return cfg
