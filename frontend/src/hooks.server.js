import { redirect } from '@sveltejs/kit';
import { getSessionUser } from '$lib/server/auth.js';

const PUBLIC_PATHS = ['/connexion', '/activation', '/logout'];

export async function handle({ event, resolve }) {
	const { pathname } = event.url;

	if (pathname.includes('.')) return resolve(event);

	event.locals.user = await getSessionUser(event.cookies).catch(() => null);

	const isPublic = PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));

	// /db/* expose les résultats de simulation (campagnes, dashboard, flux SSE)
	// — aucune exception ici, sans quoi n'importe qui peut lire les données
	// sans être authentifié.
	if (!event.locals.user && !isPublic) {
		redirect(303, '/connexion');
	}

	if (pathname.startsWith('/utilisateurs') && event.locals.user?.role !== 'admin') {
		redirect(303, '/connexion');
	}

	return resolve(event);
}
