import logging

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.logging import REQUEST_LOGGER_NAME
from app.main import app, create_app


def test_settings_use_defaults_when_values_are_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "")
    monkeypatch.setenv("AI_BASE_URL", "")
    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "")

    settings = Settings()

    assert settings.log_level == "INFO"
    assert settings.ai_base_url is None
    assert settings.ai_timeout_seconds == 30.0


def test_settings_reject_unknown_log_level_and_non_positive_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "verbose")
    with pytest.raises(ValidationError):
        Settings()

    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "0")
    with pytest.raises(ValidationError):
        Settings()


def test_settings_normalize_a_configured_ai_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("AI_BASE_URL", "http://ai.local")
    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "12")

    settings = Settings()

    assert settings.log_level == "DEBUG"
    assert str(settings.ai_base_url).rstrip("/") == "http://ai.local"
    assert settings.ai_timeout_seconds == 12.0


def test_http_client_opens_with_startup_and_closes_after_shutdown() -> None:
    with TestClient(app) as client:
        client.get("/health")
        http_client = app.state.http_client

        assert isinstance(http_client, httpx.AsyncClient)
        assert http_client.is_closed is False
        assert http_client.timeout is not None
        assert http_client.timeout.read == 30.0

    assert http_client.is_closed is True


def test_http_client_uses_configured_base_url_and_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_BASE_URL", "http://ai.local")
    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "12")
    configured_app = create_app()

    with TestClient(configured_app) as client:
        client.get("/health")
        http_client = configured_app.state.http_client

        assert str(http_client.base_url).rstrip("/") == "http://ai.local"
        assert http_client.timeout is not None
        assert http_client.timeout.read == 12.0


def test_requests_are_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger=REQUEST_LOGGER_NAME):
        with TestClient(app) as client:
            client.get("/health")

    messages = [record.message for record in caplog.records]
    assert any(message.startswith("GET /health 200 ") and message.endswith("ms") for message in messages)
