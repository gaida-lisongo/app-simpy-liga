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

import numpy as np
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import sobol as sobol_sample

from app.adapters.physics_adapter import run_cycle
from app.engine.distributions import build_ppf
from app.schemas.reporting import IndiceSobol, Loi, ParametreIncertain

N_SOBOL_DEFAUT = 64
_SEUIL_NAN = 0.20  # au-delà, la sortie est jugée non analysable


def compute_sobol(
    params: list[ParametreIncertain],
    sorties_suivies: list[str],
    cible_kW: float,
    N_sobol: int = N_SOBOL_DEFAUT,
) -> list[IndiceSobol]:
    """
    Calcule les indices de Sobol (premier ordre S1, total ST) pour chaque
    couple (sortie, paramètre variable).

    `parametre` encode "sortie::nom_param" pour tenir dans le schéma
    IndiceSobol existant (pas de champ "sortie" séparé) sans le modifier.
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

    outputs: dict[str, np.ndarray] = {s: np.full(u.shape[0], np.nan) for s in sorties_suivies}

    for i in range(u.shape[0]):
        tirage = dict(fixes)
        for j, nom in enumerate(noms):
            tirage[nom] = float(ppfs[j](float(u[i, j])))
        out = run_cycle(tirage, cible_kW=cible_kW)
        if not out.get("physically_valid", False):
            continue
        for s in sorties_suivies:
            val = out.get(s)
            if isinstance(val, (int, float)):
                outputs[s][i] = float(val)

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
