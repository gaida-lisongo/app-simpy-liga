# activeContext.md — Département Science

> Relais entre EINSTEIN et PATCHER.
> Mis à jour : 2026-08-14

## Contexte actif

Corrections A1–A7 majoritairement appliquées dans le code.
**Restant à vérifier par PATCHER** :

- [ ] A7 — Export CSV : vérifier que toutes les colonnes JSON sont dans le CSV
  - Fichier : `backend/app/engine/monte_carlo.py` section `tirages_bruts`
  - Test : `test_csv_miroir_du_json`
- [ ] M1 — Sobol analytique : vérifier que `sensitivity.py` exporte S_i et S_Ti
  - Test : `pytest backend/tests/test_sensitivity.py -v`
- [ ] Vérification numérique : lancer campagne N=200 seed=42 solaire et confirmer
  `m_dot_pri` ≈ 0.01627 kg/s (pas 0.018)

## Commande de vérification rapide

```bash
python3 -c "
from backend.app.adapters.physics_adapter import run_cycle
r = run_cycle({'G':800,'eta_col':0.68,'A_col':85,'phi_s':0.10})
dh = r['Q_utile']/r['m_dot_pri']
print(f'Δh_gen = {dh:.3f} kJ/kg (attendu 2520.874 ± 0.5)')
assert abs(dh - 2520.874) < 0.5, f'BUG A1: {dh}'
print('OK')
"
```
