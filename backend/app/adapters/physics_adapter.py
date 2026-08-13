"""
Adaptateur physique — pont unique vers le cœur thermodynamique MVC.

Principe : DIMENSIONNEMENT INVERSE UNIQUEMENT.
Q_evap est toujours imposée (cible 12 kW ± tolérance).
Le solveur interne calcule m_dot_p pour atteindre cette cible.
Les grandeurs distribuées sont : m_dot_p, m_dot_s, COP, mu, eta_ex.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations
from typing import Optional
from app.physics.modules.system.model import SystemCycleModel, CycleResult

_cycle_model = SystemCycleModel()


def core_is_real() -> bool:
    return True


def run_cycle(params: dict, cible_kW: float = 12.0) -> dict:
    """
    Dimensionnement inverse : trouve m_dot_p pour atteindre cible_kW.

    Args:
        params   : dict {nom_param: valeur} issu d'un tirage LHS.
        cible_kW : charge frigorifique cible [kW] (défaut 12 kW).

    Returns:
        dict de sorties distribuées : m_dot_p, m_dot_s, COP, mu, eta_ex.
    """
    # Extraction des paramètres tirés
    T_g      = params.get("T_g",      95.0) + 273.15   # °C → K
    T_e      = params.get("T_e",       8.0) + 273.15
    T_c      = params.get("T_c",      35.0) + 273.15
    eta_is_p = params.get("eta_is_p", 0.75)
    eta_n    = params.get("eta_n",    0.92)
    eta_d    = params.get("eta_d",    0.85)
    eta_m    = params.get("eta_m",    1.00)

    # Vérification physique minimale
    if not (T_e < T_c < T_g):
        return {"physically_valid": False,
                "error": f"Ordre des T non physique: Te={T_e:.1f} Tc={T_c:.1f} Tg={T_g:.1f}"}
    if not all(0 < e <= 1 for e in [eta_is_p, eta_n, eta_d, eta_m]):
        return {"physically_valid": False, "error": "Rendement hors (0,1]"}

    # Appel du cycle en mode inverse
    try:
        cr: CycleResult = _cycle_model.solve_cycle(
            T_gen=T_g, T_evap=T_e, T_cond=T_c,
            Q_evap_target=cible_kW,
            eta_pump=eta_is_p,
            eta_nozzle=eta_n,
            eta_diffuser=eta_d,
            eta_mixing=eta_m,
            use_ejector_v2=True,
        )
    except Exception as e:
        return {"physically_valid": False, "error": str(e)}

    m      = cr.metrics
    cop    = m.get("COP",     0.0)
    q_evap = m.get("Q_evap",  0.0)
    q_gen  = m.get("Q_gen",   0.0)
    mu     = m.get("mu",      0.0)
    m_pri  = m.get("m_dot_p", 0.0)
    m_sec  = m.get("m_dot_s", 0.0)

    # Rendement exergétique (Carnot tri-therme)
    eta_ex = 0.0
    if cop > 0 and T_g > T_c > T_e > 0:
        cop_carnot = (T_e / (T_c - T_e)) * ((T_g - T_c) / T_g)
        if cop_carnot > 0:
            eta_ex = round(min(cop / cop_carnot, 1.0), 5)

    valid = (
        cr.flags.get("success", False)
        and cop > 0 and mu > 0 and q_evap > 0
    )

    return {
        "COP":       round(cop,    5),
        "eta_ex":    eta_ex,
        "mu":        round(mu,     5),
        "Q_evap":    round(q_evap, 4),
        "Q_gen":     round(q_gen,  4),
        "m_dot_pri": round(m_pri,  6),
        "m_dot_sec": round(m_sec,  6),
        "physically_valid": bool(valid),
    }
