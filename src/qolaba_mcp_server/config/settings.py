from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, Any, Literal, Optional

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["development", "test", "staging", "production"]


class QolabaSettings(BaseSettings):
    """
    Central configuration object for the Qolaba MCP Server.

    - Values are sourced from environment variables (optionally via a .env file).
    - Secrets are represented as SecretStr to prevent accidental exposure in logs.
    - Validation ensures a supported authentication method is configured.
    """

    # Environment/profile
    env: Environment = Field(default="development", description="Execution environment profile")

    # API endpoint configuration
    api_base_url: Optional[str] = Field(
        default=None,
        description="Base URL for the Qolaba API (e.g. https://api.qolaba.ai)",
    )

    # Authentication (either API key OR OAuth client credentials)
    api_key: Optional[SecretStr] = Field(default=None, description="Qolaba API Key")

    client_id: Optional[str] = Field(default=None, description="OAuth client id")
    client_secret: Optional[SecretStr] = Field(default=None, description="OAuth client secret")
    token_url: Optional[str] = Field(default=None, description="OAuth token URL")
    scope: Optional[str] = Field(default=None, description="OAuth scope(s) if required")

    # Networking
    request_timeout: float = Field(default=30.0, ge=0.1, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Verify TLS certificates for HTTPS requests")

    # Proxies (optional)
    http_proxy: Optional[str] = Field(default=None, description="HTTP proxy URL")
    https_proxy: Optional[str] = Field(default=None, description="HTTPS proxy URL")

    @property
    def auth_method(self) -> Literal["api_key", "oauth", "none"]:
        if self.client_id and self.client_secret and self.token_url:
            return "oauth"
        if self.api_key and self.api_key.get_secret_value():
            return "api_key"
        return "none"

    def model_post_init(self, __context: Any) -> None:  # Pydantic v2 hook
        env = self.env
        if env in ("production", "staging"):
            is_api_key_auth = bool(self.api_key and self.api_key.get_secret_value())
            is_oauth = bool(self.client_id and self.client_secret and self.token_url)

            if is_api_key_auth and is_oauth:
                raise ValueError("Both API key and OAuth credentials are configured. Please provide only one.")

            if not is_api_key_auth and not is_oauth:
                raise ValueError(
                    "No authentication configured. Set QOLABA_API_KEY or OAuth env vars (QOLABA_CLIENT_ID, QOLABA_CLIENT_SECRET, QOLABA_TOKEN_URL)."
                )

    def redacted_dict(self) -> Dict[str, Any]:
        """Return a dict suitable for logging with secrets redacted."""
        d = self.dict()
        if d.get("api_key"):
            d["api_key"] = "********"
        if d.get("client_secret"):
            d["client_secret"] = "********"
        return d

    # pydantic-settings Konfiguration
    model_config = SettingsConfigDict(env_file=".env", env_prefix="QOLABA_", extra="ignore")

    @classmethod
    def from_env(cls) -> "QolabaSettings":
        """Load settings from environment variables (supports .env via python-dotenv)."""
        load_dotenv(override=False)
        return cls()  # pydantic-settings übernimmt Mapping per env_prefix


@lru_cache(maxsize=1)
def get_settings() -> QolabaSettings:
    """Cached accessor for settings to avoid repeated environment parsing.

    Use get_settings.cache_clear() in tests when modifying environment variables.
    """
    return QolabaSettings.from_env()
