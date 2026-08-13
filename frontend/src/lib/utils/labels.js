export const SOLAIRE_KPI_LABELS = {
	COP: {
		label: 'Performance globale du cycle',
		unite: '',
		tooltip: "Coefficient de performance global du cycle éjecteur R718.",
		litterature: 'Références : COP éjecteur R718 ~ 0.8–1.2'
	},
	mu: {
		label: "Taux d'entraînement éjecteur",
		unite: '',
		tooltip: "Rapport des débits secondaire/primaire aspirés par l'éjecteur.",
		litterature: 'Rapport ṁ_secondaire / ṁ_primaire'
	},
	Q_gen: {
		label: 'Puissance thermique au générateur',
		unite: 'kW',
		tooltip: 'Puissance thermique apportée au générateur pour vaporiser le fluide.',
		litterature: 'Besoin minimal : vaporiser le fluide'
	},
	eta_ex: {
		label: 'Efficacité énergétique (2e loi)',
		unite: '',
		tooltip: 'Rendement exergétique global du cycle, rapport à Carnot tri-therme.',
		litterature: 'Références : 35–38 % (Abu-Hamdeh 2020)'
	}
};

export const PARAM_LABELS = {
	G: { label: 'Rayonnement solaire direct', unite: 'W/m²', plage: '640 — 960' },
	eta_col: { label: 'Efficacité du concentrateur', unite: '', plage: '0.55 — 0.78' },
	T_0: { label: 'Température ambiante', unite: '°C', plage: '19 — 31' },
	A_col: { label: 'Surface captante', unite: 'm²', plage: '20 — 60' }
};

/** @param {number | null | undefined} v @param {number} [d] */
export function fmtVal(v, d = 3) {
	return v === undefined || v === null ? '—' : Number(v).toFixed(d);
}

/** @param {[number, number] | undefined | null} ic */
export function fmtIC95(ic) {
	if (!ic || ic.length < 2) return '—';
	return `Fourchette 95 % : [${fmtVal(ic[0], 3)} ; ${fmtVal(ic[1], 3)}]`;
}

/** @param {{ text: string, tone?: 'good'|'warning'|'neutral' }} interp */
export function fmtDelta(interp) {
	return interp.text;
}