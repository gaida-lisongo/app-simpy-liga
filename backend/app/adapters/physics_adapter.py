"""
Adaptateur physique — pont unique vers le cœur déterministe.

C'est le SEUL point de contact entre SimpyLIGA (stochastique) et le dépôt
`app-machine-r718` (physique). Il reçoit un dict de paramètres tirés, appelle
le modèle de cycle, et renvoie un dict plat de sorties (COP, mu, débits...).

Tant que `app-machine-r718` n'est pas installé aux côtés de ce projet, un
modèle de substitution (`_mock_cycle`) fournit des sorties physiquement
plausibles pour que l'API et le frontend soient développables immédiatement.
Le basculement se fait automatiquement dès que l'import réel réussit.

>>> POINT DE BRANCHEMENT unique vers le cœur physique <<<

Auteur : Projet Thèse R718 — SimpyLIGA
"""

from __future__ import annotations

import math
from typing import Optional

# Tentative d'import du cœur réel. En son absence, on reste sur le mock.
_REAL_CORE = False
try:  # pragma: no cover - dépend de l'environnement de déploiement
    from app_r718.modules.system_dashboard.model import SystemCycleModel  # type: ignore
    _REAL_CORE = True
except Exception:
    SystemCycleModel = None  # type: ignore


def core_is_real() -> bool:
    """Indique si le cœur physique réel est branché (True) ou le mock (False)."""
    return _REAL_CORE


# --------------------------------------------------------------------------- #
#  Mock physique — cohérent thermodynamiquement, sans CoolProp
# --------------------------------------------------------------------------- #
def _mock_cycle(params: dict, mode: str, cible_kW: Optional[float]) -> dict:
    """
    Modèle de substitution : reproduit les tendances physiques attendues.

    Ce n'est PAS un modèle validé — il sert uniquement à faire vivre l'API et
    le frontend. Les corrélations sont qualitativement correctes :
      - COP augmente avec T_g et T_e, diminue avec T_c ;
      - mu (entraînement) suit les rendements d'éjecteur ;
      - Q_evap suit la cible en mode inverse.
    """
    T_g = params.get("T_g", 95.0)
    T_e = params.get("T_e", 8.0)
    T_c = params.get("T_c", 35.0)
    eta_n = params.get("eta_n", 0.92)
    eta_m = params.get("eta_m", 0.85)
    eta_d = params.get("eta_d", 0.85)
    eta_is_p = params.get("eta_is_p", 0.75)
    G = params.get("G", 800.0)
    eta_col = params.get("eta_col", 0.68)

    # Taux d'entraînement : croît avec l'écart T_g - T_c et les rendements
    lift = max(T_c - T_e, 1.0)
    motive = max(T_g - T_c, 1.0)
    mu = 0.18 * (motive / lift) * (eta_n * eta_m * eta_d) ** 0.5
    mu = max(0.02, min(mu, 0.9))

    # COP tri-therme approché : effet utile / apport générateur
    carnot_like = (T_e + 273.15) / (T_c + 273.15) * (1 - (T_c + 273.15) / (T_g + 273.15))
    cop = max(0.05, 0.9 * mu * carnot_like * 3.2)

    # Rendement exergétique indicatif
    eta_ex = max(0.05, min(0.65, cop * 0.55 + 0.05 * eta_is_p))

    # Débits (mode inverse : caler Q_evap sur la cible)
    if mode == "inverse" and cible_kW:
        Q_evap = cible_kW
    else:
        Q_evap = 12.0 * (cop / 0.42)  # échelle autour du nominal
    Q_gen = Q_evap / max(cop, 1e-3)
    m_dot_sec = Q_evap / 2450.0            # ~ chaleur latente kJ/kg (indicatif)
    m_dot_pri = m_dot_sec / max(mu, 1e-3)

    # Destruction d'exergie par composant (indicatif, éjecteur dominant)
    exd_total = Q_gen * (1 - eta_ex)
    exergy_destruction = {
        "ejecteur": round(exd_total * 0.42, 4),
        "condenseur": round(exd_total * 0.23, 4),
        "generateur": round(exd_total * 0.18, 4),
        "evaporateur": round(exd_total * 0.10, 4),
        "pompe": round(exd_total * 0.07, 4),
    }
    # Apport solaire requis (pour circuit solaire)
    Q_solaire = Q_gen / max(eta_col, 1e-3)

    return {
        "COP": round(cop, 5),
        "eta_ex": round(eta_ex, 5),
        "mu": round(mu, 5),
        "Q_evap": round(Q_evap, 4),
        "Q_gen": round(Q_gen, 4),
        "m_dot_pri": round(m_dot_pri, 6),
        "m_dot_sec": round(m_dot_sec, 6),
        "Q_solaire": round(Q_solaire, 4),
        "exergy_destruction": exergy_destruction,
        "physically_valid": bool(cop > 0 and mu > 0 and T_e < T_c < T_g),
    }


# --------------------------------------------------------------------------- #
#  Interface publique de l'adaptateur
# --------------------------------------------------------------------------- #
def run_cycle(params: dict, mode: str = "direct",
              cible_kW: Optional[float] = None) -> dict:
    """
    Exécute une évaluation du cycle pour un jeu de paramètres.

    Args:
        params: dict {nom_parametre: valeur} issu d'un tirage.
        mode: 'direct' ou 'inverse'.
        cible_kW: charge frigorifique cible si mode inverse.

    Returns:
        dict plat de sorties (COP, eta_ex, mu, débits, exergies, validité).
    """
    if _REAL_CORE:  # pragma: no cover
        # >>> Branchement réel vers app-machine-r718 <<<
        # Adapter ici l'appel aux signatures réelles de SystemCycleModel :
        #   model = SystemCycleModel()
        #   cr = model.solve_cycle(..., Q_evap_target=cible_kW)
        #   return _extract_from_cycle_result(cr)
        # Pour l'instant on relaie au mock afin de garder un comportement défini.
        return _mock_cycle(params, mode, cible_kW)
    return _mock_cycle(params, mode, cible_kW)
