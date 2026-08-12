"""
Routes API — circuits et dashboard.

Expose pour chaque circuit :
  GET  /api/{circuit}/config     -> configuration par défaut (paramètres+lois)
  POST /api/{circuit}/run        -> lance une campagne, renvoie le reporting JSON
Et un agrégat :
  GET  /api/dashboard            -> synthèse globale multi-circuits

`circuit` ∈ {moteur, frigorifique, couplage, solaire}.

Auteur : Projet Thèse R718 — SimpyLIGA
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.schemas.reporting import (
    Circuit, CampagneRequest, ReportingResponse, MetaArticle,
    SimulationConfig, ModeSimulation, Cible,
)
from app.core.catalogue import get_default_config, META, PERIMETRES, PARAMETRES
from app.engine.monte_carlo import run_campaign
from app.adapters.physics_adapter import core_is_real

router = APIRouter(prefix="/api", tags=["circuits"])


def _campagne_id() -> str:
    return datetime.now(timezone.utc).strftime("camp_%Y%m%dT%H%M%SZ")


@router.get("/health")
def health() -> dict:
    """Sonde de vie + indique si le cœur physique réel est branché."""
    return {"statut": "ok", "coeur_physique_reel": core_is_real()}


@router.get("/{circuit}/config", response_model=ReportingResponse)
def get_config(circuit: Circuit) -> ReportingResponse:
    """Retourne la configuration par défaut d'un circuit (sans simuler)."""
    cfg = get_default_config(circuit)
    mode = ModeSimulation.inverse if circuit == Circuit.frigorifique else ModeSimulation.direct
    cible = Cible() if mode == ModeSimulation.inverse else None
    return ReportingResponse(
        article=MetaArticle(circuit=circuit, **cfg["meta"]),
        perimetre=cfg["perimetre"],
        simulation=SimulationConfig(mode=mode, cible=cible),
        statut="config",
        message="Configuration par défaut (paramètres et lois indicatifs).",
    )


@router.post("/{circuit}/run", response_model=ReportingResponse)
def run(circuit: Circuit, req: CampagneRequest | None = None) -> ReportingResponse:
    """
    Lance une campagne Monte Carlo pour le circuit et renvoie le reporting.

    Si le corps est vide, la configuration par défaut du catalogue est utilisée
    — pratique pour un premier appel de démonstration depuis le frontend.
    """
    if req is None:
        params = PARAMETRES[circuit]
        mode = ModeSimulation.inverse if circuit == Circuit.frigorifique else ModeSimulation.direct
        sim = SimulationConfig(mode=mode,
                               cible=Cible() if mode == ModeSimulation.inverse else None)
        sorties = _default_sorties(circuit)
    else:
        if req.circuit != circuit:
            raise HTTPException(400, "Le circuit du corps ne correspond pas à l'URL.")
        params = req.parametres_incertains or PARAMETRES[circuit]
        sim = req.simulation
        sorties = req.sorties_suivies or _default_sorties(circuit)

    resultats, _raw = run_campaign(params, sim, sorties)

    return ReportingResponse(
        article=MetaArticle(circuit=circuit, **META[circuit]),
        perimetre=PERIMETRES[circuit],
        simulation=sim,
        resultats=resultats,
        campagne_id=_campagne_id(),
        statut="ok",
        message=f"Campagne {sim.N_iterations} tirages ({sim.echantillonnage}).",
    )


@router.get("/dashboard")
def dashboard() -> dict:
    """
    Synthèse globale : lance une campagne rapide par circuit et agrège les COP.

    Destiné à la page d'accueil (/) : statistique globale du système,
    aperçu exergétique et repères d'optimisation.
    """
    apercu = {}
    for circuit in Circuit:
        mode = ModeSimulation.inverse if circuit == Circuit.frigorifique else ModeSimulation.direct
        sim = SimulationConfig(N_iterations=2000, mode=mode,
                               cible=Cible() if mode == ModeSimulation.inverse else None)
        res, _ = run_campaign(PARAMETRES[circuit], sim, _default_sorties(circuit))
        cop = res.statistiques.get("COP")
        eta = res.statistiques.get("eta_ex")
        apercu[circuit.value] = {
            "id": META[circuit]["id"],
            "titre": META[circuit]["titre"],
            "COP": cop.model_dump() if cop else None,
            "eta_ex": eta.model_dump() if eta else None,
            "taux_rejet_pct": res.taux_rejet_non_physique_pct,
        }
    return {
        "statut": "ok",
        "coeur_physique_reel": core_is_real(),
        "circuits": apercu,
        "campagne_id": _campagne_id(),
    }


def _default_sorties(circuit: Circuit) -> list[str]:
    """Grandeurs suivies par défaut selon le circuit."""
    base = {
        Circuit.moteur:       ["COP", "mu", "m_dot_pri", "Q_gen", "eta_ex"],
        Circuit.frigorifique: ["Q_evap", "m_dot_sec", "COP", "eta_ex"],
        Circuit.couplage:     ["mu", "COP", "eta_ex", "Q_gen"],
        Circuit.solaire:      ["Q_solaire", "COP", "eta_ex"],
    }
    return base[circuit]
