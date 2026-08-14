# Utilisation des agents — app-simpy-liga

## 1. Récap de l'organisation

Tu as défini **5 agents** dans `opencode.json` répartis en 2 phases :

| Agent           | Modèle              | Rôle                                                      | Mode idéal     |
| --------------- | ------------------- | --------------------------------------------------------- | -------------- |
| `planif`        | minimax-m3          | Phase 1a — Planifier une feature (analyse, pas de code)   | `primary`      |
| `code`          | deepseek-v4-flash   | Phase 1b & 2b — Implémenter le code ciblé                 | `primary`      |
| `fix`           | qwen-3.7-plus       | Phase 1c & 2c — Retouches UI/UX, bugs remontés            | `primary`      |
| `audit-check`   | glm-5.2             | Phase 2a — Audit sécurité / régressions                   | `subagent`     |
| `audit-fix`     | deepseek-v4-pro      | Phase 2b — Corriger les failles d'audit                   | `subagent`     |

⚠️ **Ta config actuelle omet le champ `mode`** (défaut = `all`). Il est recommandé de l'expliciter pour qu'ils n'apparaissent pas en double dans les menus.

## 2. Config corrigée (à fusionner dans `opencode.json`)

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["AGENTS.md"],
  "skills": { "paths": ["frontend/.opencode/skills"] },
  "maxContextTokens": 40000,
  "agents": {
    "planif": {
      "mode": "primary",
      "model": "minimax-m3",
      "temperature": 0.2,
      "description": "Phase 1a: Planification d'une mission/feature"
    },
    "code": {
      "mode": "primary",
      "model": "deepseek-v4-flash",
      "temperature": 0.1,
      "description": "Phase 1b & 2b: Implémentation rapide du code"
    },
    "fix": {
      "mode": "primary",
      "model": "qwen-3.7-plus",
      "temperature": 0.2,
      "description": "Phase 1c & 2c: Retouches, bugs UI/UX et retours utilisateurs"
    },
    "audit-check": {
      "mode": "subagent",
      "model": "glm-5.2",
      "temperature": 0.3,
      "description": "Phase 2a: Audit de sécurité, régressions et failles"
    },
    "audit-fix": {
      "mode": "subagent",
      "model": "deepseek-v4-pro",
      "temperature": 0.1,
      "description": "Phase 2b: Implémentation des correctifs d'audit"
    }
  }
}
```

## 3. Les 4 méthodes pour changer d'agent (sans `/models`)

### A. `Tab` — cycle entre primary agents ⭐ le plus rapide

Pendant une session TUI, appuie sur `Tab` (ou `Shift+Tab`) pour basculer entre `planif`, `code`, `fix` sans rien taper.

```
[planif] » planifier la feature X
          ↓ Tab
[code]   » (la conversation continue, nouveau modèle)
```

### B. `@mention` — invoquer un subagent

Dans n'importe quel message, tape `@` pour ouvrir l'autocomplétion et choisis le subagent.

```
@audit-check audite le backend FastAPI et génère le rapport
@audit-fix applique le rapport d'audit du 14 août
```

### C. Slash commands — un `/` pour orchestrer

Crée `.opencode/commands/wf-feature.md` :

```markdown
---
description: Workflow complet feature (planif → code → fix)
agent: planif
---
Analyse cette demande : $ARGUMENTS.
Sors une checklist structurée, ne touche à aucun fichier.
```

Puis tape `/wf-feature ajouter pagination sur /api/tarifs`.

Tu peux créer un fichier par étape :

- `.opencode/commands/wf-plan.md` → agent `planif`
- `.opencode/commands/wf-code.md` → agent `code`
- `.opencode/commands/wf-fix.md` → agent `fix`
- `.opencode/commands/wf-audit.md` → agent `audit-check`, `subtask: true`

### D. Sessions parallèles — un agent par terminal

Ouvre 3 terminaux et fixe l'agent au démarrage :

```bash
# Terminal 1
opencode --agent planif

# Terminal 2
opencode --agent code

# Terminal 3
opencode --agent fix
```

Chaque terminal a son contexte isolé. Idéal pour les 3 phases séquentielles.

## 4. Workflow concret (exemple de bout en bout)

**Demande** : « ajouter un bouton de reset sur la page dashboard »

**Étape 1 — Planif** (via Tab ou `/wf-plan`)
```
[planif] » @planif comment ajouter un bouton reset sur le dashboard ?
```
→ Retour : checklist des fichiers à modifier (`+page.svelte`, `Button.svelte`, etc.)

**Étape 2 — Code** (Tab pour switch auto)
```
[code] » @code implémente la checklist précédente, scope = frontend uniquement
```
→ Retour : code appliqué, `npm run build` doit passer.

**Étape 3 — Fix** (Tab)
```
[fix] » @fix le bouton reset fonctionne mais l'animation est saccadée sur mobile
```
→ Retour : retouches UI/UX ciblées.

**Étape 4 — Audit** (subagent via @)
```
[code] » @audit-check vérifie les régressions sur /dashboard après ces changements
```
→ Retour : rapport markdown.

**Étape 5 — Audit-fix** (subagent via @)
```
[code] » @audit-fix applique le rapport ci-dessus
```

## 5. Keybinds utiles (déjà fournis par défaut)

| Raccourci          | Action                              |
| ------------------ | ----------------------------------- |
| `Tab`              | Agent suivant (primary)             |
| `Shift+Tab`        | Agent précédent (primary)           |
| `Ctrl+P`           | Liste des commandes                 |
| `<leader>a` (= `Ctrl+X` puis `a`) | Liste des agents         |
| `<leader>m`        | Liste des modèles                   |
| `Up` / `Down` / `Right` / `Left` | Navigation entre sessions subagents |

## 6. Anti-pièges

- **Ne jamais utiliser `process.env` côté client** — utiliser `$env/static/public` (SvelteKit).
- **`mode: primary` ≠ permission totale** — les primary agents héritent des permissions globales. Verrouille `edit`/`bash` à `ask` sur `planif` si tu veux qu'il ne touche jamais au code.
- **`@subagent` crée une session enfant** — remonte avec `Up` (`session_parent`) pour revenir à la session parente.
- **Invoquer un subagent ne change pas ton primary agent** — tu restes sur `code` même après `@audit-check`.
