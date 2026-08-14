/**
 * Logger minimal pour événements d'authentification.
 *
 * Pousse chaque événement dans une liste Redis plafonnée (`simpy:auth:log`,
 * 500 dernières entrées). Accessible pour audit / debug — jamais dans les
 * chemins critiques (best-effort, n'échoue jamais).
 */

import { Redis } from '@upstash/redis';
import { UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN } from '$env/static/private';

const redis = new Redis({ url: UPSTASH_REDIS_REST_URL, token: UPSTASH_REDIS_REST_TOKEN });

const KEY = 'simpy:auth:log';
const LIMIT = 500;

/**
 * @typedef {'login_ok' | 'login_echec' | 'compte_cree' | 'compte_active'
 *   | 'compte_supprime' | 'auto_suppression' | 'token_demande'
 *   | 'rate_limit'} AuthEvent
 */

/** @param {AuthEvent} type @param {Record<string, any>} [details] */
export function logAuth(type, details) {
	const entry = {
		ts: new Date().toISOString(),
		type,
		...(details ?? {})
	};
	redis
		.lpush(KEY, JSON.stringify(entry))
		.then(() => redis.ltrim(KEY, 0, LIMIT - 1))
		.catch(() => {
			// best-effort
		});
}