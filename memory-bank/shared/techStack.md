# techStack.md — SimpyLIGA

## Backend

| Composant | Technologie | Notes |
|---|---|---|
| Framework | FastAPI (Python 3.11) | Async, mode ASGI |
| Thermodynamique | CoolProp (via app-machine-r718) | Singleton PropsService |
| Monte-Carlo | numpy + scipy.stats.qmc (LHS) | seed=42, N=10 000 |
| Stats | numpy, scipy, statsmodels, SALib | Sobol via SALib |
| Auth interne | InternalAuthMiddleware | Header `X-Internal-Token` |
| Cache | Upstash Redis | Redis avant chaque appel API |
| Tests | pytest + conftest _AuthClient | Token auto-injecté |
| Déploiement | Render (Procfile) | VPS production |

## Frontend

| Composant | Technologie | Notes |
|---|---|---|
| Framework | SvelteKit | Adapter-auto |
| UI | Svelte 5 (runes) | `$state` `$derived` `$effect` `$props` |
| Composants | shadcn-svelte + Bits UI | Skill svelte-pro-ui |
| Icônes | lucide-svelte | |
| Charts | Plotly.js uniquement | Interactif, axes log, hover |
| CSS | Tailwind CSS | |
| Cache | Upstash Redis (server-side) | `lib/server/redis.js` |
| Proxy API | `/api-proxy/[...path]/+server.js` | Injecte X-Internal-Token |
| Auth | Sessions Redis | `lib/server/auth.js` |
| Rate limit | `lib/server/ratelimit.js` | |
| Logs | `lib/server/log.js` | |

## Routing SvelteKit

```
(auth)/    → connexion, activation           — pas de layout auth requis
(public)/  → toutes les pages après login    — layout vérifie session
(admin)/   → utilisateurs                    — layout vérifie rôle admin
```

## Variables d'environnement

```bash
# Backend .env
INTERNAL_API_TOKEN=<32+ chars random>   # partagé avec frontend
COOLPROP_REFPROP_PATH=                  # optionnel

# Frontend .env
PUBLIC_API_URL=https://simpy-liga.elmes-solution.site
INTERNAL_API_TOKEN=<même valeur>
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
```

## URLs de production

| Ressource | URL |
|---|---|
| API Backend | https://simpy-liga.elmes-solution.site |
| Swagger | https://simpy-liga.elmes-solution.site/docs |
| Repo backend | https://github.com/gaida-lisongo/app-simpy-liga |
| Repo cœur physique | https://github.com/gaida-lisongo/app-machine-r718 |

## Endpoints API

```
GET  /api/health                → {"statut":"ok","coeur_physique_reel":true}
GET  /api/{circuit}/config      → paramètres incertains
POST /api/{circuit}/run         → campagne Monte-Carlo (SSE progress)
POST /api/solaire/fiabilite     → P(Q < Q_cible), A_col_min
GET  /api/dashboard             → synthèse 4 circuits
```

`{circuit}` ∈ `moteur | frigorifique | couplage | solaire`
