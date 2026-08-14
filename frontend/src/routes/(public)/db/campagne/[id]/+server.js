import { json } from '@sveltejs/kit';
import { getCampagneById } from '$lib/server/redis.js';

// GET /db/campagne/[id] — retourne une campagne complète par id (depuis le cache).
/** @param {{ params: { id: string } }} */
export async function GET({ params }) {
	const r = await getCampagneById(params.id);
	if (!r) return json({ error: 'Campagne introuvable dans le cache' }, { status: 404 });
	return json(r);
}