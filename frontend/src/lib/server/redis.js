import { Redis } from '@upstash/redis';
import { UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN } from '$env/static/private';
import { CIRCUITS } from '$lib/constants.js';

const redis = new Redis({ url: UPSTASH_REDIS_REST_URL, token: UPSTASH_REDIS_REST_TOKEN });

const HISTORY_LIMIT = 20;
const SUMMARY_TTL_S = 600;

const kLatest = (/** @type {string} */ circuit) => `simpy:circuit:${circuit}:latest`;
const kHistory = (/** @type {string} */ circuit) => `simpy:circuit:${circuit}:history`;
const kCampagne = (/** @type {string} */ id) => `simpy:campagne:${id}`;
const kSummary = 'simpy:dashboard:summary';

/**
 * Persiste une campagne : historique + entrée individuelle. Le "latest" est
 * dérivé de la tête de l'historique (LPUSH toujours en tête), DONC il n'y a
 * plus d'écrasement — la cache accumule toutes les campagnes par circuit.
 * @param {string} circuit @param {any} response
 */
export async function saveCampagne(circuit, response) {
	const id = response.campagne_id ?? `local_${Date.now()}`;
	const key = kCampagne(id);
	const hist = kHistory(circuit);
	const metaKey = `${key}:meta`;
	const tiragesKey = `${key}:tirages`;

	// Métadonnées légères pour getRecentCampaigns (évite de charger 40 Mo)
	const meta = {
		campagne_id: id,
		circuit,
		N_iterations: response.simulation?.N_iterations ?? null,
		echantillonnage: response.simulation?.echantillonnage ?? null,
		COP: response.resultats?.statistiques?.COP?.moyenne ?? null,
		STR: response.resultats?.statistiques?.STR?.moyenne ?? null
	};

	// Tirages bruts pour analyse détaillée
	const tirages = response.resultats?.tirages ?? [];

	await Promise.all([
		redis.set(key, response),                          // payload complet
		redis.set(metaKey, JSON.stringify(meta)),          // métadonnées légères
		redis.set(tiragesKey, JSON.stringify(tirages)),    // tirages bruts
		redis.lpush(hist, id)                              // historique
	]);
	await redis.ltrim(hist, 0, HISTORY_LIMIT - 1);
	return id;
}

/** @param {string} circuit */
export async function getLatest(circuit) {
	const id = await redis.lindex(kHistory(circuit), 0).catch(() => null);
	if (!id) return null;
	return redis.get(kCampagne(id));
}

/** @param {string} id */
export function getCampagne(id) {
	return redis.get(kCampagne(id));
}

/**
 * Consomme (RPOP) les événements en attente de la file d'une campagne (FIFO).
 * producteur = backend LPUSH ; consommateur = ici RPOP. Renvoie un tableau
 * d'événements parsés (vide si rien en attente).
 * @param {string} id @param {number} [limit] nb max d'événements drainés par appel.
 */
export async function popEvents(id, limit = 64) {
	const key = `simpy:campagne:${id}:events`;
	const out = [];
	for (let i = 0; i < limit; i++) {
		const v = await redis.rpop(key);
		if (v === null || v === undefined) break;
		try {
			out.push(typeof v === 'string' ? JSON.parse(v) : v);
		} catch {
			// valeur non-JSON : on l'ignore (file corrompue — ne doit pas arriver)
		}
	}
	return out;
}

/** @param {string} circuit */
export function getHistorique(circuit) {
	return redis.lrange(kHistory(circuit), 0, HISTORY_LIMIT - 1);
}

/**
 * Métadonnées des campagnes récentes d'un circuit (N, date), les plus récentes
 * d'abord. Utilisé par le sélecteur d'historique côté UI.
 * @param {string} circuit @param {number} [limit]
 */
export async function getRecentCampaigns(circuit, limit = 20) {
	const ids = /** @type {string[]} */ (await redis.lrange(kHistory(circuit), 0, limit - 1).catch(() => []));
	if (!ids.length) return [];

	// Lecture des :meta (≈4 Ko au lieu de ≈40 Mo pour 20 campagnes)
	const metaKey = (id) => `simpy:campagne:${id}:meta`;
	const rows = await Promise.all(ids.map((id) => redis.get(metaKey(id))));

	const out = [];
	for (let i = 0; i < rows.length; i++) {
		const r = /** @type {any} */ (rows[i]);
		if (!r) {
			// Fallback rétrocompatibilité : campagne créée avant le déploiement :meta
			const full = await redis.get(kCampagne(ids[i]));
			if (!full) continue;
			out.push({
				id: ids[i],
				campagne_id: full.campagne_id ?? ids[i],
				N_iterations: full.simulation?.N_iterations ?? null,
				echantillonnage: full.simulation?.echantillonnage ?? null,
				COP: full.resultats?.statistiques?.COP?.moyenne ?? null,
				STR: full.resultats?.statistiques?.STR?.moyenne ?? null
			});
			continue;
		}
		// Champs à plat venant de :meta
		out.push({
			id: ids[i],
			campagne_id: r.campagne_id ?? ids[i],
			N_iterations: r.N_iterations ?? null,
			echantillonnage: r.echantillonnage ?? null,
			COP: r.COP ?? null,
			STR: r.STR ?? null
		});
	}
	return out;
}

/**
 * Récupère une campagne par son id (depuis la cache).
 * @param {string} id
 */
export function getCampagneById(id) {
	return redis.get(kCampagne(id));
}

/** Dernière campagne par circuit — pour l'hydratation du store au chargement. */
export async function getLatestAll() {
	const entries = await Promise.all(CIRCUITS.map(async (c) => [c.slug, await getLatest(c.slug)]));
	return Object.fromEntries(entries);
}

/**
 * Synthèse dashboard : cache d'abord, sinon agrégée depuis les derniers résultats
 * par circuit, sinon null (l'appelant doit alors interroger l'API et appeler
 * setDashboardSummary pour amorcer le cache).
 */
export async function getDashboardSummary() {
	const cached = await redis.get(kSummary);
	if (cached) return cached;

	const latest = await getLatestAll();
	const circuits = Object.fromEntries(
		CIRCUITS.map((c) => [
			c.slug,
			latest[c.slug]
				? {
						id: c.id,
						titre: c.titre,
						COP: latest[c.slug].resultats?.statistiques?.COP ?? null,
						eta_ex: latest[c.slug].resultats?.statistiques?.eta_ex ?? null,
						m_dot_pri: latest[c.slug].resultats?.statistiques?.m_dot_pri ?? null,
						taux_rejet_pct: latest[c.slug].resultats?.taux_rejet_non_physique_pct ?? null
					}
				: null
		])
	);

	if (Object.values(circuits).every((c) => c === null)) return null;

	const summary = { statut: 'ok', cible_kW: 12.0, circuits, agrege_depuis_cache: true };
	await setDashboardSummary(summary);
	return summary;
}

/** @param {any} summary */
export function setDashboardSummary(summary) {
	return redis.set(kSummary, summary, { ex: SUMMARY_TTL_S });
}

/**
 * Supprime toutes les données d'un circuit : latest, history, campagnes
 * individuelles + files d'événements. Best-effort (erreurs non bloquantes).
 * @param {string} circuit
 */
export async function clearCircuit(circuit) {
	const ids = await redis.lrange(kHistory(circuit), 0, -1).catch(() => []);
	const keys = [
		kHistory(circuit),
		...ids.map((id) => kCampagne(id)),
		...ids.map((id) => `${kCampagne(id)}:meta`),      // ← NOUVEAU
		...ids.map((id) => `${kCampagne(id)}:tirages`),   // ← NOUVEAU
		...ids.map((id) => `simpy:campagne:${id}:events`)
	];
	if (keys.length) await redis.del(...keys);
	await redis.del(kSummary);
}

/** Supprime les données de tous les circuits + le résumé dashboard. */
export async function clearAll() {
	for (const c of CIRCUITS) {
		await clearCircuit(c.slug);
	}
	await redis.del(kSummary);
}
