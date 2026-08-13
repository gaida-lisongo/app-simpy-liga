---
name: svelte-pro-ui
description: Guidelines for crafting clean, modern, and richly animated Svelte / SvelteKit / Svelte 5 components and UI. Use when creating, editing, or refactoring any .svelte file in /frontend, building Svelte UI components, wiring Shadcn-Svelte / Bits UI primitives, lucide-svelte icons, svelte/transition animations, or designing Pro Tech / SaaS interfaces (Linear, Vercel, Supabase inspired).
---

# Svelte UI/UX & Motion Design Guidelines

Applique **automatiquement** ces directives dès que tu crées, modifies ou
refactores un composant Svelte (fichier `.svelte`) dans le sous-dossier
`/frontend`. Ne les applique pas au code backend Python ni aux fichiers non-UI.

## 0. Prérequis techniques du projet `/frontend`

- **Svelte 5 en mode runes** (compilé avec `runes: true` dans `vite.config.js`).
  Réactivité : `$state`, `$derived`, `$derived.by`, `$effect`, `$props`,
  `$bindable`. N’utilise **pas** l’ancienne syntaxe `export let` (Svelte 4) pour
  les composants du projet — sauf si le fichier vient de `node_modules`.
- **SvelteKit + adapter-node**, Tailwind via `@tailwindcss/vite`.
- Variables d’env : import depuis `$env/static/public` (client) et
  `$env/static/private` (serveur) — jamais `process.env` côté client.
- Composants réutilisables : `src/lib/components/ui/` et
  `src/lib/components/features/`. Imports projet via l’alias `$lib/`.

## 1. Direction artistique & style (Svelte + Tailwind CSS)

- **Bannis les designs d’IA génériques** : dégradés violets inutiles, cartes
  superposées sans hiérarchie, ombres partout, skeuomorphisme.
- Adopte un design **Pro Tech / SaaS moderne** : inspiré de Vercel, Linear,
  Supabase et Shadcn. Fonds sobres, beaucoup de respiration, hiérarchie claire.
- **Palette** : fonds sobres `bg-background` / `bg-muted`, surfaces discrètes
  (`bg-surface`, `bg-surface-raised`), bordures subtiles (`border` /
  `border-strong`), typographies contrastées. **Une seule** couleur d’accent
  pour les CTA.
- Utilise au maximum les **primitives et composants de Shadcn-Svelte / Bits UI**
  (`Button`, `Badge`, `Tabs`, `Tooltip`, etc.) et les icônes **`lucide-svelte`**.
  Ne réinvente pas un composant UI qui existe déjà dans la lib.
- Respecte les tokens CSS existants du projet (variables `--surface`,
  `--border`, `--text-primary`, `--accent`, `--radius-md`, etc.) plutôt que des
  couleurs en dur. Si une constante visuelle revient, ajoute-la en token.

## 2. Dynamicité & animations Svelte

- **Transitions natives Svelte :** utilise systématiquement `transition:fade`,
  `fly`, `scale` ou `slide` de `svelte/transition` (et `animate:` /
  `flip` pour les listes) pour rendre apparition et disparition fluides. Préfère
  des durées courtes (150–250 ms) et des easings doux.
- **Micro-interactions :** ajoute des retours tactiles/visuels sur chaque bouton
  ou carte — par ex. `hover:scale-[1.01]`, `active:scale-[0.98]`,
  `transition-all duration-200`. Un élément interactif ne doit jamais être
  totalement statique.
- **Loading & empty states :** génère toujours des **skeletons animés**
  (`animate-pulse`) ou des états vides élégants avec une icône `lucide-svelte`
  minimaliste et un court texte explicatif. Rien ne doit « clignoter » ou rester
  vide sans raison.
- **Données asynchrones / progression :** quand une action longue est en cours
  (ex. campagne Monte Carlo), affiche une **barre de progression** ou un
  spinner + libellé (« Simulation en cours… »). Ne laisse jamais l’UI冻结 ;
  découpe le rendu réactif avec `$derived`/`$effect`.

## 3. Architecture du code Svelte

- Place les composants réutilisables dans `src/lib/components/ui/` (primitives)
  ou `src/lib/components/features/` (blocs métier). Un composant = un fichier,
  une responsabilité.
- **Runes Svelte 5** : `$state` pour l’état local, `$derived`/`$derived.by` pour
  le calcul, `$effect` pour les effets de bord (avec cleanup si besoin), `$props`
  avec déstructuration et types JSDoc `@type`. Évite `$effect` pour de simples
  dérivations — `$derived` est plus efficace.
- **Typage :** JSDoc `@type` sur les props et les fonctions publiques (le projet
  est en JS, pas TS). Documente la forme des props complexes.
- **100% Mobile-First et responsive** : grilles Tailwind
  `grid-cols-1 sm:grid-cols-2 xl:grid-cols-4`, breakpoints mobile-first, conteneurs
  fluides. Teste mentalement le rendu à 360px, 768px et 1280px.
- **Accessibilité :** boutons avec `type`, `aria-label` pour les boutons
  icônes, `role="img"` et `aria-label` pour les graphiques, contrastes
  suffisants, navigation clavier possible, `focus:outline-none` uniquement si
  remplacé par un `focus-visible` visible.
- **Pas de commentaires superflus** (règle générale du projet) — sauf si le
  user les demande explicitement. Le code Svelte se documente via des noms
  clairs et des props typées.

## 4. Exemples de patterns à privilégier

**Bouton interactif (Svelte 5 runes + micro-interaction) :**

```svelte
<script>
  import { fly } from 'svelte/transition';
  let { label = 'Action', onclick, disabled = false } = $props();
</script>

<button
  type="button"
  {onclick}
  {disabled}
  class="rounded-md bg-[var(--accent)] px-3 py-1.5 text-sm font-medium text-white
         transition-all duration-200 hover:scale-[1.01] active:scale-[0.98]
         disabled:pointer-events-none disabled:opacity-50"
>
  {label}
</button>
```

**Transition d’apparition d’une carte :**

```svelte
{#if show}
  <div transition:fly={{ y: 8, duration: 200 }} class="..."> ... </div>
{/if}
```

**Skeleton animé :**

```svelte
<div class="h-24 rounded-md bg-surface animate-pulse" aria-hidden="true"></div>
```