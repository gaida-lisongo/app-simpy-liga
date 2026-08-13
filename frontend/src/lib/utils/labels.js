export const SOLAIRE_KPI_LABELS = {
	STR: {
		label: 'Performance solaire globale',
		unite: '',
		tooltip: 'Solar Thermal Ratio — STR = COP × η_th (Ghodbane 2015, ICT3 éq. 14).',
		litterature: 'Références : 0.10 – 0.30 (Ghodbane 2015)'
	},
	eta_th: {
		label: 'Rendement thermique du concentrateur',
		unite: '',
		tooltip: 'Rendement thermique instantané du CPC = Q_utile / Q_sol.',
		litterature: 'Idéal théorique : 92.2 % (Al-akayshee 2026)'
	},
	eta_ex: {
		label: 'Efficacité énergétique (2e loi)',
		unite: '',
		tooltip: 'Rendement exergétique du sous-système solaire (Petela 1964).',
		litterature: 'Références : 35–38 % (Abu-Hamdeh 2020)'
	},
	Q_utile: {
		label: 'Puissance livrée au générateur',
		unite: 'kW',
		tooltip: 'Puissance thermique utile après pertes optiques et thermiques.',
		litterature: 'Besoin minimal : 34 kW pour produire 12 kW de froid'
	}
};

export const PARAM_LABELS = {
	G: { label: 'Rayonnement solaire direct', unite: 'W/m²', plage: '640 — 960' },
	eta_col: { label: 'Efficacité du concentrateur', unite: '', plage: '0.55 — 0.78' },
	T_0: { label: 'Température ambiante', unite: '°C', plage: '22 — 28' },
	A_col: { label: 'Surface captante', unite: 'm²', plage: '70 — 100' },
	phi_s: { label: 'Pertes thermiques', unite: '', plage: '5% — 15%' }
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