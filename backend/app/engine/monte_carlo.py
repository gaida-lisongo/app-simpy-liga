"""
Moteur Monte Carlo — dimensionnement inverse stochastique SimpyLIGA.

Principe unique : Q_evap imposée (12 kW), paramètres incertains tirés par LHS.
Sorties distribuées : m_dot_p, m_dot_s, COP, mu, eta_ex.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

import math
from typing import Callable, Optional

import numpy as np
from scipy.stats import qmc

from app.schemas.reporting import (
    ParametreIncertain, SimulationConfig,
    Resultats, StatSortie, Convergence, EtatCycle, BilanEnergetique,
    ProfilTube, CourbesCPC, SankeySolaire,
)
from app.engine.distributions import build_ppf, nominal_value
from app.engine.pool import get_executor, MAX_WORKERS
from app.adapters.physics_adapter import run_cycle

# En dessous de ce nombre de tirages, l'overhead de répartition entre process
# (sérialisation + IPC) dépasse le gain — on reste séquentiel dans le process
# courant.
PARALLEL_THRESHOLD = 150


def _run_chunk(
    tirages: list[dict[str, float]],
    noms: list[str],
    sorties_suivies: list[str],
    cible_kW: float,
) -> dict:
    """
    Exécuté dans un worker process : calcule run_cycle() pour un lot de
    tirages déjà résolus (valeurs numériques pures — rien à pickler côté
    fonctions/closures). Fonction module-level pour rester picklable par
    référence.
    """
    collected: dict[str, list[float]] = {s: [] for s in sorties_suivies}
    lignes: list[dict[str, float]] = []
    n_rejets = 0
    for tirage in tirages:
        out = run_cycle(tirage, cible_kW=cible_kW)
        if not out.get("physically_valid", False):
            n_rejets += 1
            continue
        ligne: dict[str, float] = {nom: tirage[nom] for nom in noms}
        for s in sorties_suivies:
            if s in out and isinstance(out[s], (int, float)):
                collected[s].append(float(out[s]))
                ligne[s] = float(out[s])
        lignes.append(ligne)
    return {"collected": collected, "lignes": lignes, "n_rejets": n_rejets}


def _chunked(items: list, n_chunks: int) -> list[list]:
    """Découpe `items` en `n_chunks` tranches contiguës (ordre préservé)."""
    n = len(items)
    if n_chunks <= 1:
        return [items]
    size = math.ceil(n / n_chunks)
    return [items[i:i + size] for i in range(0, n, size)]


def run_campaign(
    params: list[ParametreIncertain],
    config: SimulationConfig,
    sorties_suivies: list[str],
    progress_cb: Optional[Callable[[int, int], None]] = None,
    N_sobol: Optional[int] = None,
) -> tuple[Resultats, dict]:
    """
    Campagne Monte Carlo — dimensionnement inverse stochastique.

    1. Échantillonnage LHS des paramètres incertains
    2. Pour chaque tirage : run_cycle() → inverse 12 kW
    3. Filtrage des tirages non physiques
    4. Analyse statistique des sorties

    N_sobol : si fourni (M1), calcule aussi les indices de Sobol (Saltelli,
    SALib) via un échantillonnage dédié de N_sobol*(d+2) appels solveur,
    indépendant de N_iterations. None (défaut) = pas de calcul Sobol — évite
    de ralentir les appels directs à run_campaign() (tests, campagnes rapides)
    qui n'en ont pas besoin.

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

    # Résolution des tirages (ppf(u) -> valeurs numériques) — rapide, pas de
    # CoolProp ici, on le fait dans le process principal pour ne pas avoir à
    # pickler les closures ppfs vers les workers.
    all_tirages: list[dict[str, float]] = []
    for i in range(n):
        tirage = dict(fixes)
        for j, nom in enumerate(noms):
            tirage[nom] = float(ppfs[j](float(u[i, j])))
        all_tirages.append(tirage)

    collected: dict[str, list[float]] = {s: [] for s in sorties_suivies}
    tirages_bruts: list[dict[str, float]] = []
    n_rejets = 0

    if n >= PARALLEL_THRESHOLD and MAX_WORKERS > 1:
        # Répartition multi-process (CPU-bound : le GIL interdit tout gain
        # réel via des threads, chaque tirage est indépendant des autres).
        n_chunks = min(n, max(MAX_WORKERS * 4, 40))
        chunks = _chunked(all_tirages, n_chunks)
        executor = get_executor()
        futures = [
            executor.submit(_run_chunk, chunk, noms, sorties_suivies, cible_kW)
            for chunk in chunks
        ]
        done = 0
        for chunk, future in zip(chunks, futures):
            result = future.result()
            for s in sorties_suivies:
                collected[s].extend(result["collected"][s])
            tirages_bruts.extend(result["lignes"])
            n_rejets += result["n_rejets"]
            done += len(chunk)
            if progress_cb is not None:
                progress_cb(done, n)
    else:
        for tirage in all_tirages:
            out = run_cycle(tirage, cible_kW=cible_kW)
            if not out.get("physically_valid", False):
                n_rejets += 1
            else:
                ligne: dict[str, float] = {nom: tirage[nom] for nom in noms}
                for s in sorties_suivies:
                    if s in out and isinstance(out[s], (int, float)):
                        collected[s].append(float(out[s]))
                        ligne[s] = float(out[s])
                tirages_bruts.append(ligne)

    if progress_cb is not None:
        progress_cb(n, n)

    # Cycle de référence (paramètres à leur valeur nominale) — pour les diagrammes
    # thermodynamiques et le bilan énergétique, plutôt qu'un tirage aléatoire quelconque.
    nominal = dict(fixes)
    for p in variables:
        nominal[p.nom] = nominal_value(p)
    ref = run_cycle(nominal, cible_kW=cible_kW, include_states=True)

    # Analyse statistique
    resultats = Resultats()
    resultats.tirages = tirages_bruts

    if ref.get("physically_valid", False):
        resultats.etats_cycle = [EtatCycle(**s) for s in ref.get("states", [])]
        resultats.bilan_energetique = BilanEnergetique(
            Q_evap=ref.get("Q_evap"), Q_gen=ref.get("Q_gen"),
            Q_cond=ref.get("Q_cond"), W_pompe=ref.get("W_pompe"),
            COP=ref.get("COP"),
        )

    # Enrichissement spécifique circuit solaire (profil_tube, courbes_cpc, sankey)
    _solar_keys = {"G", "eta_col", "A_col"}
    if any(p.nom in _solar_keys for p in params):
        from app.adapters.physics_adapter import (
            compute_profil_tube, compute_courbes_cpc, compute_sankey_solaire,
        )
        _nom = {p.nom: nominal_value(p) for p in params}
        _Q_sol   = _nom.get("G", 800) * _nom.get("A_col", 85) / 1000
        _Q_opt   = _Q_sol * _nom.get("eta_col", 0.68)
        _Q_utile = _Q_opt * (1 - _nom.get("phi_s", 0.10))

        resultats.profil_tube = ProfilTube(**compute_profil_tube(_Q_utile))
        resultats.courbes_cpc = CourbesCPC(**compute_courbes_cpc(
            eta_col_nom=_nom.get("eta_col", 0.68),
            phi_s_nom=_nom.get("phi_s", 0.10),
            cop_ref=ref.get("COP", 0.35) if ref.get("physically_valid", False) else 0.35))
        resultats.sankey_solaire = SankeySolaire(
            **compute_sankey_solaire(_Q_sol, _Q_opt, _Q_utile))

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

    # Étude de convergence — pire cas sur toutes les sorties suivies (pas
    # seulement sorties_suivies[0], qui n'est pas garanti être la plus lente
    # à converger : c'est un ordre de liste arbitraire, cf. A4).
    convergences = {
        s: _convergence(raw[s])
        for s in sorties_suivies
        if raw.get(s, np.array([])).size > 50
    }
    if convergences:
        non_stabilisees = [c for c in convergences.values() if not c.stabilise]
        resultats.convergence = (
            non_stabilisees[0] if non_stabilisees
            else max(convergences.values(), key=lambda c: c.N_stable or 0)
        )

    resultats.taux_rejet_non_physique_pct = round(100.0 * n_rejets / max(n, 1), 3)

    if N_sobol:
        from app.engine.sensitivity import compute_sobol
        resultats.sensibilite_sobol = compute_sobol(
            params, sorties_suivies, cible_kW, N_sobol=N_sobol)

    return resultats, raw


def _premier_index_stable(sous_tol: np.ndarray) -> Optional[int]:
    """
    Premier indice à partir duquel TOUT le reste de `sous_tol` est True
    (stabilité soutenue), pas le premier True isolé (qui peut être suivi
    d'une re-divergence — A4).
    """
    for i in range(len(sous_tol)):
        if sous_tol[i:].all():
            return i
    return None


def _convergence(arr: np.ndarray, tol: float = 0.01) -> Convergence:
    n      = arr.size
    grille = np.unique(np.linspace(50, n, 20, dtype=int))
    moyennes = np.array([arr[:k].mean() for k in grille])
    ref    = moyennes[-1]
    rel    = np.abs(moyennes - ref) / (abs(ref) + 1e-12)
    idx    = _premier_index_stable(rel < tol)
    N_stable = int(grille[idx]) if idx is not None else None
    return Convergence(N_stable=N_stable, stabilise=N_stable is not None)
