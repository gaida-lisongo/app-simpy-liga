import { Redis } from '@upstash/redis';
import { randomBytes, scryptSync, timingSafeEqual } from 'node:crypto';
import { UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN } from '$env/static/private';
import { dev } from '$app/environment';
import { logAuth } from './log.js';

const redis = new Redis({ url: UPSTASH_REDIS_REST_URL, token: UPSTASH_REDIS_REST_TOKEN });

export const ROLES = ['admin', 'chercheur'];
export const SESSION_COOKIE = 'simpy_session';

const ACTIVATION_TTL_S = 7 * 24 * 3600;
const SESSION_TTL_S = 12 * 3600;

const kUser = (/** @type {string} */ email) => `simpy:auth:user:${email}`;
const kUsers = 'simpy:auth:users';
const kToken = (/** @type {string} */ token) => `simpy:auth:activation:${token}`;
const kSession = (/** @type {string} */ sid) => `simpy:auth:session:${sid}`;
const kUserSessions = (/** @type {string} */ email) => `simpy:auth:user:${email}:sessions`;

/**
 * @typedef {{
 *   email: string,
 *   nom: string,
 *   role: 'admin' | 'chercheur',
 *   statut: 'declared' | 'active',
 *   hash?: string,
 *   sel?: string,
 *   created_at: string,
 *   activated_at: string | null
 * }} UserRecord
 */

/** @param {UserRecord} u */
export function publicUser(u) {
	return {
		email: u.email,
		nom: u.nom,
		role: u.role,
		statut: u.statut,
		created_at: u.created_at,
		activated_at: u.activated_at
	};
}

/** @param {string} mdp @param {string} sel */
function hashPassword(mdp, sel) {
	const N = 1 << 15;
	const r = 8;
	const p = 1;
	const maxmem = 64 * 1024 * 1024;
	return scryptSync(mdp, sel, 64, { N, r, p, maxmem }).toString('hex');
}

export async function listerUsers() {
	const emails = /** @type {string[]} */ (await redis.smembers(kUsers));
	if (!emails.length) return [];
	const rows = await Promise.all(emails.map((e) => redis.get(kUser(e))));
	return rows
		.filter(Boolean)
		.map((u) => publicUser(/** @type {UserRecord} */ (u)))
		.sort((a, b) => a.nom.localeCompare(b.nom));
}

/** @param {string} email */
export async function getUser(email) {
	const u = /** @type {UserRecord | null} */ (await redis.get(kUser(email)));
	return u ? publicUser(u) : null;
}

/**
 * Compte les admins actifs — utilisé pour empêcher la suppression du dernier admin.
 * @returns {Promise<number>}
 */
export async function compterAdminsActifs() {
	const emails = /** @type {string[]} */ (await redis.smembers(kUsers));
	if (!emails.length) return 0;
	const rows = await Promise.all(emails.map((e) => redis.get(kUser(e))));
	return rows.filter((u) => u && u.role === 'admin' && u.statut === 'active').length;
}

/** @param {{ email: string, nom: string, role: string }} input */
export async function declarerUser({ email, nom, role }) {
	if (!ROLES.includes(role)) throw new Error('role_invalide');
	const existing = await redis.get(kUser(email));
	if (existing) throw new Error('email_existant');
	/** @type {UserRecord} */
	const user = {
		email,
		nom,
		role: /** @type {'admin' | 'chercheur'} */ (role),
		statut: 'declared',
		created_at: new Date().toISOString(),
		activated_at: null
	};
	await Promise.all([redis.set(kUser(email), user), redis.sadd(kUsers, email)]);
	logAuth('compte_cree', { email, role, par: 'admin' });
	return publicUser(user);
}

/** @param {string} email */
export async function creerTokenActivation(email) {
	const token = randomBytes(32).toString('hex');
	await redis.set(kToken(token), email, { ex: ACTIVATION_TTL_S });
	return token;
}

/** @param {string} token */
export async function getUserParToken(token) {
	if (!token) return null;
	const email = await redis.get(kToken(token));
	if (!email) return null;
	const user = /** @type {UserRecord | null} */ (await redis.get(kUser(/** @type {string} */ (email))));
	return user ? { user: publicUser(user), email: /** @type {string} */ (email) } : null;
}

/** @param {string} token @param {string} mdp */
export async function activerCompte(token, mdp) {
	const email = await redis.get(kToken(token));
	if (!email) throw new Error('token_invalide');
	const user = /** @type {UserRecord | null} */ (await redis.get(kUser(/** @type {string} */ (email))));
	if (!user) throw new Error('token_invalide');
	const sel = randomBytes(16).toString('hex');
	user.sel = sel;
	user.hash = hashPassword(mdp, sel);
	user.statut = 'active';
	user.activated_at = new Date().toISOString();
	await Promise.all([redis.set(kUser(user.email), user), redis.del(kToken(token))]);
	logAuth('compte_active', { email: user.email });
	return publicUser(user);
}

/** @param {string} email @param {string} mdp */
export async function verifierLogin(email, mdp) {
	const user = /** @type {UserRecord | null} */ (await redis.get(kUser(email)));
	if (!user) return { erreur: 'identifiants_invalides' };
	if (user.statut !== 'active' || !user.hash || !user.sel) return { erreur: 'compte_non_active' };
	const calc = scryptSync(mdp, user.sel, 64, { N: 1 << 15, r: 8, p: 1, maxmem: 64 * 1024 * 1024 });
	const stored = Buffer.from(user.hash, 'hex');
	if (calc.length !== stored.length || !timingSafeEqual(calc, stored))
		return { erreur: 'identifiants_invalides' };
	return { user: publicUser(user) };
}

/**
 * Purge toutes les sessions actives d'un utilisateur. Appelé lors d'une
 * suppression de compte ou d'une réinitialisation forcée.
 * @param {string} email
 */
async function purgerSessions(email) {
	const sids = /** @type {string[]} */ (await redis.smembers(kUserSessions(email)).catch(() => []));
	if (sids.length) await redis.del(...sids.map((sid) => kSession(sid)));
	await redis.del(kUserSessions(email));
}

/**
 * @param {string} email
 * @param {{ garderEmail?: boolean }} [opts] Si `garderEmail`, ne supprime que
 *   le hash/sel/statut — permet une "désactivation" plutôt qu'une suppression
 *   définitive (utilisé pour le self-delete : le mail reste réservable plus tard).
 */
export async function supprimerUser(email, opts = {}) {
	if (!email) throw new Error('email_requis');
	const u = /** @type {UserRecord | null} */ (await redis.get(kUser(email)));
	if (!u) throw new Error('utilisateur_introuvable');

	await purgerSessions(email);
	const del = await Promise.all([redis.del(kUser(email)), redis.srem(kUsers, email)]);
	if (!opts.garderEmail) {
		// suppression définitive — l'email redevient libre
	} else {
		// on garde l'entrée user mais on efface hash/sel — le user ne peut plus se connecter
		u.hash = undefined;
		u.sel = undefined;
		u.statut = 'declared';
		u.activated_at = null;
		await redis.set(kUser(email), u);
	}
	return { ok: true, supprime: del[1] === 1 };
}

/** @param {import('@sveltejs/kit').Cookies} cookies @param {string} email */
export async function creerSession(cookies, email) {
	const sid = randomBytes(32).toString('hex');
	await Promise.all([
		redis.set(kSession(sid), email, { ex: SESSION_TTL_S }),
		redis.sadd(kUserSessions(email), sid)
	]);
	cookies.set(SESSION_COOKIE, sid, {
		path: '/',
		httpOnly: true,
		sameSite: 'lax',
		secure: !dev,
		maxAge: SESSION_TTL_S
	});
}

/** @param {import('@sveltejs/kit').Cookies} cookies */
export async function getSessionUser(cookies) {
	const sid = cookies.get(SESSION_COOKIE);
	if (!sid) return null;
	const email = await redis.get(kSession(sid));
	if (!email) return null;
	const user = /** @type {UserRecord | null} */ (await redis.get(kUser(/** @type {string} */ (email))));
	return user ? publicUser(user) : null;
}

/** @param {import('@sveltejs/kit').Cookies} cookies */
export async function detruireSession(cookies) {
	const sid = cookies.get(SESSION_COOKIE);
	if (sid) {
		const email = await redis.get(kSession(sid)).catch(() => null);
		if (email) await redis.srem(kUserSessions(/** @type {string} */ (email), sid)).catch(() => {});
		await redis.del(kSession(sid));
	}
	cookies.delete(SESSION_COOKIE, { path: '/' });
}