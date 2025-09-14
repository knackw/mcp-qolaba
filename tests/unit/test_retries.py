import asyncio
from typing import Any, Dict

import pytest

from qolaba_mcp_server.api.client import QolabaHTTPClient
from qolaba_mcp_server.config.settings import QolabaSettings


@pytest.mark.asyncio
async def test_rate_limit_retry_success(httpx_mock: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fast_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    settings = QolabaSettings(
        env="test",
        api_base_url="https://api.example/",
        api_key="dummy",  # type: ignore[arg-type]
    )

    # First 429 with Retry-After, then 200 success
    httpx_mock.add_response(
        method="POST",
        url="https://api.example/text-to-speech",
        status_code=429,
        headers={"Retry-After": "0"},
        json={"error": "rate_limited"},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.example/text-to-speech",
        status_code=200,
        json={"success": True},
    )

    async with QolabaHTTPClient(settings) as client:
        client.jitter = False
        client.max_retries = 1
        res = await client.post("text-to-speech", json={})

    assert res.status_code == 200
    assert isinstance(res.content, dict)
    assert res.content.get("success") is True


@pytest.mark.asyncio
async def test_oauth_401_refresh_then_success(httpx_mock: Any) -> None:
    settings = QolabaSettings(
        env="test",
        api_base_url="https://api.example/",
        client_id="cid",
        client_secret="csecret",  # type: ignore[arg-type]
        token_url="https://auth.example/token",
    )

    # Token endpoint returns access token
    httpx_mock.add_response(
        method="POST",
        url="https://auth.example/token",
        status_code=200,
        json={"access_token": "access123", "expires_in": 3600},
    )

    # First API call 401 to trigger refresh, second 200
    httpx_mock.add_response(
        method="POST",
        url="https://api.example/chat",
        status_code=401,
        json={"error": "unauthorized"},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.example/chat",
        status_code=200,
        json={"messages": [{"role": "assistant", "content": "ok"}]},
    )

    async with QolabaHTTPClient(settings) as client:
        res = await client.post("chat", json={"messages": [{"role": "user", "content": "hi"}]})

    assert res.status_code == 200
    assert isinstance(res.content, dict)
    assert "messages" in res.content

