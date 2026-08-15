# Guide d'utilisation des agents — SimpyLIGA

> Modèles et coûts alignés sur `opencode.json` (source de vérité). Dernière
> synchronisation : 2026-08-15.

## Commandes rapides

| Commande | Agent | Modèle | Coût indicatif* | Quand l'utiliser |
|---|---|---|---|---|
| `/status` | STATUS | `google/gemini-3.7-flash` | ~$0.002 | "Où en est-on ?" (lit 1 seul fichier) |
| `/plan-science [anomalie]` | EINSTEIN | `openai/gpt-5.6-sol-pro` | ~$0.10 | Correction backend/physique — plan |
| `/patch` | PATCHER | `deepseek/deepseek-v4-pro-0813` | ~$0.01 | Exécuter le plan EINSTEIN |
| `/audit [scope]` | SHEERLOCK → SENTINEL | `claude-sonnet-5` → `deepseek-v4-pro-0813` | ~$0.05 | Audit sécurité (plan + exécution) |
| `/secure` | SENTINEL | `deepseek/deepseek-v4-pro-0813` | ~$0.01 | Appliquer patches de sécurité |

*Estimation indicative pour un appel isolé (hypothèse ~8k tokens prompt / ~2k
completion pour un planificateur, ~15k/3k pour un exécuteur qui lit du code).
Le coût réel dépend de la taille du contexte chargé — voir `maxContextTokens`.

### UI/UX — pas de commande dédiée actuellement

SUPERMAN (`anthropic/claude-sonnet-5`) et BUILDER
(`deepseek/deepseek-v4-flash-0731`) sont toujours configurés dans
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
6. EINSTEIN tourne avec `reasoning.effort: high` (voir `opencode.json`) — délibérément
   plus lent/cher pour éviter les plans flous qui font boucler PATCHER en correctifs

## Département par tâche

```
Bug Svelte / CSS / UI               → SUPERMAN → BUILDER
Nouvelle page ou composant          → SUPERMAN → BUILDER
Correction thermodynamique backend  → EINSTEIN → PATCHER
Nouveau circuit (A1/A2/A3)          → EINSTEIN → PATCHER
Faille de sécurité                  → SHEERLOCK → SENTINEL
Rapport "où en est-on"              → STATUS
```
