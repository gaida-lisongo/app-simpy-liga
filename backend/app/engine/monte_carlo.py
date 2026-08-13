"""
Moteur Monte Carlo — dimensionnement inverse stochastique SimpyLIGA.

Principe unique : Q_evap imposée (12 kW), paramètres incertains tirés par LHS.
Sorties distribuées : m_dot_p, m_dot_s, COP, mu, eta_ex.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

import numpy as np
from scipy.stats import qmc

from app.schemas.reporting import (
    ParametreIncertain, SimulationConfig,
    Resultats, StatSortie, Convergence,
)
from app.engine.distributions import build_ppf
from app.adapters.physics_adapter import run_cycle


def run_campaign(
    params: list[ParametreIncertain],
    config: SimulationConfig,
    sorties_suivies: list[str],
) -> tuple[Resultats, dict]:
    """
    Campagne Monte Carlo — dimensionnement inverse stochastique.

    1. Échantillonnage LHS des paramètres incertains
    2. Pour chaque tirage : run_cycle() → inverse 12 kW
    3. Filtrage des tirages non physiques
    4. Analyse statistique des sorties

    Returns:
        (Resultats, raw_arrays)
    """
    variables = [p for p in params if p.loi.value != "fixe"]
    fixes     = {p.nom: (p.valeur if p.valeur is not None else p.mode or 0.0)
                 for p in params if p.loi.value == "fixe"}

    d    = len(variables)
    n    = int(config.N_iterations)
    seed = int(config.seed)
    ppfs = [build_ppf(p) for p in variables]
    noms = [p.nom for p in variables]

    cible_kW = config.cible.valeur if config.cible else 12.0

    # Échantillonnage LHS
    if d > 0:
        sampler = qmc.LatinHypercube(d=d, seed=seed)
        u = sampler.random(n)
    else:
        u = np.zeros((n, 0))

    # Boucle Monte Carlo
    collected: dict[str, list[float]] = {s: [] for s in sorties_suivies}
    n_rejets = 0

    for i in range(n):
        tirage = dict(fixes)
        for j, nom in enumerate(noms):
            tirage[nom] = float(ppfs[j](float(u[i, j])))

        out = run_cycle(tirage, cible_kW=cible_kW)

        if not out.get("physically_valid", False):
            n_rejets += 1
            continue

        for s in sorties_suivies:
            if s in out and isinstance(out[s], (int, float)):
                collected[s].append(float(out[s]))

    # Analyse statistique
    resultats = Resultats()
    raw: dict[str, np.ndarray] = {}

    for s, vals in collected.items():
        arr = np.asarray(vals, dtype=float)
        raw[s] = arr
        if arr.size == 0:
            resultats.statistiques[s] = StatSortie()
            continue
        resultats.statistiques[s] = StatSortie(
            moyenne=float(np.mean(arr)),
            ecart_type=float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0,
            mediane=float(np.median(arr)),
            IC95=[float(np.percentile(arr, 2.5)),
                  float(np.percentile(arr, 97.5))],
            minimum=float(np.min(arr)),
            maximum=float(np.max(arr)),
        )

    # Étude de convergence sur la sortie principale
    principal = sorties_suivies[0] if sorties_suivies else None
    if principal and raw.get(principal, np.array([])).size > 50:
        resultats.convergence = _convergence(raw[principal])

    resultats.taux_rejet_non_physique_pct = round(100.0 * n_rejets / max(n, 1), 3)
    return resultats, raw


def _convergence(arr: np.ndarray, tol: float = 0.01) -> Convergence:
    n      = arr.size
    grille = np.unique(np.linspace(50, n, 20, dtype=int))
    moyennes = np.array([arr[:k].mean() for k in grille])
    ref    = moyennes[-1]
    rel    = np.abs(moyennes - ref) / (abs(ref) + 1e-12)
    stables = grille[rel < tol]
    N_stable = int(stables[0]) if stables.size else None
    return Convergence(N_stable=N_stable, stabilise=N_stable is not None)
