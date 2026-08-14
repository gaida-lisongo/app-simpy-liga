import { redirect } from '@sveltejs/kit';
import { detruireSession } from '$lib/server/auth.js';

export async function POST({ cookies }) {
	await detruireSession(cookies);
	redirect(303, '/connexion');
}
