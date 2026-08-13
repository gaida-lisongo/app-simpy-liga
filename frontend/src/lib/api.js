import { PUBLIC_API_URL } from '$env/static/public';

// Toujours dérivé de PUBLIC_API_URL — jamais d'URL en dur.
const BASE = `${PUBLIC_API_URL}/api`;

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
		throw new Error(`API injoignable (${BASE}) — vérifiez la connexion réseau.`);
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
export function runCampaign(circuit, body) {
	return request(`/${circuit}/run`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
}
