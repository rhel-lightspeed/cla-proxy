"""Tests for the timeout middleware."""

import asyncio
import typing as t

from unittest.mock import MagicMock

import pytest

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.responses import StreamingResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from goose_proxy.middleware import TimeoutMiddleware


@pytest.fixture
def timeout_app():
    """Create a minimal Starlette app with TimeoutMiddleware."""

    def _timeout_app(handler):
        app = Starlette(routes=[Route("/", handler)])

        return TimeoutMiddleware(app)

    return _timeout_app


@pytest.fixture
def settings():
    def _settings(timeout: t.Union[int, float] = 5):
        mock_settings = MagicMock()
        mock_settings.backend.timeout = timeout

        return mock_settings

    return _settings


class TestTimeoutMiddleware:
    def test_successful_request_passes_through(self, timeout_app, settings, monkeypatch):
        async def handler(request):
            return PlainTextResponse("OK")

        monkeypatch.setattr("goose_proxy.middleware.get_settings", settings)

        wrapped = timeout_app(handler)
        client = TestClient(wrapped)
        resp = client.get("/")

        assert resp.status_code == 200
        assert resp.text == "OK"

    def test_slow_response_returns_504(self, timeout_app, settings, monkeypatch):
        async def handler(request):
            await asyncio.sleep(10)
            return PlainTextResponse("Too late")

        def fake_get_settings():
            return settings(timeout=0.1)

        monkeypatch.setattr("goose_proxy.middleware.get_settings", fake_get_settings)

        wrapped = timeout_app(handler)
        client = TestClient(wrapped)
        resp = client.get("/")
        body = resp.json()

        assert resp.status_code == 504
        assert body["error"]["type"] == "server_error"
        assert body["error"]["code"] == 504
        assert "timed out" in body["error"]["message"]

    async def test_non_http_scope_bypasses_timeout(self):
        """WebSocket and lifespan scopes should pass through without timeout."""
        call_log = []

        async def inner_app(scope, receive, send):
            call_log.append(scope["type"])

        middleware = TimeoutMiddleware(inner_app)
        scope = {"type": "websocket"}
        await middleware(scope, None, None)

        assert call_log == ["websocket"]

    def test_streaming_response_not_cut_short(self, timeout_app, settings, monkeypatch):
        """Once headers are sent, the middleware should not enforce a timeout."""

        async def handler(request):
            async def generate():
                yield "chunk1"
                await asyncio.sleep(0.2)
                yield "chunk2"

            return StreamingResponse(generate(), media_type="text/plain")

        wrapped = timeout_app(handler)

        def fake_get_settings():
            return settings(timeout=0.1)

        monkeypatch.setattr("goose_proxy.middleware.get_settings", fake_get_settings)

        client = TestClient(wrapped)
        resp = client.get("/")

        assert resp.status_code == 200
        assert "chunk1" in resp.text
        assert "chunk2" in resp.text

    def test_app_error_propagates(self, timeout_app, settings, monkeypatch):
        async def handler(request):
            raise ValueError("Something went wrong")

        wrapped = timeout_app(handler)

        monkeypatch.setattr("goose_proxy.middleware.get_settings", settings)
        client = TestClient(wrapped, raise_server_exceptions=False)
        resp = client.get("/")

        assert resp.status_code == 500
