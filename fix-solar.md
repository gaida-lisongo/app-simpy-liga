# SPECIFICATION TECHNIQUE — Extension du circuit solaire SimpyLIGA
## À valider scientifiquement avant implémentation

### CONTEXTE

SimpyLIGA simule une machine frigorifique à éjecteur au R718 (eau pure),
cible Q_evap = 12 kW. Le circuit solaire (Article A4) est la SOURCE CHAUDE
MOTRICE : il fournit la chaleur au générateur du cycle. Actuellement, les 4
paramètres incertains solaires (G, eta_col, T_0, A_col) sont déclarés et tirés
par LHS mais NON couplés au solveur — le COP est constant (σ=0) quel que soit
le rayonnement. On veut implémenter la physique solaire réelle.

### BASE EXISTANTE (cycle R718)

State points (convention) :
  1 = condenseur sortie (liquide saturé, P_cond, x=0)
  2 = détendeur sortie (P_evap, h2=h1, x<1)
  3 = évaporateur sortie (vapeur saturée, P_evap, x=1)
  4 = chambre mélange éjecteur
  5 = diffuseur sortie éjecteur (P_cond)
  6 = condenseur sortie (= point 1)
  7 = pompe sortie (P_gen, liquide comprimé)
  8 = générateur sortie (vapeur saturée, P_gen, x=1)

Cycle metrics existants :
  Q_gen = m_dot_p · (h8 − h7)                  [kW]
  Q_cond = m_dot_total · (h5 − h6)             [kW]
  Q_evap = m_dot_s · (h3 − h2)                 [kW]
  COP = Q_evap / (Q_gen + W_pump)
  mu = m_dot_s / m_dot_p                        (taux d'entraînement éjecteur)
  eta_ex = COP / COP_Carnot_tri_therme

Solveur actuel : mode INVERSE uniquement (impose Q_evap=12 kW, cherche
m_dot_p par itération proportionnelle).

### NOUVEAU MODULE SOLAIRE PROPOSÉ

#### A. Modèle de collecteur CPC (Hottel-Whillier-Bliss simplifié)

Inputs (paramètres incertains tirés par LHS) :
  G        : irradiance solaire directe      [W/m²]   ~ N(800, 100)
  eta_col  : efficacité optique concentrateur [-]      ~ T(0.55, 0.68, 0.78)
  A_col    : surface captante                [m²]     ~ U(20, 60)
  T_0      : température ambiante            [°C]     ~ N(25, 4)

Paramètre fixe :
  k_loss   : coefficient de pertes thermiques globales du CPC  [W/m²·K]
             (estimation : 0.8 W/m²·K, valeur modeste pour un bon CPC
              sous vide — à valider)

Équations (Hottel-Whillier-Bliss simplifié, rendement instantané) :

  Q_sol    = G · A_col / 1000                       [kW]     (puissance incidente)
  Q_opt    = eta_col · Q_sol                        [kW]     (puissance optique absorbée)
  Q_pertes = k_loss · A_col · (T_g − T_0) / 1000   [kW]     (pertes thermiques)
  Q_utile  = max(Q_opt − Q_pertes, 0)               [kW]     (puissance utile livrée)
  eta_th   = Q_utile / Q_sol                         [-]     (rendement thermique instantané)

où T_g = température de génération du cycle (°C), ici 95 °C par défaut.

Ratio thermique solaire :
  STR = Q_utile / Q_gen_cycle                      [-]
  (rapport entre l'apport solaire utile et la chaleur consommée par le générateur)
  → STR > 1 : solaire excédentaire (trop de soleil)
  → STR < 1 : solaire insuffisant (besoin d'appoint)
  → STR = 1 : dimensionnement parfait

QUESTIONS SCIENTIFIQUES À VALIDER :
  Q1. Le coefficient k_loss = 0.8 W/m²·K est-il réaliste pour un CPC sous vide
      à eau (R718, T_sat ≈ 95 °C, P ≈ 0.85 bar) ?
  Q2. Hottel-Whillier-Bliss simplifié (linéaire en ΔT) est-il acceptable pour
      notre plage de température (T_0 ∈ [19, 31] °C, T_g ≈ 95 °C), ou faut-il
      inclure les pertes radiatives (Stefan-Boltzmann) ?
  Q3. Le STR (Solar Thermal Ratio) est-il une métrique scientifiquement
      reconnue, ou s'agit-il plutôt d'un ratio Q_utile/Q_sol (= eta_th) ?
      Quelle définition est la plus pertinente pour la thèse ?
  Q4. Le rendement théorique idéal d'un CPC = 92.2 % (Al-akayshee 2026) —
      eta_th = 0.647 obtenu est-il cohérent avec la littérature R718 ?

#### B. Couplage solaire → cycle R718

Problème : le solveur existant impose Q_evap = 12 kW (inverse), pas Q_gen.

Approche proposée : « Q_gen piloté par solaire » — mode DIRECT avec m_dot_p
calculé depuis le bilan générateur :

  m_dot_p = Q_utile / (h8 − h7)                    [kg/s]
           = Q_utile · 1000 / (h8_SI − h7_SI)       (SI units)

Puis calcul FORWARD du reste du cycle (éjecteur, condenseur, évaporateur)
avec ce m_dot_p. Q_evap sera ce qu'il sera (dépend du mu de l'éjecteur).

Critère de validité physique :
  - Q_evap calculé ≥ 10 kW  → tirage valide (frigidité suffisante)
  - Q_evap < 10 kW OU mu ≤ 0  → tirage rejeté (pas assez de soleil / éjecteur HS)
  - Q_utile < 5 kW → tirage rejeté (solaire insuffisant)

QUESTIONS À VALIDER :
  Q5. Ce mode « direct piloté par solaire » est-il scientifiquement défendable ?
      Alternative : résoudre T_g tel que Q_gen_cycle(T_g) = Q_utile (sous-problème
      non-linéaire, plus complexe, mais préserve le mode inverse Q_evap=12 kW).
  Q6. Le critère Q_evap ≥ 10 kW (vs cible 12 kW ± 5 %) est-il raisonnable pour
      marquer un tirage valide, ou faut-il rester strictement sur 12 kW ± 5 % ?
  Q7. Si Q_utile est insuffisant (< besoin générateur mini), faut-il rejeter
      le tirage (approche stochastique pure) ou activer un appoint thermique
      (combustion/électricité) pour combler ?

#### C. Profil axial du tube absorbeur (graphique phare)

Modèle 1D discret à 10 points le long du tube (longueur L ≈ 2-5 m) :

Zones thermiques :
  Zone 1 — Préchauffage (liquide sous-refroidi → T_sat) : x ∈ [0, L1]
  Zone 2 — Vaporisation (plateau isotherme à T_sat = Psat⁻¹(P_gen)) : x ∈ [L1, L2]
  Zone 3 — (option) Surchauffe : x ∈ [L2, L]

Développement :
  T_fluide(x) : monotone croissante en zone 1, plateau en zone 2
  T_absorbeur(x) = T_fluide(x) + ΔT_convectif
                 où ΔT_convectif = q_local / (h_int · π · D_int)
                 h_int ≈ 500 W/m²·K (convective HT coeff interne R718 liquide,
                 à valider)
  T_vitre(x) = T_absorbeur(x) − ΔT_enveloppe
               où ΔT_enveloppe = q_local / (h_annulus · π · D_outer)
               h_annulus ≈ 5 W/m²·K (vide partiel — à valider)

q_local(x) = Q_utile / L  [W/m]  (répartition uniforme première approximation)

QUESTIONS À VALIDER :
  Q8. h_int ≈ 500 W/m²·K et h_annulus ≈ 5 W/m²·K sont-ils des ordres de
      grandeur réalistes pour un CPC R718 (eau, basse pression, ~95 °C) ?
  Q9. La répartition uniforme de q_local le long du tube est-elle acceptable
      en première approximation, ou faut-il moduler (absorbeur plus chaud
      en entrée) ?
  Q10. Combien de zones réelles pour R718 à 95 °C : 2 (préchauf + évap) ou
       3 (avec surchauffe) ? Le diagramme T-s actuel montre les points 7→8
       sans surchauffe (vapeur saturée x=1 en point 8).

#### D. Profil du fluide caloporteur (HTF)

Hypothèses :
  - HTF = huile thermique synthétique (cp ≈ 2000 J/kg·K, ρ ≈ 800 kg/m³)
  - Débit m_dot_htf ≈ 0.3 kg/s (estimation à valider)

T_HTF(x) : refroidissement linéaire (bilan calorique) :
  T_HTF(x) = T_htf_in − (Q_utile / (m_dot_htf · cp_htf)) · x

T_fluide(t) : réponse transitoire au démarrage (1er ordre) :
  τ = ρ_htf · V_htf · cp_htf / (m_dot_htf · cp_htf)     (~5-10 min)
  T_fluide(t) = T_steady · (1 − exp(−t/τ))

QUESTIONS À VALIDER :
  Q11. Le modèle HTF linéaire est-il suffisant, ou faut-il un échangeur
       contre-courant (LMTD) ?
  Q12. τ ≈ 5-10 min est-il un ordre de grandeur correct pour le temps de
       réponse thermique d'un champ CPC R718 ?

#### E. Courbes CPC (graphiques composant « concentrateur »)

Balayages pour visualisation (calculés en complément du MC, pas par tirage) :

  eta_th = f(G) :
    Pour G ∈ [400, 1200] W/m² (50 points)
    eta_th(G) = (eta_col · G − k_loss · (T_g − T_0)) / G
    (à eta_col, T_g, T_0 fixés nominalement)
    → courbe décroissante (classique)

  STR = f(T_gen) :
    Pour T_gen ∈ [80, 120] °C (20 points)
    Q_utile(T_gen) = eta_col · G − k_loss · (T_gen − T_0)
    STR(T_gen) = Q_utile / Q_gen_cycle(T_gen)
    → courbe décroissante (T_gen ↑ → Q_utile ↓ et Q_gen ↑)
    Optimum ≈ 95 °C attendu (à vérifier)

#### F. Diagramme Sankey exergétique

Flux d'exergie à tracer dans le Sankey :
  Entrée : Q_sol = G · A_col
  → Q_opt = eta_col · Q_sol
  → Pertes optiques  = Q_sol − Q_opt = (1 − eta_col) · Q_sol
  → Q_pertes_therm = k_loss · A · (T_g − T_0)
     Décomposition (optionnelle) :
       Q_pertes_conv = h_conv · A · (T_surf − T_0)
       Q_pertes_rad  = ε · σ · A · (T_surf⁴ − T_0⁴)
  → Q_utile = Q_opt − Q_pertes_therm
  → Q_gen_cycle = Q_utile
  Pertes générateur = Q_utile − Q_gen_cycle (≈ 0 en mode couplé)
  Pertes éjecteur / pompe / condenseur = exergie détruite cycle

QUESTION À VALIDER :
  Q13. Le Sankey doit-il représenter les flux d'EXERGIE (T0·S_gen capté) ou
       les flux d'ÉNERGIE (kW) ? L'exergie est plus pertinente pour la thèse,
       mais l'énergie est plus intuitive pour l'UI. On propose exergie seule.

### G. STRUCTURE DE DONNÉES API (extension du reporting)

SortieCampaign (POST /api/solaire/run) :

  "resultats": {
    "statistiques": {
      "COP":     { moyenne, ecart_type, mediane, IC95, min, max },
      "mu":      {...},
      "Q_gen":   {...},
      "eta_ex":  {...},
      "STR":     {...},       # NOUVEAU
      "eta_th":  {...},       # NOUVEAU
      "Q_utile": {...}        # NOUVEAU
    },
    "etats_cycle": [...],     # déjà présent (points 1-8)
    "bilan_energetique": {...},  # déjà présent
    "profil_tube": {          # NOUVEAU (cycle de référence)
      "x": [0, 0.1, ..., L],
      "T_fluide":    [...],
      "T_absorbeur": [...],
      "T_vitre":     [...],
      "zone": ["prechauf", "prechauf", "vaporisation", ...]
    },
    "profil_htf": {           # NOUVEAU
      "x": [...],
      "T_HTF_x":   [...],    # spatial
      "t": [...],
      "T_fluide_t": [...]    # transitoire démarrage
    },
    "courbes_cpc": {          # NOUVEAU
      "eta_th_vs_G": { "G": [...], "eta_th": [...] },
      "STR_vs_Tgen": { "T_gen": [...], "STR": [...] },
      "optimum_Tgen": 95
    },
    "sankey": {               # NOUVEAU (graphique Sankey)
      "node": { "label": ["Incident", "Optique", "Pertes opt.", ...] },
      "link": { "source": [0,1,1,...], "target": [1,2,3,...], "value": [...] }
    },
    "taux_rejet_non_physique_pct": 0,
    "tirages": [...]          # inclut G, eta_col, T_0, A_col,
                              # COP, mu, Q_gen, eta_ex, STR, eta_th, Q_utile
  }

### H. TESTS UNITAIRES BACKEND

  test_collector_basic :
    G=800, eta_col=0.68, A_col=40, T_0=25, T_g=95
    → Q_sol = 32 kW, Q_opt = 21.76 kW
    → Q_pertes = 0.8*40*70/1000 = 2.24 kW
    → Q_utile = 19.52 kW
    → eta_th = 0.61
    (à valider : cohérent avec 34 kW besoin générateur)

  test_coupling :
    Avec ces inputs, cycle calculé avec Q_gen = Q_utile
    m_dot_p = Q_utile / (h8 − h7) ≈ 0.0085 kg/s
    Q_evap résultant < 12 kW si mu typique ≈ 0.3
    → tirage possiblement rejeté (solaire seul insuffisant à 40 m²)

  test_sigma_positive :
    Avec 20 tirages aléatoires, sigma(COP) > 0
    (preuve que G, eta_col, A_col influencent bien le cycle)

  test_profil_tube :
    profil_tube a 10 points, T_fluide croissante et plateau à T_sat

  test_profil_htf :
    T_HTF_x décroissante le long du tube

  test_courbes :
    eta_th décroissant avec G (régime asymptotique classique)
    STR dépendant de T_gen

### RÉSUMÉ DES CHOIX À VALIDER SCIENTIFIQUEMENT

1. Hottel-Whillier-Bliss linéaire  vs  pertes radiatives Stefan-Boltzmann
2. k_loss = 0.8 W/m²·K  (CPC sous vide)
3. h_int = 500 W/m²·K, h_annulus = 5 W/m²·K
4. Couplage : mode DIRECT m_dot_p = Q_utile/(h8−h7)  vs  T_g ajusté (inverse)
5. Définition de STR : Q_utile/Q_gen_cycle  vs  autre définition scientifique
6. Critère validité tirage : Q_evap ≥ 10 kW (souple) vs Q_evap = 12 ± 5% (strict)
7. 2 zones (préchauf + évap) vs 3 (surchauffe) pour R718 à 95 °C
8. HTF : modèle linéaire vs LMTD contre-courant
9. τ ≈ 5-10 min temps de réponse thermique
10. Sankey exergétique (proposé) vs énergétique

### ATTENTE

Merci de valider ou corriger les hypothèses physiques (Q1-Q13) et les choix
1-10 ci-dessus. Toute correction sera intégrée avant implémentation.