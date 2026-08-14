"""Tests M2 — endpoint de fiabilité (Clopper-Pearson)."""

from app.main import app
from tests.conftest import _AuthClient

client = _AuthClient(app)


def _tirages(vals):
    return [{"STR": v} for v in vals]


def test_fiabilite_endpoint_gte():
    # 7 valeurs sur 10 >= seuil=0.6
    vals = [0.9, 0.8, 0.7, 0.65, 0.6, 0.61, 0.62, 0.3, 0.2, 0.1]
    r = client.post("/api/solaire/fiabilite", json={
        "grandeur": "STR", "seuil": 0.6, "sens": "gte", "tirages": _tirages(vals),
    })
    assert r.status_code == 200
    body = r.json()
    assert body["n_total"] == 10
    assert body["n_succes"] == 7
    assert body["p_hat"] == 0.7
    # Bornes exactes de Clopper-Pearson pour k=7, n=10 (scipy.stats.beta.ppf).
    lo, hi = body["IC95"]
    assert abs(lo - 0.34755) < 1e-3
    assert abs(hi - 0.93326) < 1e-3


def test_fiabilite_endpoint_lte():
    vals = [1.0, 2.0, 3.0, 4.0]
    r = client.post("/api/moteur/fiabilite", json={
        "grandeur": "COP", "seuil": 2.5, "sens": "lte",
        "tirages": [{"COP": v} for v in vals],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["n_succes"] == 2
    assert body["p_hat"] == 0.5


def test_fiabilite_endpoint_grandeur_absente():
    r = client.post("/api/solaire/fiabilite", json={
        "grandeur": "inconnu", "seuil": 1.0, "sens": "gte", "tirages": [{"STR": 1.0}],
    })
    assert r.status_code == 400


def test_fiabilite_endpoint_sens_invalide():
    r = client.post("/api/solaire/fiabilite", json={
        "grandeur": "STR", "seuil": 1.0, "sens": "autre", "tirages": [{"STR": 1.0}],
    })
    assert r.status_code == 400
