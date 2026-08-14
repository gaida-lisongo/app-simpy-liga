"""
Fiabilité (M2) — probabilité qu'une sortie satisfasse un seuil, avec
intervalle de confiance exact (Clopper-Pearson).

Calcul purement statistique sur des tirages déjà obtenus (resultats.tirages
d'une campagne complétée) — pas de nouvel appel solveur, pas de nouvelle
campagne : évite de dupliquer la logique seed/config d'une campagne Monte
Carlo pour une simple lecture de proportion.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

from fastapi import HTTPException
from scipy.stats import beta

from app.schemas.reporting import FiabiliteRequest, FiabiliteResponse


def compute_fiabilite(req: FiabiliteRequest) -> FiabiliteResponse:
    if req.sens not in ("gte", "lte"):
        raise HTTPException(400, "sens doit être 'gte' ou 'lte'")

    vals = [t[req.grandeur] for t in req.tirages if req.grandeur in t]
    n = len(vals)
    if n == 0:
        raise HTTPException(400, f"Aucun tirage ne contient la grandeur '{req.grandeur}'")

    if req.sens == "gte":
        k = sum(1 for v in vals if v >= req.seuil)
    else:
        k = sum(1 for v in vals if v <= req.seuil)

    p_hat = k / n
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))

    return FiabiliteResponse(
        grandeur=req.grandeur,
        seuil=req.seuil,
        sens=req.sens,
        n_total=n,
        n_succes=k,
        p_hat=round(p_hat, 5),
        IC95=[round(lo, 5), round(hi, 5)],
    )
