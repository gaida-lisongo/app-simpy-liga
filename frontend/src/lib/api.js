/**
 * Façade fetch vers le backend.
 *
 * Toutes les requêtes passent par `/api-proxy/{path}` — une route SvelteKit
 * qui injecte le `X-Internal-Token` côté serveur. Le navigateur ne voit jamais
 * le secret partagé ni l'URL interne du backend FastAPI.
 */

const BASE = '/api-proxy';

/** @param {Response} res */
async function unwrap(res) {
	if (!res.ok) {
		let detail = res.statusText;
		try {
			const body = await res.json();
			detail = body.detail ?? detail;
		} catch {
			// pas de corps JSON
		}
		throw new Error(`${res.status} ${detail}`);
	}
	return res.json();
}

/** @param {string} path @param {RequestInit} [init] */
async function request(path, init) {
	let res;
	try {
		res = await fetch(`${BASE}${path}`, init);
	} catch {
		throw new Error('API injoignable — vérifiez la connexion réseau.');
	}
	return unwrap(res);
}

export function getHealth() {
	return request('/health');
}

export function getDashboard() {
	return request('/dashboard');
}

/** @param {string} circuit */
export function getCircuitConfig(circuit) {
	return request(`/${circuit}/config`);
}

/**
 * @param {string} circuit
 * @param {object} body corps CampagneRequest (voir schemas/reporting.py)
 */
export function startRun(circuit, body) {
	return request(`/${circuit}/run`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
}