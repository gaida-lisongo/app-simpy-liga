"""
Moteur Monte Carlo — cœur stochastique de SimpyLIGA.

Chaîne complète : échantillonnage Latin Hypercube -> propagation via
l'adaptateur physique -> filtrage des tirages non physiques -> analyse
statistique (descriptif, IC95, convergence). L'analyse de sensibilité Sobol
et les tests avancés sont branchés séparément (module analysis, à venir).

Auteur : Projet Thèse R718 — SimpyLIGA
"""

from __future__ import annotations

import numpy as np
from scipy.stats import qmc

from app.schemas.reporting import (
    ParametreIncertain, SimulationConfig, Resultats, StatSortie,
    Convergence, ModeSimulation,
)
from app.engine.distributions import build_ppf
from app.adapters.physics_adapter import run_cycle


def _lhs_unit(n: int, d: int, seed: int) -> np.ndarray:
    """Échantillon Latin Hypercube dans [0,1]^d (n points)."""
    sampler = qmc.LatinHypercube(d=d, seed=seed)
    return sampler.random(n)


def run_campaign(
    params: list[ParametreIncertain],
    config: SimulationConfig,
    sorties_suivies: list[str],
) -> tuple[Resultats, dict]:
    """
    Exécute une campagne Monte Carlo complète.

    Args:
        params: paramètres incertains du circuit.
        config: configuration de simulation (N, seed, mode, cible).
        sorties_suivies: grandeurs à agréger statistiquement.

    Returns:
        (Resultats, raw) où raw contient les tableaux bruts par sortie
        (utile pour l'export CSV et les graphiques).
    """
    variables = [p for p in params if p.loi.value != "fixe"]
    fixes = {p.nom: (p.valeur if p.valeur is not None else p.mode)
             for p in params if p.loi.value == "fixe"}

    d = len(variables)
    n = int(config.N_iterations)
    seed = int(config.seed)
    ppfs = [build_ppf(p) for p in variables]
    noms = [p.nom for p in variables]

    # 1) Échantillonnage
    u = _lhs_unit(n, d, seed) if d > 0 else np.zeros((n, 0))

    # 2) Propagation
    cible = config.cible.valeur if (config.cible and
                                    config.mode == ModeSimulation.inverse) else None
    collected: dict[str, list[float]] = {s: [] for s in sorties_suivies}
    n_rejets = 0

    for i in range(n):
        tirage = dict(fixes)
        for j, nom in enumerate(noms):
            tirage[nom] = float(ppfs[j](u[i, j]))

        out = run_cycle(tirage, mode=config.mode.value, cible_kW=cible)

        # 3) Filtrage des cas non physiques
        if not out.get("physically_valid", True):
            n_rejets += 1
            continue
        for s in sorties_suivies:
            if s in out and isinstance(out[s], (int, float)):
                collected[s].append(float(out[s]))

    # 4) Analyse descriptive
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
            IC95=[float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))],
            minimum=float(np.min(arr)),
            maximum=float(np.max(arr)),
        )

    # 5) Étude de convergence sur la sortie principale (première suivie)
    principal = sorties_suivies[0] if sorties_suivies else None
    if principal and raw.get(principal) is not None and raw[principal].size > 50:
        resultats.convergence = _convergence(raw[principal])

    resultats.taux_rejet_non_physique_pct = round(100.0 * n_rejets / max(n, 1), 3)
    return resultats, raw


def _convergence(arr: np.ndarray, tol: float = 0.01) -> Convergence:
    """
    Détermine à partir de quel N la moyenne cumulée se stabilise.

    Stabilisation = variation relative de la moyenne cumulée sous `tol`
    sur les 10 derniers pas d'un balayage logarithmique.
    """
    n = arr.size
    grille = np.unique(np.linspace(50, n, 20, dtype=int))
    moyennes = np.array([arr[:k].mean() for k in grille])
    ref = moyennes[-1]
    rel = np.abs(moyennes - ref) / (abs(ref) + 1e-12)
    stables = grille[rel < tol]
    N_stable = int(stables[0]) if stables.size else None
    return Convergence(N_stable=N_stable, stabilise=N_stable is not None)
