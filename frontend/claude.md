# SimpyLIGA — Frontend Instructions (claude.md)

## 1. Contexte du projet
Application web frontend pour SimpyLIGA, simulateur stochastique d'une machine
frigorifique à eau R718 (12 kW). Le backend FastAPI est déployé sur :
https://simpy-liga.elmes-solution.site

Stack frontend : SvelteKit + Tailwind CSS + shadcn-svelte

---

## 2. Navigation — RÈGLE ABSOLUE
- PAS DE SIDEBAR. Jamais.
- Le menu de navigation principal se trouve UNIQUEMENT dans le composant
  `UserMenuDropdown` (dropdown dans le header).
- Les pages occupent 100% de la largeur disponible (pas de max-w-* restrictif
  sauf contexte lecture).
- Structure du header : Logo à gauche | Titre centré | UserMenuDropdown à droite.

### Entrées du menu (UserMenuDropdown)
- Dashboard (/)
- Circuit Moteur (/moteur)
- Circuit Frigorifique (/frigorifique)
- Circuit Couplage (/couplage)
- Circuit Solaire (/solaire)

---

## 3. Pages — Structure commune obligatoire
Chaque page circuit (Moteur, Frigorifique, Couplage, Solaire) est divisée en
3 onglets/sections dans cet ordre :

### Section 1 — SIMULATION
Rôle : lancer la campagne Monte Carlo via l'API et afficher l'avancement.

Composants requis :
- `SimulationPanel.svelte` — formulaire de paramétrage
  - Champ : N_iterations (défaut 10 000)
  - Champ : seed (défaut 42)
  - Sélecteur : méthode d'échantillonnage (LHS | Monte Carlo pur)
  - Bouton "Lancer la simulation" → POST /api/{circuit}/run
  - Indicateur de progression (spinner + message)
  - Gestion d'erreur explicite si l'API ne répond pas
- `ParametresPanel.svelte` — affiche les paramètres incertains du circuit
  (GET /api/{circuit}/config) avec leurs lois et bornes, modifiables avant run.

### Section 2 — STATISTIQUES
Rôle : visualiser les distributions et indicateurs statistiques des résultats.

Composants requis :
- `StatCard.svelte` — carte pour chaque variable de sortie
  (COP, mu, eta_ex, m_dot_p, m_dot_s) affichant :
  moyenne | écart-type | IC95 bas | IC95 haut
- `HistogrammeChart.svelte` — histogramme de distribution pour chaque variable
  (utiliser Chart.js ou recharts selon dispo)
- `ConvergenceChart.svelte` — courbe de convergence N_stable
- `TableauResultats.svelte` — tableau récapitulatif exportable (CSV)
- Badge `taux_rejet_non_physique_pct` affiché en rouge si > 5%

### Section 3 — THERMODYNAMIQUE
Rôle : afficher les états thermodynamiques du cycle et le bilan exergétique.

Composants requis :
- `EtatsCycleTable.svelte` — tableau des points d'état (T, P, h, s, x)
  pour chaque point du circuit concerné
- `DiagrammePh.svelte` — diagramme P-h du cycle (axes logarithmiques)
- `DiagrammeTs.svelte` — diagramme T-s du cycle (courbe de saturation +
  points d'état reliés dans l'ordre du cycle, même logique de tracé que
  `DiagrammePh.svelte`)
- `BilanEnergetique.svelte` — bilan Q_evap, Q_cond, W_pompe, COP
- `BilanExergetique.svelte` — destructions d'exergie par composant
  (barres horizontales triées du plus irréversible au moins)
- `FlagsPanel.svelte` — affichage des flags de cohérence physique
  (vert = OK, rouge = anomalie) retournés par l'API

---

## 4. Connexion API — RÈGLE CRITIQUE

### Endpoint principal à corriger en priorité
POST /api/{circuit}/run

```javascript
// Appel correct
const response = await fetch(`${API_BASE_URL}/api/${circuit}/run`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    N_iterations: 10000,
    seed: 42,
    methode: 'LHS'
  })
});
```

`{circuit}` ∈ `moteur | frigorifique | couplage | solaire`

### Tous les endpoints disponibles
- GET  /api/health
- GET  /api/{circuit}/config  → paramètres incertains par défaut
- POST /api/{circuit}/run     → campagne Monte Carlo (résultat JSON complet)
- GET  /api/dashboard         → synthèse 4 circuits

### Variable d'environnement
```
PUBLIC_API_URL=https://simpy-liga.elmes-solution.site
```
Toujours lire l'URL depuis cette variable, jamais en dur.

### Format de réponse attendu (POST /run)
```json
{
  "article": {"id": "A1", "titre": "...", "circuit": "moteur"},
  "simulation": {"N_iterations": 10000, "seed": 42, "echantillonnage": "LHS"},
  "resultats": {
    "statistiques": {
      "COP":       {"moyenne": 1.039, "ecart_type": 0.064, "IC95": [0.914, 1.154]},
      "mu":        {"moyenne": 1.106, "ecart_type": 0.072, "IC95": [0.966, 1.237]},
      "m_dot_pri": {"moyenne": 0.00460, "IC95": [0.00409, 0.00524]}
    },
    "convergence": {"N_stable": 573, "stabilise": true},
    "taux_rejet_non_physique_pct": 0.0
  }
}
```

---

## 5. Base de données SQLite (locale)
Autorisation : OUI — une petite base SQLite est acceptée.

Rôle : persister les résultats des campagnes pour éviter de relancer l'API
à chaque visite.

Tables minimales :
- `campagnes` : id, circuit, timestamp, N_iterations, seed, methode
- `resultats` : id, campagne_id, variable, moyenne, ecart_type, ic95_bas, ic95_haut
- `etats_cycle` : id, campagne_id, point, T, P, h, s, x

Utiliser `better-sqlite3` ou Drizzle ORM avec adaptateur SQLite.

---

## 6. Correspondance circuits / articles
| Page       | Circuit     | Article | Points d'état |
|------------|-------------|---------|---------------|
| /moteur    | moteur      | A1      | 1→7→8→4       |
| /frigorifique | frigorifique | A2   | 1→2→3→4       |
| /couplage  | couplage    | A3      | 4→5→6→1       |
| /solaire   | solaire     | A4      | externe       |

---

## 7. Règles de développement
1. Composants atomiques — chaque composant a une seule responsabilité
2. Pas de logique API dans les composants UI — utiliser des stores Svelte
3. Gestion d'erreur systématique sur tous les appels fetch
4. Les résultats de simulation sont stockés dans un store global `simulationStore`
5. Le store est hydraté depuis SQLite au chargement, puis mis à jour après chaque run
6. Aucun résultat ne doit être perdu entre les sessions

---

## 8. Priorités de développement (dans l'ordre)
1. Corriger la connexion POST /api/{circuit}/run sur les 4 pages
2. Créer SimulationPanel.svelte fonctionnel pour chaque circuit
3. Créer StatCard.svelte + TableauResultats.svelte
4. Implémenter SQLite pour la persistance
5. Créer les composants Thermodynamique
6. Créer les visualisations (histogrammes, diagramme P-h, diagramme T-s)
7. Finaliser UserMenuDropdown et layout pleine largeur
