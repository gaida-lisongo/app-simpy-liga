# activeContext.md — Département Sécurité

> Relais entre SHEERLOCK et SENTINEL.
> Mis à jour : 2026-08-14

## Statut

Aucune mission d'audit lancée. InternalAuthMiddleware en place depuis Sprint 3.

## Prochain audit recommandé

Avant Sprint 5 (Isolation multi-machine) — vérifier :
- Isolation des données entre utilisateurs dans Redis
- Validation des entrées de configuration machine (Q_evap_cible, températures)
- Exposition de stack traces en production
