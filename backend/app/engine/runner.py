"""
Runner asynchrone — lance une campagne Monte Carlo en arrière-plan et publie la
progression + le résultat final sur la file Redis (pub/sub via liste LPUSH/RPOP).

Principe : l'endpoint /run retourne immédiatement un ack {campagne_id, channel} ;
le thread worker exécute run_campaign(), pousse des événements {progress} puis
{done, result} (ou {error}) dans la liste Redis. L'UI écoute cette liste via SSE
(SvelteKit /db/campagne/{id}/events) et se met à jour en temps réel.

N_iterations est plafonné à N_MAX (10 000) côté serveur.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone

from app.engine.monte_carlo import run_campaign
from app.engine.sensitivity import N_SOBOL_DEFAUT
from app.schemas.reporting import ReportingResponse, MetaArticle
from app.core.catalogue import META, PERIMETRES
from app.core import upstash

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

    def progress_cb(n_done: int, n_total: int) -> None:
        if n_done % step == 0 or n_done == n_total:
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
            upstash.push_event(campagne_id, {
                "type": "done",
                "campagne_id": campagne_id,
                "result": resp.model_dump(mode="json"),
            })
        except Exception as e:  # noqa: BLE001
            upstash.push_event(campagne_id, {"type": "error", "message": str(e)})

    threading.Thread(target=worker, daemon=True).start()
    return {
        "campagne_id": campagne_id,
        "statut": "en_cours",
        "channel": channel,
        "N_iterations": sim.N_iterations,
    }