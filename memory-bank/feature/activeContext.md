# activeContext.md — Département UI/UX

> Relais entre SUPERMAN et BUILDER.
> SUPERMAN écrit le plan. BUILDER lit et exécute. Écrasé à chaque nouveau plan.

## Plan BUILDER — Correction saveCampagne() écriture clés :meta et :tirages — 2026-08-15

**Objectif** : `saveCampagne()` dans `redis.js` n'écrit que le payload complet + LPUSH/LTRIM. Elle n'écrit PAS les clés `:meta` et `:tirages`. Résultat : `getRecentCampaigns()` ne trouve pas les `:meta` → fallback lent et inefficace.

**Sprint** : Sprint 2 — Circuit Solaire (finitions)
**Agent** : BUILDER

---

### Fichier concerné

- `frontend/src/lib/server/redis.js` — fonction `saveCampagne()`

---

### Étapes BUILDER

- [x] **1.** Lire la fonction `saveCampagne()` actuelle dans `redis.js`
- [x] **2.** Modifier `saveCampagne()` pour écrire les 3 clés : payload complet, `:meta`, `:tirages`
- [x] **3.** Vérification : `npm run build` depuis `/frontend`

---

### Modifications apportées

Dans `saveCampagne()` :
1. **Payload complet** (inchangé) : `redis.set(key, response)` — toujours dans le `Promise.all`
2. **Nouveau** : `redis.set(metaKey, JSON.stringify(meta))` — métadonnées légères (campagne_id, circuit, N_iterations, echantillonnage, COP, STR)
3. **Nouveau** : `redis.set(tiragesKey, JSON.stringify(tirages))` — tirages bruts
4. **Historique** (inchangé) : `redis.lpush(hist, id)` + `redis.ltrim(hist, 0, 19)`

Toutes les écritures sont parallélisées dans un seul `Promise.all`.

---

### Critère d'acceptation

1. `saveCampagne()` écrit les clés `simpy:campagne:{id}:meta` et `simpy:campagne:{id}:tirages`
2. `getRecentCampaigns()` trouve les `:meta` sans fallback
3. `npm run build` passe sans erreur
4. Aucune régression sur `getCampagne()`, `getRecentCampaigns()`, `clearCircuit()`

---

### Pièges évités

- ✅ Le payload complet `redis.set(key, response)` est conservé
- ✅ `getRecentCampaigns()` et `getCampagne()` non modifiés
- ✅ `clearCircuit()` déjà compatible (lignes 174-175 suppriment `:meta` et `:tirages`)

---

### Observations en passage

- `clearCircuit()` (lignes 169-180) supprime déjà les clés `:meta` et `:tirages` — aucune modification nécessaire
- Le format du `meta` correspond exactement à ce que `getRecentCampaigns()` attend dans sa branche `:meta` (lignes 99-108)
