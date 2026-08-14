"""Tests M1 — indices de sensibilité de Sobol."""

from app.core.catalogue import PARAMETRES
from app.engine.sensitivity import compute_sobol
from app.schemas.reporting import Circuit


def test_sobol_solaire():
    sorties = ["Q_utile", "eta_th", "STR"]
    indices = compute_sobol(PARAMETRES[Circuit.solaire], sorties, cible_kW=12.0, N_sobol=32)

    assert indices, "Aucun indice de Sobol produit"

    noms_variables = {p.nom for p in PARAMETRES[Circuit.solaire]}
    vus = set()
    for ind in indices:
        sortie, nom_param = ind.parametre.split("::")
        assert sortie in sorties
        assert nom_param in noms_variables
        vus.add((sortie, nom_param))
        # Tolérance large : petit N_sobol => estimateurs bruyants, peuvent
        # légèrement déborder de [0,1].
        assert -0.3 <= ind.indice_premier <= 1.3
        assert -0.3 <= ind.indice_total <= 1.3

    # eta_th ne dépend (en forme fermée) que de eta_col et phi_s — les deux
    # doivent apparaître dans les indices calculés pour cette sortie.
    assert ("eta_th", "eta_col") in vus
    assert ("eta_th", "phi_s") in vus


def test_sobol_vide_sans_parametres_variables():
    from app.schemas.reporting import ParametreIncertain, Loi
    fixe = [ParametreIncertain(nom="x", symbole="x", unite="-", loi=Loi.fixe, valeur=1.0)]
    assert compute_sobol(fixe, ["Q_utile"], cible_kW=12.0, N_sobol=8) == []
