# Guide d'utilisation des agents — SimpyLIGA

> Modèles et coûts alignés sur `opencode.json` (source de vérité). Dernière
> synchronisation : 2026-08-15.

## Commandes rapides

| Commande | Agent | Modèle | Coût indicatif* | Quand l'utiliser |
|---|---|---|---|---|
| `/status` | STATUS | `xiaomi/mimo-v2.5` | ~$0.0008 (mesuré, cache 86,8%) | "Où en est-on ?" (lit 1 seul fichier) |
| `/plan-science [anomalie]` | EINSTEIN | `anthropic/claude-sonnet-5` | plus bas que l'ancien `gpt-5.6-sol-pro`, prompt caching actif | Correction backend/physique — plan |
| `/patch` | PATCHER | `deepseek/deepseek-chat` | ~$0.01 | Exécuter le plan EINSTEIN |
| `/audit [scope]` | SHEERLOCK → SENTINEL | `claude-sonnet-5` → `deepseek-chat` | ~$0.05 | Audit sécurité (plan + exécution) |
| `/secure` | SENTINEL | `deepseek/deepseek-chat` | ~$0.01 | Appliquer patches de sécurité |

*Estimation indicative pour un appel isolé (hypothèse ~8k tokens prompt / ~2k
completion pour un planificateur, ~15k/3k pour un exécuteur qui lit du code).
Le coût réel dépend de la taille du contexte chargé (voir `maxContextTokens`) et
du hit-rate de prompt caching sur les 3 Primary Anthropic — un contexte
`memory-bank/` répété entre appels est mis en cache.

### UI/UX — pas de commande dédiée actuellement

SUPERMAN (`anthropic/claude-sonnet-5`) et BUILDER
(`deepseek/deepseek-v4-flash`) sont toujours configurés dans
`opencode.json` — **ils ne sont pas abandonnés**. Les commandes `/plan-ui` et
`/build` ont été retirées volontairement (voir historique git). En attendant
une décision sur leur remplacement, invoque-les directement en mentionnant
l'agent (`@superman`, `@builder`) plutôt que via une commande courte.

## Workflow type — Feature UI

```
1. @superman "ajouter graphe STR=f(T_gen) dans la page solaire"
   → SUPERMAN écrit dans memory-bank/feature/activeContext.md
   → /reset ou nouvelle session

2. @builder
   → BUILDER lit le plan et implémente
   → journalise dans memory-bank/feature/journal/YYYY-MM-DD.md
   → /compact avant de terminer
```

## Workflow type — Correction scientifique

```
1. /plan-science "m_dot_pri semble encore à 0.018, vérifier A1"
   → EINSTEIN lit systemPatterns.md + science/activeContext.md
   → écrit plan détaillé dans memory-bank/science/activeContext.md
   → /reset

2. /patch
   → PATCHER reproduit → teste rouge → corrige → teste vert
   → /compact
```

## Workflow type — "Où en est-on ?"

```
/status
→ STATUS lit UNIQUEMENT memory-bank/shared/progress.md
→ Répond en 10 lignes
→ Coût : ~$0.002
```

## Règles d'économie de tokens

1. `maxContextTokens: 40000` — déjà configuré
2. STATUS lit UN seul fichier — ne jamais lui demander d'analyser du code
3. `/compact` obligatoire en fin de session BUILDER et PATCHER (long sessions)
4. SUPERMAN et EINSTEIN ne modifient aucun fichier source → pas de rollback à gérer
5. Ne jamais charger `memory-bank/shared/systemPatterns.md` dans une session UI — c'est pour Science uniquement
6. SUPERMAN, EINSTEIN et SHEERLOCK tournent avec `prompt_cache: true` (voir
   `opencode.json`) — le contexte `memory-bank/` répété entre appels est mis en
   cache, ce qui réduit le coût des plans "one-shot" sans sacrifier leur qualité

## Département par tâche

```
Bug Svelte / CSS / UI               → SUPERMAN → BUILDER
Nouvelle page ou composant          → SUPERMAN → BUILDER
Correction thermodynamique backend  → EINSTEIN → PATCHER
Nouveau circuit (A1/A2/A3)          → EINSTEIN → PATCHER
Faille de sécurité                  → SHEERLOCK → SENTINEL
Rapport "où en est-on"              → STATUS
```
