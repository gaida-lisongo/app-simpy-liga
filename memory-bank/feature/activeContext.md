# activeContext.md — Département UI/UX

> Relais entre SUPERMAN et BUILDER.
> SUPERMAN écrit le plan. BUILDER lit et exécute. Écrasé à chaque nouveau plan.

## ⚠️ Piège critique corrigé — 2026-08-15 — LIRE avant toute session UI/réseau

**Ne JAMAIS créer/modifier un wrapper `fetch()` (ex. `apiFetch()`,
`api-proxy/+server.js`) sans grep TOUS ses appelants d'abord**
(`grep -rn "nomFonction(" frontend/src/`). Un bug de déstructuration dans
`frontend/src/lib/server/api.js::apiFetch()` (elle lisait `init.json` alors
que le seul appelant réel envoyait `init.body`) a fait que **le corps de
CHAQUE requête POST passant par `/api-proxy/*` était silencieusement
remplacé par `undefined`**, et cela pendant plusieurs sessions sans qu'aucune
erreur ne se déclenche : le backend a un fallback "corps vide = config
catalogue par défaut" (`circuits.py::run()`), donc chaque requête réussissait
en 200 OK avec des résultats plausibles mais toujours identiques (N=10000,
seed=42, paramètres par défaut) — quel que soit ce que l'utilisatrice
configurait dans le drawer de simulation.

**Symptôme qui doit immédiatement faire suspecter ce pattern** : une action
utilisateur (formulaire, réglage) semble n'avoir AUCUN effet sur le résultat,
alors que le composant qui la capture est syntaxiquement correct — chercher
une couche réseau intermédiaire (proxy, wrapper fetch) qui droppe ou
transforme le corps AVANT de blâmer le composant Svelte lui-même.

**Détail complet** : `memory-bank/feature/journal/2026-08-15.md`, section
"Correction critique — apiFetch() supprimait le corps de TOUTES les requêtes
POST". Règle générale ajoutée à `memory-bank/shared/systemPatterns.md`.

**Fichier corrigé** : `frontend/src/lib/server/api.js::apiFetch()` — corps lu
depuis `init.body` (chaîne déjà sérialisée par l'appelant), plus `init.json`
inexistant côté appelant réel.

---

## Contexte antérieur (clos)

Dernier plan actif : correction `saveCampagne()` — écriture des clés `:meta`
et `:tirages` (2026-08-15, toutes étapes `[x]`, voir
`memory-bank/feature/journal/2026-08-15.md` section précédente).
