"""
Catalogue des circuits — métadonnées et paramètres incertains par défaut.

Source de vérité côté backend pour les 4 articles/circuits. Les valeurs
reprennent le Guide de rédaction (bornes indicatives, à valider chap. 2).
Chaque circuit expose : son méta (id, titre), son périmètre (composants,
états, transformations) et sa liste de paramètres incertains par défaut.

Auteur : Projet Thèse R718 — SimpyLIGA
"""

from __future__ import annotations

from app.schemas.reporting import Circuit, Loi, ParametreIncertain


# --------------------------------------------------------------------------- #
#  Périmètres (conformes à la convention d'états du mémoire, fig. 1.5)
# --------------------------------------------------------------------------- #
PERIMETRES: dict[Circuit, dict] = {
    Circuit.moteur: {
        "composants": ["pompe", "generateur", "tuyere_primaire"],
        "etats": ["1", "7", "8", "4"],
        "transformations": ["1->7", "7->8", "8->4"],
    },
    Circuit.frigorifique: {
        "composants": ["detendeur", "evaporateur", "aspiration_secondaire"],
        "etats": ["1", "2", "3", "4"],
        "transformations": ["1->2", "2->3", "3->4"],
    },
    Circuit.couplage: {
        "composants": ["chambre_melange", "diffuseur", "condenseur"],
        "etats": ["4", "5", "6", "1"],
        "transformations": ["4->5", "5->6", "6->1"],
    },
    Circuit.solaire: {
        "composants": ["concentrateur", "caloporteur", "apport_generateur"],
        "etats": ["externe"],
        "transformations": ["G->T_g"],
    },
}

META: dict[Circuit, dict] = {
    Circuit.moteur:       {"id": "A1", "titre": "Circuit Moteur (branche chaude)"},
    Circuit.frigorifique: {"id": "A2", "titre": "Circuit Frigorifique (branche froide)"},
    Circuit.couplage:     {"id": "A3", "titre": "Branche Commune — Éjecteur & Condenseur"},
    Circuit.solaire:      {"id": "A4", "titre": "Circuit Solaire (source chaude externe)"},
}


# --------------------------------------------------------------------------- #
#  Helpers de construction de paramètres
# --------------------------------------------------------------------------- #
def _tri(nom, sym, unite, a, c, b, source="chap2"):
    return ParametreIncertain(nom=nom, symbole=sym, unite=unite, loi=Loi.triangulaire,
                              min=a, mode=c, max=b, source=source)

def _uni(nom, sym, unite, a, b, source="chap2"):
    return ParametreIncertain(nom=nom, symbole=sym, unite=unite, loi=Loi.uniforme,
                              min=a, max=b, source=source)

def _nor(nom, sym, unite, mu, sigma, source="chap2"):
    return ParametreIncertain(nom=nom, symbole=sym, unite=unite, loi=Loi.normale,
                              mode=mu, sigma=sigma, source=source)


# --------------------------------------------------------------------------- #
#  Paramètres incertains par défaut, par circuit
# --------------------------------------------------------------------------- #
PARAMETRES: dict[Circuit, list[ParametreIncertain]] = {
    Circuit.moteur: [
        _tri("T_g", "T_g", "degC", 80, 95, 110),
        _uni("eta_is_p", "eta_is,p", "-", 0.65, 0.85),
        _nor("eta_m_p", "eta_m,p", "-", 0.94, 0.02),
        _uni("phi_g", "phi_g", "%", 2, 8),
        _nor("x_g", "x_g", "-", 0.995, 0.003),
    ],
    Circuit.frigorifique: [
        _tri("T_e", "T_e", "degC", 5, 8, 12),
        _nor("Q_e", "Q_e", "kW", 12.0, 0.30, source="cible_inverse"),
        _uni("dT_pp_e", "dT_pp,e", "K", 2, 6),
        _uni("dT_sh", "dT_sh", "K", 0, 5),
    ],
    Circuit.couplage: [
        _tri("eta_n", "eta_n", "-", 0.85, 0.92, 0.95),
        _tri("eta_m", "eta_m", "-", 0.75, 0.85, 0.95),
        _tri("eta_d", "eta_d", "-", 0.75, 0.85, 0.90),
        _tri("T_c", "T_c", "degC", 28, 35, 45),
        _uni("dT_pp_c", "dT_pp,c", "K", 3, 7),
        _uni("phi_sections", "Phi", "-", 4, 12),
    ],
    Circuit.solaire: [
        _nor("G",       "G",       "W/m2", 800, 80,   source="Ghodbane2015"),
        _tri("eta_col", "eta_col", "-",  0.55, 0.68, 0.78, source="ICT3_Tab2"),
        _nor("T_0",     "T_0",     "degC",  25,  3,  source="contexte_RDC"),
        _uni("A_col",   "A_col",   "m2",    70, 100,  source="memoire_eq7.14"),
        _uni("phi_s",   "phi_s",   "-",   0.05, 0.15, source="Al-akayshee2026"),
    ],
}


def get_default_config(circuit: Circuit) -> dict:
    """Retourne le méta, le périmètre et les paramètres par défaut d'un circuit."""
    return {
        "meta": META[circuit],
        "perimetre": PERIMETRES[circuit],
        "parametres_incertains": PARAMETRES[circuit],
    }
