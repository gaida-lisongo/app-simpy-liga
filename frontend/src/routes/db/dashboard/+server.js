import { json } from '@sveltejs/kit';
import { getDashboardSummary, setDashboardSummary } from '$lib/server/redis.js';

// GET /db/dashboard — synthèse en cache (agrégée depuis les derniers résultats par
// circuit si le cache "summary" est vide). Renvoie null si rien n'est encore en cache
// (aucune campagne n'a jamais tourné) — l'appelant doit alors interroger l'API.
export async function GET() {
	return json(await getDashboardSummary());
}

// POST /db/dashboard — amorce le cache avec la synthèse renvoyée par l'API
// (appelé par le client après un cache-miss GET /api/dashboard).
export async function POST({ request }) {
	const summary = await request.json();
	await setDashboardSummary(summary);
	return json({ ok: true });
}
