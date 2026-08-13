import { CIRCUITS } from '$lib/constants.js';
import { runCampaign } from '$lib/api.js';

/** @typedef {{ result: any, loading: boolean, error: string, hydrated: boolean }} CircuitState */

/** @type {Record<string, CircuitState>} */
const state = $state(
	Object.fromEntries(CIRCUITS.map((c) => [c.slug, { result: null, loading: false, error: '', hydrated: false }]))
);

let hydratePromise = /** @type {Promise<void> | null} */ (null);

// Hydrate le store depuis la SQLite locale (dernière campagne par circuit) au premier montage.
function hydrate() {
	if (hydratePromise) return hydratePromise;
	hydratePromise = (async () => {
		try {
			const res = await fetch('/db/campagnes');
			if (!res.ok) return;
			const data = await res.json();
			for (const slug of Object.keys(data)) {
				if (state[slug] && data[slug]) state[slug].result = data[slug];
			}
		} catch {
			// Persistance indisponible — on continue sans historique local, non bloquant.
		} finally {
			for (const slug of Object.keys(state)) state[slug].hydrated = true;
		}
	})();
	return hydratePromise;
}

/** @param {string} circuit @param {any} response */
async function persist(circuit, response) {
	try {
		await fetch('/db/campagnes', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ circuit, response })
		});
	} catch {
		// Persistance best-effort : le résultat reste affiché même si l'écriture échoue.
	}
}

/**
 * Lance une campagne pour un circuit et met à jour le store + la persistance locale.
 * @param {string} circuit
 * @param {object} body corps CampagneRequest
 */
async function run(circuit, body) {
	const s = state[circuit];
	s.loading = true;
	s.error = '';
	try {
		const result = await runCampaign(circuit, body);
		s.result = result;
		persist(circuit, result);
		return result;
	} catch (/** @type {any} */ e) {
		s.error = e?.message ?? 'Erreur lors de la campagne.';
		throw e;
	} finally {
		s.loading = false;
	}
}

export const simulationStore = { state, hydrate, run };
