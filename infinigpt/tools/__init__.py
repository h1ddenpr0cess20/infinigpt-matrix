from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List

import importlib
import json
import pkgutil
from pathlib import Path
import logging


_TOOL_REGISTRY: Dict[str, Callable[..., str]] | None = None
logger = logging.getLogger(__name__)


def _schema_path() -> Path:
    """Return the filesystem path to the builtin tools schema file."""
    return Path(__file__).resolve().parent / "schema.json"


def load_schema(path: str | None = None) -> List[Dict[str, Any]]:
    """Load the tools JSON schema definitions.

    Args:
        path: Optional path to a schema JSON file. Defaults to the packaged
            ``schema.json``.

    Returns:
        A list of tool definition dictionaries.

    Raises:
        ValueError: If the top-level JSON value is not a list.
    """
    p = Path(path) if path else _schema_path()
    logger.debug("Loading tools schema from %s", p)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("schema.json must be a JSON array of tool definitions")
    logger.debug("Loaded %d builtin tool definition(s)", len(data))
    return data


def _discover_functions(names: Iterable[str]) -> Dict[str, Callable[..., str]]:
    """Locate tool functions by name across modules in this package.

    Args:
        names: Iterable of function names to look up.

    Returns:
        Mapping of function name to callable.
    """
    names = list(dict.fromkeys(names))
    remaining = set(names)
    found: Dict[str, Callable[..., str]] = {}

    pkg_path = Path(__file__).resolve().parent
    package_name = __name__

    for modinfo in pkgutil.iter_modules([str(pkg_path)]):
        mod_name = modinfo.name
        if mod_name.startswith("_") or mod_name == "__init__":
            continue
        module = importlib.import_module(f"{package_name}.{mod_name}")
        for fname in list(remaining):
            func = getattr(module, fname, None)
            if callable(func):
                found[fname] = func  # type: ignore[assignment]
                remaining.discard(fname)
        if not remaining:
            break

    return found


def _build_registry_from_schema(schema: List[Dict[str, Any]]) -> Dict[str, Callable[..., str]]:
    """Construct a function registry from tool schema definitions."""
    names: List[str] = []
    for tool in schema:
        fn = (tool.get("function") or {}).get("name")
        if isinstance(fn, str) and fn:
            names.append(fn)
    return _discover_functions(names)


def _get_registry() -> Dict[str, Callable[..., str]]:
    """Return the global tool registry, building it on first use."""
    global _TOOL_REGISTRY
    if _TOOL_REGISTRY is None:
        try:
            schema = load_schema()
        except Exception:
            logger.exception("Failed to load builtin tools schema during registry build")
            schema = []
        _TOOL_REGISTRY = _build_registry_from_schema(schema)
    return _TOOL_REGISTRY


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Execute a builtin tool and normalize its return value to JSON.

    Args:
        name: Tool function name.
        arguments: Keyword arguments to call the tool with.

    Returns:
        JSON string encoding of the tool result or error.
    """
    registry = _get_registry()
    func = registry.get(name)
    if func is None:
        logger.warning("Unknown builtin tool '%s'", name)
        return f"Unknown tool: {name}"
    try:
        try:
            _args_str = json.dumps(arguments or {}, ensure_ascii=False, default=str)
        except Exception:
            _args_str = str(arguments)
        if len(_args_str) > 800:
            _args_str = _args_str[:800] + "…"
        logger.info("Tool (builtin): %s args=%s", name, _args_str)
        result = func(**(arguments or {}))
        if isinstance(result, (dict, list, int, float, bool)) or result is None:
            return json.dumps(result, ensure_ascii=False)
        if isinstance(result, str):
            try:
                json.loads(result)
                return result
            except Exception:
                return json.dumps({"result": result}, ensure_ascii=False)
        return json.dumps({"result": str(result)}, ensure_ascii=False)
    except TypeError as e:
        logger.exception("Invalid arguments for builtin tool '%s'", name)
        return json.dumps({"error": f"Invalid arguments for {name}: {e}"}, ensure_ascii=False)
    except Exception as e:
        logger.exception("Tool execution error for builtin tool '%s'", name)
        return json.dumps({"error": f"Tool execution error for {name}: {e}"}, ensure_ascii=False)
