"""
Adaptateur physique — pont vers le vrai cœur thermodynamique MVC.

Reçoit un dict de paramètres tirés par Monte Carlo, appelle SystemCycleModel
(CoolProp, architecture MVC identique à app-machine-r718), et renvoie un dict
plat de sorties.

MODE DIRECT  : T_g, T_e, T_c, rendements, m_dot_p varient selon les tirages
               → COP, Q_evap, mu, m_dot_s sont TOUS distribués.

MODE INVERSE : Q_evap est imposée (12 kW), le solveur interne calcule m_dot_p
               → m_dot_p, m_dot_s, COP sont distribués ; Q_evap est fixé par
               construction (c'est le but du dimensionnement inverse robuste).

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations
from typing import Optional

from app.physics.modules.system.model import SystemCycleModel, CycleResult

_cycle_model = SystemCycleModel()


def core_is_real() -> bool:
    return True


def run_cycle(params: dict, mode: str = "direct",
              cible_kW: Optional[float] = None) -> dict:
    """
    Exécute une évaluation du cycle R718 avec les vrais modèles CoolProp.

    Args:
        params   : dict {nom_param: valeur} issu d'un tirage LHS.
        mode     : 'direct' ou 'inverse'.
        cible_kW : charge frigorifique cible si mode inverse [kW].

    Returns:
        dict plat de sorties (COP, eta_ex, mu, débits, Q_evap, validité).
    """
    # ------------------------------------------------------------------ #
    #  Extraction des paramètres tirés (avec valeurs nominales par défaut)
    # ------------------------------------------------------------------ #
    T_g      = params.get("T_g",      95.0) + 273.15   # °C → K
    T_e      = params.get("T_e",       8.0) + 273.15
    T_c      = params.get("T_c",      35.0) + 273.15
    eta_is_p = params.get("eta_is_p", 0.75)
    eta_n    = params.get("eta_n",    0.92)
    eta_d    = params.get("eta_d",    0.85)
    eta_m    = params.get("eta_m",    1.00)
    # m_dot_p : paramètre stochastique en mode direct
    # (peut être rendu incertain dans le JSON de config)
    m_dot_p  = params.get("m_dot_p",  0.02)            # kg/s

    # ------------------------------------------------------------------ #
    #  Vérification physique minimale avant appel
    #  (évite de soumettre des cas impossibles au solveur)
    # ------------------------------------------------------------------ #
    if not (T_e < T_c < T_g):
        return {"physically_valid": False,
                "error": "Ordre des températures non physique"}
    if not (0 < eta_is_p <= 1 and 0 < eta_n <= 1
            and 0 < eta_d <= 1 and 0 < eta_m <= 1):
        return {"physically_valid": False,
                "error": "Rendement hors [0,1]"}

    # ------------------------------------------------------------------ #
    #  Appel du cycle selon le mode
    # ------------------------------------------------------------------ #
    try:
        if mode == "inverse" and cible_kW:
            # MODE INVERSE : Q_evap imposée → m_dot_p calculé par le solveur.
            # Les grandeurs distribuées sont : m_dot_p, m_dot_s, COP, eta_ex.
            cr: CycleResult = _cycle_model.solve_cycle(
                T_gen=T_g, T_evap=T_e, T_cond=T_c,
                Q_evap_target=cible_kW,
                eta_pump=eta_is_p,
                eta_nozzle=eta_n,
                eta_diffuser=eta_d,
                eta_mixing=eta_m,
                use_ejector_v2=True,
            )
        else:
            # MODE DIRECT : m_dot_p varie avec le tirage.
            # Les grandeurs distribuées sont : Q_evap, COP, mu, m_dot_s, eta_ex.
            cr: CycleResult = _cycle_model.solve_cycle(
                T_gen=T_g, T_evap=T_e, T_cond=T_c,
                m_dot_p=m_dot_p,
                eta_pump=eta_is_p,
                eta_nozzle=eta_n,
                eta_diffuser=eta_d,
                eta_mixing=eta_m,
                use_ejector_v2=True,
            )
    except Exception as e:
        return {"physically_valid": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    #  Extraction des métriques du CycleResult
    # ------------------------------------------------------------------ #
    m      = cr.metrics
    cop    = m.get("COP",     0.0)
    q_evap = m.get("Q_evap",  0.0)   # kW
    q_gen  = m.get("Q_gen",   0.0)   # kW
    mu     = m.get("mu",      0.0)
    m_pri  = m.get("m_dot_p", 0.0)   # kg/s — résultat du solveur en inverse
    m_sec  = m.get("m_dot_s", 0.0)

    # Rendement exergétique (Carnot tri-therme)
    eta_ex = 0.0
    if cop > 0 and T_g > T_c > T_e > 0:
        cop_carnot = (T_e / (T_c - T_e)) * ((T_g - T_c) / T_g)
        if cop_carnot > 0:
            eta_ex = round(min(cop / cop_carnot, 1.0), 5)

    valid = (
        cr.flags.get("success", False)
        and cop > 0
        and mu  > 0
        and q_evap > 0
    )

    return {
        "COP":       round(cop,    5),
        "eta_ex":    eta_ex,
        "mu":        round(mu,     5),
        "Q_evap":    round(q_evap, 4),   # kW
        "Q_gen":     round(q_gen,  4),   # kW
        "m_dot_pri": round(m_pri,  6),   # kg/s
        "m_dot_sec": round(m_sec,  6),   # kg/s
        "physically_valid": bool(valid),
    }
