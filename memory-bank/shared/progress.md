# progress.md — Avancement SimpyLIGA

> Fichier unique de vérité sur l'état des sprints.
> Lu par STATUS à chaque "où en est-on?".
> Mis à jour par BUILDER, PATCHER, SENTINEL en fin de session.
> Dernière mise à jour : 2026-08-15

---

## Vue synthétique

```
✅ Sprint 1  — Initialisation projet
🔄 Sprint 2  — Circuit Solaire (finitions)
✅ Sprint 3  — Authentification
⬜ Sprint 4  — Multi-Machine
⬜ Sprint 5  — Isolation multi-machine (nouveau)
⬜ Sprint 6  — Circuit Couplage
⬜ Sprint 7  — Circuit Moteur
⬜ Sprint 8  — Circuit Frigorifique
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
| P1 | Persistance campagnes : 413 SvelteKit (payload 4 Mo > 512 Ko) + persist fire-and-forget | `[x]` backend PATCHER ✅ (37/37 tests verts, Δh_gen OK, intégration réelle Upstash validée) — frontend BUILDER ✅ (contrat SSE adapté, fetch Redis après done, build OK) |
| P2 | Dénormalisation Redis : getRecentCampaigns 40 Mo → ~4 Ko (clés :meta) | `[x]` backend PATCHER ✅ (43/43 tests verts, Δh_gen OK, 6 nouveaux tests) — frontend BUILDER ✅ (redis.js modifié : saveCampagne écrit désormais :meta et :tirages, build OK) |
| A4-2 | Solaire : `_run_cycle_solaire()` écrasait `m_dot_pri`/`Q_gen` (solveur) par des valeurs déduites du champ solaire → COP incohérent (0.292 vs 1.009) | `[x]` corrigé 2026-08-15 (50/50 tests verts) — voir `memory-bank/science/activeContext.md` « Plan A4-2 ». Nouvelles sorties : `m_dot_pri_potentiel`, `Q_surplus`, `taux_couverture` |
| A4-5 | `simulation_n_*_cycle.csv` toujours identique (même md5) — `etats_cycle` calculé une seule fois sur le nominal, états par tirage jetés dans `_run_chunk()` | `[x]` corrigé 2026-08-15 (56/56 tests verts) — voir `memory-bank/science/activeContext.md` « Plan A4-5 ». Nouveau `resultats.etats_par_iteration` (flag `collecter_etats`, défaut `False`, exposé sur `POST /api/{circuit}/run`) |
| P3 | Rechargement de page = campagne perdue — `etats_par_iteration` (jusqu'à ~7,5 Mo à N=10 000, activé systématiquement depuis A4-5 frontend) embarqué dans le pipeline Upstash unique de `save_campaign()` → 413 Request Entity Too Large → pipeline atomique échoue intégralement, y compris l'historique | `[x]` corrigé 2026-08-15 (25/25 tests verts) sur branche `feature-streaming-campaign` — `etats_par_iteration` retiré du payload principal, persisté à part par lots de 500 (`RPUSH simpy:campagne:{id}:etats`), reconstruit à la lecture (`redis.js::attacherEtats`). Repro réelle N=10 000 validée (10 000 éléments écrits/relus, 0 erreur 413, vs 4 échecs confirmés en prod avant correctif). |
| P4 | Suite P3 : persistance incrémentale pendant le calcul (pas seulement à la fin) + notification email de fin de campagne | `[x]` corrigé 2026-08-15 (58/58 tests verts) sur `feature-streaming-campaign` — `run_campaign()` prend un callback `on_etats_chunk` appelé par chunk parallèle (`upstash.append_etats_batch`, réutilisé aussi par `save_campaign`) ; `CampagneRequest` gagne `email`/`nom`/`url_webhook` (optionnels, envoyés par `+page.svelte` depuis `locals.user` + `window.location.origin`) ; `runner.py` POST un webhook (`httpx` + `X-Internal-Token`) vers `frontend/.../webhooks/campagne-terminee/+server.js` (route ajoutée aux `PUBLIC_PATHS` de `hooks.server.js`, sinon redirigée vers `/connexion`), qui appelle `sendMail()`. Zéro SMTP côté Python. Validé en réel : streaming observé en direct (progression 150→2000 pendant le calcul, pas en bloc à la fin), webhook testé positif (mail envoyé, aucune erreur loguée) et négatif (URL invalide → échec correctement capturé et loggé, ne bloque jamais le worker). |

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
| HistorySelector (toujours visible) | `[x]` restauré — select visible même sans campagne, option "— Aucune campagne —" |

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

## Sprint 4 — Multi-Machine ⬜

**Objectif** : Dimensionner n'importe quelle machine en inverse (Q_evap_cible libre).
**Dépend de** : Sprint 5 (isolation) + Sprints 4/6/7 (tous les circuits).
**Démo jury** : configurer live une machine 50 kW et simuler.

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

## Sprint 7 — Circuit Moteur ⬜

**Périmètre** : États 1→7→8→4, pompe + générateur + tuyère primaire.
**Frontend** : Même structure que solaire (KpiGrid, Diagramme, EtatCycle, Sankey).
**Specs** : voir `docs/sprints/sprint4-moteur.md` (à créer avec EINSTEIN).

---

## Sprint 8 — Circuit Frigorifique ⬜

**Périmètre** : États 1→2→3→4, détendeur + évaporateur + aspiration secondaire.

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
