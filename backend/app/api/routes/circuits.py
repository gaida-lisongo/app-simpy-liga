"""
Routes API — un endpoint par circuit + dashboard global.

Principe unique : dimensionnement INVERSE, cible Q_evap = 12 kW.
Les sorties distribuées sont : m_dot_p, m_dot_s, COP, mu, eta_ex.

GET  /api/{circuit}/config  → paramètres incertains par défaut
POST /api/{circuit}/run     → campagne Monte Carlo, retourne reporting JSON
GET  /api/dashboard         → synthèse globale des 4 circuits

{circuit} ∈ {moteur, frigorifique, couplage, solaire}

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.schemas.reporting import (
    Circuit, CampagneRequest, ReportingResponse,
    MetaArticle, SimulationConfig, Cible,
)
from app.core.catalogue import get_default_config, META, PERIMETRES, PARAMETRES
from app.engine.monte_carlo import run_campaign
from app.adapters.physics_adapter import core_is_real

router = APIRouter(prefix="/api", tags=["circuits"])

# Sorties pertinentes par circuit (dimensionnement inverse)
SORTIES: dict[Circuit, list[str]] = {
    Circuit.moteur:       ["COP", "mu", "m_dot_pri", "Q_gen",  "eta_ex"],
    Circuit.frigorifique: ["COP", "mu", "m_dot_pri", "m_dot_sec", "eta_ex"],
    Circuit.couplage:     ["COP", "mu", "Q_gen",     "eta_ex"],
    Circuit.solaire:      ["COP", "mu", "Q_gen",     "eta_ex"],
}

_CIBLE_DEFAUT = Cible(grandeur="Q_e", valeur=12.0, unite="kW", tol_pct=5.0)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("camp_%Y%m%dT%H%M%SZ")


@router.get("/health")
def health() -> dict:
    return {"statut": "ok", "coeur_physique_reel": core_is_real()}


@router.get("/{circuit}/config", response_model=ReportingResponse)
def get_config(circuit: Circuit) -> ReportingResponse:
    """Retourne les paramètres incertains par défaut sans simuler."""
    cfg = get_default_config(circuit)
    return ReportingResponse(
        article=MetaArticle(circuit=circuit, **cfg["meta"]),
        perimetre=cfg["perimetre"],
        simulation=SimulationConfig(cible=_CIBLE_DEFAUT),
        parametres_incertains=cfg["parametres_incertains"],
        statut="config",
        message="Configuration par défaut — dimensionnement inverse 12 kW.",
    )


@router.post("/{circuit}/run", response_model=ReportingResponse)
def run(circuit: Circuit, req: CampagneRequest | None = None) -> ReportingResponse:
    """
    Lance une campagne Monte Carlo (dimensionnement inverse).
    Corps vide = configuration catalogue par défaut.
    """
    if req is None:
        params  = PARAMETRES[circuit]
        sim     = SimulationConfig(cible=_CIBLE_DEFAUT)
        sorties = SORTIES[circuit]
    else:
        if req.circuit != circuit:
            raise HTTPException(400, "Circuit du corps ≠ circuit de l'URL.")
        params  = req.parametres_incertains or PARAMETRES[circuit]
        sim     = req.simulation
        sim.cible = sim.cible or _CIBLE_DEFAUT   # garantir la cible
        sorties = req.sorties_suivies or SORTIES[circuit]

    resultats, _ = run_campaign(params, sim, sorties)

    return ReportingResponse(
        article=MetaArticle(circuit=circuit, **META[circuit]),
        perimetre=PERIMETRES[circuit],
        simulation=sim,
        parametres_incertains=params,
        resultats=resultats,
        campagne_id=_now(),
        statut="ok",
        message=f"Inv. {sim.N_iterations} tirages LHS — cible {sim.cible.valeur} kW.",
    )


@router.get("/dashboard")
def dashboard() -> dict:
    """Synthèse globale : campagne rapide (500 tirages) par circuit."""
    apercu = {}
    sim = SimulationConfig(N_iterations=500, cible=_CIBLE_DEFAUT)

    for circuit in Circuit:
        res, _ = run_campaign(PARAMETRES[circuit], sim, SORTIES[circuit])
        cop    = res.statistiques.get("COP")
        eta    = res.statistiques.get("eta_ex")
        m_dot  = res.statistiques.get("m_dot_pri")
        apercu[circuit.value] = {
            "id":    META[circuit]["id"],
            "titre": META[circuit]["titre"],
            "COP":      cop.model_dump()   if cop   else None,
            "eta_ex":   eta.model_dump()   if eta   else None,
            "m_dot_pri": m_dot.model_dump() if m_dot else None,
            "taux_rejet_pct": res.taux_rejet_non_physique_pct,
        }

    return {
        "statut": "ok",
        "cible_kW": 12.0,
        "coeur_physique_reel": core_is_real(),
        "circuits": apercu,
        "campagne_id": _now(),
    }
