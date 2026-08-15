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
        """Les 8 commandes sont émises avec les bonnes clés (dénormalisation P2)."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                result = upstash.save_campaign("solaire", "camp_test123", {"foo": "bar"})

        assert result is True
        assert len(captured) == 8

        cmd_set, cmd_expire, cmd_meta_set, cmd_meta_expire, cmd_tir_set, cmd_tir_expire, cmd_lpush, cmd_ltrim = captured

        # 1. SET payload complet
        assert cmd_set[0] == "SET"
        assert cmd_set[1] == "simpy:campagne:camp_test123"
        assert json.loads(cmd_set[2]) == {"foo": "bar"}

        # 2. EXPIRE payload complet
        assert cmd_expire[0] == "EXPIRE"
        assert cmd_expire[1] == "simpy:campagne:camp_test123"
        assert cmd_expire[2] == 86400 * 30

        # 3. SET :meta
        assert cmd_meta_set[0] == "SET"
        assert cmd_meta_set[1] == "simpy:campagne:camp_test123:meta"

        # 4. EXPIRE :meta
        assert cmd_meta_expire[0] == "EXPIRE"
        assert cmd_meta_expire[1] == "simpy:campagne:camp_test123:meta"
        assert cmd_meta_expire[2] == 86400 * 30

        # 5. SET :tirages
        assert cmd_tir_set[0] == "SET"
        assert cmd_tir_set[1] == "simpy:campagne:camp_test123:tirages"

        # 6. EXPIRE :tirages
        assert cmd_tir_expire[0] == "EXPIRE"
        assert cmd_tir_expire[1] == "simpy:campagne:camp_test123:tirages"
        assert cmd_tir_expire[2] == 86400 * 7

        # 7. LPUSH
        assert cmd_lpush[0] == "LPUSH"
        assert cmd_lpush[1] == "simpy:circuit:solaire:history"
        assert cmd_lpush[2] == "camp_test123"

        # 8. LTRIM
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
            with patch.object(upstash, "_pipeline", return_value=["OK"] * 8) as mock_pipe:
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
        # Le flag persiste doit être présent dans result (rétro-compat)
        assert "persiste" in done_result
        assert done_result["persiste"] is True
        # Le flag persiste doit AUSSI être au niveau racine de l'événement (pour le frontend)
        assert done_events[0]["payload"]["persiste"] is True
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

        # Le done doit quand même avoir persiste=False (dans result ET au niveau racine)
        done_events = [p for p in captured_pushes if p["payload"].get("type") == "done"]
        assert done_events[0]["payload"]["result"]["persiste"] is False
        assert done_events[0]["payload"]["persiste"] is False

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


# --------------------------------------------------------------------------- #
#  Dénormalisation P2 — clés :meta et :tirages
# --------------------------------------------------------------------------- #

class TestSaveCampaignDenormalized:
    """save_campaign écrit aussi :meta et :tirages (dénormalisation P2)."""

    def test_meta_key_written_with_six_fields(self):
        """La clé :meta contient exactement 6 champs."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        response = {
            "simulation": {"N_iterations": 10000, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {
                    "COP": {"moyenne": 1.042},
                    "STR": {"moyenne": 0.628},
                },
                "tirages": [{"G": 800, "COP": 1.0}],
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                result = upstash.save_campaign("solaire", "camp_test_meta", response)

        assert result is True
        assert len(captured) == 8

        # Trouver la commande SET :meta
        meta_cmds = [c for c in captured if c[0] == "SET" and ":meta" in str(c[1])]
        assert len(meta_cmds) == 1
        meta_payload = json.loads(meta_cmds[0][2])
        assert meta_payload == {
            "campagne_id": "camp_test_meta",
            "circuit": "solaire",
            "N_iterations": 10000,
            "echantillonnage": "LHS",
            "COP": 1.042,
            "STR": 0.628,
        }

    def test_tirages_key_written_separately(self):
        """La clé :tirages contient uniquement le tableau de tirages bruts."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        tirages_data = [{"G": 800, "COP": 1.0}, {"G": 750, "COP": 0.95}]
        response = {
            "simulation": {"N_iterations": 2, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {"COP": {"moyenne": 0.975}, "STR": {"moyenne": 0.6}},
                "tirages": tirages_data,
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("solaire", "camp_test_tir", response)

        # Trouver la commande SET :tirages
        tir_cmds = [c for c in captured if c[0] == "SET" and ":tirages" in str(c[1])]
        assert len(tir_cmds) == 1
        tir_payload = json.loads(tir_cmds[0][2])
        assert tir_payload == tirages_data

    def test_tirages_ttl_is_7_days(self):
        """Le TTL de :tirages est 604800 (7 jours), pas 30 jours."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        response = {
            "simulation": {"N_iterations": 1, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {"COP": {"moyenne": 1.0}, "STR": {"moyenne": 0.5}},
                "tirages": [{"G": 800}],
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("solaire", "camp_ttl", response)

        # Trouver EXPIRE pour :tirages
        expire_cmds = [c for c in captured if c[0] == "EXPIRE"]
        tir_expire = [c for c in expire_cmds if ":tirages" in str(c[1])]
        assert len(tir_expire) == 1
        assert tir_expire[0][2] == 86400 * 7  # 7 jours

    def test_meta_ttl_is_30_days(self):
        """Le TTL de :meta est 2592000 (30 jours), comme le payload complet."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        response = {
            "simulation": {"N_iterations": 1, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {"COP": {"moyenne": 1.0}, "STR": {"moyenne": 0.5}},
                "tirages": [],
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("solaire", "camp_meta_ttl", response)

        expire_cmds = [c for c in captured if c[0] == "EXPIRE"]
        meta_expire = [c for c in expire_cmds if ":meta" in str(c[1])]
        assert len(meta_expire) == 1
        assert meta_expire[0][2] == 86400 * 30  # 30 jours

    def test_meta_handles_missing_statistiques_gracefully(self):
        """Si COP/STR absents, les champs meta valent None (pas d'exception)."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        response = {
            "simulation": {"N_iterations": 5, "echantillonnage": "MC"},
            "resultats": {},  # pas de statistiques
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("moteur", "camp_no_stats", response)

        meta_cmds = [c for c in captured if c[0] == "SET" and ":meta" in str(c[1])]
        meta_payload = json.loads(meta_cmds[0][2])
        assert meta_payload["COP"] is None
        assert meta_payload["STR"] is None
        assert meta_payload["N_iterations"] == 5

    def test_full_payload_still_has_tirages(self):
        """Le payload complet (clé principale) contient TOUJOURS les tirages."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        tirages_data = [{"G": 800, "COP": 1.0}]
        response = {
            "simulation": {"N_iterations": 1, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {"COP": {"moyenne": 1.0}, "STR": {"moyenne": 0.5}},
                "tirages": tirages_data,
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("solaire", "camp_full", response)

        # La première commande SET (payload complet) doit contenir les tirages
        main_set = [c for c in captured if c[0] == "SET" and c[1] == "simpy:campagne:camp_full"]
        assert len(main_set) == 1
        main_payload = json.loads(main_set[0][2])
        assert main_payload["resultats"]["tirages"] == tirages_data
