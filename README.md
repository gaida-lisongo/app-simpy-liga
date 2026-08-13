# app-simpy-liga

Application web de **validation stochastique** (Monte Carlo) d'une machine
frigorifique à éjecteur au **R718 (eau)**, 12 kW. Backend **FastAPI** exposant
un reporting JSON par circuit ; frontend **SvelteKit + Tailwind**, dashboard
sombre avec 5 pages (`/`, `/moteur`, `/frigorifique`, `/couplage`, `/solar`).

Ce dépôt est **distinct** de `app-machine-r718` (le cœur physique déterministe),
qu'il n'importe que via un unique adaptateur, sans jamais le dupliquer.

---

## Architecture

```
app-simpy-liga/
├── backend/                     ← FastAPI, port 4004
│   ├── app/
│   │   ├── main.py               → application FastAPI (CORS + routes)
│   │   ├── api/routes/circuits.py→ endpoints par circuit + dashboard
│   │   ├── schemas/reporting.py  → format JSON commun (Pydantic)
│   │   ├── core/catalogue.py     → 4 circuits : méta, périmètre, params défaut
│   │   ├── engine/
│   │   │   ├── distributions.py  → lois U / N / Triang → quantiles (LHS)
│   │   │   └── monte_carlo.py    → échantillonnage LHS + propagation + stats
│   │   ├── physics/               → cœur MVC + CoolProp (7 modules, transposé
│   │   │                            depuis app-machine-r718, jamais modifié)
│   │   │   ├── core/               ThermoState + PropsService
│   │   │   └── modules/            pompe, générateur, éjecteur V2, condenseur,
│   │   │                           détendeur, évaporateur, système
│   │   └── adapters/physics_adapter.py → pont UNIQUE vers SystemCycleModel
│   ├── tests/test_api.py
│   └── requirements.txt
└── frontend/                    ← SvelteKit + Tailwind, port 3000
    └── src/routes/               /, /moteur, /frigorifique, /couplage, /solar
```

Les quatre circuits correspondent aux quatre articles. Dimensionnement
**inverse uniquement** : Q_evap = 12 kW est imposée pour les quatre circuits,
le solveur calcule m_dot_p pour l'atteindre.

| Circuit | Article | Pages frontend |
|---|---|---|
| moteur | A1 | `/moteur` |
| frigorifique | A2 | `/frigorifique` |
| couplage | A3 | `/couplage` |
| solaire | A4 | `/solar` |
| (agrégat) | — | `/` (dashboard) |

---

## Installation & lancement (backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

- API : http://localhost:8000
- Documentation interactive (Swagger) : http://localhost:8000/docs

## Installation & lancement (frontend)

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173, proxy /api -> http://localhost:4004
```

Le proxy dev est configurable via `API_PROXY_TARGET` (voir `vite.config.js`).
Toutes les pages appellent l'API en fetch natif sur des chemins relatifs
(`/api/...`) — aucune URL absolue n'est codée en dur, ce qui fonctionne à la
fois en dev (proxy Vite) et en prod (Traefik).

```bash
npm run build           # adapter-node -> dossier build/
node build               # sert le frontend sur le port 3000 (PORT env pour changer)
```

### Tests

```bash
cd backend
pytest -q
```

---

## Endpoints

| Méthode | Chemin | Rôle |
|---|---|---|
| GET | `/api/health` | Sonde de vie ; indique si le cœur physique réel est branché |
| GET | `/api/dashboard` | Synthèse globale multi-circuits (page d'accueil) |
| GET | `/api/{circuit}/config` | Configuration par défaut d'un circuit (paramètres + lois) |
| POST | `/api/{circuit}/run` | Lance une campagne Monte Carlo ; renvoie le reporting JSON |

`{circuit}` ∈ `moteur | frigorifique | couplage | solaire`.

Le corps de `POST /run` est optionnel : sans corps, la configuration par défaut
du catalogue est utilisée (pratique pour une démonstration immédiate).

### Exemple de réponse (`POST /api/moteur/run`, extrait — valeurs réelles CoolProp, N=500)

```json
{
  "article": { "id": "A1", "titre": "Circuit Moteur (branche chaude)", "circuit": "moteur" },
  "perimetre": { "composants": ["pompe","generateur","tuyere_primaire"],
                 "etats": ["1","7","8","4"] },
  "simulation": { "echantillonnage": "LHS", "N_iterations": 500, "seed": 42,
                   "cible": { "grandeur": "Q_e", "valeur": 12.0, "unite": "kW", "tol_pct": 5.0 } },
  "resultats": {
    "statistiques": {
      "COP":       { "moyenne": 1.039, "ecart_type": 0.064, "IC95": [0.913, 1.153] },
      "mu":        { "moyenne": 1.106, "ecart_type": 0.072, "IC95": [0.964, 1.236] },
      "m_dot_pri": { "moyenne": 0.00460, "ecart_type": 0.00031, "IC95": [0.00410, 0.00525] },
      "eta_ex":    { "moyenne": 0.615, "ecart_type": 0.015, "IC95": [0.588, 0.645] }
    },
    "convergence": { "N_stable": 50, "stabilise": true },
    "taux_rejet_non_physique_pct": 0.0
  },
  "campagne_id": "camp_20260813T012348Z",
  "statut": "ok"
}
```

> Dimensionnement **inverse** : Q_evap = 12 kW est la cible fixée, `m_dot_pri`
> est calculé par le solveur pour l'atteindre — c'est la grandeur distribuée
> phare de la thèse, pas Q_evap qui est fixée par construction.

---

## Production (pm2 + Traefik)

Deux process **pm2** tournent en parallèle :

| Process pm2 | Dossier | Port interne |
|---|---|---|
| `app-simpy-liga` | `backend/` (uvicorn) | `4004` |
| `app-simpy-liga-front` | `frontend/` (`node build`, adapter-node) | `3000` |

**Traefik** (`/home/ubuntu/elmesacad/config/traefik/dynamic/app-simpy-liga.yml`)
route `https://simpy-liga.elmes-solution.site` en deux routeurs sur le même
host : `/api*`, `/docs`, `/redoc`, `/openapi.json` → `4004` (priorité haute) ;
tout le reste (`/*`) → `3000` (le frontend SvelteKit).

### Redémarrer après un `git pull`

```bash
cd /home/ubuntu/apps/app-simpy-liga
git pull

# backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt   # seulement si requirements.txt a changé
pm2 restart app-simpy-liga

# frontend
cd ../frontend
npm install                       # seulement si package.json a changé
npm run build
pm2 restart app-simpy-liga-front
```

Vérifier que ça tourne bien :

```bash
pm2 status
pm2 logs app-simpy-liga --lines 30 --nostream
pm2 logs app-simpy-liga-front --lines 30 --nostream
curl -s https://simpy-liga.elmes-solution.site/api/health
curl -s -o /dev/null -w "%{http_code}\n" https://simpy-liga.elmes-solution.site/
```

Pas besoin de retoucher Traefik ni le firewall pour un déploiement courant —
seul le code applicatif change (le fichier Traefik ne change que si le
schéma de routage lui-même évolue).

---

## Branchement du cœur physique réel

Le cœur physique réel est **branché et actif** : `GET /api/health` renvoie
`"coeur_physique_reel": true`. `physics_adapter.py` est le pont **unique**
vers `app/physics/modules/system/model.py` (`SystemCycleModel`), une
transposition MVC + CoolProp des 7 modules du cycle (pompe, générateur,
éjecteur V2, condenseur, détendeur, évaporateur, système) — dérivée de
`app-machine-r718` (jamais modifié ni importé directement ailleurs dans le
code). Aucun mock n'est utilisé en production.

Le dimensionnement est **inverse uniquement** : Q_evap = 12 kW est imposée,
`run_cycle()` retourne les grandeurs distribuées `m_dot_p`, `m_dot_s`, `COP`,
`mu`, `eta_ex` calculées par le solveur pour atteindre cette cible.

---

## Feuille de route

- [x] Backend FastAPI : schémas, catalogue, moteur Monte Carlo, routes, tests
- [x] Branchement du cœur physique réel (CoolProp, MVC, dimensionnement inverse 12 kW)
- [x] Frontend SvelteKit + Tailwind (pages /, /moteur, /frigorifique, /couplage, /solar) — pm2 + Traefik en place
- [ ] Analyse de sensibilité Sobol (SALib) + tests White/Shapiro/Student
- [ ] Export CSV/PNG des campagnes (`campaigns/`)
