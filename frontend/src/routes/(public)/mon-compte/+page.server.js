import { error, fail, redirect } from '@sveltejs/kit';
import { supprimerUser, compterAdminsActifs, detruireSession } from '$lib/server/auth.js';
import { logAuth } from '$lib/server/log.js';

export async function load({ locals }) {
	if (!locals.user) throw redirect(303, '/connexion');
	return { user: locals.user };
}

export const actions = {
	supprimer: async ({ request, locals, cookies }) => {
		if (!locals.user) throw error(401, 'Non authentifié.');

		const fd = await request.formData();
		const confirmation = String(fd.get('confirmation') ?? '').trim();
		if (confirmation !== 'SUPPRIMER')
			return fail(400, { error: 'Tapez SUPPRIMER pour confirmer la suppression.' });

		const email = locals.user.email;

		if (locals.user.role === 'admin') {
			const restants = await compterAdminsActifs();
			if (restants <= 1)
				return fail(400, {
					error:
						'Vous êtes le dernier administrateur actif. Promouvez un autre admin avant de supprimer votre compte.'
				});
		}

		try {
			await supprimerUser(email);
		} catch (/** @type {any} */ e) {
			return fail(500, {
				error: e?.message ?? 'Suppression impossible. Réessayez.'
			});
		}

		logAuth('auto_suppression', { email });
		await detruireSession(cookies);
		throw redirect(303, '/connexion?supprime=1');
	}
};