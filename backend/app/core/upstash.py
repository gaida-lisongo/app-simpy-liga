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

    Écrit en un seul pipeline 8 commandes (dénormalisation P2) :
      1. SET  simpy:campagne:{id}              — payload JSON complet (avec tirages)
      2. EXPIRE simpy:campagne:{id}            — TTL 30 jours
      3. SET  simpy:campagne:{id}:meta         — 6 métadonnées légères (~200 o)
      4. EXPIRE simpy:campagne:{id}:meta       — TTL 30 jours
      5. SET  simpy:campagne:{id}:tirages      — tirages bruts seuls (~1.8 Mo)
      6. EXPIRE simpy:campagne:{id}:tirages    — TTL 7 jours
      7. LPUSH simpy:circuit:{circuit}:history — id en tête de liste
      8. LTRIM simpy:circuit:{circuit}:history 0 19 — garde les 20 dernières

    Les états thermodynamiques par itération (`resultats.etats_par_iteration`,
    potentiellement volumineux — jusqu'à ~7,5 Mo à N=10 000) sont retirés de ce
    payload et écrits séparément, par lots (RPUSH), sous
    `simpy:campagne:{id}:etats` : le pipeline ci-dessus est atomique, et un
    payload trop gros le ferait échouer intégralement (413 Upstash), y compris
    le LPUSH d'historique — la campagne entière serait alors introuvable.

    Returns:
        True si le pipeline principal a réussi (les lots d'états sont
        best-effort : un lot en échec est loggé mais ne fait pas échouer la
        fonction — le cœur de la campagne est déjà sauvegardé à ce stade).
    """
    if not available():
        log.warning(
            "Upstash non configuré — save_campaign ignorée "
            "(circuit=%s, campagne_id=%s)", circuit_slug, campagne_id,
        )
        return False

    etats: list = []
    if "resultats" in response:
        resultats = dict(response["resultats"])
        etats = resultats.pop("etats_par_iteration", None) or []
        resultats["etats_par_iteration"] = []
        response = {**response, "resultats": resultats}

    payload_json = json.dumps(response)
    camp_key = f"simpy:campagne:{campagne_id}"
    hist_key = f"simpy:circuit:{circuit_slug}:history"

    CAMP_TTL_S = 86400 * 30    # 30 jours — les campagnes restent consultables un mois
    META_TTL_S = 86400 * 30    # 30 jours — les métadonnées suivent le payload
    TIRAGES_TTL_S = 86400 * 7  # 7 jours — les tirages bruts sont éphémères
    ETATS_BATCH_SIZE = 500     # ≈ 375 Ko/lot (8 pts × 5 champs) — large marge de sécurité
    ETATS_TTL_S = 86400 * 7    # 7 jours — éphémère, comme :tirages

    # Construire la métadonnée légère (6 champs)
    meta = {
        "campagne_id": campagne_id,
        "circuit": circuit_slug,
        "N_iterations": response.get("simulation", {}).get("N_iterations"),
        "echantillonnage": response.get("simulation", {}).get("echantillonnage"),
        "COP": (
            response.get("resultats", {})
            .get("statistiques", {})
            .get("COP", {})
            .get("moyenne")
        ),
        "STR": (
            response.get("resultats", {})
            .get("statistiques", {})
            .get("STR", {})
            .get("moyenne")
        ),
    }
    meta_json = json.dumps(meta)

    # Extraire les tirages bruts (s'ils existent)
    tirages = response.get("resultats", {}).get("tirages", [])
    tirages_json = json.dumps(tirages)

    try:
        _pipeline([
            ["SET", camp_key, payload_json],
            ["EXPIRE", camp_key, CAMP_TTL_S],
            ["SET", f"{camp_key}:meta", meta_json],
            ["EXPIRE", f"{camp_key}:meta", META_TTL_S],
            ["SET", f"{camp_key}:tirages", tirages_json],
            ["EXPIRE", f"{camp_key}:tirages", TIRAGES_TTL_S],
            ["LPUSH", hist_key, campagne_id],
            ["LTRIM", hist_key, 0, 19],
        ])
        log.info(
            "Campagne persistée : %s (%d octets, meta=%d o, tirages=%d o, circuit=%s)",
            campagne_id, len(payload_json), len(meta_json), len(tirages_json), circuit_slug,
        )
    except Exception as exc:
        log.error(
            "save_campaign échouée (circuit=%s, campagne_id=%s, payload=%d octets) : %s",
            circuit_slug, campagne_id, len(payload_json), exc,
        )
        return False

    etats_key = f"{camp_key}:etats"
    for i in range(0, len(etats), ETATS_BATCH_SIZE):
        batch = etats[i:i + ETATS_BATCH_SIZE]
        try:
            _pipeline([["RPUSH", etats_key, *[json.dumps(e) for e in batch]]])
        except Exception as exc:
            log.error(
                "Lot d'états [%d:%d] échoué pour %s : %s",
                i, i + len(batch), campagne_id, exc,
            )
            break
    if etats:
        try:
            _pipeline([["EXPIRE", etats_key, ETATS_TTL_S]])
        except Exception:
            pass

    return True