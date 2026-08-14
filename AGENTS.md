# Directives du Projet (FastAPI + Svelte)

## Structure du dépôt
- `backend/` : API Python FastAPI
- `frontend/` : Application Svelte

## RÈGLES D'ÉCONOMIE DE TOKENS (STRICT)
1. Ne lis **QUE** les fichiers nécessaires à la tâche courante.
2. N'écris pas de longs discours. Va droit au but dans tes réponses.
3. Ne fais pas de refactoring non sollicité sur l'autre partie de l'application (ex: ne touche pas au backend si la tâche ne concerne que le frontend Svelte).

## Workflow de travail par agent

### Phase 1 - Mission (Features)
- `@planif` (**MiniMax M3**) : Analyse le besoin FastAPI/Svelte et donne une checklist. Ne modifie AUCUN fichier.
- `@code` (**DeepSeek V4 Flash**) : Code la solution de façon concise et ciblée sur base de la checklist.
- `@fix` (**Qwen 3.7 Plus**) : Corrige les bugs ciblés et retouches UI/UX remontés lors des tests réels.

### Phase 2 - Audit (Sécurité & Stabilité)
- `@audit-check` (**GLM 5.2**) : Inspecte le code backend/frontend pour trouver les failles de sécurité, vulnérabilités et régressions. Génère un rapport avec checklist.
- `@audit-fix` (**DeepSeek V4 Pro**) : Implémente les correctifs de sécurité et résout les failles identifiées dans le rapport d'audit.

# Instructions projet — app-simpy-liga

Mono-dépôt : backend FastAPI dans `/backend`, frontend SvelteKit + Svelte 5
(runes) dans `/frontend`. Voir `frontend/README.md` et `frontend/claude.md`
pour le contexte applicatif.

## Skill `svelte-pro-ui` → application automatique

Applique **automatiquement** le skill `svelte-pro-ui` dès que tu crées,
modifies ou refactores un **composant Svelte** (fichier `.svelte`) dans le
sous-dossier `/frontend`. Le skill décrit la direction artistique, les
animations (svelte/transition, micro-interactions), l’architecture runes et
l’usage de Shadcn-Svelte / Bits UI / lucide-svelte.

Règles de déclenchement :

- Trigger : tout `.svelte` sous `/frontend/src/lib/components/` ou
  `/frontend/src/routes/`, tout nouvel import de `lucide-svelte`, toute
  transition/animation Svelte.
- Portée : uniquement le frontend. Ne pas appliquer au backend Python ni aux
  schémas/données.
- Si le skill n’est pas déjà chargé dans la session, charge-le avant d’écrire le
  composant (son contenu prime sur ces lignes).
- Toujours vérifier `frontend/vite.config.js` et un composant existant
  (`frontend/src/lib/components/ui/Button.svelte`) avant d’introduire un
  nouveau pattern, pour rester cohérent avec le style Svelte 5 runes du projet.

## Conventions générales

- Svelte 5 en mode runes (`$state`, `$derived`, `$effect`, `$props`,
  `$bindable`). Pas de `export let` dans les composants du projet.
- Variables d’environnement : `$env/static/public` côté client,
  `$env/static/private` côté serveur. Jamais de `process.env` côté client.
- Imports projet via l’alias `$lib/`.
- Composants réutilisables : `src/lib/components/ui/` (primitives) ou
  `src/lib/components/features/` (blocs métier).
- Ne pas ajouter de commentaires sauf demande explicite.
- Vérifier le build (`npm run build` depuis `/frontend`) après un changement
  structurel.
