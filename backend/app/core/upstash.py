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
import logging
import os

import httpx

log = logging.getLogger(__name__)

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


def push_event(campagne_id: str, payload: dict) -> bool:
    """Pousse un événement JSON dans la file de la campagne (best-effort).

    Returns:
        True si l'événement a été poussé avec succès, False sinon.
    """
    if not available():
        log.warning("Upstash non configuré — push_event ignoré (campagne_id=%s)", campagne_id)
        return False
    key = f"simpy:campagne:{campagne_id}:events"
    try:
        _pipeline([
            ["LPUSH", key, json.dumps(payload)],
            ["EXPIRE", key, 3600],
        ])
        return True
    except Exception as exc:
        payload_size = len(json.dumps(payload))
        log.error(
            "push_event échoué (campagne_id=%s, payload=%d octets) : %s",
            campagne_id, payload_size, exc,
        )
        return False


def save_campaign(circuit_slug: str, campagne_id: str, response: dict) -> bool:
    """Persiste le résultat complet d'une campagne dans Upstash Redis.

    Écrit en un seul pipeline :
      1. SET  simpy:campagne:{id}          — payload JSON complet (avec tirages)
      2. LPUSH simpy:circuit:{circuit}:history  — id en tête de liste
      3. LTRIM simpy:circuit:{circuit}:history 0 19 — garde les 20 dernières

    Returns:
        True si le pipeline a réussi, False sinon.
    """
    if not available():
        log.warning(
            "Upstash non configuré — save_campaign ignorée "
            "(circuit=%s, campagne_id=%s)", circuit_slug, campagne_id,
        )
        return False

    payload_json = json.dumps(response)
    camp_key = f"simpy:campagne:{campagne_id}"
    hist_key = f"simpy:circuit:{circuit_slug}:history"

    try:
        _pipeline([
            ["SET", camp_key, payload_json],
            ["LPUSH", hist_key, campagne_id],
            ["LTRIM", hist_key, 0, 19],
        ])
        log.info(
            "Campagne persistée : %s (%d octets, circuit=%s)",
            campagne_id, len(payload_json), circuit_slug,
        )
        return True
    except Exception as exc:
        log.error(
            "save_campaign échouée (circuit=%s, campagne_id=%s, payload=%d octets) : %s",
            circuit_slug, campagne_id, len(payload_json), exc,
        )
        return False