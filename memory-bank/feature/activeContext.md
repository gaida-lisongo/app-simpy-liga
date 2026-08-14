# activeContext.md — Département UI/UX

> Relais entre SUPERMAN et BUILDER.
> SUPERMAN écrit le plan. BUILDER lit et exécute. Écrasé à chaque nouveau plan.

## Plan SUPERMAN — Correction contrat SSE post-persistence Upstash — 2026-08-14

**Objectif** : Adapter `simulationStore.svelte.js` au nouveau contrat SSE où `done` contient un payload léger (`tirages: []`) et un flag `ev.persiste`. Le frontend doit récupérer la campagne complète depuis Redis.

**Sprint** : Sprint 2 — Circuit Solaire (finitions)
**Agent** : BUILDER

---

### Contexte technique

Backend commit `2bc4a93` a introduit la persistance Upstash côté backend. Le contrat SSE a changé :
- **Avant** : `done` → `ev.result` contenait la campagne complète (stats + tirages)
- **Après** : `done` → `ev.result` contient `{ campagne_id, ...métadonnées, tirages: [] }` (léger)
- **Nouveau champ** : `ev.persiste` (boolean) — indique si la campagne a été persistée côté backend

**Problème** : Le store fait `s.result = ev.result` (léger) + `persist(circuit, ev.result)` (4 Mo duplicate). Les composants (McDonutChart, DensityTabs) font `s.result.tirages` → vide → composants disparaissent.

---

### Fichier frontend concerné

- `frontend/src/lib/stores/simulationStore.svelte.js`

---

### Étapes BUILDER

- [x] **1.** Dans le handler `done` (ligne 124), extraire le flag `ev.persiste`
- [x] **2.** Si `ev.persiste === true` : appeler `GET /db/campagne/{id}` pour récupérer la campagne complète depuis Redis, puis assigner à `s.result`
- [x] **3.** Supprimer l'appel `persist(circuit, ev.result)` (plus nécessaire — backend persiste déjà)
- [x] **4.** Si `ev.persiste === false` (fallback,simulation courte ou mode dégradé) : conserver `s.result = ev.result` (comportement inchangé)
- [x] **5.** Vérification : `npm run build` depuis `/frontend`

---

### Règles Svelte 5 à rappeler

- `$state`, `$derived`, `$effect`, `$props`, `$bindable` — jamais `export let`
- Plotly.js uniquement — jamais recharts/chart.js/SVG statique
- Redis avant API — cache Upstash avant chaque appel VPS
- Labels UI = français descriptif — jamais notation technique dans l'UI

---

### Code cible (fragment — lignes 119–137)

```js
source.onmessage = (/** @type {MessageEvent} */ e) => {
    try {
        const ev = JSON.parse(e.data);
        if (ev.type === 'progress') {
            s.progress = ev.pct ?? 0;
        } else if (ev.type === 'done') {
            settled = true;
            s.progress = 100;
            if (ev.persiste) {
                // Backend a persisté en Upstash — va chercher la campagne complète
                const full = await fetch(`/db/campagne/${id}`).then((r) => r.json());
                s.result = full;
                // Plus de persist() ici — backend a déjà persisté
            } else {
                // Fallback : result complet vient directement du SSE
                s.result = ev.result;
            }
            resolve();
        } else if (ev.type === 'error') {
            settled = true;
            reject(new Error(ev.message ?? 'Erreur de simulation.'));
        }
    } catch (err) {
        settled = true;
        reject(/** @type {Error} */ (err));
    }
};
```

**Note** : `id` vient de `ack.campagne_id` (capture à la ligne 106). Il est disponible dans la closure.

---

### Critère d'acceptation

1. Après `done` avec `persiste: true`, `s.result` contient les `tirages` (tableau non vide)
2. McDonutChart et DensityTabs affichent les données (plus de composants vides)
3. L'historique des campagnes se charge correctement (appel à `/db/campagnes` au hydrate)
4. `npm run build` passe sans erreur
5. Aucune régression sur le chemin `ev.persiste === false` (simulation sans persistance)

---

### Pièges connus

- **Ne pas supprimer `resolve()`** dans le bloc `done` — le Promise caller attend la résolution
- **L'appel `fetch` est async** — le `source.onmessage` handler doit être `async` (ajouter le mot-clé)
- **`id` est capturé** dans la closure (ligne 106) — ne pas le redéclarer dans le handler
- **`persist()` n'existe plus après modification** — vérifier qu'aucun autre code ne l'appelle
- **Fallback** : si `fetch('/db/campagne/{id}')` échoue, le bloc catch du caller `run()` gère l'erreur

---

### Observations en passage

- Le endpoint `GET /db/campagne/{id}` existe déjà (appelé par `selectCampaign()` ligne 83) — pas de nouveau endpoint à créer
- La fonction `persist()` devient dead code après cette modification — la laisser en place (elle peut servir à d'autres appels later) mais ne plus l'appeler depuis `run()`
- La fonction `selectCampaign()` continue de fonctionner — même endpoint, même comportement

---

## Reprendre ici

**Après fix** : vérifier que `s.result.tirages` n'est plus vide dans la console et que les graphiques Monte Carlo réapparaissent dans l'UI solaire.
