"""Tests unitaires du moteur Monte Carlo — convergence (A4)."""

import numpy as np

from app.engine.monte_carlo import _convergence, _premier_index_stable


def test_premier_index_stable_ignore_croisement_isole():
    """
    Un croisement isolé suivi d'une re-divergence ne doit PAS être retenu —
    seul un plateau de stabilité soutenue jusqu'à la fin de la grille compte.
    """
    sous_tol = np.array([False, False, True, False, False, False, True, True, True])
    assert _premier_index_stable(sous_tol) == 6


def test_premier_index_stable_jamais_stable():
    sous_tol = np.array([False, True, False, True, False])
    assert _premier_index_stable(sous_tol) is None


def test_premier_index_stable_stable_des_le_debut():
    sous_tol = np.array([True, True, True])
    assert _premier_index_stable(sous_tol) == 0


def test_convergence_serie_instable_force_N_stable_tardif():
    """
    Le dernier point de grille se compare toujours à lui-même (écart nul par
    construction), donc `stabilise` est trivialement vrai au pire point (N=n).
    Une série qui n'arrête jamais d'osciller avant la fin doit donc reporter
    N_stable proche de n (pas un point intermédiaire trompeusement stable).
    """
    n = 500
    arr = 100.0 + 50.0 * np.sin(np.arange(n, dtype=float) / 3.0)
    conv = _convergence(arr, tol=0.0001)
    assert conv.stabilise is True
    assert conv.N_stable == n


def test_convergence_pire_sortie_via_run_campaign():
    """
    A4 : resultats.convergence doit refléter la sortie la plus lente à
    converger parmi sorties_suivies, pas seulement sorties_suivies[0].
    """
    from app.schemas.reporting import Circuit, SimulationConfig, Cible
    from app.core.catalogue import PARAMETRES
    from app.engine.monte_carlo import run_campaign

    sim = SimulationConfig(N_iterations=200, cible=Cible(valeur=12.0))
    sorties = ["Q_utile", "eta_th", "STR", "m_dot_pri", "eta_ex", "COP"]
    resultats, raw = run_campaign(PARAMETRES[Circuit.solaire], sim, sorties)

    # Convergence individuelle de chaque sortie suivie, calculée indépendamment.
    from app.engine.monte_carlo import _convergence as conv_fn
    par_sortie = {
        s: conv_fn(raw[s]) for s in sorties if raw.get(s, np.array([])).size > 50
    }
    non_stabilisees = [c for c in par_sortie.values() if not c.stabilise]
    if non_stabilisees:
        assert resultats.convergence.stabilise is False
    else:
        pire_N = max(c.N_stable or 0 for c in par_sortie.values())
        assert resultats.convergence.N_stable == pire_N
