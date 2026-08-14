import { json } from '@sveltejs/kit';
import { saveCampagne, getLatestAll, clearCircuit, clearAll, getRecentCampaigns } from '$lib/server/redis.js';
import { CIRCUITS } from '$lib/constants.js';

const VALID_SLUGS = new Set(CIRCUITS.map((c) => c.slug));

// GET /db/campagnes                       — dernière campagne par circuit (hydratation)
// GET /db/campagnes?circuit=solaire       — historique (métadonnées) d'un circuit
export async function GET({ url }) {
	const circuit = url.searchParams.get('circuit');
	if (circuit) {
		if (!VALID_SLUGS.has(circuit)) {
			return json({ error: `circuit inconnu: ${circuit}` }, { status: 400 });
		}
		return json(await getRecentCampaigns(circuit, 20));
	}
	return json(await getLatestAll());
}

// POST /db/campagnes — persiste une campagne { circuit, response }. Accumule (n'écrase pas).
export async function POST({ request }) {
	const { circuit, response } = await request.json();
	if (!circuit || !response) {
		return json({ error: 'circuit et response requis' }, { status: 400 });
	}
	const id = await saveCampagne(circuit, response);
	return json({ ok: true, id });
}

// DELETE /db/campagnes?circuit=solaire — supprime l'historique d'un circuit.
// DELETE /db/campagnes (sans circuit)   — supprime tous les circuits.
export async function DELETE({ url }) {
	const circuit = url.searchParams.get('circuit');

	if (circuit === 'all' || !circuit) {
		await clearAll();
		return json({ ok: true, cleared: 'all' });
	}

	if (!VALID_SLUGS.has(circuit)) {
		return json({ error: `circuit inconnu: ${circuit}` }, { status: 400 });
	}

	await clearCircuit(circuit);
	return json({ ok: true, cleared: circuit });
}