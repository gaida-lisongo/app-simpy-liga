import { error } from '@sveltejs/kit';
import { apiFetch } from '$lib/server/api.js';

/**
 * Proxy `/api-proxy/{path}` → `${API_INTERNAL_URL}/api/{path}` avec injection
 * du `X-Internal-Token`. Permet au navigateur d'appeler l'API sans jamais voir
 * le secret partagé.
 *
 * GET/POST/PUT/PATCH/DELETE supportés. Le corps et les headers de contenu
 * sont forwardés tels quels ; les headers de réponse sont recopiés à
 * l'exception de `content-encoding` (géré par SvelteKit) et `set-cookie`
 * (jamais renvoyé ici).
 */
async function handle(/** @type {{ request: Request, params: { path: string } }} */ ctx) {
	const { request, params } = ctx;
	const path = (params.path ?? '').replace(/^\/+/, '');
	if (!path) throw error(400, 'Chemin API manquant.');

	const init = { method: request.method };
	if (request.method !== 'GET' && request.method !== 'HEAD') {
		const ct = request.headers.get('content-type');
		if (ct) init.headers = { 'content-type': ct };
		init.body = await request.text();
	}

	try {
		const upstream = await apiFetch(`/${path}`, init);
		const body = typeof upstream === 'string' ? upstream : JSON.stringify(upstream);
		return new Response(body, {
			status: 200,
			headers: { 'content-type': 'application/json' }
		});
	} catch (/** @type {any} */ e) {
		const msg = e?.message ?? 'Erreur API.';
		const m = msg.match(/^(\d{3})\s+(.*)$/);
		const status = m ? Number(m[1]) : 502;
		return new Response(JSON.stringify({ detail: m ? m[2] : msg }), {
			status,
			headers: { 'content-type': 'application/json' }
		});
	}
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;