"""
Adaptateur physique — pont unique vers le cœur thermodynamique MVC.

Principe : DIMENSIONNEMENT INVERSE UNIQUEMENT.
Q_evap est toujours imposée (cible 12 kW ± tolérance).
Le solveur interne calcule m_dot_p pour atteindre cette cible.
Les grandeurs distribuées sont : m_dot_p, m_dot_s, COP, mu, eta_ex.

Circuit solaire (A4) : les paramètres G, eta_col, A_col, T_0 décrivent le
sous-système capteur solaire externe. Ils déterminent Q_utile (puissance livrée
au générateur), eta_th, STR et m_dot_pri — pas directement T_g qui reste fixée
par le cycle. Un sous-modèle solaire dédié calcule ces sorties spécifiques.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations
import math
from app.physics.modules.system.model import SystemCycleModel, CycleResult

_cycle_model = SystemCycleModel()

T_SOLEIL_K = 5777.0


def core_is_real() -> bool:
    return True


def _solve_cycle_from_params(params: dict, cible_kW: float):
    """
    Lit T_g/T_e/T_c/eta_is_p/eta_n/eta_d/eta_m depuis params (mêmes défauts et
    validations pour tous les circuits, y compris solaire depuis A6/Voie B) et
    résout le cycle R718 en mode inverse (Q_evap = cible_kW imposée).

    Returns:
        (CycleResult, None) si succès, (None, error_dict) sinon.
    """
    T_g      = params.get("T_g",      95.0) + 273.15
    T_e      = params.get("T_e",       8.0) + 273.15
    T_c      = params.get("T_c",      35.0) + 273.15
    eta_is_p = params.get("eta_is_p", 0.75)
    eta_n    = params.get("eta_n",    0.92)
    eta_d    = params.get("eta_d",    0.85)
    eta_m    = params.get("eta_m",    1.00)

    if not (T_e < T_c < T_g):
        return None, {"physically_valid": False,
                       "error": f"Ordre T non physique: Te={T_e:.1f} Tc={T_c:.1f} Tg={T_g:.1f}"}
    if not all(0 < e <= 1 for e in [eta_is_p, eta_n, eta_d, eta_m]):
        return None, {"physically_valid": False, "error": "Rendement hors (0,1]"}

    try:
        cr: CycleResult = _cycle_model.solve_cycle(
            T_gen=T_g, T_evap=T_e, T_cond=T_c,
            Q_evap_target=cible_kW,
            eta_pump=eta_is_p, eta_nozzle=eta_n,
            eta_diffuser=eta_d, eta_mixing=eta_m,
            use_ejector_v2=True,
        )
    except Exception as e:
        return None, {"physically_valid": False, "error": str(e)}

    return cr, None


def _run_cycle_solaire(params: dict, cible_kW: float = 12.0,
                       include_states: bool = False) -> dict:
    """
    Sous-modèle circuit solaire (A4) — MODE INVERSE PRÉSERVÉ.

    Les paramètres G, eta_col, A_col, T_0, phi_s déterminent Q_utile.
    Le cycle R718 (T_g, T_e, T_c, rendements) est désormais couplé réellement
    (A6/Voie B) : tiré du même catalogue que moteur/frigorifique/couplage,
    plus figé aux conditions nominales.

    PRINCIPE FONDAMENTAL : Q_evap reste imposée à 12 kW. Le mode inverse
    n'est PAS abandonné. m_dot_pri est une SORTIE calculée depuis Q_utile,
    pas une entrée du solveur.

    STR = COP_ejc × eta_th  (définition Ghodbane et al. 2015, ICT3 éq. 14)
    PAS Q_utile/Q_gen — ce sont deux grandeurs différentes.

    Sorties : Q_utile, Q_sol, Q_opt, eta_th, STR, m_dot_pri, eta_ex.
    """
    G       = params.get("G",       800.0)
    eta_col = params.get("eta_col",  0.68)
    A_col   = params.get("A_col",   85.0)
    T_0_C   = params.get("T_0",     25.0)
    phi_s   = params.get("phi_s",    0.10)

    T_0_K = T_0_C + 273.15

    if G <= 0 or A_col <= 0 or not (0 < eta_col <= 1):
        return {"physically_valid": False,
                "error": f"Paramètre solaire hors bornes: G={G}, "
                         f"A_col={A_col}, eta_col={eta_col}"}
    if not (0.0 <= phi_s < 1.0):
        return {"physically_valid": False,
                "error": f"phi_s hors [0, 1) : {phi_s}"}

    Q_sol   = G * A_col / 1000.0
    Q_opt   = Q_sol * eta_col
    Q_utile = Q_opt * (1.0 - phi_s)
    eta_th  = Q_utile / Q_sol if Q_sol > 0 else 0.0

    if Q_utile <= 0:
        return {"physically_valid": False, "error": "Q_utile ≤ 0"}

    T_g_K = params.get("T_g", 95.0) + 273.15

    cr, err = _solve_cycle_from_params(params, cible_kW)
    if err is not None:
        return err

    m   = cr.metrics
    cop = m.get("COP", 0.0)
    mu  = m.get("mu",  0.0)

    if not (cr.flags.get("success", False) and cop > 0 and mu > 0):
        return {"physically_valid": False, "error": "Cycle de référence invalide"}

    # A1 (corrigé) : vraies enthalpies du cycle résolu — pas une re-saturation
    # à P_gen qui ne capterait que la chaleur latente et omettrait le
    # préchauffage sensible réel entre la sortie pompe (état 7) et la
    # vapeur saturée en sortie générateur (état 8).
    h_7 = cr.states[7].h
    h_8 = cr.states[8].h
    delta_h = (h_8 - h_7) / 1000.0

    m_dot_pri = Q_utile / delta_h if delta_h > 0 else 0.0

    STR = cop * eta_th

    facteur_carnot = 1.0 - T_0_K / T_g_K
    facteur_soleil = 1.0 - T_0_K / T_SOLEIL_K
    eta_ex = (eta_th * facteur_carnot / facteur_soleil
              if facteur_soleil > 0 else 0.0)
    eta_ex = round(min(max(eta_ex, 0.0), 1.0), 5)

    out = {
        "COP":        round(cop,       5),
        "mu":         round(mu,        5),
        "Q_utile":    round(Q_utile,   4),
        "Q_sol":      round(Q_sol,     4),
        "Q_opt":      round(Q_opt,     4),
        "Q_gen":      round(Q_utile,   4),
        "Q_evap":     round(m.get("Q_evap",  cible_kW), 4),
        "Q_cond":     round(m.get("Q_cond",  0.0),     4),
        "W_pompe":    round(m.get("W_pump",   0.0),     4),
        "m_dot_pri":  round(m_dot_pri, 6),
        "m_dot_sec":  round(m.get("m_dot_s",  0.0),     6),
        "eta_th":     round(eta_th,    5),
        "eta_ex":     eta_ex,
        "STR":        round(STR,       5),
        "physically_valid": True,
    }

    if include_states:
        out["states"] = _serialize_states(cr.states)

    return out


def run_cycle(params: dict, cible_kW: float = 12.0,
              include_states: bool = False) -> dict:
    """
    Point d'entrée unique — détecte le circuit et délègue.

    Circuit solaire détecté si G ou eta_col ou A_col présents dans params.
    Circuits classiques (moteur/frigorifique/couplage) : chemin existant.
    """
    _SOLAR_KEYS = {"G", "eta_col", "A_col"}
    if _SOLAR_KEYS & params.keys():
        return _run_cycle_solaire(params, cible_kW=cible_kW,
                                  include_states=include_states)

    T_g = params.get("T_g", 95.0) + 273.15
    T_c = params.get("T_c", 35.0) + 273.15
    T_e = params.get("T_e",  8.0) + 273.15

    cr, err = _solve_cycle_from_params(params, cible_kW)
    if err is not None:
        return err

    m      = cr.metrics
    cop    = m.get("COP",     0.0)
    q_evap = m.get("Q_evap",  0.0)
    q_gen  = m.get("Q_gen",   0.0)
    q_cond = m.get("Q_cond",  0.0)
    w_pump = m.get("W_pump",  0.0)
    mu     = m.get("mu",      0.0)
    m_pri  = m.get("m_dot_p", 0.0)
    m_sec  = m.get("m_dot_s", 0.0)

    eta_ex = 0.0
    if cop > 0 and T_g > T_c > T_e > 0:
        cop_carnot = (T_e / (T_c - T_e)) * ((T_g - T_c) / T_g)
        if cop_carnot > 0:
            eta_ex = round(min(cop / cop_carnot, 1.0), 5)

    valid = (cr.flags.get("success", False) and cop > 0
             and mu > 0 and q_evap > 0)

    out = {
        "COP":       round(cop,    5),
        "eta_ex":    eta_ex,
        "mu":        round(mu,     5),
        "Q_evap":    round(q_evap, 4),
        "Q_gen":     round(q_gen,  4),
        "Q_cond":    round(q_cond, 4),
        "W_pompe":   round(w_pump, 4),
        "m_dot_pri": round(m_pri,  6),
        "m_dot_sec": round(m_sec,  6),
        "physically_valid": bool(valid),
    }

    if include_states:
        out["states"] = _serialize_states(cr.states)

    return out


def _serialize_states(states: dict) -> list[dict]:
    """ThermoState SI → unités reporting (°C, bar, kJ/kg, kJ/kg·K)."""
    out = []
    for point in sorted(states.keys()):
        st = states[point]
        out.append({
            "point": str(point),
            "T": round(st.T - 273.15, 3) if st.T is not None else None,
            "P": round(st.P / 1e5,    4) if st.P is not None else None,
            "h": round(st.h / 1000.0, 3) if st.h is not None else None,
            "s": round(st.s / 1000.0, 5) if st.s is not None else None,
            "x": round(st.x,          5) if st.x is not None else None,
        })
    return out


# --------------------------------------------------------------------------- #
#  Enrichissements spécifiques au circuit solaire (calculés sur les nominaux)
# --------------------------------------------------------------------------- #
def compute_profil_tube(Q_utile_kW: float, T_g_C: float = 95.0,
                        T_7_C: float = 36.0, L: float = 3.0,
                        n_points: int = 15) -> dict:
    """
    Profil axial T_fluide / T_absorbeur / T_vitre le long du tube.

    Modèle 1D simplifié — 2 zones (préchauffage + vaporisation, pas de surchauffe
    car état 8 = vapeur saturée x=1).

    h_int = 500 W/m²·K (liquide monophasique R718)
    h_ann = 5 W/m²·K   (vide partiel dans l'anneau tube-vitre)
    D_int = 0.020 m, D_ext = 0.022 m, D_vitre = 0.026 m
    """
    import numpy as np

    T_sat = T_g_C
    q_lin = Q_utile_kW * 1000.0 / L

    D_int  = 0.020
    D_ext  = 0.022
    D_vitre= 0.026
    h_int  = 500.0
    h_ann  = 5.0

    L1 = L * 0.10

    xs = np.linspace(0, L, n_points)
    T_fluide    = np.zeros(n_points)
    T_absorbeur = np.zeros(n_points)
    T_vitre     = np.zeros(n_points)
    zones       = []

    for i, x in enumerate(xs):
        if x <= L1:
            t_f = T_7_C + (T_sat - T_7_C) * (x / L1) if L1 > 0 else T_sat
            zone = "préchauffage"
        else:
            t_f = T_sat
            zone = "vaporisation"

        dT_abs_fluide = q_lin / (h_int * math.pi * D_int)
        dT_vitre      = q_lin / (h_ann * math.pi * D_vitre)

        T_fluide[i]    = round(t_f, 2)
        T_absorbeur[i] = round(t_f + dT_abs_fluide, 2)
        T_vitre[i]     = round(t_f + dT_abs_fluide - dT_vitre, 2)
        zones.append(zone)

    return {
        "x_m":        [round(x, 3) for x in xs.tolist()],
        "T_fluide":   T_fluide.tolist(),
        "T_absorbeur":T_absorbeur.tolist(),
        "T_vitre":    T_vitre.tolist(),
        "zones":      zones,
    }


def compute_courbes_cpc(eta_col_nom: float = 0.68,
                        phi_s_nom: float = 0.10,
                        A_col_nom: float = 85.0,
                        T_0_nom: float = 25.0,
                        cop_ref: float | None = None) -> dict:
    """
    Courbes de balayage pour visualisation frontend.

    eta_th = f(G) : à eta_col, phi_s, A_col, T_0 nominaux
    STR = f(T_gen) : STR = COP_ejc(T_gen) × eta_th_nom

    cop_ref : COP issu du cycle nominal résolu (Voie B).
              Si None (cycle nominal invalide), la courbe STR est omise
              plutôt que calculée avec 0.35 qui est l'ancien COP incompatible.
    """
    import numpy as np

    G_range = np.linspace(400, 1200, 50).tolist()
    eta_th_vs_G = [
        round(eta_col_nom * (1.0 - phi_s_nom), 5)
        for _ in G_range
    ]

    T_gen_range = np.linspace(75, 120, 30).tolist()
    if cop_ref is not None and cop_ref > 0:
        STR_vs_Tgen = [
            round(cop_ref * (1.0 + 0.005 * (t - 95.0)) * eta_col_nom
                  * (1.0 - phi_s_nom), 5)
            for t in T_gen_range
        ]
    else:
        # cop_ref absent ou invalide : on ne fabrique pas de courbe STR avec
        # une valeur arbitraire (l'ancien 0.35 était l'hypothèse COP=0.35
        # du dimensionnement préliminaire, incompatible avec le COP réel ~1.04).
        STR_vs_Tgen = [None] * len(T_gen_range)

    return {
        "G_range":       [round(g, 1) for g in G_range],
        "eta_th_vs_G":   eta_th_vs_G,
        "T_gen_range":   [round(t, 1) for t in T_gen_range],
        "STR_vs_Tgen":   STR_vs_Tgen,
    }


def compute_sankey_solaire(Q_sol: float, Q_opt: float,
                           Q_utile: float) -> dict:
    """
    Données Sankey pour les flux d'énergie du circuit solaire.
    """
    Q_pertes_opt   = Q_sol - Q_opt
    Q_pertes_therm = Q_opt - Q_utile

    return {
        "labels":    ["Rayonnement incident", "Absorbé (optique)",
                      "Pertes optiques", "Pertes thermiques",
                      "Livré au générateur"],
        "values_kW": [round(Q_sol, 2), round(Q_opt, 2),
                      round(Q_pertes_opt, 2), round(Q_pertes_therm, 2),
                      round(Q_utile, 2)],
        "source":    [0, 1, 1],
        "target":    [1, 4, 3],
    }