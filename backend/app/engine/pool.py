"""
Pool de process partagé pour paralléliser les tirages Monte Carlo.

Chaque tirage (run_cycle -> CoolProp + solveur scipy) est CPU-bound et pur
Python : le GIL empêche le threading d'apporter un vrai gain multi-cœur ici,
il faut des process séparés. Les tirages étant indépendants les uns des
autres (pas d'état partagé), la campagne se répartit naturellement en lots
traités en parallèle.

Le pool est créé une seule fois au premier besoin (pas par requête HTTP —
le fork/spawn d'un process a un coût non négligeable) et réutilisé par
toutes les campagnes, y compris concurrentes.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor

# Nombre de workers : par défaut, tous les cœurs sauf un (réservé au serveur
# web), plafonné à 4 pour rester raisonnable sur les instances Render
# modestes. Réglable via SIMPY_MAX_WORKERS si l'hébergement offre plus de
# cœurs.
_DEFAULT_WORKERS = max(1, min(4, (os.cpu_count() or 2) - 1))
MAX_WORKERS = int(os.getenv("SIMPY_MAX_WORKERS", str(_DEFAULT_WORKERS)))

_executor: ProcessPoolExecutor | None = None


def get_executor() -> ProcessPoolExecutor:
    """Retourne le pool de process partagé (créé au premier appel)."""
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(
            max_workers=MAX_WORKERS,
            mp_context=multiprocessing.get_context("fork"),
        )
    return _executor


def shutdown_executor() -> None:
    """Arrête proprement le pool (appelé au shutdown de l'app FastAPI)."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=True)
        _executor = None
