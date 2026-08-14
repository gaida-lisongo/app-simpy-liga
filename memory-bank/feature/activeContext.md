# activeContext.md — Département UI/UX

> Relais entre SUPERMAN et BUILDER.
> SUPERMAN écrit le plan. BUILDER lit et exécute. Écrasé à chaque nouveau plan.

## Contexte actif — Sprint 2 finitions

**Dernière action** : Anomalie A2 backend (cop_ref=None) corrigée.
**Prochaine tâche UI** : Gérer `STR_vs_Tgen = [None, ...]` côté frontend dans `SolaireCourbesCPC.svelte`.

## Reprendre ici

`SolaireCourbesCPC.svelte` : quand `STR_vs_Tgen` contient des valeurs `null`,
afficher un message "COP non disponible" à la place du graphe STR=f(T_gen),
plutôt que de crasher ou d'afficher une courbe plate à zéro.

## Observations en passant

_(aucune pour l'instant)_
