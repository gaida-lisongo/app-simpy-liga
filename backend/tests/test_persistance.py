"""Tests unitaires de la persistance Redis — sans réseau (mock _pipeline)."""

from __future__ import annotations

import json
import threading
from unittest.mock import MagicMock, patch

import pytest

from app.core import upstash
from app.schemas.reporting import (
    Circuit, SimulationConfig, Cible, Resultats, StatSortie, Convergence,
    ReportingResponse, MetaArticle,
)
from app.core.catalogue import META, PERIMETRES


# --------------------------------------------------------------------------- #
#  save_campaign
# --------------------------------------------------------------------------- #

class TestSaveCampaign:
    """save_campaign émet [SET, LPUSH, LTRIM] et renvoie True/False."""

    def test_save_campaign_pipeline_commands(self):
        """Les 3 commandes sont émises avec les bonnes clés et LTRIM 0 19."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK", 1, "OK"]

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                result = upstash.save_campaign("solaire", "camp_test123", {"foo": "bar"})

        assert result is True
        assert len(captured) == 3

        cmd_set, cmd_lpush, cmd_ltrim = captured
        assert cmd_set[0] == "SET"
        assert cmd_set[1] == "simpy:campagne:camp_test123"
        assert json.loads(cmd_set[2]) == {"foo": "bar"}

        assert cmd_lpush[0] == "LPUSH"
        assert cmd_lpush[1] == "simpy:circuit:solaire:history"
        assert cmd_lpush[2] == "camp_test123"

        assert cmd_ltrim[0] == "LTRIM"
        assert cmd_ltrim[1] == "simpy:circuit:solaire:history"
        assert cmd_ltrim[2] == 0
        assert cmd_ltrim[3] == 19

    def test_save_campaign_returns_false_on_exception(self):
        """En cas d'exception du pipeline, renvoie False."""
        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=ConnectionError("timeout")):
                result = upstash.save_campaign("moteur", "camp_err", {"x": 1})

        assert result is False

    def test_save_campaign_returns_false_when_unavailable(self):
        """Si Upstash non configuré, renvoie False sans appeler _pipeline."""
        with patch.object(upstash, "_CLIENT", None):
            with patch.object(upstash, "_pipeline", return_value=["OK", 1, "OK"]) as mock_pipe:
                result = upstash.save_campaign("solaire", "camp_no", {"x": 1})

        assert result is False
        mock_pipe.assert_not_called()


# --------------------------------------------------------------------------- #
#  push_event
# --------------------------------------------------------------------------- #

class TestPushEvent:
    """push_event renvoie True/False et n'émet pas d'exception."""

    def test_push_event_returns_true_on_success(self):
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return [1, True]

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                result = upstash.push_event("camp_abc", {"type": "progress", "pct": 50})

        assert result is True
        assert len(captured) == 2
        assert captured[0][0] == "LPUSH"
        assert captured[0][1] == "simpy:campagne:camp_abc:events"

    def test_push_event_returns_false_on_exception(self):
        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=RuntimeError("fail")):
                result = upstash.push_event("camp_xyz", {"type": "done"})

        assert result is False

    def test_push_event_returns_false_when_unavailable(self):
        with patch.object(upstash, "_CLIENT", None):
            with patch.object(upstash, "_pipeline", return_value=[1, True]) as mock_pipe:
                result = upstash.push_event("camp_no", {"type": "progress"})

        assert result is False
        mock_pipe.assert_not_called()

    def test_push_event_never_raises(self):
        """Même en cas d'erreur, push_event ne lève jamais d'exception."""
        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=OSError("network")):
                # Ne doit pas lever
                result = upstash.push_event("camp_err", {"type": "error", "message": "boom"})
        assert result is False


# --------------------------------------------------------------------------- #
#  Runner integration (thread synchronisé via monkeypatch)
# --------------------------------------------------------------------------- #

def _fake_resultats():
    """Résultats minimaux avec quelques tirages pour les tests."""
    r = Resultats()
    r.statistiques = {
        "COP": StatSortie(moyenne=1.0, ecart_type=0.1, mediane=1.0,
                          IC95=[0.9, 1.1], minimum=0.9, maximum=1.1),
        "m_dot_pri": StatSortie(moyenne=0.016, ecart_type=0.002, mediane=0.016,
                                IC95=[0.012, 0.020], minimum=0.010, maximum=0.022),
    }
    r.convergence = Convergence(N_stable=100, stabilise=True)
    r.tirages = [
        {"G": 800, "COP": 1.0, "m_dot_pri": 0.016},
        {"G": 750, "COP": 0.95, "m_dot_pri": 0.017},
        {"G": 850, "COP": 1.05, "m_dot_pri": 0.015},
    ]
    r.taux_rejet_non_physique_pct = 0.0
    return r


class TestRunnerPersistance:
    """Test du runner : save_campaign appelé avec tirages, done léger, error si échec."""

    def _run_sync(self, monkeypatch, save_campaign_ok=True, push_event_always_ok=True):
        """Exécute start_run de manière synchrone en interceptant le thread."""
        captured_save = {}
        captured_pushes = []

        def fake_save_campaign(circuit_slug, campagne_id, response):
            captured_save["circuit"] = circuit_slug
            captured_save["campagne_id"] = campagne_id
            captured_save["response"] = response
            return save_campaign_ok

        def fake_push_event(campagne_id, payload):
            captured_pushes.append({"campagne_id": campagne_id, "payload": payload})
            return push_event_always_ok

        monkeypatch.setattr(upstash, "save_campaign", fake_save_campaign)
        monkeypatch.setattr(upstash, "push_event", fake_push_event)

        # Rendre le thread synchrone : intercepter Thread.start pour exécuter
        # la target directement
        original_thread = threading.Thread
        thread_holder = []

        class SyncThread:
            def __init__(self, target, daemon=True):
                self.target = target
                self.daemon = daemon

            def start(self):
                thread_holder.append(self)
                self.target()  # exécution synchrone

            def join(self, timeout=None):
                pass  # déjà exécuté

        monkeypatch.setattr(threading, "Thread", SyncThread)

        from app.engine import runner
        from app.schemas.reporting import Circuit as CircuitEnum

        sim = SimulationConfig(N_iterations=10, seed=42, cible=Cible(valeur=12.0))
        params = []  # pas de paramètres — on mock run_campaign
        sorties = ["COP", "m_dot_pri"]

        ack = runner.start_run(CircuitEnum.solaire, params, sim, sorties)
        assert ack["statut"] == "en_cours"

        return captured_save, captured_pushes

    def test_save_campaign_called_with_full_payload(self, monkeypatch):
        """save_campaign reçoit le payload complet AVEC les tirages."""
        with patch("app.engine.runner.run_campaign", return_value=(_fake_resultats(), {})):
            captured_save, captured_pushes = self._run_sync(monkeypatch, save_campaign_ok=True)

        assert captured_save["circuit"] == "solaire"
        assert captured_save["campagne_id"].startswith("camp_")
        resp = captured_save["response"]
        # Le payload persisté DOIT contenir les tirages
        assert len(resp["resultats"]["tirages"]) == 3
        assert resp["resultats"]["tirages"][0]["G"] == 800

    def test_done_event_is_light_no_tirages(self, monkeypatch):
        """L'événement done poussé a resultats.tirages == [] et contient persiste."""
        with patch("app.engine.runner.run_campaign", return_value=(_fake_resultats(), {})):
            captured_save, captured_pushes = self._run_sync(monkeypatch, save_campaign_ok=True)

        # Trouver l'événement done
        done_events = [p for p in captured_pushes if p["payload"].get("type") == "done"]
        assert len(done_events) == 1

        done_result = done_events[0]["payload"]["result"]
        # Les tirages doivent être vides dans le done
        assert done_result["resultats"]["tirages"] == []
        # Le flag persiste doit être présent
        assert "persiste" in done_result
        assert done_result["persiste"] is True
        # Les statistiques doivent être intactes
        assert done_result["resultats"]["statistiques"]["COP"]["moyenne"] == 1.0
        assert done_result["resultats"]["convergence"]["N_stable"] == 100

    def test_error_event_on_save_failure(self, monkeypatch):
        """Si save_campaign échoue, un événement error est poussé après le done."""
        with patch("app.engine.runner.run_campaign", return_value=(_fake_resultats(), {})):
            captured_save, captured_pushes = self._run_sync(monkeypatch, save_campaign_ok=False)

        types = [p["payload"].get("type") for p in captured_pushes]
        assert "done" in types
        assert "error" in types

        # L'error doit être APRÈS le done
        done_idx = types.index("done")
        error_idx = types.index("error")
        assert error_idx > done_idx

        # Le message d'erreur doit correspondre
        error_events = [p for p in captured_pushes if p["payload"].get("type") == "error"]
        assert len(error_events) == 1
        assert "Persistance Redis échouée" in error_events[0]["payload"]["message"]

        # Le done doit quand même avoir persiste=False
        done_events = [p for p in captured_pushes if p["payload"].get("type") == "done"]
        assert done_events[0]["payload"]["result"]["persiste"] is False

    def test_resp_not_mutated(self, monkeypatch):
        """L'objet resp original n'est pas muté (ses tirages restent intacts)."""
        resp_holder = {}

        original_run_campaign = None

        def capturing_run_campaign(*args, **kwargs):
            return (_fake_resultats(), {})

        def capturing_save(circuit_slug, campagne_id, response):
            resp_holder["response"] = response
            return True

        def capturing_push(campagne_id, payload):
            return True

        monkeypatch.setattr("app.engine.runner.run_campaign", capturing_run_campaign)
        monkeypatch.setattr(upstash, "save_campaign", capturing_save)
        monkeypatch.setattr(upstash, "push_event", capturing_push)

        original_thread = threading.Thread

        class SyncThread:
            def __init__(self, target, daemon=True):
                self.target = target

            def start(self):
                self.target()

            def join(self, timeout=None):
                pass

        monkeypatch.setattr(threading, "Thread", SyncThread)

        from app.engine import runner
        from app.schemas.reporting import Circuit as CircuitEnum

        sim = SimulationConfig(N_iterations=10, seed=42, cible=Cible(valeur=12.0))
        runner.start_run(CircuitEnum.solaire, [], sim, ["COP"])

        # Le payload sauvegardé doit avoir les tirages
        assert len(resp_holder["response"]["resultats"]["tirages"]) == 3
