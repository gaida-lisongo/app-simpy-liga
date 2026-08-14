/**
 * Rate-limiter partagé (Upstash Redis).
 *
 * Stratégie : compteur à fenêtre fixe via INCR + EXPIRE atomique (best-effort).
 * Adapté à un backend HTTP stateless — pas de mémoire locale à synchroniser
 * entre instances.
 *
 * Retourne `null` si la requête est autorisée, sinon le nombre de secondes
 * restantes avant réinitialisation de la fenêtre.
 */

import { Redis } from '@upstash/redis';
import { UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN } from '$env/static/private';

const redis = new Redis({ url: UPSTASH_REDIS_REST_URL, token: UPSTASH_REDIS_REST_TOKEN });

/**
 * Incrémente le compteur et refuse si > max dans la fenêtre.
 * @param {string} scope namespace fonctionnel (ex: "connexion", "activation")
 * @param {string} identifiant stable (email ou IP)
 * @param {{ max: number, windowS: number }} opts
 * @returns {Promise<{ ok: true } | { ok: false, retryAfterS: number }>}
 */
export async function rateLimit(scope, identifiant, opts) {
	const key = `simpy:rl:${scope}:${identifiant}`;
	try {
		const count = await redis.incr(key);
		if (count === 1) await redis.expire(key, opts.windowS);
		if (count > opts.max) {
			const ttl = await redis.ttl(key).catch(() => opts.windowS);
			return { ok: false, retryAfterS: Math.max(1, ttl) };
		}
		return { ok: true };
	} catch {
		return { ok: true };
	}
}