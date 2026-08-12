"""Tests de l'API SimpyLIGA."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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


def test_run_moteur():
    r = client.post("/api/moteur/run")
    assert r.status_code == 200
    body = r.json()
    assert body["statut"] == "ok"
    cop = body["resultats"]["statistiques"]["COP"]
    assert cop["moyenne"] > 0
    assert cop["IC95"][0] <= cop["moyenne"] <= cop["IC95"][1]


def test_inverse_cale_cible():
    r = client.post("/api/frigorifique/run")
    assert r.status_code == 200
    qe = r.json()["resultats"]["statistiques"]["Q_evap"]
    assert abs(qe["moyenne"] - 12.0) < 1e-6


def test_dashboard():
    r = client.get("/api/dashboard")
    assert r.status_code == 200
    circuits = r.json()["circuits"]
    assert set(circuits.keys()) == {"moteur", "frigorifique", "couplage", "solaire"}
