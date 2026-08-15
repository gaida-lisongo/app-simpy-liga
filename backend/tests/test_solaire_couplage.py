"""
Tests A4-2 — correction de l'écrasement de m_dot_pri et Q_gen dans le circuit
solaire. Avant correction, _run_cycle_solaire() écrasait les grandeurs réelles
du solveur (m_dot_p, Q_gen) par des valeurs déduites du champ solaire
(Q_utile / delta_h, Q_utile), rendant COP = Q_evap / Q_gen incohérent avec le
COP réellement calculé par le solveur (0.292 vs 1.0094 mesuré sur 305 tirages).

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from app.adapters.physics_adapter import _run_cycle_solaire, _solve_cycle_from_params

PARAMS_NOMINAUX = {
    "G": 800.0, "eta_col": 0.68, "T_0": 25.0, "A_col": 85.0, "phi_s": 0.10,
    "T_g": 95.0, "T_e": 8.0, "T_c": 35.0,
    "eta_is_p": 0.75, "eta_n": 0.92, "eta_d": 0.85, "eta_m": 1.00,
}


def test_solaire_q_evap_reste_12kW():
    """Le mode inverse doit être préservé : Q_evap = 12 kW imposée."""
    out = _run_cycle_solaire(PARAMS_NOMINAUX, cible_kW=12.0)
    assert abs(out["Q_evap"] - 12.0) < 0.5


def test_solaire_coherence_COP():
    """COP = Q_evap / Q_gen doit être vérifié dans le dict exporté.
    C'est le test qui échouait avant correction (0.292 vs 1.009)."""
    out = _run_cycle_solaire(PARAMS_NOMINAUX, cible_kW=12.0)
    cop_reconstruit = out["Q_evap"] / out["Q_gen"]
    assert abs(cop_reconstruit - out["COP"]) / out["COP"] < 0.01


def test_solaire_m_dot_pri_ordre_grandeur():
    """Débit réel ≈ 0.0046 kg/s (référence mémoire), PAS 0.0163."""
    out = _run_cycle_solaire(PARAMS_NOMINAUX, cible_kW=12.0)
    assert 0.003 < out["m_dot_pri"] < 0.007


def test_solaire_m_dot_pri_egal_solveur():
    """m_dot_pri exporté == m_dot_p du solveur, comme les 3 autres circuits."""
    cr, err = _solve_cycle_from_params(PARAMS_NOMINAUX, 12.0)
    assert err is None
    out = _run_cycle_solaire(PARAMS_NOMINAUX, cible_kW=12.0)
    assert abs(out["m_dot_pri"] - cr.metrics["m_dot_p"]) < 1e-6


def test_solaire_potentiel_present_et_superieur():
    """La capacité solaire reste exportée, sous son vrai nom."""
    out = _run_cycle_solaire(PARAMS_NOMINAUX, cible_kW=12.0)
    assert out["m_dot_pri_potentiel"] > out["m_dot_pri"]
    assert abs(out["taux_couverture"] - out["Q_utile"] / out["Q_gen"]) < 1e-4


def test_solaire_surplus_coherent():
    out = _run_cycle_solaire(PARAMS_NOMINAUX, cible_kW=12.0)
    assert abs(out["Q_surplus"] - (out["Q_utile"] - out["Q_gen"])) < 1e-3


def test_run_cycle_classique_non_touche():
    """run_cycle() (moteur/frigorifique/couplage) n'est pas affectée — pas de
    clés G/eta_col/A_col dans les params, donc chemin classique inchangé."""
    from app.adapters.physics_adapter import run_cycle

    nominal = {
        "T_g": 95.0, "T_e": 8.0, "T_c": 35.0,
        "eta_is_p": 0.75, "eta_n": 0.92, "eta_d": 0.85, "eta_m": 1.00,
    }
    out = run_cycle(nominal, cible_kW=12.0)
    assert out["physically_valid"]
    assert "m_dot_pri_potentiel" not in out
    assert "taux_couverture" not in out
