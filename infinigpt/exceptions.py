class ConfigError(Exception):
    """Raised when configuration is invalid or missing required fields."""


class ProviderError(Exception):
    """Raised when an LLM provider configuration is invalid."""

