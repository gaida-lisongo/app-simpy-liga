# app-simpy-liga

Application web de **validation stochastique** (Monte Carlo) d'une machine
frigorifique à éjecteur au **R718 (eau)**, 12 kW. Backend **FastAPI** exposant
un reporting JSON par circuit ; frontend **SvelteKit + Tailwind + shadcn**
(à venir).

Ce dépôt est **distinct** de `app-machine-r718` (le cœur physique déterministe),
qu'il n'importe que via un unique adaptateur, sans jamais le dupliquer.

---

## Architecture

```
app-simpy-liga/
└── backend/
    ├── app/
    │   ├── main.py                  → application FastAPI (CORS + routes)
    │   ├── api/routes/circuits.py   → endpoints par circuit + dashboard
    │   ├── schemas/reporting.py     → format JSON commun (Pydantic)
    │   ├── core/catalogue.py        → 4 circuits : méta, périmètre, params défaut
    │   ├── engine/
    │   │   ├── distributions.py     → lois U / N / Triang → quantiles (LHS)
    │   │   └── monte_carlo.py       → échantillonnage LHS + propagation + stats
    │   └── adapters/physics_adapter.py → pont UNIQUE vers app-machine-r718
    │                                     (mock physique tant que le cœur réel
    │                                      n'est pas installé)
    ├── config/                      → fichiers JSON de campagnes (guide)
    ├── campaigns/                   → sorties horodatées (csv, png, json)
    ├── tests/test_api.py
    └── requirements.txt
```

Les quatre circuits correspondent aux quatre articles :

| Circuit | Article | Pages frontend | Mode |
|---|---|---|---|
| moteur | A1 | `/moteur` | direct |
| frigorifique | A2 | `/frigorifique` | inverse (cible 12 kW) |
| couplage | A3 | `/couplage` | direct |
| solaire | A4 | `/solar` | direct |
| (agrégat) | — | `/` (dashboard) | — |

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

### Exemple de réponse (`POST /api/moteur/run`, extrait)

```json
{
  "article": { "id": "A1", "titre": "Circuit Moteur (branche chaude)", "circuit": "moteur" },
  "perimetre": { "composants": ["pompe","generateur","tuyere_primaire"],
                 "etats": ["1","7","8","4"] },
  "simulation": { "echantillonnage": "LHS", "N_iterations": 10000, "seed": 42, "mode": "direct" },
  "resultats": {
    "statistiques": {
      "COP": { "moyenne": 0.141, "ecart_type": 0.026, "IC95": [0.094, 0.193] },
      "mu":  { "moyenne": 0.326, "IC95": [0.263, 0.389] }
    },
    "convergence": { "N_stable": 573, "stabilise": true },
    "taux_rejet_non_physique_pct": 0.0
  },
  "campagne_id": "camp_20260812T235010Z",
  "statut": "ok"
}
```

---

## Production (pm2 + Traefik)

En production, le backend tourne sous **pm2** (process `app-simpy-liga`, port
`4004`) et est exposé en HTTPS via **Traefik** sur
`https://simpy-liga.elmes-solution.site` (config Traefik :
`/home/ubuntu/elmesacad/config/traefik/dynamic/app-simpy-liga.yml`).

### Redémarrer après un `git pull`

```bash
cd /home/ubuntu/apps/app-simpy-liga
git pull

cd backend
source .venv/bin/activate
pip install -r requirements.txt   # seulement si requirements.txt a changé

pm2 restart app-simpy-liga
```

Vérifier que ça tourne bien :

```bash
pm2 status app-simpy-liga
pm2 logs app-simpy-liga --lines 30 --nostream
curl -s https://simpy-liga.elmes-solution.site/api/health
```

Pas besoin de toucher à Traefik ni au firewall — seul le code applicatif change.

---

## Branchement du cœur physique réel

Tant que `app-machine-r718` n'est pas disponible, `physics_adapter.py` utilise
un **mock physiquement cohérent** (tendances correctes du COP, de μ, des
débits). Le basculement est automatique : dès que
`from app_r718.modules.system_dashboard.model import SystemCycleModel`
réussit, `core_is_real()` renvoie `True`. Il reste alors à compléter l'appel
réel dans `run_cycle()` (une zone est balisée dans le fichier).

---

## Feuille de route

- [x] Backend FastAPI : schémas, catalogue, moteur Monte Carlo, routes, tests
- [ ] Analyse de sensibilité Sobol (SALib) + tests White/Shapiro/Student
- [ ] Export CSV/PNG des campagnes (`campaigns/`)
- [ ] Branchement du cœur physique réel `app-machine-r718`
- [ ] Frontend SvelteKit + Tailwind + shadcn (pages /, /moteur, /frigorifique, /solar, /couplage)
```
