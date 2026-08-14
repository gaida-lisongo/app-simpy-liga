import { fail, redirect } from '@sveltejs/kit';
import { activerCompte, creerSession, getUserParToken } from '$lib/server/auth.js';

export async function load({ url }) {
	const token = url.searchParams.get('token') ?? '';
	const res = await getUserParToken(token);
	return { token, valide: !!res, user: res?.user ?? null };
}

export const actions = {
	default: async ({ request, cookies }) => {
		const fd = await request.formData();
		const token = String(fd.get('token') ?? '');
		const mdp = String(fd.get('password') ?? '');
		const confirm = String(fd.get('confirm') ?? '');

		if (mdp.length < 8) {
			return fail(400, { error: 'Le mot de passe doit contenir au moins 8 caractères.' });
		}
		if (mdp !== confirm) {
			return fail(400, { error: 'Les deux mots de passe ne correspondent pas.' });
		}

		let user;
		try {
			user = await activerCompte(token, mdp);
		} catch {
			return fail(400, {
				error: 'Lien invalide ou expiré. Demandez un nouveau lien à un administrateur.'
			});
		}

		await creerSession(cookies, user.email);
		redirect(303, '/');
	}
};
