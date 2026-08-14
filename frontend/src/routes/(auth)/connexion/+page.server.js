import { fail, redirect } from '@sveltejs/kit';
import { verifierLogin, creerSession } from '$lib/server/auth.js';
import { rateLimit } from '$lib/server/ratelimit.js';
import { logAuth } from '$lib/server/log.js';

export async function load({ locals }) {
	if (locals.user) throw redirect(303, '/');
	return {};
}

export const actions = {
	default: async ({ request, cookies, getClientAddress }) => {
		const fd = await request.formData();
		const email = String(fd.get('email') ?? '').trim().toLowerCase();
		const mdp = String(fd.get('password') ?? '');

		const ip = getClientAddress?.() ?? 'unknown';
		const rl = await rateLimit('connexion', `${ip}|${email}`, { max: 5, windowS: 15 * 60 });
		if (!rl.ok) {
			logAuth('rate_limit', { scope: 'connexion', ip, email });
			return fail(429, {
				error: `Trop de tentatives. Réessayez dans ${Math.ceil(rl.retryAfterS / 60)} min.`,
				email
			});
		}

		const res = await verifierLogin(email, mdp);
		if (res.erreur === 'compte_non_active') {
			return fail(400, {
				error: "Votre compte n'est pas encore activé. Utilisez le lien reçu par email.",
				email
			});
		}
		if (res.erreur || !res.user) {
			logAuth('login_echec', { email, ip });
			return fail(400, { error: 'Email ou mot de passe incorrect.', email });
		}

		await creerSession(cookies, res.user.email);
		logAuth('login_ok', { email, ip });
		throw redirect(303, '/');
	}
};