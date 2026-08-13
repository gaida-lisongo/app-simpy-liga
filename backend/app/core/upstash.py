"""
Client minimaliste Upstash Redis (REST) — file d'événements pub/sub.

Pourquoi REST et non SUBSCRIBE : Upstash expose une API HTTP (client @upstash/redis)
qui ne supporte pas la commande SUBSCRIBE (connexion persistante). On émule
donc une queue pub/sub via une liste Redis ordonnée :
    - producteur : LPUSH simpy:campagne:{id}:events <json>  (en-tête de liste)
    - consommateur : RPOP simpy:campagne:{id}:events         (queue de liste) → FIFO
La clé expire après 1 h pour éviter toute fuite.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

import json
import os

import httpx

_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "").rstrip("/")
_REST_TOK = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
_CLIENT: httpx.Client | None = httpx.Client(timeout=10.0) if _REST_URL else None


def available() -> bool:
    """Indique si Upstash est configuré (URL + token présents)."""
    return _CLIENT is not None


def _pipeline(commands: list[list]) -> list:
    """Exécute un batch de commandes Redis via l'API pipeline Upstash."""
    if _CLIENT is None:
        return []
    r = _CLIENT.post(
        f"{_REST_URL}/pipeline",
        json=commands,
        headers={"Authorization": f"Bearer {_REST_TOK}"},
    )
    r.raise_for_status()
    return r.json()


def push_event(campagne_id: str, payload: dict) -> None:
    """Pousse un événement JSON dans la file de la campagne (best-effort)."""
    if not available():
        return
    key = f"simpy:campagne:{campagne_id}:events"
    try:
        _pipeline([
            ["LPUSH", key, json.dumps(payload)],
            ["EXPIRE", key, 3600],
        ])
    except Exception:
        # Best-effort : la simulation continue même si le push échoue.
        pass