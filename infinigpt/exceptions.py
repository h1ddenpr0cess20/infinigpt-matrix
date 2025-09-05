class InfiniGPTError(Exception):
    """Base error for InfiniGPT components."""

class ConfigurationError(InfiniGPTError):
    """Invalid or missing configuration."""

class NetworkError(InfiniGPTError):
    """HTTP or connection failure talking to external services."""

class AuthError(InfiniGPTError):
    """Authentication or authorization failure."""

class RuntimeFailure(InfiniGPTError):
    """Unexpected runtime error."""
