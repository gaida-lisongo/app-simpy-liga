# AGENTS.md — SimpyLIGA

Simulateur stochastique (Monte-Carlo + LHS) d'une machine frigorifique à éjecteur R718.
Les sorties alimentent des articles scientifiques. Une erreur silencieuse = un résultat publié faux.

---

## Organisation en 3 départements

| Département | Agents | Modèles | Rôle |
|---|---|---|---|
| **UI/UX** | SUPERMAN (primary) + BUILDER (primary) | qwen-3.8-max + deepseek-v4-flash | Features et corrections interface |
| **Science** | EINSTEIN (primary) + PATCHER (primary) | claude-sonnet-4-7 + qwen-3.7-plus | Corrections thermodynamiques backend |
| **Sécurité** | SHEERLOCK (primary) + SENTINEL (subagent) | glm-5.2 + deepseek-v4-pro | Audit et patches sécurité |
| **Transversal** | STATUS | inclusionai/ling-2.6-flash | "Où en est-on ?" uniquement |

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
