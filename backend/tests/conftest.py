"""Pytest fixtures partagées."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


os.environ.setdefault("INTERNAL_API_TOKEN", "test-token")


class _AuthClient(TestClient):
    """TestClient qui injecte automatiquement le header d'auth interne."""

    def __init__(self, app, token: str | None = None) -> None:
        super().__init__(app)
        self._token = token or os.environ.get("INTERNAL_API_TOKEN", "test-token")

    def request(self, method, url, **kwargs):  # type: ignore[override]
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("x-internal-token", self._token)
        return super().request(method, url, headers=headers, **kwargs)


__all__ = ["_AuthClient"]