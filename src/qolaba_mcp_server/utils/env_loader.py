"""
Environment variable loading utilities for Qolaba MCP Server.

This module provides utilities for loading and validating environment variables
from .env files using python-dotenv.
"""

import os
from pathlib import Path
from typing import Optional, Union

from dotenv import load_dotenv


def load_environment(env_file: Optional[Union[str, Path]] = None) -> bool:
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to the .env file. If None, searches for .env in project root.

    Returns:
        bool: True if .env file was found and loaded, False otherwise.

    Example:
        >>> load_environment()
        True
        >>> load_environment(".env.production")
        True
    """
    if env_file is None:
        # Search for .env file in project root
        project_root = Path(__file__).parent.parent.parent.parent
        env_file = project_root / ".env"

    env_path = Path(env_file)

    if env_path.exists():
        load_dotenv(env_path)
        return True

    return False


def get_env_var(
    key: str,
    default: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    """
    Get environment variable value with optional default and validation.

    Args:
        key: Environment variable name
        default: Default value if variable is not set
        required: If True, raises ValueError when variable is not set

    Returns:
        str: Environment variable value or default

    Raises:
        ValueError: If required=True and variable is not set

    Example:
        >>> get_env_var("QOLABA_API_KEY", required=True)
        "your_api_key_here"
        >>> get_env_var("LOG_LEVEL", default="INFO")
        "INFO"
    """
    value = os.getenv(key, default)

    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")

    return value


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get environment variable as boolean value.

    Args:
        key: Environment variable name
        default: Default value if variable is not set

    Returns:
        bool: Parsed boolean value

    Example:
        >>> get_env_bool("DEBUG", default=False)
        False
        >>> get_env_bool("SSL_VERIFY", default=True)
        True
    """
    value = os.getenv(key)

    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """
    Get environment variable as integer value.

    Args:
        key: Environment variable name
        default: Default value if variable is not set or invalid

    Returns:
        int: Parsed integer value

    Example:
        >>> get_env_int("SERVER_PORT", default=8000)
        8000
        >>> get_env_int("RETRY_MAX_ATTEMPTS", default=3)
        3
    """
    value = os.getenv(key)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """
    Get environment variable as float value.

    Args:
        key: Environment variable name
        default: Default value if variable is not set or invalid

    Returns:
        float: Parsed float value

    Example:
        >>> get_env_float("RETRY_BACKOFF_FACTOR", default=2.0)
        2.0
    """
    value = os.getenv(key)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def validate_required_env_vars() -> None:
    """
    Validate that all required environment variables are set.

    Raises:
        ValueError: If any required environment variable is missing or has placeholder values

    Example:
        >>> validate_required_env_vars()
        # Raises ValueError if QOLABA_API_KEY is not set or has placeholder value
    """
    required_vars = [
        "QOLABA_API_KEY",
    ]

    # Placeholder values that should be considered as "not set"
    placeholder_values = [
        "your_qolaba_api_key_here",
        "your_api_key_here",
        "change_me",
        "placeholder",
        "",
    ]

    missing_vars = []
    placeholder_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif value in placeholder_values:
            placeholder_vars.append(var)

    error_messages = []

    if missing_vars:
        error_messages.append(f"Missing required environment variables: {', '.join(missing_vars)}")

    if placeholder_vars:
        error_messages.append(f"Environment variables with placeholder values: {', '.join(placeholder_vars)}")

    if error_messages:
        raise ValueError(
            ". ".join(error_messages) + ". Please check your .env file."
        )


# Auto-load .env file when module is imported
if not load_environment():
    # If no .env file found, that's okay for testing/CI environments
    pass