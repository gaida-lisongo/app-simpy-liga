# progress.md — Avancement SimpyLIGA

> Fichier unique de vérité sur l'état des sprints.
> Lu par STATUS à chaque "où en est-on?".
> Mis à jour par BUILDER, PATCHER, SENTINEL en fin de session.
> Dernière mise à jour : 2026-08-14

---

## Vue synthétique

```
✅ Sprint 1  — Initialisation projet
🔄 Sprint 2  — Circuit Solaire (finitions)
✅ Sprint 3  — Authentification
⬜ Sprint 4  — Circuit Moteur
⬜ Sprint 5  — Isolation multi-machine (nouveau)
⬜ Sprint 6  — Circuit Couplage
⬜ Sprint 7  — Circuit Frigorifique
⬜ Sprint 8  — Multi-Machine
⬜ Sprint 9  — Dashboard
⬜ Sprint 10 — Déploiement final
```

---

## Sprint 1 — Initialisation ✅

Architecture FastAPI + SvelteKit opérationnelle. Déploiement Render fonctionnel.
Cœur physique CoolProp intégré. Monte-Carlo LHS seed=42 validé.

---

## Sprint 2 — Circuit Solaire 🔄

**Objectif** : Simulation stochastique complète du circuit solaire A4, page frontend, article.

### Backend — finitions restantes

| Anomalie | Description | Statut |
|---|---|---|
| A1 | h_7 depuis cr.states[7].h (pas saturation) | `[x]` corrigé |
| A2 | cop_ref=None si cycle invalide (plus de 0.35) | `[x]` corrigé |
| A3 | σ(COP) > 0 — couplage Voie B | `[x]` implémenté |
| A4 | N_stable = dernier franchissement soutenu | `[x]` corrigé |
| A5 | IC95 = percentiles (pas μ±1.96σ) | `[x]` corrigé |
| A6 | solve_cycle() appelé par itération | `[x]` Voie B active |
| A7 | Export CSV = miroir JSON | `[ ]` à faire |
| M1 | sensitivity.py — Sobol, SRC, Spearman | `[~]` partiel |
| M2 | /api/solaire/fiabilite endpoint | `[~]` fiabilite.py présent |

### Frontend — page solaire

| Composant | Statut |
|---|---|
| SolaireBreadcrumb | `[x]` |
| SolaireCourbesCPC | `[x]` |
| SolaireDiagramme | `[x]` |
| SolaireEtatCycle | `[x]` |
| SolaireKpiGrid | `[x]` |
| SolaireProfilTube | `[x]` |
| SolaireSankey | `[x]` |
| STR_vs_Tgen avec cop_ref=None | `[ ]` à gérer côté UI |

### Article A4

| Étape | Statut |
|---|---|
| Campagne N=10 000 seed=42 | `[x]` camp_20260813T161420Z |
| Analyse statistique complète | `[x]` manuscrit_solaire_v1.tex |
| Validation par doctorant | `[ ]` en attente |

---

## Sprint 3 — Authentification ✅

InternalAuthMiddleware opérationnel. Sessions Redis. Groupes (auth)/(public)/(admin).
Proxy SvelteKit `/api-proxy`. Rate limiting. Logs. Page mon-compte. Gestion utilisateurs admin.

---

## Sprint 4 — Circuit Moteur ⬜

**Périmètre** : États 1→7→8→4, pompe + générateur + tuyère primaire.
**Frontend** : Même structure que solaire (KpiGrid, Diagramme, EtatCycle, Sankey).
**Specs** : voir `docs/sprints/sprint4-moteur.md` (à créer avec EINSTEIN).

---

## Sprint 5 — Isolation multi-machine ⬜

**Objectif** : Chaque chercheur crée ses propres machines et simule chaque circuit.
**Architecture** :
- Modèle de données `Machine` avec `Q_evap_cible`, `T_gen`, `T_evap`, `T_cond`, config complète
- Isolation Redis par `user_id:machine_id:circuit`
- Frontend : dashboard machines → sélection → simulation par circuit
- Backend : `POST /api/machines` + `GET /api/machines/{id}/circuits/{circuit}/run`
**Débloque** : Sprint 8 Dashboard multi-machines + démonstration jury

---

## Sprint 6 — Circuit Couplage ⬜

**Périmètre** : États 4→5→6→1, chambre mélange + diffuseur + condenseur.
**Dépend de** : Sprint 4 (moteur) pour les enthalpies 8→4.

---

## Sprint 7 — Circuit Frigorifique ⬜

**Périmètre** : États 1→2→3→4, détendeur + évaporateur + aspiration secondaire.

---

## Sprint 8 — Multi-Machine ⬜

**Objectif** : Dimensionner n'importe quelle machine en inverse (Q_evap_cible libre).
**Dépend de** : Sprint 5 (isolation) + Sprints 4/6/7 (tous les circuits).
**Démo jury** : configurer live une machine 50 kW et simuler.

---

## Sprint 9 — Dashboard ⬜

Vue globale multi-machines, comparaison campagnes, export publications.

---

## Sprint 10 — Déploiement final ⬜

Hardening sécurité, CI/CD, documentation utilisateur, rapport final thèse.

---

## Ce qui ne doit pas casser

```
✅ Mode inverse Q_evap = cible utilisateur (toujours imposée)
✅ LHS seed=42 reproductible
✅ IC95 par percentiles dans StatSortie
✅ InternalAuthMiddleware sur tous les /api sauf /health
✅ Parallélisation multi-process au-dessus de 150 tirages
✅ Redis cache-first côté frontend
```
