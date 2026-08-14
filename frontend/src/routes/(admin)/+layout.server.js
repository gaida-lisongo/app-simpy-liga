import { error, redirect } from '@sveltejs/kit';

export async function load({ locals }) {
	if (!locals.user) throw redirect(303, '/connexion');
	if (locals.user.role !== 'admin') throw error(403, 'Accès réservé aux administrateurs.');
	return {};
}
