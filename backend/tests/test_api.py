"""Tests de l'API SimpyLIGA."""

from fastapi.testclient import TestClient
from app.main import app
from app.schemas.reporting import Circuit, SimulationConfig, Cible, Resultats, StatSortie
from app.core.catalogue import PARAMETRES
from app.engine.monte_carlo import run_campaign
from app.engine.runner import N_MAX

client = TestClient(app)


def _fake_resultats():
    """Résultats minimaux pour mocker run_campaign (évite le coût CoolProp dans les tests HTTP)."""
    r = Resultats()
    r.statistiques = {
        "COP": StatSortie(moyenne=1.0, ecart_type=0.1, mediane=1.0, IC95=[0.9, 1.1], minimum=0.9, maximum=1.1),
        "eta_ex": StatSortie(moyenne=0.6),
        "m_dot_pri": StatSortie(moyenne=0.001),
        "Q_gen": StatSortie(moyenne=15.0),
        "mu": StatSortie(moyenne=0.5),
        "m_dot_sec": StatSortie(moyenne=0.002),
    }
    r.taux_rejet_non_physique_pct = 0.0
    return r


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["statut"] == "ok"


def test_racine():
    r = client.get("/")
    assert r.status_code == 200
    assert "circuits" in r.json()


def test_config_tous_circuits():
    for circ in ["moteur", "frigorifique", "couplage", "solaire"]:
        r = client.get(f"/api/{circ}/config")
        assert r.status_code == 200
        body = r.json()
        assert body["article"]["circuit"] == circ
        assert "perimetre" in body


def test_run_ack_asynchrone(monkeypatch):
    """L'endpoint /run renvoie immédiatement un ack asynchrone (campagne en arrière-plan)."""
    monkeypatch.setattr("app.engine.runner.run_campaign", lambda *a, **k: (_fake_resultats(), {}))
    r = client.post("/api/moteur/run")
    assert r.status_code == 200
    body = r.json()
    assert body["statut"] == "en_cours"
    assert body["campagne_id"].startswith("camp_")
    assert body["channel"].startswith("simpy:campagne:")


def test_run_cap_N(monkeypatch):
    """N_iterations est plafonné à N_MAX (10 000) côté serveur."""
    monkeypatch.setattr("app.engine.runner.run_campaign", lambda *a, **k: (_fake_resultats(), {}))
    r = client.post(
        "/api/moteur/run",
        json={"circuit": "moteur", "simulation": {"N_iterations": 100000}},
    )
    assert r.status_code == 200
    assert r.json()["N_iterations"] == N_MAX


def test_inverse_cale_cible():
    """Le dimensionnement inverse impose Q_evap = cible (12 kW) sur le cycle de référence."""
    params = PARAMETRES[Circuit.frigorifique]
    sim = SimulationConfig(N_iterations=50, cible=Cible(valeur=12.0))
    resultats, _ = run_campaign(params, sim, ["COP"])
    bilan = resultats.bilan_energetique
    assert bilan is not None
    assert abs(bilan.Q_evap - 12.0) < 1e-6


def test_dashboard(monkeypatch):
    """Le dashboard synthétise les 4 circuits (run_campaign moqué pour la rapidité)."""
    monkeypatch.setattr("app.api.routes.circuits.run_campaign", lambda *a, **k: (_fake_resultats(), {}))
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    circuits = r.json()["circuits"]
    assert set(circuits.keys()) == {"moteur", "frigorifique", "couplage", "solaire"}


# --------------------------------------------------------------------------- #
#  Tests du circuit solaire (A4) — couplage G/eta_col/A_col, STR, enrichissements
# --------------------------------------------------------------------------- #
_SOLAR_SORTIES = ["Q_utile", "eta_th", "STR", "m_dot_pri", "eta_ex", "COP"]


def test_solaire_sigma_non_nul():
    """Régression : σ ≠ 0 — les params G/eta_col/A_col doivent influencer les sorties."""
    sim = SimulationConfig(N_iterations=30, cible=Cible(valeur=12.0))
    resultats, _ = run_campaign(PARAMETRES[Circuit.solaire], sim, _SOLAR_SORTIES)
    stats = resultats.statistiques
    assert stats["STR"].ecart_type > 0.01,    "STR constant — bug couplage solaire"
    assert stats["Q_utile"].ecart_type > 1.0, "Q_utile constant — bug couplage"
    assert stats["eta_th"].ecart_type > 0.01, "eta_th constant — bug couplage"
    assert stats["COP"].ecart_type > 0.0,     "COP constant — cycle non couplé (A6)"


def test_solaire_STR_definition():
    """STR = COP_ref × eta_th (Ghodbane 2015) — pas Q_utile/Q_gen."""
    sim = SimulationConfig(N_iterations=20, cible=Cible(valeur=12.0))
    resultats, _ = run_campaign(PARAMETRES[Circuit.solaire], sim, _SOLAR_SORTIES)
    stats = resultats.statistiques
    str_moy    = stats["STR"].moyenne
    eta_th_moy = stats["eta_th"].moyenne
    assert 0.05 < str_moy < 2.0, f"STR hors plage physique : {str_moy}"
    cop_implique = str_moy / eta_th_moy if eta_th_moy > 0 else 0
    assert 0.1 < cop_implique < 3.0, f"COP implicite incohérent : {cop_implique}"
    # Garde de régression : STR ne doit pas pouvoir passer les bornes ci-dessus
    # avec un COP silencieusement constant (c'était le cas avant A6/Voie B,
    # quand le cycle tournait à T_g/T_e/T_c figés).
    assert stats["COP"].ecart_type > 0.0, "COP constant — STR ne reflète pas le couplage réel"


def test_solaire_m_dot_pri_realiste():
    """
    A1 : m_dot_pri doit utiliser les vraies enthalpies du cycle résolu (états 7/8),
    pas une re-saturation à P_gen qui ne capterait que la chaleur latente et
    omettrait le préchauffage sensible réel (~35°C -> 95°C) fourni par le générateur.
    """
    from app.adapters.physics_adapter import run_cycle

    nominal = {
        "G": 800.0, "eta_col": 0.68, "T_0": 25.0, "A_col": 85.0, "phi_s": 0.10,
        "T_g": 95.0, "T_e": 8.0, "T_c": 35.0,
        "eta_is_p": 0.75, "eta_n": 0.92, "eta_d": 0.85, "eta_m": 1.00,
    }
    out = run_cycle(nominal, cible_kW=12.0, include_states=True)
    assert out["physically_valid"], out.get("error")

    par_point = {s["point"]: s for s in out["states"]}
    h_7 = par_point["7"]["h"]  # kJ/kg
    h_8 = par_point["8"]["h"]  # kJ/kg
    delta_h_reel = h_8 - h_7

    # Chaleur latente seule à P_gen (l'ancien bug) est ~2260-2270 kJ/kg pour l'eau à 95°C.
    # Le vrai Δh doit être strictement supérieur car il inclut le préchauffage sensible
    # entre la sortie pompe (proche de T_cond) et la vapeur saturée à T_gen.
    assert delta_h_reel > 2300.0, (
        f"Δh implicite ({delta_h_reel:.1f} kJ/kg) ne semble pas inclure le "
        f"préchauffage sensible — A1 non corrigé ?"
    )

    Q_utile = out["Q_utile"]
    m_dot_pri_attendu = Q_utile / delta_h_reel
    assert abs(out["m_dot_pri"] - m_dot_pri_attendu) < 1e-4, (
        f"m_dot_pri ({out['m_dot_pri']}) != Q_utile/Δh_reel ({m_dot_pri_attendu})"
    )


def test_solaire_mode_inverse_preserve():
    """Q_evap reste 12 kW — mode inverse non abandonné pour le circuit solaire."""
    sim = SimulationConfig(N_iterations=20, cible=Cible(valeur=12.0))
    resultats, _ = run_campaign(PARAMETRES[Circuit.solaire], sim, _SOLAR_SORTIES)
    bilan = resultats.bilan_energetique
    assert bilan is not None, "Bilan énergétique manquant"
    assert abs(bilan.Q_evap - 12.0) < 1.0, "Mode inverse abandonné"


def test_solaire_enrichissements():
    """Les blocs profil_tube, courbes_cpc, sankey_solaire sont présents."""
    sim = SimulationConfig(N_iterations=15, cible=Cible(valeur=12.0))
    resultats, _ = run_campaign(PARAMETRES[Circuit.solaire], sim, _SOLAR_SORTIES)

    assert resultats.profil_tube is not None,   "profil_tube manquant"
    assert resultats.courbes_cpc is not None,   "courbes_cpc manquant"
    assert resultats.sankey_solaire is not None, "sankey_solaire manquant"

    pt = resultats.profil_tube
    assert len(pt.x_m) == len(pt.T_fluide) == len(pt.zones)
    assert "vaporisation" in pt.zones

    cc = resultats.courbes_cpc
    assert len(cc.G_range) == len(cc.eta_th_vs_G) == 50
    assert len(cc.T_gen_range) == len(cc.STR_vs_Tgen) == 30

    # A2 : la courbe STR=f(T_gen) doit être ancrée sur le vrai COP nominal résolu
    # (resultats.bilan_energetique.COP), pas sur le littéral déconnecté cop_ref=0.35.
    bilan = resultats.bilan_energetique
    assert bilan is not None and bilan.COP is not None
    idx_95 = min(range(len(cc.T_gen_range)), key=lambda i: abs(cc.T_gen_range[i] - 95.0))
    eta_th_nom = cc.eta_th_vs_G[0]
    str_attendu_95 = bilan.COP * eta_th_nom
    assert abs(cc.STR_vs_Tgen[idx_95] - str_attendu_95) < 0.05, (
        f"courbes_cpc.STR_vs_Tgen ne reflète pas le COP nominal réel "
        f"({cc.STR_vs_Tgen[idx_95]} vs attendu {str_attendu_95})"
    )


def test_solaire_params_corrects():
    """Vérifie que les bornes du catalogue solaire sont conformes à la référence A4."""
    r = client.get("/api/solaire/config")
    assert r.status_code == 200
    params = {p["nom"]: p for p in r.json()["parametres_incertains"]}

    assert "G" in params
    assert params["G"]["mode"] == 800
    assert params["G"]["sigma"] == 80

    assert "A_col" in params
    assert params["A_col"]["min"] == 70
    assert params["A_col"]["max"] == 100

    assert "phi_s" in params
    assert params["T_0"]["sigma"] == 3

    # A6/Voie B — couplage réel : le cycle R718 solaire tire T_g/T_e/T_c et
    # les rendements comme les circuits moteur/frigorifique/couplage.
    assert params["T_g"]["min"] == 80
    assert params["T_g"]["mode"] == 95
    assert params["T_g"]["max"] == 110

    assert params["T_e"]["min"] == 5
    assert params["T_e"]["mode"] == 8
    assert params["T_e"]["max"] == 12

    assert params["T_c"]["min"] == 28
    assert params["T_c"]["mode"] == 35
    assert params["T_c"]["max"] == 45

    assert params["eta_is_p"]["min"] == 0.65
    assert params["eta_is_p"]["max"] == 0.85

    for nom in ("eta_n", "eta_d", "eta_m"):
        assert nom in params, f"{nom} manquant du catalogue solaire"
