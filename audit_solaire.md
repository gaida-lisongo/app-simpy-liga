# Audit et correction — Circuit solaire (A4), SimpyLIGA

Base : commit `61c9a6b6` (avant correctifs). Circuit audité : `Circuit.solaire`.
Décisions du doctorant : **A6 → Voie B (couplage réel)** ; **périmètre → A1–A7 + M1 (Sobol) + M2 (fiabilité)**.

---

## A1 — m_dot_pri : re-saturation au lieu des vraies enthalpies du cycle

**Diagnostic : CONFIRMÉ**

**Localisation** : `backend/app/adapters/physics_adapter.py`, fonction `_run_cycle_solaire` (lignes ~96-99 avant correctif).

**Extrait fautif** :
```python
P_gen   = props.Psat_T(T_g_K)
h_8     = props.hv_P(P_gen)
h_7     = props.hl_P(P_gen)          # liquide SATURÉ à P_gen — pas l'état réel
delta_h = (h_8 - h_7) / 1000.0
m_dot_pri = Q_utile / delta_h if delta_h > 0 else 0.0
```
`h_7` était recalculé comme liquide saturé à la pression du générateur (T=95°C), alors que l'état réel en sortie de pompe (état 7) est un liquide comprimé proche de T_cond (35°C). Le Δh obtenu (~2269-2270 kJ/kg) ne contenait que la chaleur latente à T_gen et omettait le préchauffage sensible réel (~35°C → 95°C) fourni par le générateur.

**Correctif appliqué** : réutilisation des états réels déjà calculés par `SystemCycleModel.solve_cycle()` (`cr.states[7]`, `cr.states[8]`), disponibles depuis A6 via le nouveau helper `_solve_cycle_from_params()` :
```python
h_7 = cr.states[7].h   # J/kg — vraie enthalpie sortie pompe (liquide comprimé)
h_8 = cr.states[8].h   # J/kg — vraie enthalpie vapeur saturée à P_gen
delta_h = (h_8 - h_7) / 1000.0
m_dot_pri = Q_utile / delta_h if delta_h > 0 else 0.0
```
Les appels `props.Psat_T/hv_P/hl_P` et l'import `get_props_service` (devenus inutiles) ont été supprimés.

**Valeurs au point nominal** (T_g=95°C, T_e=8°C, T_c=35°C, rendements nominaux) :

| Grandeur | Avant (bug) | Après (corrigé) |
|---|---|---|
| h_7 (kJ/kg) | 398.09 (liquide sat. à P_gen) | 146.74 (liquide comprimé réel, ~35°C) |
| h_8 (kJ/kg) | 2667.61 | 2667.61 (inchangé — déjà correct) |
| Δh (kJ/kg) | 2269.52 | 2520.87 |
| m_dot_pri (kg/s, nominal) | 0.01833 | 0.01651 |

**Test ajouté** : `test_solaire_m_dot_pri_realiste` (`backend/tests/test_api.py`) — vérifie Δh > 2300 kJ/kg (garde contre le retour de la re-saturation) et `m_dot_pri == Q_utile/Δh_réel`.

**Effets de bord** : aucun — m_dot_pri était une sortie terminale, non réinjectée ailleurs dans le calcul.

---

## A2 — courbes_cpc : COP de référence déconnecté (littéral 0.35)

**Diagnostic : CONFIRMÉ**

**Localisation** : `backend/app/adapters/physics_adapter.py::compute_courbes_cpc` (signature, `cop_ref: float = 0.35`) ; appelant `backend/app/engine/monte_carlo.py` (bloc d'enrichissement solaire, ~ligne 121).

**Extrait fautif** :
```python
resultats.courbes_cpc = CourbesCPC(**compute_courbes_cpc(
    eta_col_nom=_nom.get("eta_col", 0.68),
    phi_s_nom=_nom.get("phi_s", 0.10)))
# cop_ref jamais transmis -> reste à son défaut 0.35, déconnecté du COP réel (~1.04)
```

**Correctif appliqué** : le cycle de référence `ref` (déjà calculé plus haut dans `run_campaign`, `ref = run_cycle(nominal, ..., include_states=True)`) contient déjà le vrai COP résolu. Il est désormais transmis :
```python
resultats.courbes_cpc = CourbesCPC(**compute_courbes_cpc(
    eta_col_nom=_nom.get("eta_col", 0.68),
    phi_s_nom=_nom.get("phi_s", 0.10),
    cop_ref=ref.get("COP", 0.35) if ref.get("physically_valid", False) else 0.35))
```
Aucun nouvel appel solveur — réutilisation d'une valeur déjà calculée.

**Delta** : `STR_vs_Tgen` (T_gen≈95°C) passe de ~0.35×(...) ≈ 0.214 (littéral) à `COP_réel × eta_th_nom` ≈ 1.042 × 0.612 ≈ 0.638 (cohérent avec le STR nominal réellement mesuré par la campagne).

**Test ajouté** : extension de `test_solaire_enrichissements` — vérifie que `courbes_cpc.STR_vs_Tgen` au point T_gen≈95°C est cohérent avec `bilan_energetique.COP × eta_th_nominal` (tolérance 0.05).

**Effets de bord** : aucun.

---

## A3 — Définition de STR

**Diagnostic : INFIRMÉ**

**Localisation** : `backend/app/adapters/physics_adapter.py::_run_cycle_solaire`, `STR = cop * eta_th`.

STR est déjà défini conformément à Ghodbane et al. (2015), éq. 14 : `STR = COP_ejc × η_th`. Aucune redéfinition en `Q_utile/Q_gen` n'a été trouvée dans le code. Aucun correctif de code nécessaire.

**Test renforcé (pas supprimé)** : `test_solaire_STR_definition` validait déjà les bornes physiques de STR mais pouvait passer même avec un COP silencieusement constant (avant A6). Une assertion a été ajoutée : `stats["COP"].ecart_type > 0` — garde désormais contre ce cas, conformément à la contrainte de ne pas supprimer un test qui validait un bug sans distinguer si c'est le test ou le code qui avait tort.

---

## A4 — Convergence : premier croisement au lieu de stabilité soutenue, sortie arbitraire

**Diagnostic : CONFIRMÉ (partiellement différent de l'hypothèse initiale)**

**Localisation** : `backend/app/engine/monte_carlo.py::_convergence` et `run_campaign` (sélection de la sortie analysée).

**Constat précis** : `_convergence()` retournait le premier point de grille où l'écart relatif à la moyenne finale passait sous la tolérance, sans exiger que cette stabilité se maintienne (un croisement isolé suivi d'une re-divergence était compté comme "stable"). Par ailleurs, seule `sorties_suivies[0]` était analysée — pour le solaire, cela valait `"Q_utile"`, qui se trouve être (empiriquement) la sortie la plus lente à converger, mais cet ordre est arbitraire (`SORTIES[Circuit.solaire]` dans `circuits.py`), pas garanti par une logique de sélection du pire cas.

**Correctif appliqué** :
1. `_convergence()` exige désormais la stabilité soutenue jusqu'à la fin de la grille (extraction de la logique dans `_premier_index_stable`, testable indépendamment).
2. `run_campaign()` calcule la convergence pour **toutes** les `sorties_suivies` et rapporte le pire cas (`N_stable` le plus grand, ou non-stabilisé si une sortie ne l'est jamais) dans `resultats.convergence` — schéma Pydantic inchangé (objet unique), pour ne pas casser `McDonutChart.svelte`/`CircuitPage.svelte`.

**Tests ajoutés** (`backend/tests/test_monte_carlo.py`) : `test_premier_index_stable_ignore_croisement_isole`, `test_premier_index_stable_jamais_stable`, `test_premier_index_stable_stable_des_le_debut`, `test_convergence_serie_instable_force_N_stable_tardif`, `test_convergence_pire_sortie_via_run_campaign`.

**Effets de bord** : `N_stable` rapporté peut désormais être plus élevé qu'avant (pire cas parmi toutes les sorties suivies, algorithme de stabilité plus strict) — voir tableau de synthèse.

---

## A5 — IC95

**Diagnostic : INFIRMÉ**

**Localisation** : `backend/app/engine/monte_carlo.py::run_campaign`, `IC95=[percentile(2.5), percentile(97.5)]`.

L'IC95 est déjà un intervalle empirique par percentiles, pas une approximation gaussienne ±1.96σ. Aucun correctif de code nécessaire.

---

## A6 — Couplage solaire/cycle figé (Voie B — couplage réel)

**Diagnostic : CONFIRMÉ — décision Voie B validée par le doctorant**

**Localisation** : `backend/app/adapters/physics_adapter.py::_run_cycle_solaire` (constantes `T_g_K=368.15`, `T_e_K=281.15`, `T_c_K=308.15`, `eta_pump=0.75`, `eta_nozzle=0.92`, `eta_diffuser=0.85`, `eta_mixing=1.00`) ; `backend/app/core/catalogue.py::PARAMETRES[Circuit.solaire]` (absence de ces dimensions).

**Correctif appliqué** :
1. `catalogue.py` — 7 nouveaux paramètres ajoutés au catalogue solaire, en réutilisant les lois déjà validées pour moteur/frigorifique/couplage (mêmes bornes, `_tri`/`_uni` helpers) : `T_g`, `T_e`, `T_c`, `eta_is_p`, `eta_n`, `eta_d`, `eta_m`.
2. `physics_adapter.py` — extraction de `_solve_cycle_from_params(params, cible_kW)`, partagée entre `run_cycle()` (chemin classique) et `_run_cycle_solaire()` : élimine la duplication et fait tourner le cycle R718 solaire aux conditions tirées par LHS, pas figées. **Aucun appel solveur supplémentaire** : `solve_cycle()` était déjà appelé une fois par tirage pour le solaire.
3. `circuits.py::SORTIES[Circuit.solaire]` — ajout de `"COP"` : avant A6, COP était constant sur toute la campagne solaire (calculé à conditions figées) et son absence de la liste des sorties suivies expliquait la case COP toujours `null` du dashboard (`/api/dashboard`). Après A6, COP varie réellement.

**M4 (T_gen figé) est résolu comme effet de bord de cette étape** — pas de correctif séparé.

**Tests** : `test_solaire_params_corrects` étendu (bornes des 7 nouveaux paramètres) ; `test_solaire_sigma_non_nul` et `test_solaire_STR_definition` étendus (`stats["COP"].ecart_type > 0`).

**Effets de bord** : la dimensionnalité de l'espace des paramètres solaire passe de 5 à 12 — la campagne rejouée à seed=42 n'est **pas** bit-à-bit identique à l'ancienne (attendu, documenté dans invariant 5). COP et mu deviennent des sorties suivies pertinentes ; le taux de rejet non-physique peut légèrement augmenter (plus de dimensions échantillonnées, quoique les bornes T_e<T_c<T_g ne se chevauchent jamais par construction).

---

## A7 — Export CSV solaire : colonnes codées en dur

**Diagnostic : CONFIRMÉ**

**Localisation** : `frontend/src/lib/components/solaire/SolaireDonneesBrutes.svelte` (`CSV_COLS = ['id','G_W_m2','eta_col','T0_degC','A_col_m2','COP','mu']`).

`phi_s`, toutes les sorties (`Q_utile, eta_th, STR, m_dot_pri, eta_ex`), et les 7 nouveaux paramètres de A6 étaient absents de l'export.

**Correctif appliqué** : remplacement par le composant générique `RawDataTable.svelte` (déjà utilisé par moteur/frigorifique/couplage), qui dérive ses colonnes dynamiquement (`Object.keys(tirages[0])`) — capte automatiquement toutes les clés présentes. `frontend/src/routes/solaire/+page.svelte` mis à jour ; `SolaireDonneesBrutes.svelte` supprimé (plus aucune référence).

**Effets de bord** : le CSV exporté contient désormais 12 paramètres + 6 sorties suivies (18 colonnes) au lieu de 7 colonnes partiellement vides.

---

## M1 — Indices de sensibilité de Sobol

**Statut : IMPLÉMENTÉ**

**Localisation** : nouveau fichier `backend/app/engine/sensitivity.py` (`compute_sobol`), branché dans `run_campaign()` (paramètre optionnel `N_sobol`) et dans `runner.start_run()` (chemin HTTP `/run`, `N_sobol=N_SOBOL_DEFAUT=64`).

**Conception** : échantillonnage Saltelli/Sobol générique (`SALib`, déjà déclarée en dépendance mais jamais utilisée), pas de cas particulier analytique — les sorties ne sont pas de forme produit pure une fois A6 en place (COP dépend non-linéairement de T_g/T_e/T_c/η_* via le solveur itératif). Réutilise `build_ppf()` (même logique de transformation quantile → valeur physique que le LHS principal) et `run_cycle()` (même point d'entrée que la campagne principale). Résultats stockés dans `resultats.sensibilite_sobol: list[IndiceSobol]`, avec `parametre` encodé `"sortie::nom_param"` (schéma Pydantic `IndiceSobol` inchangé, pas de champ "sortie" séparé).

**Choix de N_sobol** : `run_campaign()` n'appelle PAS Sobol par défaut (`N_sobol=None`) — évite de ralentir les appels directs (tests, campagnes rapides). Le chemin HTTP `/run` (production) l'active avec `N_SOBOL_DEFAUT=64` (mesuré : ~0.115s/appel solveur ⇒ 64×(d+2) appels ≈ 900 appels ≈ 100s pour le circuit solaire à d=12 — proportionné face à un appel principal N=10000 qui prend lui-même ~19 min). **Question ouverte pour le doctorant** : ce N_sobol=64 est un compromis vitesse/précision pour l'usage API courant ; pour une analyse de sensibilité publiable, relancer `compute_sobol(..., N_sobol=1024)` ou plus en offline est recommandé.

**Test ajouté** : `backend/tests/test_sensitivity.py`.

---

## M2 — Endpoint de fiabilité (Clopper-Pearson)

**Statut : IMPLÉMENTÉ**

**Localisation** : `POST /api/{circuit}/fiabilite` (`backend/app/api/routes/circuits.py`), logique dans `backend/app/engine/fiabilite.py::compute_fiabilite`, schémas `FiabiliteRequest`/`FiabiliteResponse` (`backend/app/schemas/reporting.py`).

**Conception** : calcul purement statistique sur des tirages déjà obtenus (`resultats.tirages` d'une campagne complétée, déjà en mémoire côté client après un `/run`) — pas de nouvel appel solveur, endpoint synchrone (pas de file Redis). IC95 exact via `scipy.stats.beta.ppf` (Clopper-Pearson).

**Test ajouté** : `backend/tests/test_fiabilite.py`.

**Question ouverte pour le doctorant** : l'intégration UI (bouton "calculer la fiabilité" sur `/solaire`) n'a pas été faite dans ce lot — le prompt demandait la fonctionnalité backend ; ce n'est pas bloquant pour la livraison de l'audit.

---

## M3 — thermal_mismatch (code mort)

**Statut : TRANCHÉ — non branché dans ce lot**

`GeneratorController`/`CondenserController`/`EvaporatorController` calculent un flag `thermal_mismatch` réel (KA/LMTD vs bilan massique) mais `SystemCycleModel._solve_cycle_direct()` ne les appelle jamais (`result.flags['mismatch_active'] = False` codé en dur). Brancher M3 nécessiterait de fournir des K/A réalistes par composant (actuellement des valeurs par défaut arbitraires, jamais issues du catalogue) — hors périmètre validé de ce lot. Documenté comme dette technique identifiée.

## M4 — T_gen figé

**Statut : RÉSOLU** comme effet de bord de A6/Voie B (voir ci-dessus).

---

## Tableau de synthèse — delta avant/après (N=10000, seed=42)

Rejeu exécuté sur deux copies isolées du code (worktree git pour l'état avant-correctifs
au commit `61c9a6b6`, working tree courant pour l'état après-correctifs), même
configuration `N_iterations=10000, seed=42, cible=12kW`.

| Sortie | μ avant | μ après | σ avant | σ après | IC95 avant | IC95 après |
|---|---|---|---|---|---|---|
| Q_utile | 41.006 | 41.002 | 6.701 | 6.673 | [29.167, 54.956] | [29.159, 54.751] |
| eta_th | 0.6030 | 0.6030 | 0.04667 | 0.04678 | [0.5133, 0.6927] | [0.5133, 0.6933] |
| STR | 0.6282 | 0.6083 | **0.04862** | **0.10884** | [0.5347, 0.7217] | [0.4198, 0.8394] |
| m_dot_pri | 0.018068 | 0.016293 | 0.002953 | 0.002654 | [0.01285, 0.02422] | [0.01159, 0.02179] |
| eta_ex | 0.12090 | 0.12078 | 0.01074 | 0.01388 | [0.1006, 0.1426] | [0.0946, 0.1481] |
| COP | **1.04185** | 1.00863 | **0.0 (constant)** | **0.16088** | **[1.04185, 1.04185]** | [0.7256, 1.3439] |

**Lecture des deltas les plus significatifs** :
- **COP** : σ=0 avant (cycle figé, confirme A6 tel que diagnostiqué) → σ=0.161 après (cycle réellement couplé à T_g/T_e/T_c/rendements tirés).
- **STR** : σ presque doublé (0.0486 → 0.1088) — avant A6, la variance de STR ne venait que de eta_th (via eta_col/phi_s) ; après, elle inclut aussi la variance réelle de COP. Confirme que `test_solaire_STR_definition` validait un bug (STR passait les bornes physiques avec un COP silencieusement constant) — voir A3/A6.
- **m_dot_pri** : μ passe de 0.01807 à 0.01629 kg/s (−9.8%) — effet direct de la correction A1 (Δh réel 2521 kJ/kg > Δh buggé 2270 kJ/kg au nominal, donc m_dot_pri réel plus faible pour le même Q_utile).
- **Q_utile, eta_th, eta_ex** : quasiment inchangés — attendu, ces sorties dépendent de G/eta_col/A_col/phi_s/T_0, non touchés par A1/A6.

Taux de rejet non-physique : avant 0.0 %, après 0.0 % (les nouvelles bornes T_g/T_e/T_c/η_* de A6 ne se chevauchent jamais, aucun rejet introduit).

Convergence (pire sortie parmi les 6 suivies, algorithme de stabilité soutenue) : avant N_stable=50, après N_stable=573. Le saut est cohérent avec A6 : COP (avant constant, donc trivialement "stable" dès le premier point de grille) devient une vraie source de variance qui prend plus de tirages à stabiliser — c'est exactement le genre de sous-estimation de N_stable que l'algorithme corrigé (stabilité soutenue + pire sortie) est censé éliminer.

Durées de calcul mesurées : avant 1191.8 s, après 1059.9 s (10000 tirages chacun, même machine, exécutions concurrentes — ordre de grandeur cohérent, pas de régression de performance introduite par A6 malgré les 7 dimensions supplémentaires).

---

## Tests ajoutés — récapitulatif

| Fichier | Tests | Statut |
|---|---|---|
| `backend/tests/test_api.py` | `test_solaire_m_dot_pri_realiste`, extension `test_solaire_STR_definition`, `test_solaire_sigma_non_nul`, `test_solaire_enrichissements`, `test_solaire_params_corrects` | PASS |
| `backend/tests/test_monte_carlo.py` (nouveau) | `test_premier_index_stable_*` (3), `test_convergence_serie_instable_force_N_stable_tardif`, `test_convergence_pire_sortie_via_run_campaign` | PASS |
| `backend/tests/test_sensitivity.py` (nouveau) | `test_sobol_solaire`, `test_sobol_vide_sans_parametres_variables` | PASS |
| `backend/tests/test_fiabilite.py` (nouveau) | `test_fiabilite_endpoint_gte`, `_lte`, `_grandeur_absente`, `_sens_invalide` | PASS |

Suite complète : `cd backend && pytest` — 24 tests, tous verts (aucun test existant supprimé ; `test_solaire_mode_inverse_preserve` passe sans modification).

---

## Questions ouvertes pour le doctorant

1. **M3** : faut-il fournir des K/A réalistes par composant pour activer le contrôle `thermal_mismatch`, ou rester en dimensionnement idéal (état actuel) ?
2. **M2** : intégration UI de l'endpoint `/fiabilite` sur la page `/solaire` — priorité et maquette à définir.
3. **M1** : `N_SOBOL_DEFAUT=64` (production) est un compromis vitesse/précision — confirmer si une analyse de sensibilité à plus haute résolution (N≥1024) doit être lancée offline pour publication.
4. **A6/Voie B** : les 7 nouvelles distributions reprennent telles quelles les bornes de moteur/frigorifique/couplage — à confirmer que ces bornes restent pertinentes une fois appliquées spécifiquement au sous-système solaire (même plage physique, contexte d'usage potentiellement différent).
