import { fail, redirect } from '@sveltejs/kit';
import { verifierLogin, creerSession } from '$lib/server/auth.js';

export async function load({ locals }) {
	if (locals.user) redirect(303, '/');
	return {};
}

export const actions = {
	default: async ({ request, cookies }) => {
		const fd = await request.formData();
		const email = String(fd.get('email') ?? '').trim().toLowerCase();
		const mdp = String(fd.get('password') ?? '');

		const res = await verifierLogin(email, mdp);
		if (res.erreur === 'compte_non_active') {
			return fail(400, {
				error: "Votre compte n'est pas encore activé. Utilisez le lien reçu par email.",
				email
			});
		}
		if (res.erreur || !res.user) {
			return fail(400, { error: 'Email ou mot de passe incorrect.', email });
		}

		await creerSession(cookies, res.user.email);
		redirect(303, '/');
	}
};
