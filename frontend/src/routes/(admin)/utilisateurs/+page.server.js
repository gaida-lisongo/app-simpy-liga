import { fail } from '@sveltejs/kit';
import {
	listerUsers,
	declarerUser,
	creerTokenActivation,
	supprimerUser,
	compterAdminsActifs,
	getUser
} from '$lib/server/auth.js';
import { sendMail, mailActivationHtml } from '$lib/server/mail.js';
import { logAuth } from '$lib/server/log.js';

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

		if (!nom || nom.length < 2) return fail(400, { section: 'creer', error: 'Le nom est requis (2 caractères minimum).' });
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
	},

	supprimer: async ({ request, locals }) => {
		const fd = await request.formData();
		const email = String(fd.get('email') ?? '').trim().toLowerCase();
		const confirmation = String(fd.get('confirmation') ?? '').trim();

		if (confirmation !== 'SUPPRIMER')
			return fail(400, { section: 'supprimer', error: 'Tapez SUPPRIMER pour confirmer.' });

		if (!email) return fail(400, { section: 'supprimer', error: 'Email manquant.' });
		if (locals.user?.email === email)
			return fail(400, {
				section: 'supprimer',
				error: 'Vous ne pouvez pas supprimer votre propre compte depuis cette interface.'
			});

		try {
			const cible = await getUser(email);
			if (cible?.role === 'admin') {
				const restants = await compterAdminsActifs();
				if (restants <= 1)
					return fail(400, {
						section: 'supprimer',
						error: 'Impossible de supprimer le dernier administrateur actif.'
					});
			}
			await supprimerUser(email);
			logAuth('compte_supprime', { email, par: locals.user?.email });
			return { ok: true, section: 'supprimer', email };
		} catch (e) {
			if (String(/** @type {Error} */ (e)?.message).includes('utilisateur_introuvable'))
				return fail(404, { section: 'supprimer', error: 'Utilisateur introuvable.' });
			return fail(500, { section: 'supprimer', error: 'Suppression impossible. Réessayez.' });
		}
	}
};