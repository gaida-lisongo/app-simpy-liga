"""
Middleware d'authentification interne.

Le frontend SvelteKit injecte un secret partagé (`X-Internal-Token`) sur
chaque requête qu'il relaie vers l'API FastAPI. Toute requête directe depuis
le navigateur (sans passer par le proxy SvelteKit) est rejetée.

Endpoints exemptés : `/api/health` (monitoring public) et `/` (racine).
"""

from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


_PATHS_EXEMPT = ("/api/health", "/")


def _expected_token() -> str:
    return os.environ.get("INTERNAL_API_TOKEN", "")


class InternalAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in _PATHS_EXEMPT or not path.startswith("/api"):
            return await call_next(request)

        expected = _expected_token()
        if not expected:
            return JSONResponse(
                {"detail": "INTERNAL_API_TOKEN non configuré côté serveur."},
                status_code=503,
            )

        sent = request.headers.get("x-internal-token", "")
        if not sent or sent != expected:
            return JSONResponse(
                {"detail": "Jeton interne manquant ou invalide."},
                status_code=401,
            )

        return await call_next(request)