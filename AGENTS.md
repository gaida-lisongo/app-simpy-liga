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