"""
Runner asynchrone — lance une campagne Monte Carlo en arrière-plan et publie la
progression + le résultat final sur la file Redis (pub/sub via liste LPUSH/RPOP).

Principe : l'endpoint /run retourne immédiatement un ack {campagne_id, channel} ;
le thread worker exécute run_campaign(), pousse des événements {progress} puis
{done} (léger — sans tirages bruts) dans la liste Redis. Le résultat complet
est persisté côté serveur via save_campaign(). L'UI écoute cette liste via SSE
(SvelteKit /db/campagne/{id}/events) et se met à jour en temps réel, puis
re-fetch la campagne complète via /db/campagne/{id}.

N_iterations est plafonné à N_MAX (10 000) côté serveur.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

import copy
import logging
import threading
from datetime import datetime, timezone

from app.engine.monte_carlo import run_campaign
from app.engine.sensitivity import N_SOBOL_DEFAUT
from app.schemas.reporting import ReportingResponse, MetaArticle
from app.core.catalogue import META, PERIMETRES
from app.core import upstash

log = logging.getLogger(__name__)

# Plafond de tirages — au-delà, le coût computationnel est prohibitif (solveur
# CoolProp par tirage + sérialisation Pydantic des tirages bruts).
N_MAX = 10000


def _now() -> str:
    return datetime.now(timezone.utc).strftime("camp_%Y%m%dT%H%M%SZ")


def start_run(circuit, params, sim, sorties) -> dict:
    """
    Lance la campagne en arrière-plan et renvoie un ack immédiat.

    Args:
        circuit   : Circuit (enum)
        params    : list[ParametreIncertain]
        sim       : SimulationConfig (muté : N_iterations plafonné à N_MAX)
        sorties   : list[str] — sorties suivies
    Returns:
        dict {campagne_id, statut, channel, N_iterations}
    """
    sim.N_iterations = max(1, min(int(sim.N_iterations), N_MAX))
    campagne_id = _now()
    channel = f"simpy:campagne:{campagne_id}:events"

    step = max(1, sim.N_iterations // 200)
    _last_reported = 0

    def progress_cb(n_done: int, n_total: int) -> None:
        nonlocal _last_reported
        # Le moteur peut appeler ce callback par lots de taille variable
        # (chunks parallèles) plutôt qu'à chaque tirage : on ne compte plus
        # sur une correspondance exacte au modulo, seulement sur l'écart
        # cumulé depuis le dernier événement publié.
        if n_done - _last_reported >= step or n_done >= n_total:
            _last_reported = n_done
            upstash.push_event(campagne_id, {
                "type": "progress",
                "n_done": n_done,
                "n_total": n_total,
                "pct": round(100.0 * n_done / n_total, 1) if n_total else 0.0,
            })

    def worker() -> None:
        try:
            resultats, _ = run_campaign(params, sim, sorties, progress_cb=progress_cb,
                                        N_sobol=N_SOBOL_DEFAUT)
            cible_v = sim.cible.valeur if sim.cible else 12.0
            resp = ReportingResponse(
                article=MetaArticle(circuit=circuit, **META[circuit]),
                perimetre=PERIMETRES[circuit],
                simulation=sim,
                parametres_incertains=params,
                resultats=resultats,
                campagne_id=campagne_id,
                statut="ok",
                message=f"Inv. {sim.N_iterations} tirages LHS — cible {cible_v} kW.",
            )

            # 1. Persistance server-side du payload COMPLET (avec tirages)
            payload_complet = resp.model_dump(mode="json")
            ok = upstash.save_campaign(circuit.value, campagne_id, payload_complet)

            # 2. Construire l'événement done LÉGER (copie sans tirages bruts)
            done_event = copy.deepcopy(payload_complet)
            if "resultats" in done_event and isinstance(done_event["resultats"], dict):
                done_event["resultats"]["tirages"] = []
            done_event["persiste"] = ok

            upstash.push_event(campagne_id, {
                "type": "done",
                "campagne_id": campagne_id,
                "result": done_event,
            })

            # 3. Si la persistance a échoué, signaler l'erreur après le done
            if not ok:
                upstash.push_event(campagne_id, {
                    "type": "error",
                    "message": "Persistance Redis échouée — résultats affichés mais non sauvegardés",
                })

        except Exception as e:  # noqa: BLE001
            log.exception("Erreur dans le worker de la campagne %s", campagne_id)
            upstash.push_event(campagne_id, {"type": "error", "message": str(e)})

    threading.Thread(target=worker, daemon=True).start()
    return {
        "campagne_id": campagne_id,
        "statut": "en_cours",
        "channel": channel,
        "N_iterations": sim.N_iterations,
    }