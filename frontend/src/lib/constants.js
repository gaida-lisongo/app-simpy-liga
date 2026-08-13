// Métadonnées statiques des 4 circuits (miroir de backend/app/core/catalogue.py)
// Utilisées pour la navigation, les libellés et les tooltips du frontend.

export const CIRCUITS = [
	{
		slug: 'moteur',
		id: 'A1',
		titre: 'Circuit Moteur',
		sousTitre: 'Branche chaude',
		etats: '1 → 7 → 8 → 4',
		composants: ['Pompe', 'Générateur', 'Tuyère primaire'],
		icon: 'pump',
		accent: '#06c167',
		kpis: ['COP', 'mu', 'm_dot_pri', 'eta_ex'],
		segments: [
			{ label: 'Pompe', from: '1', to: '7' },
			{ label: 'Générateur', from: '7', to: '8' },
			{ label: 'Tuyère primaire', from: '8', to: '4' }
		]
	},
	{
		slug: 'frigorifique',
		id: 'A2',
		titre: 'Circuit Frigorifique',
		sousTitre: 'Branche froide',
		etats: '1 → 2 → 3 → 4',
		composants: ['Détendeur', 'Évaporateur (12 kW)', 'Aspiration secondaire'],
		icon: 'snowflake',
		accent: '#06c167',
		kpis: ['COP', 'mu', 'm_dot_sec', 'eta_ex'],
		segments: [
			{ label: 'Détendeur', from: '1', to: '2' },
			{ label: 'Évaporateur (12 kW)', from: '2', to: '3' },
			{ label: 'Aspiration secondaire', from: '3', to: '4' }
		]
	},
	{
		slug: 'couplage',
		id: 'A3',
		titre: 'Circuit de Couplage',
		sousTitre: 'Éjecteur & condenseur',
		etats: '4 → 5 → 6 → 1',
		composants: ['Chambre de mélange', 'Diffuseur', 'Condenseur'],
		icon: 'merge',
		accent: '#06c167',
		kpis: ['COP', 'mu', 'Q_gen', 'eta_ex'],
		segments: [
			{ label: 'Chambre de mélange', from: '3', to: '4' },
			{ label: 'Diffuseur', from: '4', to: '5' },
			{ label: 'Condenseur', from: '5', to: '6' }
		]
	},
	{
		slug: 'solaire',
		id: 'A4',
		titre: 'Circuit Solaire',
		sousTitre: 'Source chaude externe',
		etats: 'Externe',
		composants: ['Concentrateur cylindro-parabolique', 'Caloporteur', "Apport au générateur"],
		icon: 'sun',
		accent: '#06c167',
		kpis: ['COP', 'mu', 'Q_gen', 'eta_ex'],
		segments: []
	}
];

/**
 * Circuit -> nom de route API (le slug frontend correspond au circuit API).
 * @param {{slug: string}} circuit
 */
export function apiCircuitOf(circuit) {
	return circuit.slug;
}

/** @param {string} slug */
export function circuitBySlug(slug) {
	const found = CIRCUITS.find((c) => c.slug === slug);
	if (!found) throw new Error(`Circuit inconnu : ${slug}`);
	return found;
}

// Description + tooltip par paramètre incertain (nom = clé backend ParametreIncertain.nom)
/** @type {Record<string, {label: string, tooltip: string}>} */
export const PARAM_INFO = {
	T_g: {
		label: 'Température de génération',
		tooltip:
			"Température de la source chaude au générateur — pilote le débit primaire admis à l'éjecteur."
	},
	eta_is_p: {
		label: 'Rendement isentropique pompe',
		tooltip: "Rendement isentropique de la pompe d'alimentation en circuit moteur."
	},
	eta_m_p: {
		label: 'Rendement mécanique pompe',
		tooltip: 'Rendement mécanique de la pompe (pertes mécaniques/électriques).'
	},
	phi_g: {
		label: 'Pertes thermiques générateur',
		tooltip: 'Pertes thermiques au générateur, en % de la puissance apportée.'
	},
	x_g: {
		label: 'Titre vapeur générateur',
		tooltip: 'Titre vapeur en sortie de générateur (proche de 1 = vapeur quasi saturée sèche).'
	},
	T_e: {
		label: "Température d'évaporation",
		tooltip: 'Température au niveau de l’évaporateur — fixe le niveau de froid produit.'
	},
	Q_e: {
		label: 'Charge frigorifique cible',
		tooltip:
			'Puissance frigorifique imposée (12 kW) — cible fixe du dimensionnement inverse ; m_dot_pri est calculé pour l’atteindre.'
	},
	dT_pp_e: {
		label: 'Pincement évaporateur',
		tooltip: "Écart de température minimal (pincement) à l'évaporateur."
	},
	dT_sh: {
		label: 'Surchauffe aspiration secondaire',
		tooltip: "Surchauffe à l'aspiration secondaire de l'éjecteur."
	},
	eta_n: {
		label: 'Rendement tuyère primaire',
		tooltip: "Rendement de la tuyère primaire de l'éjecteur (détente supersonique)."
	},
	eta_m: {
		label: 'Rendement chambre de mélange',
		tooltip: "Rendement de la chambre de mélange de l'éjecteur (chocs normaux)."
	},
	eta_d: {
		label: 'Rendement diffuseur',
		tooltip: "Rendement du diffuseur de l'éjecteur (recompression subsonique)."
	},
	T_c: {
		label: 'Température de condensation',
		tooltip: 'Température de saturation au condenseur.'
	},
	dT_pp_c: {
		label: 'Pincement condenseur',
		tooltip: 'Écart de température minimal (pincement) au condenseur.'
	},
	phi_sections: {
		label: 'Rapport des sections',
		tooltip: "Rapport des sections primaire/secondaire de l'éjecteur (aire de mélange)."
	},
	G: {
		label: 'Irradiance solaire',
		tooltip: 'Irradiance solaire incidente sur le concentrateur cylindro-parabolique.'
	},
	eta_col: {
		label: 'Rendement optique concentrateur',
		tooltip: 'Rendement optique du concentrateur cylindro-parabolique.'
	},
	T_0: {
		label: 'Température ambiante',
		tooltip: 'Température ambiante de référence pour les pertes du caloporteur.'
	},
	A_col: {
		label: 'Surface de captation',
		tooltip: 'Surface de captation du champ de concentrateurs solaires.'
	}
};

/** @type {Record<string, string>} */
export const LOI_LABELS = {
	uniforme: 'Uniforme U(min, max)',
	normale: 'Normale N(μ, σ)',
	triangulaire: 'Triangulaire T(min, mode, max)',
	fixe: 'Fixe'
};

/** @type {Record<string, {label: string, tooltip: string}>} */
export const SORTIE_LABELS = {
	COP: { label: 'COP', tooltip: 'Coefficient de performance global du cycle.' },
	mu: { label: 'μ (taux entraînement)', tooltip: "Taux d'entraînement de l'éjecteur (m_dot_sec / m_dot_pri)." },
	m_dot_pri: {
		label: 'ṁ_p (débit primaire)',
		tooltip:
			'Débit primaire — grandeur distribuée phare : calculé par le solveur pour garantir Q_evap = 12 kW malgré l’incertitude.'
	},
	m_dot_sec: { label: 'ṁ_s (débit secondaire)', tooltip: "Débit secondaire aspiré à l'évaporateur." },
	Q_gen: { label: 'Q_gen (puissance générateur)', tooltip: 'Puissance thermique apportée au générateur.' },
	eta_ex: { label: 'η_ex (rendement exergétique)', tooltip: 'Rendement exergétique global du cycle.' }
};
