"""
Analyse de sensibilité de Sobol (M1) — indices S1/ST par paramètre et par sortie.

Principe : échantillonnage Saltelli/Sobol générique (SALib), pas de cas
particulier analytique par sortie — les sorties du solveur R718 ne sont pas
de forme produit pure une fois le cycle couplé (A6/Voie B), une approche
fermée ne couvrirait qu'un sous-ensemble des sorties.

Réutilise build_ppf() (app.engine.distributions) — même logique de
transformation quantile -> valeur physique que pour l'échantillonnage LHS
principal — et run_cycle() (app.adapters.physics_adapter) — le même point
d'entrée unique que la campagne principale.

Auteur : Projet Thèse R718 — SimpyLIGA
"""
from __future__ import annotations

import math
from typing import Callable, Optional

import numpy as np
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import sobol as sobol_sample

from app.adapters.physics_adapter import run_cycle
from app.engine.distributions import build_ppf
from app.engine.pool import get_executor, MAX_WORKERS
from app.schemas.reporting import IndiceSobol, Loi, ParametreIncertain

N_SOBOL_DEFAUT = 64
_SEUIL_NAN = 0.20  # au-delà, la sortie est jugée non analysable
PARALLEL_THRESHOLD = 150


def sobol_sample_size(d: int, N_sobol: int) -> int:
    """Taille de l'échantillon Saltelli (calc_second_order=False) : N*(d+2)."""
    return 0 if d <= 0 else N_sobol * (d + 2)


def _run_chunk_ordered(
    tirages: list[dict[str, float]],
    sorties_suivies: list[str],
    cible_kW: float,
) -> list[Optional[dict[str, float]]]:
    """
    Exécuté dans un worker process : calcule run_cycle() pour un lot de
    tirages, en conservant l'ORDRE (None si non physique) — nécessaire pour
    réaligner les sorties sur la matrice d'échantillonnage Sobol/Saltelli.
    """
    rows: list[Optional[dict[str, float]]] = []
    for tirage in tirages:
        out = run_cycle(tirage, cible_kW=cible_kW)
        if not out.get("physically_valid", False):
            rows.append(None)
            continue
        rows.append({
            s: float(out[s]) for s in sorties_suivies
            if s in out and isinstance(out[s], (int, float))
        })
    return rows


def _chunked(items: list, n_chunks: int) -> list[list]:
    n = len(items)
    if n_chunks <= 1:
        return [items]
    size = math.ceil(n / n_chunks)
    return [items[i:i + size] for i in range(0, n, size)]


def compute_sobol(
    params: list[ParametreIncertain],
    sorties_suivies: list[str],
    cible_kW: float,
    N_sobol: int = N_SOBOL_DEFAUT,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> list[IndiceSobol]:
    """
    Calcule les indices de Sobol (premier ordre S1, total ST) pour chaque
    couple (sortie, paramètre variable).

    `parametre` encode "sortie::nom_param" pour tenir dans le schéma
    IndiceSobol existant (pas de champ "sortie" séparé) sans le modifier.

    `progress_cb(n_done)` : nombre de tirages Sobol traités — permet à
    l'appelant (run_campaign) de continuer à publier la progression pendant
    cette phase, qui peut représenter plusieurs centaines d'appels solveur
    sans quoi le flux SSE semble figé après les tirages LHS principaux.
    """
    variables = [p for p in params if p.loi != Loi.fixe]
    fixes = {p.nom: (p.valeur if p.valeur is not None else p.mode or 0.0)
             for p in params if p.loi == Loi.fixe}

    d = len(variables)
    if d == 0 or not sorties_suivies:
        return []

    noms = [p.nom for p in variables]
    ppfs = [build_ppf(p) for p in variables]

    problem = {"num_vars": d, "names": noms, "bounds": [[0.0, 1.0]] * d}
    u = sobol_sample.sample(problem, N_sobol, calc_second_order=False, seed=42)
    n_total = u.shape[0]

    all_tirages: list[dict[str, float]] = []
    for i in range(n_total):
        tirage = dict(fixes)
        for j, nom in enumerate(noms):
            tirage[nom] = float(ppfs[j](float(u[i, j])))
        all_tirages.append(tirage)

    outputs: dict[str, np.ndarray] = {s: np.full(n_total, np.nan) for s in sorties_suivies}

    if n_total >= PARALLEL_THRESHOLD and MAX_WORKERS > 1:
        n_chunks = min(n_total, max(MAX_WORKERS * 4, 40))
        chunks = _chunked(all_tirages, n_chunks)
        executor = get_executor()
        futures = [
            executor.submit(_run_chunk_ordered, chunk, sorties_suivies, cible_kW)
            for chunk in chunks
        ]
        idx = 0
        for chunk, future in zip(chunks, futures):
            for row in future.result():
                if row is not None:
                    for s in sorties_suivies:
                        if s in row:
                            outputs[s][idx] = row[s]
                idx += 1
            if progress_cb is not None:
                progress_cb(idx)
    else:
        step = max(1, n_total // 50)
        for i, tirage in enumerate(all_tirages):
            out = run_cycle(tirage, cible_kW=cible_kW)
            if out.get("physically_valid", False):
                for s in sorties_suivies:
                    val = out.get(s)
                    if isinstance(val, (int, float)):
                        outputs[s][i] = float(val)
            if progress_cb is not None and ((i + 1) % step == 0 or i + 1 == n_total):
                progress_cb(i + 1)

    indices: list[IndiceSobol] = []
    for s, Y in outputs.items():
        frac_nan = float(np.isnan(Y).mean())
        if frac_nan > _SEUIL_NAN:
            continue
        if frac_nan > 0.0:
            Y = np.where(np.isnan(Y), np.nanmean(Y), Y)

        try:
            Si = sobol_analyze.analyze(problem, Y, calc_second_order=False, seed=42)
        except Exception:
            continue

        for j, nom in enumerate(noms):
            indices.append(IndiceSobol(
                parametre=f"{s}::{nom}",
                indice_premier=round(float(Si["S1"][j]), 5),
                indice_total=round(float(Si["ST"][j]), 5),
            ))

    return indices
