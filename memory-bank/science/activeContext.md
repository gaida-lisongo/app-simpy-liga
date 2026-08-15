# activeContext.md — Département Science

> Relais entre EINSTEIN et PATCHER.
> Mis à jour : 2026-08-15

---

## Plan A4-2 — écrasement de `m_dot_pri` et `Q_gen` dans le circuit solaire — 2026-08-15 ✅ CORRIGÉ

**Statut** : terminé et vérifié. À lire par PATCHER/opencode avant tout nouveau
travail sur `_run_cycle_solaire()` ou sur les sorties du circuit solaire.

### Diagnostic (avant correction)

Dans `_run_cycle_solaire()` (`backend/app/adapters/physics_adapter.py`), les
grandeurs réelles issues du solveur (`m.get("m_dot_p")`, `m.get("Q_gen")`)
étaient **écrasées** par des valeurs déduites du champ solaire :

```python
m_dot_pri = Q_utile / delta_h if delta_h > 0 else 0.0   # ❌ AVANT
out["Q_gen"] = round(Q_utile, 4)                         # ❌ AVANT
```

Conséquence : `COP = Q_evap / Q_gen` reconstruit à partir des clés exportées
ne correspondait plus au COP réellement calculé par le solveur
(mesuré : **0.292 vs 1.0094** sur 305 tirages) — la même incohérence que le
bug A1 historique, mais réintroduite côté solaire uniquement. `m_dot_pri`
valait ~0.0163 kg/s (capacité du champ solaire) au lieu de ~0.0046 kg/s
(débit réel du cycle).

### Correction appliquée

- `backend/app/adapters/physics_adapter.py` — `_run_cycle_solaire()` :
  - `m_dot_pri` et `Q_gen` exportés viennent désormais **du solveur**
    (`m.get("m_dot_p")`, `m.get("Q_gen")`), comme pour moteur/frigorifique/couplage.
    Ne plus jamais les recalculer depuis le champ solaire.
  - La grandeur `Q_utile / Δh` (capacité de dimensionnement du champ solaire,
    PAS le débit du cycle) est conservée mais exportée sous son propre nom :
    **`m_dot_pri_potentiel`**.
  - Deux nouvelles sorties ajoutées : **`Q_surplus`** (`Q_utile − Q_gen`) et
    **`taux_couverture`** (`Q_utile / Q_gen`).
  - `run_cycle()` (moteur/frigorifique/couplage) **non touché** — chemin de
    code totalement séparé, confirmé par test dédié.
- `backend/app/api/routes/circuits.py` — `SORTIES[Circuit.solaire]` étendu
  avec `Q_gen`, `taux_couverture`, `Q_surplus`.
- `backend/tests/test_solaire_couplage.py` (nouveau, 7 tests) — vérifie
  Q_evap=12kW imposée, cohérence COP=Q_evap/Q_gen, ordre de grandeur de
  m_dot_pri (0.003–0.007 kg/s), égalité m_dot_pri == solveur, présence et
  supériorité de m_dot_pri_potentiel, cohérence de Q_surplus, non-régression
  de `run_cycle()` classique.
- `backend/tests/test_api.py::test_solaire_m_dot_pri_realiste` — réécrit :
  l'ancien contrat (`m_dot_pri == Q_utile/Δh`) encodait le bug ; l'assertion
  vérifie maintenant `m_dot_pri_potentiel == Q_utile/Δh_reel` et
  `m_dot_pri < m_dot_pri_potentiel`.

**Suite complète** : `pytest backend/tests/ -v` → 50/50 verts.

### ⚠️ Impact sur la vérification de l'invariant A1

La commande de vérification rapide plus bas dans ce fichier (et dans
`shared/systemPatterns.md`) utilisait `r['m_dot_pri']` pour calculer Δh_gen.
Depuis A4-2, **`m_dot_pri` a changé de sens pour le circuit solaire**
(débit réel du solveur, plus petit) : il faut désormais utiliser
`r['m_dot_pri_potentiel']` pour retrouver Δh_gen ≈ 2520.874 kJ/kg. Voir
commande corrigée en bas de ce fichier.

### Campagne de contrôle N=200 seed=42 (post-correction)

```
Q_utile             mu=41.063  sigma=7.080   (réf. N=10000 : 41.006 — cohérent)
eta_th              mu=0.6031  sigma=0.0477  (réf. : 0.6030 — inchangé, formule non touchée)
STR                 mu=0.6094  sigma=0.1130
m_dot_pri           mu=0.00486 sigma=0.00087 (débit RÉEL solveur — nouveau, remplace l'ancien 0.018)
m_dot_pri_potentiel mu=0.01632 sigma=0.00282 (≈ ancienne valeur exportée à tort sous m_dot_pri)
eta_ex              mu=0.1208  sigma=0.0144  (réf. : 0.1209 — inchangé)
COP                 mu=1.0094  sigma=0.1634
Q_gen               mu=12.218  sigma=2.095
Q_evap              mu=11.9997 sigma=0.0130  (12 kW imposée — OK)
taux_couverture     mu=3.459   sigma=0.828
Q_surplus           mu=28.846  sigma=7.498
tirages valides = 200 / 200
```

Confirme : la physique du champ solaire (Q_utile, η_th, η_ex, Q_evap) est
**inchangée**, seules les clés d'export m_dot_pri/Q_gen/m_dot_pri_potentiel
ont été corrigées.

### Pièges pour PATCHER / opencode

- Ne jamais recalculer `m_dot_pri` ou `Q_gen` depuis les grandeurs solaires
  (`Q_utile`, `Δh`, `A_col`, ...) pour le circuit solaire — elles doivent
  toujours venir de `m.get("m_dot_p")` / `m.get("Q_gen")` (sortie du solveur),
  exactement comme les 3 autres circuits.
- Si besoin de la capacité de dimensionnement du champ solaire, utiliser/lire
  `m_dot_pri_potentiel` — jamais réutiliser le nom `m_dot_pri` pour ça.
- `run_cycle()` (chemin classique) est un code path séparé de
  `_run_cycle_solaire()` : ne pas mélanger les deux en cas de refactor futur.

---

## Plan EINSTEIN — Anomalie P1 : campagnes non persistées dans Redis — 2026-08-14

**Objectif** : Plus aucune campagne Monte-Carlo perdue — la persistance devient
server-side (backend → Upstash direct), l'événement SSE `done` devient léger,
tout échec devient visible (plus de `except: pass` silencieux).

### Diagnostic confirmé (EINSTEIN, preuves à l'appui)

1. **N=10000** : le `done` (4 153 508 o ≈ 470 o/tirage × ~8830 tirages valides)
   arrive au navigateur, puis `POST /db/campagnes` → **413 SvelteKit**
   (`Content-length of 4153508 exceeds limit of 524288 bytes`, log pm2
   `app-simpy-liga-front-error.log`). Le store avale l'erreur (`catch {}`).
   Rien n'est écrit dans Redis. Mesure locale : N=200 → 94 112 o JSON total.
2. **N=500** (~235 Ko < 512 Ko) : pas de 413, mais persistance
   *fire-and-forget* navigateur sans confirmation ; le rechargement de page
   immédiat interrompt le POST en vol. Campagne absente de Redis (vérifié :
   `LRANGE simpy:circuit:solaire:history` = seulement N=200/5/100 du matin).
3. Amplificateurs : `upstash.push_event` avale toutes les exceptions sans log ;
   les files d'événements expirent en 1 h (TTL 3600) ; le flux SSE serveur n'a
   pas de hook `cancel()` (connexions zombies qui peuvent consommer le `done`).
4. Les deux campagnes du jour sont **perdues** (aucune copie backend).
   Reproductibles à l'identique avec seed=42 (LHS déterministe).

### Clés Redis — contrat EXACT à respecter (miroir de frontend/src/lib/server/redis.js)

```
simpy:campagne:{id}                 SET   — ReportingResponse JSON complet
simpy:circuit:{circuit}:history     LIST  — LPUSH {id} en tête, LTRIM 0..19
```
`{circuit}` = slug minuscule (`solaire`, `moteur`, ...). HISTORY_LIMIT = 20.
Ne PAS écrire `simpy:circuit:{circuit}:latest` (dérivé de la tête d'historique
côté frontend ; une clé orpheline existe déjà, la laisser).

### Fichiers concernés (backend)

- `backend/app/core/upstash.py`
  - `push_event()` : renvoyer `bool`, logger l'erreur (module `logging`,
    niveau ERROR, avec campagne_id + taille payload) au lieu de `pass`.
  - Ajouter `save_campaign(circuit_slug: str, campagne_id: str, response: dict) -> bool` :
    pipeline [`SET simpy:campagne:{id} <json>`,
              `LPUSH simpy:circuit:{circuit}:history {id}`,
              `LTRIM simpy:circuit:{circuit}:history 0 19`]
    en UNE requête pipeline. Renvoie False + log ERROR si échec ou Upstash absent.
- `backend/app/engine/runner.py`
  - Dans `worker()` après construction de `resp` :
    1. `ok = upstash.save_campaign(circuit.value, campagne_id, resp.model_dump(mode="json"))`
    2. Construire un événement `done` LÉGER : copie du dump SANS
       `resultats.tirages` (liste vide) — le frontend re-fetchera la campagne
       complète via `/db/campagne/{id}`. Ajouter `"persiste": ok`.
    3. Si `not ok` : pousser AUSSI un événement `{"type": "error",
       "message": "Persistance Redis échouée — résultats affichés mais non sauvegardés"}`
       (après le done, pour que l'UI affiche quand même le résultat).
  - Ne jamais muter `resp` : travailler sur une copie du dict.
- `backend/tests/test_persistance.py` (nouveau) — voir tests ci-dessous.

### Étapes PATCHER

- [x] 1. Reproduire : `backend/.venv/bin/python /tmp/opencode/measure_payload.py`
       (doit afficher ~94 Ko pour N=200 ; extrapolation N=10000 ≈ 4,7 Mo > 512 Ko).
- [x] 2. Implémenter `save_campaign()` dans `upstash.py` (+ `push_event` bool/log).
- [x] 3. Modifier `runner.py` : persistance server-side + `done` léger.
- [x] 4. Tests unitaires (mock `_pipeline`, pas de réseau) :
       `pytest backend/tests/test_persistance.py -v`
       - save_campaign émet exactement [SET, LPUSH, LTRIM] avec les bonnes clés ;
       - l'événement done poussé ne contient AUCUN tirage et pèse < 100 Ko ;
       - échec save_campaign → événement error poussé ;
       - le done contient bien statistiques, convergence, sobol, etats_cycle,
         bilan, profil_tube, courbes_cpc, sankey (tout SAUF tirages).
- [x] 5. Non-régression : `pytest backend/tests/ -v` (tout doit rester vert).
- [x] 6. Vérification numérique (invariant A1) : la commande de vérification
       Δh_gen ci-dessous doit toujours passer (aucune physique touchée).
- [x] 7. Intégration réelle (avec Upstash configuré dans l'env pm2) :
        POST /api/solaire/run N=50 seed=42 → après done, vérifier :
        `LRANGE simpy:circuit:solaire:history 0 0` = id de la campagne,
        `GET simpy:campagne:{id}` contient les tirages, taille done < 100 Ko.
        (Script d'inspection : `/tmp/opencode/inspect_redis2.py` — READ-ONLY.)
        ✅ Validé 2026-08-14 : save_campaign OK, 50 tirages lus, tête historique OK,
        done léger = 4,4 Ko (< 100 Ko).

### Critère d'acceptation

```
Une campagne N=10000 seed=42 se termine → la clé simpy:campagne:{id} existe
avec ≥ 8000 tirages, l'historique solaire la contient en tête, et l'événement
done sur la file pèse < 100 Ko. Aucun chemin de code n'avale une exception
Redis sans log.
```

### Pièges pour PATCHER

- NE PAS changer les noms de clés Redis ni l'ordre LPUSH/LTRIM (le frontend
  lit ces clés telles quelles — `getRecentCampaigns`, `getLatest`).
- NE PAS supprimer `tirages` de `resp` elle-même (la clé Redis doit contenir
  le payload COMPLET) ; seulement de l'événement done.
- NE PAS toucher à la physique (run_cycle, statistiques, IC95 percentiles).
- Le pipeline Upstash renvoie un tableau de résultats ; vérifier les statuts
  (`"OK"`, integer) sans être fragile sur le format exact.
- `upstash.available()` False (dev sans Upstash) : save_campaign renvoie False,
  la campagne continue et le done est poussé quand même sur la file locale… 
  en réalité sans Upstash la file n'existe pas non plus : comportement
  inchangé (best-effort), mais LOGGÉ.
- Ne pas attendre de PATCHER les modifications frontend : elles sont dans le
  plan SUPERMAN ci-dessous. Sans le fix frontend, le backend persiste déjà
  tout — l'UI devra juste re-fetcher au done (fallback actuel : hydrate au
  rechargement de page récupérera la campagne, donc même sans fix frontend
  l'anomalie "disparition au refresh" est corrigée par ce plan backend).

### Escalade SUPERMAN / BUILDER (frontend — INTERDIT à PATCHER)

1. `simulationStore.svelte.js` : au `done`, re-fetcher la campagne complète
   via `/db/campagne/${ev.campagne_id}` (le done est désormais léger) ;
   supprimer le POST du payload complet dans `persist()` ; afficher une
   confirmation/erreur de persistance (`ev.persiste`).
2. `vite.config.js` (options kit du plugin sveltekit) : ajouter
   `bodySizeLimit: '16mb'` — défense en profondeur, nécessaire aussi pour
   `POST /api-proxy/solaire/fiabilite` qui envoie les tirages.
3. `db/campagne/[id]/events/+server.js` : ajouter le hook `cancel()` au
   ReadableStream pour stopper la boucle RPOP quand le client se déconnecte
   (supprime les consommateurs zombies qui peuvent voler le `done`).

### Tests de non-régression

`pytest backend/tests/ -v` : test_api, test_monte_carlo, test_fiabilite,
test_sensitivity — tous verts obligatoirement.

### Données perdues le 2026-08-14

camp_20260814T18xx (N=10000, seed=42) et camp suivante (N=500, seed=42) :
irrécupérables. Relancer N=10000 seed=42 reproduira des statistiques
identiques (LHS déterministe).

---

## Contexte antérieur (toujours ouvert)

Corrections A1–A7 majoritairement appliquées dans le code.
**Restant à vérifier par PATCHER** :

- [ ] A7 — Export CSV : vérifier que toutes les colonnes JSON sont dans le CSV
  - Fichier : `backend/app/engine/monte_carlo.py` section `tirages_bruts`
  - Test : `test_csv_miroir_du_json`
- [ ] M1 — Sobol analytique : vérifier que `sensitivity.py` exporte S_i et S_Ti
  - Test : `pytest backend/tests/test_sensitivity.py -v`
- [ ] Vérification numérique : lancer campagne N=200 seed=42 solaire et confirmer
  `m_dot_pri` ≈ 0.01627 kg/s (pas 0.018)

## Commande de vérification rapide

```bash
backend/.venv/bin/python -c "
from app.adapters.physics_adapter import _run_cycle_solaire
r = _run_cycle_solaire({'G':800,'eta_col':0.68,'A_col':85,'phi_s':0.10,'T_0':25,
                          'T_g':95,'T_e':8,'T_c':35,'eta_is_p':0.75,'eta_n':0.92,
                          'eta_d':0.85,'eta_m':1.00}, cible_kW=12.0)
dh = r['Q_utile']/r['m_dot_pri_potentiel']   # A4-2 : m_dot_pri_potentiel, PAS m_dot_pri
print(f'Δh_gen = {dh:.3f} kJ/kg (attendu 2520.874 ± 0.5)')
assert abs(dh - 2520.874) < 0.5, f'BUG A1: {dh}'
print('OK')
"
```
(à lancer depuis backend/ — le python système n'a pas les dépendances,
utiliser backend/.venv/bin/python)

**⚠️ Depuis A4-2 (2026-08-15)** : pour le circuit solaire, `r['m_dot_pri']`
est le débit RÉEL du solveur (petit, ~0.005 kg/s) — utiliser
`r['m_dot_pri_potentiel']` pour retrouver Δh_gen. Pour les 3 autres circuits
(`run_cycle()`), `m_dot_pri` reste la seule et unique grandeur (pas de
`_potentiel`) et la commande historique avec `run_cycle()` reste valide.

---

## Plan EINSTEIN — Optimisation P2 : dénormalisation Redis (page solaire 30s → <1s) — 2026-08-14

**Objectif** : `getRecentCampaigns()` passe de 40 Mo téléchargés (20 × 2 Mo) à ~4 Ko
(20 × 200 o) en lisant des clés `:meta` au lieu des payloads complets. La page circuit
solaire charge en <1s au lieu de 30s.

### Diagnostic

`frontend/src/lib/server/redis.js:74-92` — `getRecentCampaigns()` :
```javascript
const rows = await Promise.all(ids.map((id) => redis.get(kCampagne(id))));
```
Chaque `redis.get(kCampagne(id))` lit `simpy:campagne:{id}` = payload complet
(~2 Mo pour N=10000). 20 campagnes = **40 Mo** transférés depuis Upstash
pour extraire 5 champs : `campagne_id`, `N_iterations`, `echantillonnage`, `COP`, `STR`.

Le `done` SSE est déjà léger (P1 corrigé — `tirages: []`). Le goulot restant
est l'hydratation de l'historique au chargement de page.

### Solution : dénormalisation Redis

Au lieu d'un seul blob monolithique par campagne, le backend écrit **3 clés** :

```
simpy:campagne:{id}          SET  — payload complet (inchangé, rétrocompatible)
simpy:campagne:{id}:meta     SET  — 5 métadonnées (~200 o, TTL 30j)
simpy:campagne:{id}:tirages  SET  — tirages bruts seuls (~2 Mo, TTL 7j)
```

Le frontend `getRecentCampaigns()` lit `:meta` (20 × 200 o = 4 Ko, instantané).
`getCampagne()` lit toujours le payload complet (1 × 2 Mo, acceptable).

### Invariants physiques — à vérifier dans CHAQUE étape

```
h_7 = cr.states[7].h  (146.740 kJ/kg — refoulement pompe)
h_8 = cr.states[8].h  (2667.614 kJ/kg — vapeur sat. sèche)
Δh_gen = 2520.874 kJ/kg ± 0.5  —  si tu vois 2269.52 → bug A1 rechuté
STR = COP_ejc × η_th  (Ghodbane 2015 éq.14 — JAMAIS redéfinir)
Q_gen_requis = 12 / COP_ejc  — jamais de 0.35 ou 34.28 en dur
IC95 = np.percentile(arr, [2.5, 97.5])  — jamais μ ± 1.96σ
Q_evap = 12 kW imposée — mode inverse uniquement
physics_adapter.py = seul pont physique — jamais dupliquer
app-machine-r718 = INTOUCHÉ
```

### Fichiers concernés (backend — département Science)

- `backend/app/core/upstash.py` — `save_campaign()` : ajouter 2 clés au pipeline
- `backend/app/engine/runner.py` — inchangé (le `done` léger est déjà en place via P1)
- `backend/tests/test_persistance.py` — nouveaux tests pour les clés `:meta` et `:tirages`

### Fichiers concernés (frontend — escalade SUPERMAN/BUILDER, INTERDIT à PATCHER)

- `frontend/src/lib/server/redis.js` — `getRecentCampaigns()` : lire `:meta` au lieu du payload complet
- `frontend/src/lib/stores/simulationStore.svelte.js` — inchangé (utilise déjà `getRecentCampaigns`)

---

### Étape 1 — Modifier `save_campaign()` dans `upstash.py`

- [x] Fait — 8 commandes pipeline (SET+EXPIRE ×3 + LPUSH + LTRIM)

### Étape 2 — Tests unitaires pour les nouvelles clés

- [x] Fait — 6 tests dans `TestSaveCampaignDenormalized`

### Étape 3 — Mise à jour des tests existants (8 commandes au lieu de 4)

- [x] Fait — `test_save_campaign_pipeline_commands` adapté + mock `return_value` corrigé

### Étape 4 — Non-régression

- [x] Fait — 43/43 tests verts

### Étape 5 — Vérification numérique (invariant A1)

- [x] Fait — Δh_gen = 2520.807 kJ/kg (OK)

**Fichier** : `backend/app/core/upstash.py`

Ajouter 2 commandes au pipeline existant (après le `SET` du payload complet,
avant `LPUSH`/`LTRIM`) :

```python
# Construire la métadonnée légère (5 champs)
meta = {
    "campagne_id": campagne_id,
    "circuit": circuit_slug,
    "N_iterations": response.get("simulation", {}).get("N_iterations"),
    "echantillonnage": response.get("simulation", {}).get("echantillonnage"),
    "COP": (
        response.get("resultats", {})
        .get("statistiques", {})
        .get("COP", {})
        .get("moyenne")
    ),
    "STR": (
        response.get("resultats", {})
        .get("statistiques", {})
        .get("STR", {})
        .get("moyenne")
    ),
}
meta_json = json.dumps(meta)

# Extraire les tirages bruts (s'ils existent)
tirages = response.get("resultats", {}).get("tirages", [])
tirages_json = json.dumps(tirages)

META_TTL_S = 86400 * 30   # 30 jours
TIRAGES_TTL_S = 86400 * 7  # 7 jours

_pipeline([
    ["SET", camp_key, payload_json],
    ["EXPIRE", camp_key, CAMP_TTL_S],
    ["SET", f"{camp_key}:meta", meta_json],        # ← NOUVEAU
    ["EXPIRE", f"{camp_key}:meta", META_TTL_S],     # ← NOUVEAU
    ["SET", f"{camp_key}:tirages", tirages_json],   # ← NOUVEAU
    ["EXPIRE", f"{camp_key}:tirages", TIRAGES_TTL_S], # ← NOUVEAU
    ["LPUSH", hist_key, campagne_id],
    ["LTRIM", hist_key, 0, 19],
])
```

**Contrat exact des clés** :
| Clé | Contenu | Taille (N=10000) | TTL |
|---|---|---|---|
| `simpy:campagne:{id}` | Payload complet (inchangé) | ~2 Mo | 30 j |
| `simpy:campagne:{id}:meta` | `{campagne_id, circuit, N_iterations, echantillonnage, COP, STR}` | ~200 o | 30 j |
| `simpy:campagne:{id}:tirages` | `[{G:800, COP:1.0, ...}, ...]` | ~1.8 Mo | 7 j |

**Piège** : le pipeline passe de 4 à 8 commandes. Le mock dans les tests doit
être mis à jour (8 retours au lieu de 4).

---

### Étape 2 — Tests unitaires pour les nouvelles clés

**Fichier** : `backend/tests/test_persistance.py`

Ajouter une classe `TestSaveCampaignDenormalized` :

```python
class TestSaveCampaignDenormalized:
    """save_campaign écrit aussi :meta et :tirages."""

    def test_meta_key_written_with_five_fields(self):
        """La clé :meta contient exactement 6 champs (campagne_id, circuit, N, éch., COP, STR)."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8  # 8 commandes maintenant

        response = {
            "simulation": {"N_iterations": 10000, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {
                    "COP": {"moyenne": 1.042},
                    "STR": {"moyenne": 0.628},
                },
                "tirages": [{"G": 800, "COP": 1.0}],
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                result = upstash.save_campaign("solaire", "camp_test_meta", response)

        assert result is True
        assert len(captured) == 8

        # Trouver la commande SET :meta
        meta_cmds = [c for c in captured if c[0] == "SET" and ":meta" in str(c[1])]
        assert len(meta_cmds) == 1
        meta_payload = json.loads(meta_cmds[0][2])
        assert meta_payload == {
            "campagne_id": "camp_test_meta",
            "circuit": "solaire",
            "N_iterations": 10000,
            "echantillonnage": "LHS",
            "COP": 1.042,
            "STR": 0.628,
        }

    def test_tirages_key_written_separately(self):
        """La clé :tirages contient uniquement le tableau de tirages bruts."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        tirages_data = [{"G": 800, "COP": 1.0}, {"G": 750, "COP": 0.95}]
        response = {
            "simulation": {"N_iterations": 2, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {"COP": {"moyenne": 0.975}, "STR": {"moyenne": 0.6}},
                "tirages": tirages_data,
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("solaire", "camp_test_tir", response)

        # Trouver la commande SET :tirages
        tir_cmds = [c for c in captured if c[0] == "SET" and ":tirages" in str(c[1])]
        assert len(tir_cmds) == 1
        tir_payload = json.loads(tir_cmds[0][2])
        assert tir_payload == tirages_data

    def test_tirages_ttl_is_7_days(self):
        """Le TTL de :tirages est 604800 (7 jours), pas 30 jours."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        response = {
            "simulation": {"N_iterations": 1, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {"COP": {"moyenne": 1.0}, "STR": {"moyenne": 0.5}},
                "tirages": [{"G": 800}],
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("solaire", "camp_ttl", response)

        # Trouver EXPIRE pour :tirages
        expire_cmds = [c for c in captured if c[0] == "EXPIRE"]
        tir_expire = [c for c in expire_cmds if ":tirages" in str(c[1])]
        assert len(tir_expire) == 1
        assert tir_expire[0][2] == 86400 * 7  # 7 jours

    def test_meta_ttl_is_30_days(self):
        """Le TTL de :meta est 2592000 (30 jours), comme le payload complet."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        response = {
            "simulation": {"N_iterations": 1, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {"COP": {"moyenne": 1.0}, "STR": {"moyenne": 0.5}},
                "tirages": [],
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("solaire", "camp_meta_ttl", response)

        expire_cmds = [c for c in captured if c[0] == "EXPIRE"]
        meta_expire = [c for c in expire_cmds if ":meta" in str(c[1])]
        assert len(meta_expire) == 1
        assert meta_expire[0][2] == 86400 * 30  # 30 jours

    def test_meta_handles_missing_statistiques_gracefully(self):
        """Si COP/STR absents, les champs meta valent None (pas d'exception)."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        response = {
            "simulation": {"N_iterations": 5, "echantillonnage": "MC"},
            "resultats": {},  # pas de statistiques
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("moteur", "camp_no_stats", response)

        meta_cmds = [c for c in captured if c[0] == "SET" and ":meta" in str(c[1])]
        meta_payload = json.loads(meta_cmds[0][2])
        assert meta_payload["COP"] is None
        assert meta_payload["STR"] is None
        assert meta_payload["N_iterations"] == 5

    def test_full_payload_still_has_tirages(self):
        """Le payload complet (clé principale) contient TOUJOURS les tirages."""
        captured = []

        def fake_pipeline(commands):
            captured.extend(commands)
            return ["OK"] * 8

        tirages_data = [{"G": 800, "COP": 1.0}]
        response = {
            "simulation": {"N_iterations": 1, "echantillonnage": "LHS"},
            "resultats": {
                "statistiques": {"COP": {"moyenne": 1.0}, "STR": {"moyenne": 0.5}},
                "tirages": tirages_data,
            },
        }

        with patch.object(upstash, "_CLIENT", MagicMock()):
            with patch.object(upstash, "_pipeline", side_effect=fake_pipeline):
                upstash.save_campaign("solaire", "camp_full", response)

        # La première commande SET (payload complet) doit contenir les tirages
        main_set = [c for c in captured if c[0] == "SET" and c[1] == "simpy:campagne:camp_full"]
        assert len(main_set) == 1
        main_payload = json.loads(main_set[0][2])
        assert main_payload["resultats"]["tirages"] == tirages_data
```

---

### Étape 3 — Mise à jour des tests existants (8 commandes au lieu de 4)

**Fichier** : `backend/tests/test_persistance.py`

Dans `TestSaveCampaign.test_save_campaign_pipeline_commands` :
- `assert len(captured) == 4` → `assert len(captured) == 8`
- Le mock `return ["OK", True, 1, "OK"]` → `return ["OK"] * 8`

Dans `TestRunnerPersistance` : aucun changement nécessaire — le runner ne change pas
(le `done` léger est déjà en place, `save_campaign` est mocké).

---

### Étape 4 — Non-régression

```bash
pytest backend/tests/ -v
```

Tous les tests doivent rester verts :
- `test_api` — endpoints REST
- `test_monte_carlo` — boucle LHS, stats, IC95 percentiles
- `test_fiabilite` — Clopper-Pearson
- `test_sensitivity` — Sobol, SRC, Spearman
- `test_persistance` — 6 tests existants + 6 nouveaux = 12 tests

---

### Étape 5 — Vérification numérique (invariant A1)

```bash
cd backend && .venv/bin/python -c "
from app.adapters.physics_adapter import run_cycle
r = run_cycle({'G':800,'eta_col':0.68,'A_col':85,'phi_s':0.10})
dh = r['Q_utile']/r['m_dot_pri']
print(f'Δh_gen = {dh:.3f} kJ/kg (attendu 2520.874 ± 0.5)')
assert abs(dh - 2520.874) < 0.5, f'BUG A1: {dh}'
print('OK')
"
```

---

### Étape 6 — Intégration réelle (avec Upstash configuré)

Lancer une campagne N=50 seed=42, puis vérifier :

```bash
# Vérifier que les 3 clés existent
redis-cli -u "$UPSTASH_REDIS_REST_URL" --pass "$UPSTASH_REDIS_REST_TOKEN" \
  KEYS "simpy:campagne:camp_*"

# Pour la dernière campagne :
# 1. La clé :meta existe et pèse <500 o
# 2. La clé :tirages existe et contient 50 objets
# 3. La clé principale existe toujours (payload complet)
```

---

### Critère d'acceptation

```
1. Une campagne N=10000 seed=42 persistée → 3 clés Redis :
   - simpy:campagne:{id}        : payload complet (~2 Mo)
   - simpy:campagne:{id}:meta   : 6 champs (~200 o)
   - simpy:campagne:{id}:tirages: tableau brut (~1.8 Mo, TTL 7j)

2. getRecentCampaigns() (via GET /db/campagnes?circuit=solaire) :
   - Temps de réponse < 500 ms (contre 30s actuellement)
   - Retourne 20 entrées avec les 5 champs attendus

3. getCampagne(id) (via GET /db/campagne/{id}) :
   - Retourne le payload complet avec tirages (inchangé)

4. Aucune exception silencieuse — tous les échecs Redis sont loggés

5. pytest backend/tests/ -v : 100% vert
```

---

### Pièges pour PATCHER

- **NE PAS** supprimer le `SET` du payload complet — `getCampagne()` et `getLatest()` en dépendent
- **NE PAS** changer l'ordre LPUSH/LTRIM — le frontend lit ces clés telles quelles
- **NE PAS** toucher à `runner.py` — le `done` léger est déjà en place (P1)
- **NE PAS** toucher à la physique (run_cycle, statistiques, IC95 percentiles)
- **NE PAS** modifier les fichiers frontend — c'est le territoire de SUPERMAN/BUILDER
- Le pipeline passe de 4 à 8 commandes : adapter TOUS les mocks qui comptent les commandes
- `response.get("resultats", {}).get("statistiques", {}).get("COP", {}).get("moyenne")` — utiliser `.get()` en cascade pour éviter les KeyError si la structure est incomplète
- Les tirages peuvent être absents (campagne vide ou erreur) → `tirages_json = "[]"` dans ce cas
- `upstash.available()` False : comportement inchangé (best-effort, loggé)

---

### Escalade SUPERMAN / BUILDER (frontend — INTERDIT à PATCHER)

Une fois le backend déployé (les clés `:meta` existent pour les nouvelles campagnes) :

1. **`frontend/src/lib/server/redis.js` — `getRecentCampaigns()`** :
   ```javascript
   // AVANT (lit 20 payloads complets → 40 Mo)
   const rows = await Promise.all(ids.map((id) => redis.get(kCampagne(id))));

   // APRÈS (lit 20 métadonnées → 4 Ko)
   const metaKey = (id) => `simpy:campagne:${id}:meta`;
   const rows = await Promise.all(ids.map((id) => redis.get(metaKey(id))));
   // Fallback : si :meta n'existe pas (vieille campagne), lire le payload complet
   // et extraire les champs manuellement
   ```

2. **`frontend/src/lib/server/redis.js` — `clearCircuit()`** :
   Ajouter le nettoyage des clés `:meta` et `:tirages` :
   ```javascript
   const keys = [
       kHistory(circuit),
       ...ids.map((id) => kCampagne(id)),
       ...ids.map((id) => `${kCampagne(id)}:meta`),     // ← NOUVEAU
       ...ids.map((id) => `${kCampagne(id)}:tirages`),  // ← NOUVEAU
       ...ids.map((id) => `simpy:campagne:${id}:events`),
   ];
   ```

3. **Fallback rétrocompatibilité** : pour les campagnes créées avant ce déploiement,
   la clé `:meta` n'existe pas. `getRecentCampaigns()` doit détecter `null` sur `:meta`
   et fallback vers le payload complet (comportement actuel). Ajouter un log
   `console.warn` pour traquer les vieilles campagnes.

---

### Tests de non-régression

```bash
pytest backend/tests/ -v
```
Tous les tests existants doivent rester verts. Aucune physique modifiée.

---

### Impact sur les campagnes existantes

Les campagnes déjà dans Redis (camp_20260813T161420Z, etc.) n'ont **pas** de clé `:meta`.
Elles continuent de fonctionner normalement via `getCampagne()` (payload complet).
Le frontend devra implémenter un fallback (cf. escalade SUPERMAN).

Pour les nouvelles campagnes (post-déploiement), les 3 clés seront écrites
systématiquement par `save_campaign()`.

