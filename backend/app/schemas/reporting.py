"""
Schémas Pydantic — Format JSON commun de reporting (SimpyLIGA).

Ces modèles définissent la structure de réponse de l'API, alignée sur le
« format JSON commun » du Guide de rédaction des 4 articles. Ils servent à la
fois de contrat d'API (documentation OpenAPI automatique) et de validation.

Auteur : Projet Thèse R718 — SimpyLIGA
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
#  Énumérations
# --------------------------------------------------------------------------- #
class Circuit(str, Enum):
    """Les quatre circuits de la machine, un par article."""
    moteur = "moteur"
    frigorifique = "frigorifique"
    couplage = "couplage"
    solaire = "solaire"


class Loi(str, Enum):
    """Lois de probabilité supportées pour les paramètres incertains."""
    uniforme = "uniforme"
    normale = "normale"
    triangulaire = "triangulaire"
    fixe = "fixe"


class ModeSimulation(str, Enum):
    """Sens de résolution du cycle."""
    direct = "direct"
    inverse = "inverse"


# --------------------------------------------------------------------------- #
#  Entrées : paramètres et configuration
# --------------------------------------------------------------------------- #
class ParametreIncertain(BaseModel):
    """Un paramètre du modèle décrit par une loi de probabilité."""
    nom: str = Field(..., description="Identifiant machine, ex. 'T_g'")
    symbole: str = Field(..., description="Symbole affiché, ex. 'T_g'")
    unite: str = Field("-", description="Unité physique, ex. 'degC'")
    loi: Loi = Field(..., description="Loi de probabilité")
    min: Optional[float] = Field(None, description="Borne basse (uniforme/triangulaire)")
    mode: Optional[float] = Field(None, description="Mode (triangulaire) ou moyenne (normale)")
    max: Optional[float] = Field(None, description="Borne haute (uniforme/triangulaire)")
    sigma: Optional[float] = Field(None, description="Écart-type (normale)")
    valeur: Optional[float] = Field(None, description="Valeur imposée (fixe)")
    source: str = Field("chap2", description="Référence bibliographique")


class Cible(BaseModel):
    """Cible du dimensionnement inverse."""
    grandeur: str = "Q_e"
    valeur: float = 12.0
    unite: str = "kW"
    tol_pct: float = 5.0


class SimulationConfig(BaseModel):
    """Configuration d'une campagne de simulation Monte Carlo."""
    outil: str = "SimpyLIGA"
    echantillonnage: str = Field("LHS", description="LHS ou MonteCarlo")
    N_iterations: int = Field(10000, ge=1, description="Nombre de tirages")
    seed: int = Field(42, description="Graine aléatoire (reproductibilité)")
    proprietes: str = "CoolProp"
    mode: ModeSimulation = ModeSimulation.direct
    cible: Optional[Cible] = None


class CampagneRequest(BaseModel):
    """Requête de lancement d'une campagne pour un circuit."""
    circuit: Circuit
    parametres_incertains: list[ParametreIncertain] = Field(default_factory=list)
    parametres_fixes: list[ParametreIncertain] = Field(default_factory=list)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    sorties_suivies: list[str] = Field(
        default_factory=lambda: ["COP", "eta_ex", "m_dot_pri", "mu"]
    )


# --------------------------------------------------------------------------- #
#  Sorties : résultats statistiques
# --------------------------------------------------------------------------- #
class StatSortie(BaseModel):
    """Statistiques descriptives d'une grandeur de sortie."""
    moyenne: Optional[float] = None
    ecart_type: Optional[float] = None
    mediane: Optional[float] = None
    IC95: Optional[list[float]] = Field(None, description="[p2.5, p97.5]")
    minimum: Optional[float] = None
    maximum: Optional[float] = None


class IndiceSobol(BaseModel):
    """Indice de sensibilité de Sobol pour un paramètre."""
    parametre: str
    indice_premier: Optional[float] = None
    indice_total: Optional[float] = None


class Convergence(BaseModel):
    """Résultat de l'étude de convergence."""
    N_stable: Optional[int] = None
    stabilise: Optional[bool] = None


class TestStatistique(BaseModel):
    """Résultat d'un test statistique (p-value + interprétation)."""
    test: str
    p_value: Optional[float] = None
    significatif: Optional[bool] = None
    commentaire: Optional[str] = None


class EtatCycle(BaseModel):
    """Point d'état thermodynamique du cycle de référence (valeurs nominales des paramètres)."""
    point: str = Field(..., description="Numéro du point, ex. '1', '7', '8'")
    T: Optional[float] = Field(None, description="Température [°C]")
    P: Optional[float] = Field(None, description="Pression [bar]")
    h: Optional[float] = Field(None, description="Enthalpie massique [kJ/kg]")
    s: Optional[float] = Field(None, description="Entropie massique [kJ/kg·K]")
    x: Optional[float] = Field(None, description="Titre vapeur [-], None si monophasique")


class BilanEnergetique(BaseModel):
    """Bilan énergétique du cycle de référence (valeurs nominales des paramètres)."""
    Q_evap: Optional[float] = Field(None, description="Puissance frigorifique [kW]")
    Q_gen: Optional[float] = Field(None, description="Puissance apportée au générateur [kW]")
    Q_cond: Optional[float] = Field(None, description="Puissance rejetée au condenseur [kW]")
    W_pompe: Optional[float] = Field(None, description="Puissance de pompage [kW]")
    COP: Optional[float] = None


class Resultats(BaseModel):
    """Bloc de résultats statistiques d'une campagne."""
    statistiques: dict[str, StatSortie] = Field(default_factory=dict)
    convergence: Convergence = Field(default_factory=Convergence)
    sensibilite_sobol: list[IndiceSobol] = Field(default_factory=list)
    tests: list[TestStatistique] = Field(default_factory=list)
    taux_rejet_non_physique_pct: Optional[float] = None
    etats_cycle: list[EtatCycle] = Field(
        default_factory=list,
        description="Points d'état du cycle de référence (paramètres à leur valeur nominale).",
    )
    bilan_energetique: Optional[BilanEnergetique] = Field(
        None, description="Bilan Q_evap/Q_gen/Q_cond/W_pompe/COP du cycle de référence."
    )
    tirages: list[dict[str, float]] = Field(
        default_factory=list,
        description="Tirages Monte Carlo bruts (paramètres variables + sorties suivies), un par ligne.",
    )


# --------------------------------------------------------------------------- #
#  Réponse complète (format commun du guide)
# --------------------------------------------------------------------------- #
class MetaArticle(BaseModel):
    """Métadonnées de l'article/circuit."""
    id: str = Field(..., description="A1, A2, A3, A4")
    titre: str
    circuit: Circuit
    version: str = "provisoire"


class ReportingResponse(BaseModel):
    """
    Réponse JSON complète d'une campagne — le contrat de reporting.

    C'est l'objet que le frontend Svelte consommera pour peupler
    les pages /moteur, /frigorifique, /couplage, /solar et le dashboard.
    """
    article: MetaArticle
    perimetre: dict = Field(default_factory=dict)
    simulation: SimulationConfig
    parametres_incertains: list[ParametreIncertain] = Field(
        default_factory=list,
        description="Paramètres incertains par défaut (présents sur /config ; échos de la requête sur /run).",
    )
    resultats: Resultats = Field(default_factory=Resultats)
    campagne_id: Optional[str] = Field(None, description="Horodatage de campagne")
    statut: str = Field("ok", description="ok | en_cours | erreur")
    message: Optional[str] = None
