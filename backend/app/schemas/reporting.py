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
        default_factory=list,
        description="Sorties suivies. Vide = utilise SORTIES[circuit] par défaut."
    )
    collecter_etats: bool = Field(
        False,
        description="Si True, collecte les états thermodynamiques de chaque tirage "
                     "retenu (resultats.etats_par_iteration). Coûteux en mémoire "
                     "(~×8) — désactivé par défaut, à activer pour le bilan exergétique.",
    )
    email: Optional[str] = Field(
        None,
        description="Email du chercheur connecté à l'origine de la campagne. "
                     "Fourni avec url_webhook, déclenche une notification à la fin.",
    )
    nom: Optional[str] = Field(
        None, description="Nom affiché dans le mail de notification de fin de campagne.",
    )
    url_webhook: Optional[str] = Field(
        None,
        description="URL du webhook frontend à appeler à la fin de la campagne "
                     "(notification email) — construite côté navigateur, le backend "
                     "n'a pas besoin de connaître l'adresse du frontend.",
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


class FiabiliteRequest(BaseModel):
    """Requête de calcul de fiabilité (M2) — à partir de tirages déjà obtenus."""
    grandeur: str = Field(..., description="Clé de sortie à évaluer, ex. 'STR'")
    seuil: float = Field(..., description="Seuil de succès")
    sens: str = Field("gte", description="'gte' (>= seuil) ou 'lte' (<= seuil)")
    tirages: list[dict[str, float]] = Field(
        ..., description="Tirages bruts déjà obtenus (resultats.tirages d'une campagne).")


class FiabiliteResponse(BaseModel):
    """Probabilité de succès + IC95 exact (Clopper-Pearson)."""
    grandeur: str
    seuil: float
    sens: str
    n_total: int
    n_succes: int
    p_hat: float
    IC95: list[float]
    methode: str = "Clopper-Pearson"


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


class ProfilTube(BaseModel):
    """Profil axial du tube absorbeur — graphique phare du circuit solaire."""
    x_m: list[float] = Field(default_factory=list,
        description="Positions le long du tube [m]")
    T_fluide: list[float] = Field(default_factory=list,
        description="Température fluide R718 [°C]")
    T_absorbeur: list[float] = Field(default_factory=list,
        description="Température paroi tube absorbeur [°C]")
    T_vitre: list[float] = Field(default_factory=list,
        description="Température enveloppe vitre [°C]")
    zones: list[str] = Field(default_factory=list,
        description="Zone thermique : préchauffage | vaporisation | surchauffe")


class CourbesCPC(BaseModel):
    """Courbes de performance du concentrateur pour visualisation."""
    G_range: list[float] = Field(default_factory=list,
        description="Plage d'irradiance [W/m²]")
    eta_th_vs_G: list[float] = Field(default_factory=list,
        description="Rendement thermique en fonction de G [-]")
    T_gen_range: list[float] = Field(default_factory=list,
        description="Plage de température génération [°C]")
    STR_vs_Tgen: list[float] = Field(default_factory=list,
        description="STR en fonction de T_gen [-]")


class SankeySolaire(BaseModel):
    """Données Sankey énergétique/exergétique du circuit solaire."""
    labels: list[str] = Field(default_factory=list)
    values_kW: list[float] = Field(default_factory=list)
    source: list[int] = Field(default_factory=list)
    target: list[int] = Field(default_factory=list)


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
    etats_par_iteration: list[dict] = Field(
        default_factory=list,
        description="États thermodynamiques par tirage retenu (un élément "
                     "{iteration, states} par tirage) — vide si collecter_etats=False.",
    )
    bilan_energetique: Optional[BilanEnergetique] = Field(
        None, description="Bilan Q_evap/Q_gen/Q_cond/W_pompe/COP du cycle de référence."
    )
    tirages: list[dict[str, float]] = Field(
        default_factory=list,
        description="Tirages Monte Carlo bruts (paramètres variables + sorties suivies), un par ligne.",
    )
    profil_tube: Optional[ProfilTube] = Field(
        None, description="Profil axial T_fluide/T_abs/T_vitre — circuit solaire uniquement")
    courbes_cpc: Optional[CourbesCPC] = Field(
        None, description="η_th=f(G) et STR=f(T_gen) — circuit solaire uniquement")
    sankey_solaire: Optional[SankeySolaire] = Field(
        None, description="Flux énergétiques Sankey — circuit solaire uniquement")


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
