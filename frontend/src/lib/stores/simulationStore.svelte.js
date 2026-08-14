import { CIRCUITS } from '$lib/constants.js';
import { startRun } from '$lib/api.js';

/** @typedef {{ result: any, loading: boolean, error: string, progress: number, hydrated: boolean, campaigns: any[] }} CircuitState */

/** @type {Record<string, CircuitState>} */
const state = $state(
	Object.fromEntries(
		CIRCUITS.map((c) => [c.slug, { result: null, loading: false, error: '', progress: 0, hydrated: false, campaigns: [] }])
	)
);

let hydratePromise = /** @type {Promise<void> | null} */ (null);

// Hydrate le store depuis le cache Redis (dernière campagne par circuit + historique)
// au premier montage. La cache accumule toutes les campagnes sans écraser.
function hydrate() {
	if (hydratePromise) return hydratePromise;
	hydratePromise = (async () => {
		try {
			// 1. Latest par circuit
			const latestAll = await fetch('/db/campagnes').then((r) => r.json());
			if (latestAll) {
				for (const slug of Object.keys(latestAll)) {
					if (state[slug] && latestAll[slug]) state[slug].result = latestAll[slug];
				}
			}
			// 2. Historique (métadonnées) par circuit
			const lists = await Promise.all(
				Object.keys(state).map(async (slug) => {
					const r = await fetch(`/db/campagnes?circuit=${slug}`);
					if (!r.ok) return [slug, []];
					const arr = await r.json();
					return [slug, Array.isArray(arr) ? arr : []];
				})
			);
			for (const [slug, arr] of lists) {
				if (state[slug]) state[slug].campaigns = arr;
			}
		} catch {
			// Persistance indisponible — non bloquant.
		} finally {
			for (const slug of Object.keys(state)) state[slug].hydrated = true;
		}
	})();
	return hydratePromise;
}

/** @param {string} circuit @param {any} response */
async function persist(circuit, response) {
	try {
		const ack = await fetch('/db/campagnes', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ circuit, response })
		}).then((r) => r.json()).catch(() => null);
		// Prépend la métadonnée de la nouvelle campagne dans l'historique local.
		if (ack?.id) {
			const s = state[circuit];
			const meta = {
				id: ack.id,
				campagne_id: response.campagne_id ?? ack.id,
				N_iterations: response.simulation?.N_iterations ?? null,
				echantillonnage: response.simulation?.echantillonnage ?? null,
				COP: response.resultats?.statistiques?.COP?.moyenne ?? null,
				STR: response.resultats?.statistiques?.STR?.moyenne ?? null
			};
			s.campaigns = [meta, ...s.campaigns].slice(0, 20);
		}
	} catch {
		// best-effort
	}
}

/**
 * Récupère une campagne passée par id et l'affiche dans l'état du circuit.
 * @param {string} circuit @param {string} id
 */
async function selectCampaign(circuit, id) {
	const s = state[circuit];
	if (!s) return;
	try {
		const r = await fetch(`/db/campagne/${id}`);
		if (!r.ok) throw new Error(`Campagne ${id} introuvable`);
		s.result = await r.json();
	} catch (/** @type {any} */ e) {
		s.error = e?.message ?? 'Erreur lors du chargement de la campagne.';
	}
}

/**
 * Lance une campagne asynchrone pour un circuit et écoute la file Redis via SSE.
 * Le résultat final est persisté dans le cache Redis (kLatest dérivé de l'historique —
 * accumulate, n'écrase pas) et prepended à l'historique local.
 * @param {string} circuit
 * @param {object} body corps CampagneRequest
 */
async function run(circuit, body) {
	const s = state[circuit];
	s.loading = true;
	s.error = '';
	s.progress = 0;
	let es = /** @type {EventSource | null} */ (null);
	try {
		const ack = await startRun(circuit, body);
		const id = ack?.campagne_id;
		if (!id) throw new Error("Réponse d'ack invalide (campagne_id manquant).");

		await /** @type {Promise<void>} */ (new Promise((resolve, reject) => {
			let settled = false;
			let retries = 0;
			const MAX_RETRIES = 5;

			const connect = () => {
				const source = (es = new EventSource(`/db/campagne/${id}/events`));
				source.onopen = () => {
					retries = 0;
				};
				source.onmessage = (/** @type {MessageEvent} */ e) => {
					try {
						const ev = JSON.parse(e.data);
						if (ev.type === 'progress') {
							s.progress = ev.pct ?? 0;
						} else if (ev.type === 'done') {
							settled = true;
							s.result = ev.result;
							s.progress = 100;
							persist(circuit, ev.result);
							resolve();
						} else if (ev.type === 'error') {
							settled = true;
							reject(new Error(ev.message ?? 'Erreur de simulation.'));
						}
					} catch (err) {
						settled = true;
						reject(/** @type {Error} */ (err));
					}
				};
				source.onerror = () => {
					if (settled) return;
					// readyState CONNECTING : EventSource retente nativement — on laisse faire.
					if (source.readyState === EventSource.CONNECTING) return;
					// readyState CLOSED : le navigateur a abandonné, on retente nous-mêmes
					// (avec le même id — le backend reprend la file Redis là où elle en est).
					source.close();
					retries += 1;
					if (retries > MAX_RETRIES) {
						settled = true;
						reject(new Error('Connexion au flux interrompue (délai de reconnexion dépassé).'));
						return;
					}
					setTimeout(connect, Math.min(1000 * retries, 5000));
				};
			};
			connect();
		}));
	} catch (/** @type {any} */ e) {
		s.error = e?.message ?? 'Erreur lors de la campagne.';
	} finally {
		if (es) es.close();
		s.loading = false;
	}
}

export const simulationStore = { state, hydrate, run, selectCampaign };