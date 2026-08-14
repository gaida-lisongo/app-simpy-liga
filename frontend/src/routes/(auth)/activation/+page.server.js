import { fail, redirect } from '@sveltejs/kit';
import { activerCompte, creerSession, getUserParToken } from '$lib/server/auth.js';
import { rateLimit } from '$lib/server/ratelimit.js';
import { logAuth } from '$lib/server/log.js';

export async function load({ url }) {
	const token = url.searchParams.get('token') ?? '';
	const res = await getUserParToken(token);
	return { token, valide: !!res, user: res?.user ?? null };
}

export const actions = {
	default: async ({ request, cookies, getClientAddress }) => {
		const fd = await request.formData();
		const token = String(fd.get('token') ?? '');
		const mdp = String(fd.get('password') ?? '');
		const confirm = String(fd.get('confirm') ?? '');

		const ip = getClientAddress?.() ?? 'unknown';
		const rl = await rateLimit('activation', ip, { max: 5, windowS: 15 * 60 });
		if (!rl.ok) {
			logAuth('rate_limit', { scope: 'activation', ip });
			return fail(429, {
				error: `Trop de tentatives. Réessayez dans ${Math.ceil(rl.retryAfterS / 60)} min.`
			});
		}

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
		throw redirect(303, '/');
	}
};