/**
 * Wrapper serveur vers le backend FastAPI.
 *
 * Injecte le secret partagé `X-Internal-Token` à chaque requête pour que le
 * middleware `InternalAuthMiddleware` du backend accepte l'appel. Utilisé
 * exclusivement depuis les routes `+server.js` / `+page.server.js` côté SvelteKit.
 */

import { API_INTERNAL_URL, INTERNAL_API_TOKEN } from '$env/static/private';

/** @param {string} path */
function url(path) {
	const base = API_INTERNAL_URL.replace(/\/$/, '');
	const p = path.startsWith('/') ? path : `/${path}`;
	return `${base}${p}`;
}

/**
 * @param {string} path
 * @param {RequestInit & { json?: any }} [init]
 */
export async function apiFetch(path, init = {}) {
	const { json: body, headers, ...rest } = init;
	const finalHeaders = new Headers(headers);
	finalHeaders.set('x-internal-token', INTERNAL_API_TOKEN);
	if (body !== undefined) finalHeaders.set('content-type', 'application/json');

	const res = await fetch(url(`/api${path}`), {
		...rest,
		headers: finalHeaders,
		body: body !== undefined ? JSON.stringify(body) : undefined,
		cache: 'no-store'
	});

	if (!res.ok) {
		let detail = res.statusText;
		try {
			const b = await res.json();
			detail = b.detail ?? detail;
		} catch {
			// pas de JSON
		}
		throw new Error(`${res.status} ${detail}`);
	}

	const ct = res.headers.get('content-type') ?? '';
	return ct.includes('application/json') ? res.json() : res.text();
}