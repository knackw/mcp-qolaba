import os
import builtins
from importlib import reload

import pytest

from qolaba_mcp_server.config import settings as settings_mod
from pydantic import SecretStr


def _clear_env(monkeypatch: pytest.MonkeyPatch):
    # Clear all relevant env vars
    for k in [
        "QOLABA_ENV",
        "ENV",
        "QOLABA_API_BASE_URL",
        "API_BASE_URL",
        "QOLABA_API_KEY",
        "QOLABA_CLIENT_ID",
        "QOLABA_CLIENT_SECRET",
        "QOLABA_TOKEN_URL",
        "QOLABA_SCOPE",
        "QOLABA_TIMEOUT",
        "QOLABA_VERIFY_SSL",
        "QOLABA_HTTP_PROXY",
        "QOLABA_HTTPS_PROXY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
    ]:
        monkeypatch.delenv(k, raising=False)


def test_settings_with_api_key(monkeypatch: pytest.MonkeyPatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("QOLABA_ENV", "development")
    monkeypatch.setenv("QOLABA_API_KEY", "testkey123")

    settings_mod.get_settings.cache_clear()
    s = settings_mod.get_settings()

    assert s.auth_method == "api_key"
    assert isinstance(s.api_key, SecretStr)
    assert s.api_key.get_secret_value() == "testkey123"
    assert "testkey123" not in repr(s)
    assert "testkey123" not in str(s)


def test_settings_with_oauth_in_production(monkeypatch: pytest.MonkeyPatch):
    _clear_env(monkeypatch)
    # Explicitly set API key to empty to avoid "both auth methods" error in production
    monkeypatch.setenv("QOLABA_API_KEY", "")
    monkeypatch.setenv("QOLABA_ENV", "production")
    monkeypatch.setenv("QOLABA_CLIENT_ID", "client-abc")
    monkeypatch.setenv("QOLABA_CLIENT_SECRET", "supersecret")
    monkeypatch.setenv("QOLABA_TOKEN_URL", "https://auth.example.com/token")

    settings_mod.get_settings.cache_clear()
    s = settings_mod.get_settings()

    assert s.auth_method == "oauth"
    assert s.client_id == "client-abc"
    assert isinstance(s.client_secret, SecretStr)
    assert s.client_secret.get_secret_value() == "supersecret"


def test_missing_credentials_raises_in_production(monkeypatch: pytest.MonkeyPatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("QOLABA_ENV", "production")
    # Explicitly set API key to empty to ensure no auth method is detected
    monkeypatch.setenv("QOLABA_API_KEY", "")

    settings_mod.get_settings.cache_clear()
    with pytest.raises(ValueError, match="No authentication configured"):
        _ = settings_mod.get_settings()


def test_raises_error_if_both_auth_methods_configured(monkeypatch: pytest.MonkeyPatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("QOLABA_ENV", "production")
    monkeypatch.setenv("QOLABA_API_KEY", "testkey123")
    monkeypatch.setenv("QOLABA_CLIENT_ID", "client-abc")
    monkeypatch.setenv("QOLABA_CLIENT_SECRET", "supersecret")
    monkeypatch.setenv("QOLABA_TOKEN_URL", "https://auth.example.com/token")

    settings_mod.get_settings.cache_clear()
    with pytest.raises(ValueError, match="Both API key and OAuth credentials are configured"):
        _ = settings_mod.get_settings()


def test_default_timeout_and_flags(monkeypatch: pytest.MonkeyPatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("QOLABA_ENV", "development")
    monkeypatch.setenv("QOLABA_API_KEY", "abc")

    settings_mod.get_settings.cache_clear()
    s = settings_mod.get_settings()

    assert s.request_timeout == 30.0
    assert s.verify_ssl is True