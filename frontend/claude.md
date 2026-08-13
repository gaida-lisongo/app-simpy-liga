# SimpyLIGA — Instructions Frontend (claude.md)
> Fichier lu par OpenCode à chaque session. Toujours s'y référer avant de coder.
> Dernière mise à jour : 13 août 2026

---

## 1. Contexte du projet

SimpyLIGA est un simulateur stochastique (Monte Carlo + LHS) d'une machine
frigorifique à éjecteur au R718 (eau pure), cible Q_evap = 12 kW.

Le backend FastAPI est déployé sur :
  https://simpy-liga.elmes-solution.site

Stack frontend : SvelteKit + Tailwind CSS + shadcn-svelte

---

## 2. RÈGLES ABSOLUES — à ne jamais violer

1. **PAS DE SIDEBAR** — navigation uniquement dans `UserMenuDropdown` (header)
2. **Pages pleine largeur** — pas de `max-w-*` restrictif
3. **Plotly.js UNIQUEMENT** — pas de recharts, pas de chart.js, pas de SVG statique
4. **Upstash Redis** — pas de SQLite, pas de localStorage
5. **Labels UI = français descriptif** — notation technique interdite dans l'UI
6. **Redis avant API** — vérifier le cache avant chaque appel VPS
7. **Mode inverse préservé** — Q_evap = 12 kW toujours imposée côté backend
8. **Gestion d'erreur** explicite sur tous les fetch

---

## 3. Philosophie UI — Labels lisibles

L'application doit être compréhensible par un ingénieur, un décideur ou un
partenaire industriel sans formation en thermodynamique avancée.

### ❌ Ne jamais afficher dans l'UI

```
T_0 (degC)    η_th    G (W/m²)    h_8 = 2675 kJ/kg
N(μ, σ)       COP     s_7 (kJ/kg·K)
```

### ✅ Afficher à la place

```
Température ambiante      Rendement thermique    Rayonnement solaire
Performance solaire globale                      Enthalpie sortie générateur
```

### Table de correspondance UI ↔ Technique

| Label UI affiché | Notation technique | Unité |
|---|---|---|
| Rayonnement solaire direct | G | W/m² |
| Efficacité du concentrateur | η_col | — |
| Température ambiante | T₀ | °C |
| Surface captante | A_col | m² |
| Pertes thermiques | φ_s | % |
| Performance solaire globale | STR | — |
| Rendement thermique | η_th | — |
| Efficacité énergétique (2e loi) | η_ex | — |
| Puissance livrée au générateur | Q_utile | kW |
| Puissance solaire incidente | Q_sol | kW |
| Débit fluide primaire | ṁ_pri | kg/s |
| Rapport d'entraînement | mu (μ) | — |
| Performance du cycle | COP | — |
| Température de génération | T_g | °C |
| Température d'évaporation | T_e | °C |
| Température de condensation | T_c | °C |
| Taux de simulations invalides | taux_rejet | % |

> La notation technique (G, η_th, STR...) reste dans le code, les exports CSV/JSON
> et les tooltips avancés. Jamais dans les labels visibles à l'écran.

---

## 4. Layout — 6 sections par page (style Zenith Dashboard)

Voir `DASHBOARD_LAYOUT.md` pour le schéma visuel complet.
Pas d'onglets. Tout sur une seule page, layout vertical.

```
SECTION 1 — Fil d'ariane (breadcrumb + titre + tags)
SECTION 2 — 4 KPI Cards (métriques clés du circuit)
SECTION 3 — Diagramme thermodynamique (70%) | SECTION 4A Donut MC (30%)
                                              SECTION 4B Histogrammes VA (tabs)
SECTION 5 — Données brutes table + export  | SECTION 6 Panneau simulation
```

### Thème couleurs

- Fond page : `#0f1117`
- Fond cards : `#1a1d27`
- Bordures : `#2d3148` (0.5px)
- Texte primaire : `#f1f5f9`
- Texte secondaire : `#94a3b8`
- Texte muted : `#64748b`

| Circuit | Accent | Hex |
|---|---|---|
| Solaire | Vert lime | `#4ade80` |
| Moteur | Indigo | `#818cf8` |
| Frigorifique | Cyan | `#22d3ee` |
| Couplage | Ambre | `#f59e0b` |

---

## 5. Plotly.js — Configuration obligatoire

### Installation (bundle partiel — évite les 3MB du bundle complet)

```javascript
// src/lib/plotly.js
import Plotly from 'plotly.js/lib/core'
import scatter   from 'plotly.js/lib/scatter'
import bar       from 'plotly.js/lib/bar'
import histogram from 'plotly.js/lib/histogram'
import pie       from 'plotly.js/lib/pie'
Plotly.register([scatter, bar, histogram, pie])
export default Plotly
```

### Thème dark global (à réutiliser sur tous les graphiques)

```javascript
export const darkLayout = {
  paper_bgcolor: 'transparent',
  plot_bgcolor:  '#0f1117',
  font:          { color: '#94a3b8', size: 11, family: 'system-ui' },
  xaxis: { gridcolor: '#1e2435', linecolor: '#2d3148',
           zerolinecolor: '#2d3148', tickfont: { color: '#64748b', size: 9 } },
  yaxis: { gridcolor: '#1e2435', linecolor: '#2d3148',
           zerolinecolor: '#2d3148', tickfont: { color: '#64748b', size: 9 } },
  margin: { t: 16, r: 12, b: 40, l: 48 },
  legend: { bgcolor: '#1a1d27', bordercolor: '#2d3148', borderwidth: 1,
            font: { color: '#94a3b8', size: 9 } }
}
```

### Wrapper Svelte réutilisable

Créer `src/lib/components/ui/PlotlyChart.svelte` :

```svelte
<script>
  import { onMount, onDestroy } from 'svelte'
  export let data = []
  export let layout = {}
  export let config = { responsive: true, displayModeBar: false }
  let container
  let PlotlyInstance

  const merged = { ...darkLayout, ...layout }

  onMount(async () => {
    const mod = await import('$lib/plotly.js')
    PlotlyInstance = mod.default
    PlotlyInstance.newPlot(container, data, merged, config)
  })

  export function update(newData, newLayout = {}) {
    if (PlotlyInstance)
      PlotlyInstance.react(container, newData, { ...merged, ...newLayout }, config)
  }

  onDestroy(() => {
    if (PlotlyInstance && container) PlotlyInstance.purge(container)
  })
</script>
<div bind:this={container} style="width:100%;height:100%;"></div>
```

### Axe logarithmique pour P-H et P-S

```javascript
// R718 opère entre 1.07 kPa (évap) et 84.5 kPa (gen) → 2 décades
// Axe Y logarithmique OBLIGATOIRE sur tous les diagrammes P-H et P-S
yaxis: { type: 'log', title: 'Pression (kPa)' }
```

---

## 6. Upstash Redis — Structure des clés

```javascript
// src/lib/server/redis.js  (déjà créé — ne pas recréer)
// Clés utilisées :
simpy:circuit:{circuit}:latest    // JSON dernière campagne
simpy:circuit:{circuit}:history   // liste campagne_ids (LPUSH)
simpy:campagne:{id}               // JSON complet
simpy:dashboard:summary           // synthèse 4 circuits

// {circuit} ∈ solaire | moteur | frigorifique | couplage
```

### Logique cache-first (à respecter partout)

```javascript
// 1. Charger depuis Redis
const cached = await getLatest(circuit)
if (cached) { hydrate(cached); return }

// 2. Si null → appeler API → stocker Redis → afficher
const data = await runCampaign(circuit, payload)
await saveCampagne(circuit, data)
hydrate(data)
```

---

## 7. API — Endpoints et format de réponse

### Endpoints

```
GET  /api/health
GET  /api/{circuit}/config   → paramètres incertains par défaut
POST /api/{circuit}/run      → lancer campagne Monte Carlo
GET  /api/dashboard          → synthèse 4 circuits
```

`{circuit}` ∈ `moteur | frigorifique | couplage | solaire`

### Payload POST /api/{circuit}/run

Corps optionnel — sans corps = configuration catalogue par défaut.

```json
{
  "circuit": "solaire",
  "simulation": { "N_iterations": 10000, "seed": 42, "echantillonnage": "LHS" }
}
```

### Format de réponse complet (POST /run)

```json
{
  "article": { "id": "A4", "titre": "Circuit Solaire", "circuit": "solaire" },
  "perimetre": { "composants": ["concentrateur", "caloporteur", "apport_generateur"] },
  "simulation": { "N_iterations": 10000, "seed": 42, "echantillonnage": "LHS" },
  "parametres_incertains": [
    { "nom": "G", "symbole": "G", "unite": "W/m2", "loi": "normale",
      "mode": 800, "sigma": 80, "source": "Ghodbane2015" }
  ],
  "resultats": {
    "statistiques": {
      "Q_utile": { "moyenne": 40.97, "ecart_type": 6.27,
                   "mediane": 40.5, "IC95": [28.8, 53.9], "minimum": 15.2, "maximum": 68.1 },
      "eta_th":  { "moyenne": 0.603, "ecart_type": 0.049, "IC95": [0.510, 0.696] },
      "STR":     { "moyenne": 0.628, "ecart_type": 0.051, "IC95": [0.532, 0.725] },
      "m_dot_pri":{ "moyenne": 0.0181,"ecart_type": 0.0028,"IC95": [0.0127, 0.0238] },
      "eta_ex":  { "moyenne": 0.121, "ecart_type": 0.011, "IC95": [0.100, 0.143] }
    },
    "convergence": { "N_stable": 71, "stabilise": true },
    "taux_rejet_non_physique_pct": 0.0,
    "etats_cycle": [
      { "point": "7", "T": 36.0, "P": 0.845, "h": 419.17, "s": 1.307, "x": 0.0 },
      { "point": "8", "T": 95.0, "P": 0.845, "h": 2675.6, "s": 7.354, "x": 1.0 }
    ],
    "bilan_energetique": {
      "Q_evap": 12.0, "Q_gen": 34.2, "Q_cond": 46.2, "W_pompe": 0.18, "COP": 0.35
    },
    "tirages": [
      { "G": 815.4, "eta_col": 0.656, "T_0": 22.98, "A_col": 30.6,
        "Q_utile": 33.8, "eta_th": 0.601, "STR": 0.625 }
    ],
    "profil_tube": {
      "x_m": [0.0, 0.2, 0.4, "..."],
      "T_fluide":    [36.0, 56.0, 76.0, "..."],
      "T_absorbeur": [163.0, 183.0, 203.0, "..."],
      "T_vitre":     [36.0, 56.0, 76.0, "..."],
      "zones":       ["préchauffage", "préchauffage", "vaporisation", "..."]
    },
    "courbes_cpc": {
      "G_range": [400, "...", 1200],
      "eta_th_vs_G": [0.54, "...", 0.54],
      "T_gen_range": [75, "...", 120],
      "STR_vs_Tgen": [0.58, "...", 0.55]
    },
    "sankey_solaire": {
      "labels": ["Rayonnement incident", "Absorbé (optique)", "Pertes optiques",
                 "Pertes thermiques", "Livré au générateur"],
      "values_kW": [68.0, 46.2, 21.8, 6.9, 39.3],
      "source": [0, 1, 1],
      "target": [1, 4, 3]
    }
  },
  "campagne_id": "camp_20260813T115757Z",
  "statut": "ok"
}
```

---

## 8. KPI Cards par circuit

### RÈGLE : les KPI cards affichent des labels lisibles, pas des symboles

| Circuit | KPI 1 | KPI 2 | KPI 3 | KPI 4 |
|---|---|---|---|---|
| **Solaire** | Performance solaire globale (STR) | Rendement thermique (η_th) | Efficacité 2e loi (η_ex) | Puissance générateur (Q_utile) |
| **Moteur** | Performance cycle (COP) | Rapport entraînement (μ) | Débit fluide primaire (ṁ_pri) | Efficacité 2e loi (η_ex) |
| **Frigorifique** | Performance cycle (COP) | Rapport entraînement (μ) | Débit fluide secondaire (ṁ_sec) | Efficacité 2e loi (η_ex) |
| **Couplage** | Performance cycle (COP) | Rapport entraînement (μ) | Chaleur générateur (Q_gen) | Efficacité 2e loi (η_ex) |

### Clés JSON correspondantes (pour lire les stats)

```javascript
// Circuit solaire — clés dans resultats.statistiques
const SOLAR_KPI_KEYS = ['STR', 'eta_th', 'eta_ex', 'Q_utile']

// Circuits classiques
const MOTEUR_KPI_KEYS      = ['COP', 'mu', 'm_dot_pri', 'eta_ex']
const FRIGO_KPI_KEYS       = ['COP', 'mu', 'm_dot_sec', 'eta_ex']  // m_dot_sec pas m_dot_pri
const COUPLAGE_KPI_KEYS    = ['COP', 'mu', 'Q_gen', 'eta_ex']
```

---

## 9. Diagrammes thermodynamiques par circuit

### Circuit Solaire — dropdowns

**Type de diagramme** : `Température-Entropie` | `Pression-Enthalpie` | `Pression-Entropie`

**Composant** :
- `Vue d'ensemble` → T-S cycle complet avec zone générateur surlignée
- `Concentrateur` → η_th=f(G) et STR=f(T_gen) depuis `courbes_cpc`
- `Tube absorbeur` → T_fluide/T_abs/T_vitre=f(x) avec 3 zones colorées depuis `profil_tube`
- `Caloporteur` → T_HTF le long du circuit
- `Générateur (7→8)` → T-S / P-H / P-S transformation 7→8
- `Bilan exergétique` → Sankey depuis `sankey_solaire`

### Graphique tube absorbeur — 3 zones obligatoires

```javascript
// Zones colorées en arrière-plan (shapes Plotly)
shapes: [
  { type: 'rect', x0: 0, x1: L1, fillcolor: '#3b82f610', line: {width:0},
    name: 'Préchauffage' },
  { type: 'rect', x0: L1, x1: L2, fillcolor: '#f59e0b10', line: {width:0},
    name: 'Vaporisation' }
]
// 4 traces : T_fluide (vert) · T_absorbeur (rouge) · T_vitre (gris) · T_amb (pointillé)
```

### Axe P logarithmique (P-H et P-S)

```javascript
// R718 : P_evap ≈ 1.07 kPa, P_gen ≈ 84.5 kPa → 2 décades → log OBLIGATOIRE
yaxis: { type: 'log', title: { text: 'Pression (kPa)' } }
```

---

## 10. Section données brutes — Colonnes par circuit

### Circuit Solaire

| En-tête UI | Clé JSON dans tirages | Couleur |
|---|---|---|
| # | id | muted |
| Rayonnement solaire | G | default |
| Efficacité concentrateur | eta_col | default |
| Température ambiante | T_0 | default |
| Surface captante | A_col | default |
| Puissance au générateur | Q_utile | amber |
| Rendement thermique | eta_th | cyan |
| Performance globale | STR | accent vert, bold |

Export CSV : colonnes avec notation technique `G_W_m2, eta_col, T0_degC, A_col_m2, Q_utile_kW, eta_th, STR`

---

## 11. Section simulation — Labels des paramètres

### Circuit Solaire

| Nom lisible | Clé technique | Description courte |
|---|---|---|
| Rayonnement solaire direct | G | N(μ=800, σ=80) W/m² |
| Efficacité du concentrateur | eta_col | T(0.55 / 0.68 / 0.78) |
| Température ambiante | T_0 | N(μ=25, σ=3) °C |
| Surface captante | A_col | U(70 — 100) m² |
| Pertes thermiques | phi_s | U(5% — 15%) |

**RÈGLE** : dans le panneau simulation, ne jamais afficher la notation
mathématique (N(μ,σ), U(a,b)). Afficher uniquement :
- Le nom lisible
- Un visuel de plage (slider ou range bar)
- La valeur centrale en clair : "Centré sur 800 W/m²"
- La variabilité : "Variation ±80 W/m²"

---

## 12. Règles physiques backend — NE PAS CONTREDIRE

Ces règles viennent du moteur physique. Le frontend ne doit jamais
les contredire dans ses calculs ou ses labels.

```
STR = COP_ejc × η_th    (Ghodbane et al. 2015, ICT3 éq. 14)
PAS Q_utile / Q_gen_cycle — c'est une définition différente et incorrecte.

MODE INVERSE uniquement : Q_evap = 12 kW toujours imposée
m_dot_pri est une SORTIE calculée, jamais une entrée contrôlée

T_SOLEIL = 5777 K (convention Petela 1964) pour η_ex exergétique

Points d'état R718 générateur (nominaux) :
  Point 7 : T=36°C, P=0.845 bar, h=419 kJ/kg, s=1.307 kJ/kg·K, x=0
  Point 8 : T=95°C, P=0.845 bar, h=2676 kJ/kg, s=7.354 kJ/kg·K, x=1
```

---

## 13. Variables d'environnement

```bash
# .env (public — accessible côté client)
PUBLIC_API_URL=https://simpy-liga.elmes-solution.site

# .env (privé — côté serveur uniquement)
UPSTASH_REDIS_REST_URL=...    # récupérer dans elmesacad-marketplace/.env
UPSTASH_REDIS_REST_TOKEN=...  # idem
```

---

## 14. Fichiers existants — ne pas recréer

Ces fichiers ont déjà été créés et sont corrects :
- `src/lib/api.js` — wrapper fetch vers l'API
- `src/lib/server/redis.js` — client Upstash Redis
- `src/lib/constants.js` — métadonnées circuits (KPIs mis à jour)
- `src/lib/stores/simulationStore.svelte.js` — store Svelte global

---

## 15. Priorités de développement

```
1. Vérifier que PlotlyChart.svelte existe — sinon créer
2. Page /solaire — 6 sections complètes avec vraies données API
3. Labels lisibles partout (section 3 de ce fichier)
4. Diagramme tube absorbeur (profil_tube) + 3 zones colorées
5. Sankey solaire (sankey_solaire)
6. Courbes CPC (courbes_cpc)
7. Répliquer le squelette pour /moteur, /frigorifique, /couplage
   (métriques et composants selon section 8 de ce fichier)
```
