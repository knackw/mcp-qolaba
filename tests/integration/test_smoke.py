import asyncio
import os

import pytest

from qolaba_mcp_server.core.business_logic import (
    get_orchestrator,
    OperationType,
)
from qolaba_mcp_server.config import get_settings


@pytest.mark.asyncio
async def test_validation_only_path_no_network() -> None:
    orchestrator = get_orchestrator()
    # Missing required fields should trigger validation error and avoid network calls
    result = await orchestrator.execute_operation(OperationType.TEXT_TO_IMAGE, {}, request_id="smoke")

    assert isinstance(result, dict)
    assert "error" in result


def test_settings_redaction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QOLABA_API_KEY", "supersecret")
    monkeypatch.setenv("QOLABA_ENV", "development")

    settings = get_settings()
    data = settings.redacted_dict()
    assert data.get("api_key") == "********"


def test_module_entrypoint_importable() -> None:
    # Ensure module entrypoint exists and is importable
    import qolaba_mcp_server.__main__ as entry

    assert hasattr(entry, "main")

