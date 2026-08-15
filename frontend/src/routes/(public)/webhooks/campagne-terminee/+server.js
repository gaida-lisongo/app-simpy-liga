import { json } from '@sveltejs/kit';
import { INTERNAL_API_TOKEN } from '$env/static/private';
import { sendMail, mailCampagneTermineeHtml } from '$lib/server/mail.js';

/**
 * POST /webhooks/campagne-terminee — appelé par le backend Python (runner.py,
 * jamais par un navigateur) à la fin d'une campagne, pour déclencher l'email
 * de notification. Authentifié par le même secret partagé que le proxy
 * /api-proxy (X-Internal-Token), pas par un cookie de session — c'est un
 * appel serveur-à-serveur.
 */
export async function POST({ request }) {
	const sent = request.headers.get('x-internal-token') ?? '';
	if (!INTERNAL_API_TOKEN || sent !== INTERNAL_API_TOKEN) {
		return json({ error: 'Jeton interne manquant ou invalide.' }, { status: 401 });
	}

	const body = await request.json().catch(() => null);
	const email = body?.email ? String(body.email).trim() : '';
	if (!email) return json({ error: 'email requis' }, { status: 400 });

	const nom = body?.nom ?? '';
	const circuit = body?.circuit ?? '';
	const campagneId = body?.campagne_id ?? '';
	const lien = `${new URL(request.url).origin}/${circuit}`;

	try {
		await sendMail({
			to: email,
			subject: 'Votre campagne de simulation est terminée',
			html: mailCampagneTermineeHtml({ nom, circuit, campagneId, lien })
		});
	} catch (/** @type {any} */ e) {
		console.error('webhook campagne-terminee — envoi du mail échoué', { email, campagneId, error: e?.message });
		return json({ ok: false, error: 'Envoi du mail échoué.' }, { status: 502 });
	}

	return json({ ok: true });
}
