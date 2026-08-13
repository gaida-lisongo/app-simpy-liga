"""
Adaptateur physique — pont vers le vrai cœur thermodynamique MVC.

Reçoit un dict de paramètres tirés par Monte Carlo, appelle SystemCycleModel
(CoolProp, architecture MVC identique à app-machine-r718), et renvoie un dict
plat de sorties. C'est le SEUL point de contact entre la couche stochastique
et la physique.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations
from typing import Optional

from app.physics.modules.system.model import SystemCycleModel, CycleResult

# Instance singleton du modèle de cycle
_cycle_model = SystemCycleModel()


def core_is_real() -> bool:
    return True


def run_cycle(params: dict, mode: str = "direct",
              cible_kW: Optional[float] = None) -> dict:
    """
    Exécute une évaluation du cycle R718 avec les vrais modèles CoolProp.

    Args:
        params : dict {nom_param: valeur} issu d'un tirage LHS.
        mode   : 'direct' ou 'inverse'.
        cible_kW : charge frigorifique cible si mode inverse.

    Returns:
        dict plat de sorties (COP, eta_ex, mu, débits, exergies, validité).
    """
    # --- Extraction des paramètres avec valeurs nominales par défaut ---
    T_g   = params.get("T_g",   95.0) + 273.15   # °C → K
    T_e   = params.get("T_e",    8.0) + 273.15
    T_c   = params.get("T_c",   35.0) + 273.15
    eta_is_p = params.get("eta_is_p", 0.75)
    eta_n    = params.get("eta_n",    0.92)
    eta_d    = params.get("eta_d",    0.85)
    eta_m    = params.get("eta_m",    1.0)

    # --- Appel du cycle ---
    try:
        cr: CycleResult = _cycle_model.solve_cycle(
            T_gen=T_g, T_evap=T_e, T_cond=T_c,
            m_dot_p=0.02,
            Q_evap_target=cible_kW if mode == "inverse" else None,
            eta_pump=eta_is_p,
            eta_nozzle=eta_n,
            eta_diffuser=eta_d,
            eta_mixing=eta_m,
            use_ejector_v2=True,
        )
    except Exception as e:
        return {"physically_valid": False, "error": str(e)}

    m = cr.metrics
    cop    = m.get("COP", 0.0)
    q_evap = m.get("Q_evap", 0.0)
    q_gen  = m.get("Q_gen",  0.0)
    mu     = m.get("mu", 0.0)
    m_pri  = m.get("m_dot_p", 0.0)
    m_sec  = m.get("m_dot_s", 0.0)

    # Rendement exergétique indicatif (T en K)
    eta_ex = 0.0
    if cop > 0 and T_g > T_c > T_e:
        cop_carnot = (T_e / (T_c - T_e)) * ((T_g - T_c) / T_g)
        eta_ex = round(min(cop / max(cop_carnot, 1e-6), 1.0), 5)

    valid = (
        cr.flags.get("success", False)
        and cop > 0
        and mu > 0
        and q_evap > 0
    )

    return {
        "COP":      round(cop,    5),
        "eta_ex":   eta_ex,
        "mu":       round(mu,     5),
        "Q_evap":   round(q_evap, 4),
        "Q_gen":    round(q_gen,  4),
        "m_dot_pri": round(m_pri, 6),
        "m_dot_sec": round(m_sec, 6),
        "physically_valid": bool(valid),
    }
