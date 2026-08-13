import { CIRCUITS } from '$lib/constants.js';
import { startRun } from '$lib/api.js';

/** @typedef {{ result: any, loading: boolean, error: string, progress: number, hydrated: boolean }} CircuitState */

/** @type {Record<string, CircuitState>} */
const state = $state(
	Object.fromEntries(
		CIRCUITS.map((c) => [c.slug, { result: null, loading: false, error: '', progress: 0, hydrated: false }])
	)
);

let hydratePromise = /** @type {Promise<void> | null} */ (null);

// Hydrate le store depuis le cache Redis (dernière campagne par circuit) au premier montage.
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
 * Lance une campagne asynchrone pour un circuit et écoute la file Redis via SSE.
 * - POST /api/{circuit}/run → ack {campagne_id, channel}
 * - EventSource /db/campagne/{id}/events → progression puis done/error
 * Le résultat final est persisté dans le cache Redis (kLatest/kHistory) pour
 * l'hydratation au prochain chargement et pour le dashboard.
 * @param {string} circuit
 * @param {object} body corps CampagneRequest
 */
async function run(circuit, body) {
	const s = state[circuit];
	s.loading = true;
	s.error = '';
	s.progress = 0;
	let es = null;
	try {
		const ack = await startRun(circuit, body);
		const id = ack?.campagne_id;
		if (!id) throw new Error("Réponse d'ack invalide (campagne_id manquant).");

		await new Promise((resolve, reject) => {
			es = new EventSource(`/db/campagne/${id}/events`);
			es.onmessage = (/** @type {MessageEvent} */ e) => {
				try {
					const ev = JSON.parse(e.data);
					if (ev.type === 'progress') {
						s.progress = ev.pct ?? 0;
					} else if (ev.type === 'done') {
						s.result = ev.result;
						s.progress = 100;
						persist(circuit, ev.result);
						resolve();
					} else if (ev.type === 'error') {
						reject(new Error(ev.message ?? 'Erreur de simulation.'));
					}
				} catch (err) {
					reject(/** @type {Error} */ (err));
				}
			};
			es.onerror = () => reject(new Error('Connexion au flux interrompue.'));
		});
	} catch (/** @type {any} */ e) {
		s.error = e?.message ?? 'Erreur lors de la campagne.';
	} finally {
		if (es) es.close();
		s.loading = false;
	}
}

export const simulationStore = { state, hydrate, run };