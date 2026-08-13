import { json } from '@sveltejs/kit';
import { saveCampagne, getLatestAll } from '$lib/server/redis.js';

// GET /db/campagnes — dernière campagne persistée par circuit (hydratation du store au chargement).
export async function GET() {
	return json(await getLatestAll());
}

// POST /db/campagnes — persiste le résultat d'une campagne { circuit, response }.
export async function POST({ request }) {
	const { circuit, response } = await request.json();
	if (!circuit || !response) {
		return json({ error: 'circuit et response requis' }, { status: 400 });
	}
	const id = await saveCampagne(circuit, response);
	return json({ ok: true, id });
}
