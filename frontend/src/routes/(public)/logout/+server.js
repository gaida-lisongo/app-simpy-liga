import { redirect } from '@sveltejs/kit';
import { detruireSession } from '$lib/server/auth.js';
import { logAuth } from '$lib/server/log.js';

export async function POST({ cookies, locals }) {
	if (locals.user) logAuth('logout', { email: locals.user.email });
	await detruireSession(cookies);
	redirect(303, '/connexion');
}