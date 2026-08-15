"""
Tests unitaires — collecte des états thermodynamiques par itération (A4-5).

Le bug corrigé : `simulation_n_*_cycle.csv` exportait toujours le même cycle
nominal (md5 identique quel que soit N), car `resultats.etats_cycle` n'est
calculé qu'une seule fois sur les valeurs nominales des paramètres — les états
des N cycles réellement résolus par la campagne étaient calculés dans
`_run_chunk()` puis jetés. Ces tests valident la collecte optionnelle
(`collecter_etats=True`) qui les conserve dans `resultats.etats_par_iteration`,
sans toucher au cycle nominal `resultats.etats_cycle`.
"""

import numpy as np
import pytest

from app.core.catalogue import PARAMETRES
from app.engine.monte_carlo import run_campaign
from app.schemas.reporting import Circuit, Cible, SimulationConfig
from app.api.routes.circuits import SORTIES

PARAMS_SOLAIRE = PARAMETRES[Circuit.solaire]
SORTIES_SOLAIRE = SORTIES[Circuit.solaire]


@pytest.fixture
def sim_N50() -> SimulationConfig:
    """Sous PARALLEL_THRESHOLD (150) — exerce le chemin séquentiel."""
    return SimulationConfig(N_iterations=50, seed=42, cible=Cible(valeur=12.0))


@pytest.fixture
def sim_N500() -> SimulationConfig:
    """Au-dessus de PARALLEL_THRESHOLD — exerce le chemin multi-process
    (rebasage de l'index d'itération après fusion des chunks)."""
    return SimulationConfig(N_iterations=500, seed=42, cible=Cible(valeur=12.0))


def test_etats_desactives_par_defaut(sim_N50):
    """Aucune régression : sans le flag, rien ne change."""
    res, _ = run_campaign(PARAMS_SOLAIRE, sim_N50, SORTIES_SOLAIRE)
    assert res.etats_par_iteration == []
    assert len(res.etats_cycle) == 8          # nominal toujours présent


def test_nombre_etats_collectes(sim_N50):
    res, _ = run_campaign(PARAMS_SOLAIRE, sim_N50, SORTIES_SOLAIRE,
                           collecter_etats=True)
    assert len(res.etats_par_iteration) == len(res.tirages)
    assert all(len(e["states"]) == 8 for e in res.etats_par_iteration)


def test_index_iteration_unique_et_contigu(sim_N500):
    """Vérifie le rebasage après fusion des chunks parallèles."""
    res, _ = run_campaign(PARAMS_SOLAIRE, sim_N500, SORTIES_SOLAIRE,
                           collecter_etats=True)
    idx = sorted(e["iteration"] for e in res.etats_par_iteration)
    assert idx == list(range(len(idx)))       # 0..N-1 sans doublon ni trou


def test_etats_varient_entre_iterations(sim_N50):
    """C'est le test qui échouait avant : les états ne doivent PAS être identiques."""
    res, _ = run_campaign(PARAMS_SOLAIRE, sim_N50, SORTIES_SOLAIRE,
                           collecter_etats=True)
    h8 = [e["states"][7]["h"] for e in res.etats_par_iteration]
    assert len(set(h8)) > 1
    assert np.std(h8) > 1.0                   # kJ/kg — T_g varie sur T(80,95,110)


def test_coherence_etats_vs_tirage(sim_N50):
    """L'état 8 doit correspondre au T_g tiré à la même itération."""
    res, _ = run_campaign(PARAMS_SOLAIRE, sim_N50, SORTIES_SOLAIRE,
                           collecter_etats=True)
    for e in res.etats_par_iteration[:10]:
        i = e["iteration"]
        T_g_tire = res.tirages[i]["T_g"]
        T_8 = e["states"][7]["T"]
        assert abs(T_8 - T_g_tire) < 0.5


def test_invariant_delta_h_par_iteration(sim_N50):
    """Δh_gen = h_8 - h_7 doit rester physiquement cohérent à chaque itération."""
    res, _ = run_campaign(PARAMS_SOLAIRE, sim_N50, SORTIES_SOLAIRE,
                           collecter_etats=True)
    for e in res.etats_par_iteration:
        dh = e["states"][7]["h"] - e["states"][6]["h"]
        assert 2300.0 < dh < 2700.0
