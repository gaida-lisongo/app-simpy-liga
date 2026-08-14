import { fail } from '@sveltejs/kit';
import { listerUsers, declarerUser, creerTokenActivation } from '$lib/server/auth.js';
import { sendMail, mailActivationHtml } from '$lib/server/mail.js';

export async function load() {
	return { users: await listerUsers() };
}

/** @param {string} origin @param {string} token */
const lienActivation = (origin, token) => `${origin}/activation?token=${token}`;

export const actions = {
	creer: async ({ request, url }) => {
		const fd = await request.formData();
		const email = String(fd.get('email') ?? '').trim().toLowerCase();
		const nom = String(fd.get('nom') ?? '').trim();
		const role = String(fd.get('role') ?? 'chercheur');
		const envoyer = fd.get('envoyer') === 'on';

		if (!nom) return fail(400, { section: 'creer', error: 'Le nom est requis.' });
		if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email))
			return fail(400, { section: 'creer', error: 'Adresse email invalide.' });

		try {
			await declarerUser({ email, nom, role });
		} catch (e) {
			if (String(/** @type {Error} */ (e)?.message).includes('email_existant'))
				return fail(400, { section: 'creer', error: 'Un compte existe déjà pour cet email.' });
			return fail(500, { section: 'creer', error: 'Création impossible. Réessayez.' });
		}

		const token = await creerTokenActivation(email);
		const lien = lienActivation(url.origin, token);

		if (envoyer) {
			try {
				await sendMail({
					to: email,
					subject: 'Activez votre compte SimpyLIGA',
					html: mailActivationHtml({ nom, lien })
				});
				return { ok: true, section: 'creer', email, mailEnvoye: true };
			} catch {
				return { ok: true, section: 'creer', email, lien, mailErreur: true };
			}
		}
		return { ok: true, section: 'creer', email, lien };
	},

	renvoyer: async ({ request, url }) => {
		const fd = await request.formData();
		const email = String(fd.get('email') ?? '').trim().toLowerCase();
		const nom = String(fd.get('nom') ?? '');
		const reinitialisation = fd.get('reinitialisation') === '1';

		const token = await creerTokenActivation(email);
		const lien = lienActivation(url.origin, token);

		try {
			await sendMail({
				to: email,
				subject: reinitialisation
					? 'Réinitialisez votre mot de passe SimpyLIGA'
					: 'Activez votre compte SimpyLIGA',
				html: mailActivationHtml({ nom, lien, reinitialisation })
			});
			return { ok: true, section: 'renvoyer', email, mailEnvoye: true };
		} catch {
			return { ok: true, section: 'renvoyer', email, lien, mailErreur: true };
		}
	}
};
