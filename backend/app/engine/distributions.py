"""
Distributions — conversion d'un ParametreIncertain en loi échantillonnable.

Transforme la description JSON d'un paramètre (uniforme / normale / triangulaire
/ fixe) en une fonction inverse-CDF utilisable par l'échantillonnage Latin
Hypercube. On travaille via la CDF inverse (ppf) pour être compatible LHS :
le sampler fournit des quantiles dans [0,1] que chaque loi transforme en valeur.

Auteur : Projet Thèse R718 — SimpyLIGA
"""

from __future__ import annotations

from typing import Callable
from scipy import stats

from app.schemas.reporting import ParametreIncertain, Loi


def build_ppf(p: ParametreIncertain) -> Callable[[float], float]:
    """
    Retourne la fonction quantile (ppf) d'un paramètre.

    Args:
        p: description du paramètre incertain.

    Returns:
        Une fonction q in [0,1] -> valeur physique.
    """
    if p.loi == Loi.fixe:
        val = p.valeur if p.valeur is not None else (p.mode or 0.0)
        return lambda q, v=val: v

    if p.loi == Loi.uniforme:
        a, b = float(p.min), float(p.max)
        return lambda q, a=a, b=b: a + q * (b - a)

    if p.loi == Loi.normale:
        mu = float(p.mode)
        sigma = float(p.sigma) if p.sigma is not None else abs(mu) * 0.05 or 1.0
        return lambda q, mu=mu, s=sigma: stats.norm.ppf(q, loc=mu, scale=s)

    if p.loi == Loi.triangulaire:
        a, c, b = float(p.min), float(p.mode), float(p.max)
        # scipy: c_rel = (mode - a) / (b - a)
        span = (b - a) if (b - a) != 0 else 1e-9
        c_rel = (c - a) / span
        return lambda q, a=a, span=span, c=c_rel: stats.triang.ppf(
            q, c, loc=a, scale=span
        )

    raise ValueError(f"Loi non supportée : {p.loi}")


def sample_names(params: list[ParametreIncertain]) -> list[str]:
    """Noms des paramètres réellement variables (hors 'fixe')."""
    return [p.nom for p in params if p.loi != Loi.fixe]
