# AGENTS.md — SimpyLIGA

Simulateur stochastique (Monte-Carlo + LHS) d'une machine frigorifique à éjecteur R718.
Les sorties alimentent des articles scientifiques. Une erreur silencieuse = un résultat publié faux.

---

## Organisation en 3 départements + Orchestration

Chaque département est un binôme **Primary (planificateur, `mode: primary`,
`edit: deny`, `bash: deny`)** → **Subagent (exécuteur, `mode: subagent`,
`edit: allow`, `bash: allow`)**. Le planificateur ne touche **jamais** au code,
ni via l'outil d'édition (bloqué techniquement) ni via `bash` (bloqué
techniquement aussi — pas de contournement possible par `echo >`, `sed -i`, etc.).
Il écrit un plan dans `memory-bank/{dept}/activeContext.md` que l'exécuteur lit et
applique dans une session séparée. **Tous les Primary sont concernés, pas
seulement STATUS** — voir Protocole de délégation ci-dessous.

> ⚠️ **Ce tableau est un résumé.** `opencode.json` (racine du repo) est la seule
> source de vérité pour les model-id exacts, les permissions et les modes — en cas
> de doute, relire `opencode.json`, pas ce fichier.

| Département | Primary (planifie) | Subagent (exécute) | Rôle |
|---|---|---|---|
| **UI/UX** | SUPERMAN — `anthropic/claude-sonnet-5-20260630` | BUILDER — `deepseek/deepseek-v4-flash-0731-20260731` | Features et corrections interface |
| **Science** | EINSTEIN — `openai/gpt-5.6-sol-pro-20260709` (reasoning=high) | PATCHER — `deepseek/deepseek-v4-pro-20260813` | Corrections thermodynamiques backend |
| **Sécurité** | SHEERLOCK — `anthropic/claude-sonnet-5-20260630` | SENTINEL — `deepseek/deepseek-v4-pro-20260813` | Audit et patches sécurité |
| **Transversal** | STATUS — `google/gemini-3.7-flash-20260813` | — | Passerelle & Orchestrateur — informe, évalue les prompts, améliore, transmet aux primaires, fait le rapport. JAMAIS de code. |

Tous les modèles ci-dessus sont accédés via le provider `openrouter` (voir
`opencode.json`). Les planificateurs (SUPERMAN, EINSTEIN, SHEERLOCK) utilisent des
modèles haut de gamme pour produire des plans complets dès la première tentative
("one-shot") — un plan flou coûte plus cher en itérations de correctif chez
l'exécuteur qu'un modèle plus capable en amont. Les exécuteurs (BUILDER, PATCHER,
SENTINEL) utilisent des modèles rapides/économiques une fois le plan cadré avec
précision — sauf PATCHER/SENTINEL qui reçoivent le modèle DeepSeek "pro" (et non
"flash") car leur exécution (physique, sécurité) demande plus de rigueur logique
que l'implémentation UI de BUILDER.

### Protocole de délégation (TOUS les Primary : SUPERMAN, EINSTEIN, SHEERLOCK, STATUS)

Ce protocole existait déjà pour STATUS ; il s'applique désormais identiquement aux
3 planificateurs de département.

```
Si l'utilisateur demande une édition/implémentation directe
("corrige X", "ajoute Y", "applique le patch Z") :

1. NE JAMAIS tenter d'éditer ou d'exécuter bash pour le faire (de toute façon
   edit: deny et bash: deny bloquent techniquement l'agent — mais l'agent ne
   doit même pas essayer de contourner).
2. TOUJOURS répondre explicitement que cela dépasse le rôle de planification.
3. TOUJOURS proposer un plan concret + désigner l'exécuteur pertinent
   (SUPERMAN→BUILDER, EINSTEIN→PATCHER, SHEERLOCK→SENTINEL).
4. TOUJOURS terminer par une question de validation explicite
   ("Valides-tu ce plan pour que je le transmette à [EXÉCUTEUR] ?").
5. NE JAMAIS transmettre à l'exécuteur sans validation explicite de l'utilisateur.
```

Raison : un plan flou + une édition non validée = boucle de correctifs coûteuse
chez l'exécuteur, et une édition accidentelle par un Primary = coût direct non
souhaité pour l'utilisateur.

### Transversal — Protocole STATUS

```
STATUS reçoit  → requête utilisateur
              → évalue le prompt (clarté, complétude)
              → identifie l'agent primaire (EINSTEIN / SUPERMAN / SHEERLOCK)
              → améliore le prompt
              → transmet via task(subagent_type=primaire)
              → reçoit le résultat
              → synthétise pour l'utilisateur

STATUS contacte UNIQUEMENT : einstein, superman, sheerlock
STATUS ne contacte JAMAIS   : patcher, builder, sentinel, explore, general
```

---

## Règles d'accès aux fichiers

```
UI/UX    (SUPERMAN, BUILDER)  → ÉCRITURE /frontend uniquement
                               → LECTURE /backend autorisée
                               → ÉCRITURE /backend = INTERDIT

Science  (EINSTEIN, PATCHER)  → ÉCRITURE /backend uniquement
                               → LECTURE /frontend autorisée
                               → ÉCRITURE /frontend = INTERDIT

Sécurité (SHEERLOCK, SENTINEL)→ LECTURE + ÉCRITURE /backend ET /frontend
```

**Règle universelle** : `app-machine-r718` est intouché. Jamais.

---

## Protocoles de communication inter-agents

### UI/UX Department
```
SUPERMAN écrit  → memory-bank/feature/activeContext.md
                  (plan avec étapes numérotées, fichiers exacts, critère d'acceptation)
/reset ou nouvelle session
BUILDER lit     → memory-bank/feature/activeContext.md
                → exécute → coche les étapes → journalise
BUILDER écrit   → memory-bank/feature/journal/YYYY-MM-DD.md
BUILDER met à jour → memory-bank/shared/progress.md
```

### Science Department
```
EINSTEIN écrit  → memory-bank/science/activeContext.md
                  (plan avec invariants physiques, tests attendus, valeurs numériques)
/reset ou nouvelle session
PATCHER lit     → memory-bank/science/activeContext.md
                → reproduit → teste rouge → corrige → teste vert
PATCHER écrit   → memory-bank/science/journal/YYYY-MM-DD.md
PATCHER met à jour → memory-bank/shared/progress.md
```

### Sécurité Department
```
SHEERLOCK écrit → memory-bank/security/activeContext.md (plan d'audit)
SENTINEL exécute → memory-bank/security/findings/YYYY-MM-DD.md (rapport)
SHEERLOCK relit → écrit plan de patch dans activeContext.md
SENTINEL relancé → applique les patches → coche dans le plan
```

### Escalades
```
BUILDER voit un bug backend → note dans memory-bank/feature/activeContext.md#Observations
                             → N'y touche pas
PATCHER voit un bug frontend → même chose
SENTINEL trouve une faille archi → remonte à SHEERLOCK avant de toucher
```

---

## Protocole de fin de session (TOUS les agents)

Avant chaque `/compact` ou `/reset` :
1. Mettre à jour le fichier `activeContext.md` de son département (cocher les étapes)
2. Mettre à jour `memory-bank/shared/progress.md`
3. Écrire le journal de session `journal/YYYY-MM-DD.md`
4. Lancer `/compact`

---

## Invariants physiques (département Science)

```python
h_7   = cr.states[7].h          # 146.740 kJ/kg — refoulement pompe — PAS saturation
h_8   = cr.states[8].h          # 2667.614 kJ/kg
Δh_gen = 2520.874 kJ/kg ± 0.5  # si 2269.52 → bug A1 rechuté

STR = COP_ejc × η_th            # Ghodbane 2015 — JAMAIS redéfinir
Q_gen_requis = 12 / COP_ejc     # JAMAIS 0.35 ou 34.28 en dur
IC95 = np.percentile(arr,[2.5,97.5])  # JAMAIS μ ± 1.96σ
Q_evap = 12 kW  imposée          # mode inverse — jamais comme sortie
```

---

## Conventions frontend (département UI/UX)

```
Svelte 5 runes : $state $derived $effect $props $bindable — JAMAIS export let
Plotly.js uniquement — jamais recharts / chart.js / SVG statique
Redis avant API — cache Upstash avant appel VPS
Labels UI = français descriptif — jamais notation technique
$env/static/public côté client — jamais process.env
Skill svelte-pro-ui : charger avant tout .svelte
```

---

## Contexte étendu (charger sur besoin, pas systématiquement)

- `memory-bank/shared/systemPatterns.md` — architecture complète + invariants
- `memory-bank/shared/techStack.md` — stack technique
- `memory-bank/shared/progress.md` — état des 10 sprints
- `frontend/claude.md` — règles UI détaillées
