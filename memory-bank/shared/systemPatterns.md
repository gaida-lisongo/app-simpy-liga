# systemPatterns.md — SimpyLIGA

> Invariants physiques et architecture. Lu par EINSTEIN et PATCHER à chaque session.
> Mis à jour uniquement si l'architecture change fondamentalement.

---

## Invariants physiques — violation = bug silencieux publié

| Constante | Valeur | Piège à éviter |
|---|---|---|
| `h_7` | `cr.states[7].h` ≈ 146.740 kJ/kg | ❌ PropsSI(Q=0, P_gen) = 398.09 → bug A1 |
| `h_8` | `cr.states[8].h` ≈ 2667.614 kJ/kg | — |
| `Δh_gen` | **2520.874 kJ/kg ± 0.5** | ❌ 2269.52 = chaleur latente seule → bug A1 rechuté |
| `T_soleil` | 5777 K | Petela 1964 — constante physique |
| `Q_evap` | **12 kW imposée** | Jamais incertaine, jamais sortie |
| `T_gen nominal` | 95 °C = 368.15 K | Saturation R718 à 84.61 kPa |
| `COP_ejc` | issu de `cr.metrics["COP"]` | ❌ Jamais 0.35 en dur — fallback = None |

## Formules canoniques

```python
Q_utile    = G · A_col · η_col · (1 − φ_s) / 1000    # kW
η_th       = η_col · (1 − φ_s)
STR        = COP_ejc × η_th          # Ghodbane 2015 éq.14 — DÉFINITION UNIQUE
m_dot_pri  = m.get("m_dot_p")        # débit RÉEL du solveur — TOUS circuits, y compris solaire (A4-2)
η_ex       = η_th · (1−T₀/T_gen) / (1−T₀/T_soleil)
Q_gen_requis = 12.0 / COP_ejc        # jamais 12/0.35
IC95       = np.percentile(arr, [2.5, 97.5])  # jamais μ ± 1.96σ
```

**Circuit solaire uniquement (A4-2, 2026-08-15)** — `m_dot_pri` vient du
solveur comme les 3 autres circuits (JAMAIS `Q_utile/Δh`). La capacité de
dimensionnement du champ solaire est exportée séparément :

```python
m_dot_pri_potentiel = Q_utile / Δh_gen   # Δh_gen = h_8 − h_7 — capacité champ solaire, PAS le débit cycle
Q_surplus            = Q_utile − Q_gen
taux_couverture      = Q_utile / Q_gen
```

## Architecture stricte

```
app-simpy-liga/
├── backend/app/
│   ├── adapters/physics_adapter.py   ← SEUL pont physique — ne jamais dupliquer
│   ├── engine/
│   │   ├── monte_carlo.py            ← boucle LHS, stats, Sobol
│   │   ├── distributions.py          ← ppf(u) → valeurs
│   │   ├── sensitivity.py            ← Sobol, SRC, Spearman
│   │   ├── fiabilite.py              ← P(Q < Q_cible), A_col_min
│   │   └── pool.py                   ← workers multi-process
│   ├── core/
│   │   ├── catalogue.py              ← 31 paramètres incertains
│   │   └── upstash.py                ← cache Redis
│   └── schemas/reporting.py          ← contrat Pydantic
├── frontend/src/
│   ├── routes/(public)/              ← pages accessibles après login
│   ├── routes/(auth)/                ← connexion + activation
│   └── routes/(admin)/               ← gestion utilisateurs
└── app-machine-r718/                 ← INTOUCHÉ — cœur physique séparé
```

## Lois d'architecture

1. Mode inverse uniquement — `Q_evap = 12 kW` (ou cible utilisateur Sprint 5+)
2. Un seul pont physique — `physics_adapter.py`
3. Ne jamais modifier `app-machine-r718`
4. `STR = COP_ejc × η_th` — ne pas redéfinir
5. `h_7` toujours depuis `cr.states[7].h`
6. `cop_ref` dans `compute_courbes_cpc` = `None` si cycle invalide (jamais `0.35`)
7. Upstash Redis côté frontend — jamais SQLite / localStorage
8. Plotly.js uniquement — jamais recharts / chart.js / SVG statique

## Valeurs de référence campagne camp_20260813T161420Z (N=10 000, seed=42)

| Sortie | μ | σ | IC95 percentiles |
|---|---|---|---|
| Q_utile | 41.006 kW | 6.7015 | [29.167 ; 54.956] |
| η_th | 0.60300 | 0.046668 | [0.5133 ; 0.6927] |
| STR | 0.62824 | 0.048621 | [0.5347 ; 0.7217] |
| m_dot_pri | 0.018068 kg/s | 0.0029528 | [0.01285 ; 0.02422] |
| η_ex | 0.120898 | 0.010743 | [0.1006 ; 0.1426] |

> Après correction A1 complète : m_dot_pri attendu ≈ 0.01627 kg/s (−11.07 %)

> ⚠️ **Campagne antérieure à A4-2 (2026-08-15)** : la ligne `m_dot_pri`
> ci-dessus a été mesurée AVANT la correction A4-2 et correspond en réalité
> à ce qui s'appelle désormais `m_dot_pri_potentiel` (capacité du champ
> solaire). Depuis A4-2, `m_dot_pri` pour le circuit solaire est le débit
> RÉEL du solveur : contrôle N=200 seed=42 → μ ≈ 0.00486 kg/s, σ ≈ 0.00087
> (voir `memory-bank/science/activeContext.md`, section « Plan A4-2 »).
> Q_utile/η_th/η_ex restent inchangés (formules solaires non touchées).
