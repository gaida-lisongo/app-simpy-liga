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
 * Persiste une campagne : latest + historique + entrée individuelle.
 * @param {string} circuit @param {any} response
 */
export async function saveCampagne(circuit, response) {
	const id = response.campagne_id ?? `local_${Date.now()}`;
	await Promise.all([
		redis.set(kLatest(circuit), response),
		redis.set(kCampagne(id), response),
		redis.lpush(kHistory(circuit), id)
	]);
	await redis.ltrim(kHistory(circuit), 0, HISTORY_LIMIT - 1);
	return id;
}

/** @param {string} circuit */
export function getLatest(circuit) {
	return redis.get(kLatest(circuit));
}

/** @param {string} id */
export function getCampagne(id) {
	return redis.get(kCampagne(id));
}

/** @param {string} circuit */
export function getHistorique(circuit) {
	return redis.lrange(kHistory(circuit), 0, HISTORY_LIMIT - 1);
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
