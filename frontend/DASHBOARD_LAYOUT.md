# SimpyLIGA — Dashboard Layout Specification (Global Template)
> Ce fichier est la référence de design partagée par toutes les pages circuits.
> Chaque page = même squelette, données différentes.

---

## Architecture visuelle globale

Inspirée du dashboard Zenith (DashboardPack) — thème sombre, palette achromatique,
un seul accent couleur par circuit, pas de sidebar.

```
┌──────────────────────────────────────────────────────────────────────┐
│  HEADER : Logo | Nav circuits (pills) | API status | UserMenuDropdown│
├──────────────────────────────────────────────────────────────────────┤
│  SECTION 1 — FIL D'ARIANE                                            │
│  SimPy-LIGA / Circuit {Nom} — {Article}                              │
│  Titre H1 | Description | Tags (article, date, méthode)             │
├────────────┬────────────┬────────────┬───────────────────────────────┤
│  SECTION 2 — 4 KPI CARDS (métriques clés du circuit)                 │
│  KPI 1     │  KPI 2     │  KPI 3     │  KPI 4                        │
│  val+delta │  val+delta │  val+delta │  val+delta                    │
│  sparkline │  sparkline │  sparkline │  sparkline                    │
│  IC95      │  IC95      │  IC95      │  IC95 / statut                │
├────────────────────────────────────────┬─────────────────────────────┤
│  SECTION 3 — DIAGRAMME THERMODYNAMIQUE │  SECTION 4A — MC DONUT      │
│  (≈ 70% largeur)                       │  Distribution globale        │
│                                        │  résultats simulation        │
│  Dropdown : type [P-s | T-s | T-P]    ├─────────────────────────────┤
│  Dropdown : composant du circuit       │  SECTION 4B — HISTOGRAMMES   │
│                                        │  VA (tabs : une par param)   │
│  [graphique thermodynamique pleine     │  G | η_col | T₀ | ...        │
│   hauteur avec points d'état étiquetés│  Histo + loi de référence    │
│   et courbe de saturation]             │                              │
├────────────────────────────────────────┼─────────────────────────────┤
│  SECTION 5 — DONNÉES BRUTES            │  SECTION 6 — SIMULATION      │
│  Table exportable (CSV / JSON)         │  Paramètres d'entrée         │
│  Colonnes : params + sorties           │  (éditables par param)       │
│  Pagination 10 000 lignes             │  N_iter | Méthode | Seed     │
│  Badge : compatible R · Jupyter        │  [▶ Lancer la simulation]    │
└────────────────────────────────────────┴─────────────────────────────┘
```

---

## Sections détaillées

### SECTION 1 — Fil d'ariane
- Breadcrumb : `SimPy-LIGA / Circuit {Nom} — {Article}`
- H1 : nom du circuit
- Sous-titre : description physique du circuit
- Tags : article ID · N itérations · méthode · date

### SECTION 2 — 4 KPI Cards
Chaque card contient :
- Label + icône thématique
- Valeur principale (grande, bold)
- Delta / interprétation (couleur accent)
- Sparkline SVG (tendance sur la campagne)
- IC95 en sous-texte

> **Les 4 métriques sont définies par circuit** (voir specs par page).
> Elles peuvent être déterministes, stochastiques ou résultats phares.

### SECTION 3 — Diagramme thermodynamique
- Dropdown 1 : type de diagramme → `[P-s | T-s | T-P]`
- Dropdown 2 : composant → liste propre à chaque circuit
- Graphique : SVG ou Canvas (points d'état numérotés + courbe saturation R718)
- Légende couleur sous le graphique

> **Les composants du dropdown sont définis par circuit.**

### SECTION 4A — Distribution Monte Carlo (donut)
- Donut recharts : distribution de la variable de sortie principale
- Centre : N itérations
- Légende : μ+σ / μ±σ / μ-σ avec pourcentages
- Sous-texte : N_stable, taux rejet

### SECTION 4B — Histogrammes des variables aléatoires (tabs)
- Une tab par paramètre incertain du circuit
- Histogramme barres vertes + label loi sous le graphique
- Tabs : paramètre actif en vert, autres en gris

### SECTION 5 — Données brutes
- Table avec colonnes : paramètres d'entrée + sorties clés
- Pagination (10 000 lignes côté serveur)
- Boutons export : CSV · JSON
- Badge : "Compatible R · Jupyter · Excel"

> **Les colonnes sont définies par circuit.**

### SECTION 6 — Panneau simulation
- Liste des paramètres incertains : symbole · description · loi · unité
- Chaque paramètre a un bouton ✎ pour éditer les bornes
- Controls : N_iterations · Méthode [LHS|MC] · Seed
- Bouton ▶ Lancer → POST /api/{circuit}/run
- Barre de progression + statut

---

## Palette couleurs par circuit

| Circuit  | Accent    | Hex       | Usage                  |
|----------|-----------|-----------|------------------------|
| Solaire  | Vert lime | #4ade80   | KPIs, sparklines, run  |
| Moteur   | Indigo    | #818cf8   | KPIs, sparklines, run  |
| Frigori. | Cyan      | #22d3ee   | KPIs, sparklines, run  |
| Couplage | Ambre     | #f59e0b   | KPIs, sparklines, run  |

---

## Stack technique

- **Frontend** : SvelteKit + Tailwind CSS + shadcn-svelte
- **Cache / BDD** : Upstash Redis (remplace SQLite)
- **Charts** : recharts (histos, donut, sparklines) + SVG natif (T-s, P-h)
- **API** : FastAPI déployée sur VPS → https://simpy-liga.elmes-solution.site
- **Variables d'env** : récupérer depuis `elmesacad-marketplace/.env` ou `.env.local`

---

## Structure Redis (Upstash)

```
simpy:circuit:{circuit}:latest        → JSON résultats dernière campagne
simpy:circuit:{circuit}:history       → liste triée des campagne_ids
simpy:campagne:{id}                   → JSON complet (params + résultats)
simpy:dashboard:summary               → synthèse des 4 circuits
```

`{circuit}` ∈ `solaire | moteur | frigorifique | couplage`

### Opérations Redis par action

| Action              | Redis op                                      |
|---------------------|-----------------------------------------------|
| Run simulation      | SET latest + LPUSH history + SET campagne:{id}|
| Load page           | GET latest → si null → appel API             |
| Dashboard global    | GET summary → si null → agréger les 4 latest  |
| Export données      | GET campagne:{id} → stream CSV                |

---

## Endpoints API

```
GET  /api/health
GET  /api/{circuit}/config   → paramètres incertains par défaut
POST /api/{circuit}/run      → lancer campagne Monte Carlo
GET  /api/dashboard          → synthèse 4 circuits
```

### Payload POST /api/{circuit}/run

```json
{
  "N_iterations": 10000,
  "seed": 42,
  "methode": "LHS",
  "parametres": {
    "G": { "loi": "normale", "mu": 800, "sigma": 80 }
  }
}
```

---

## Règles absolues

1. PAS DE SIDEBAR — navigation uniquement dans UserMenuDropdown (header)
2. Pages pleine largeur — pas de max-w restrictif
3. Thème sombre — `#0f1117` fond, `#1a1d27` cards, `#2d3148` bordures
4. Un seul accent couleur par circuit (voir tableau ci-dessus)
5. Toujours mode inverse — Q_evap = 12 kW imposée
6. Redis avant API — toujours vérifier le cache avant d'appeler le VPS
7. Gestion d'erreur explicite sur tous les fetch
8. Export CSV/JSON toujours disponible en section 5
