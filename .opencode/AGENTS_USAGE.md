# Guide d'utilisation des agents — SimpyLIGA

## Commandes rapides

| Commande | Agent | Coût estimé | Quand l'utiliser |
|---|---|---|---|
| `/status` | STATUS (MiMo V2.5) | ~$0.001 | "Où en est-on ?" |
| `/plan-ui [demande]` | SUPERMAN (GLM-5.3) | ~$0.05 | Nouvelle feature UI ou correction |
| `/build` | BUILDER (DeepSeek Flash) | ~$0.02 | Exécuter le plan SUPERMAN |
| `/plan-science [anomalie]` | EINSTEIN (Qwen3.8 Max) | ~$0.08 | Correction backend/physique |
| `/patch` | PATCHER (Kimi K2.6) | ~$0.03 | Exécuter le plan EINSTEIN |
| `/audit [scope]` | SHEERLOCK→SENTINEL | ~$0.15 | Audit sécurité |
| `/secure` | SENTINEL (DeepSeek Pro) | ~$0.04 | Appliquer patches sécurité |

## Workflow type — Feature UI

```
1. /plan-ui "ajouter graphe STR=f(T_gen) dans la page solaire"
   → SUPERMAN écrit dans memory-bank/feature/activeContext.md
   → /reset ou nouvelle session

2. /build
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
→ Coût : ~$0.001
```

## Règles d'économie de tokens

1. `maxContextTokens: 40000` — déjà configuré
2. STATUS lit UN seul fichier — ne jamais lui demander d'analyser du code
3. `/compact` obligatoire en fin de session BUILDER et PATCHER (long sessions)
4. SUPERMAN et EINSTEIN ne modifient aucun fichier source → pas de rollback à gérer
5. Ne jamais charger `memory-bank/shared/systemPatterns.md` dans une session UI — c'est pour Science uniquement

## Département par tâche

```
Bug Svelte / CSS / UI               → SUPERMAN → BUILDER
Nouvelle page ou composant          → SUPERMAN → BUILDER
Correction thermodynamique backend  → EINSTEIN → PATCHER
Nouveau circuit (A1/A2/A3)          → EINSTEIN → PATCHER
Faille de sécurité                  → SHEERLOCK → SENTINEL
Rapport "où en est-on"              → STATUS
```
