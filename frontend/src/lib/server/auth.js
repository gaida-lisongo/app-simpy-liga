import { Redis } from '@upstash/redis';
import { randomBytes, scryptSync, timingSafeEqual } from 'node:crypto';
import { UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN } from '$env/static/private';
import { dev } from '$app/environment';

const redis = new Redis({ url: UPSTASH_REDIS_REST_URL, token: UPSTASH_REDIS_REST_TOKEN });

export const ROLES = ['admin', 'chercheur'];
export const SESSION_COOKIE = 'simpy_session';

const ACTIVATION_TTL_S = 7 * 24 * 3600;
const SESSION_TTL_S = 12 * 3600;

const kUser = (/** @type {string} */ email) => `simpy:auth:user:${email}`;
const kUsers = 'simpy:auth:users';
const kToken = (/** @type {string} */ token) => `simpy:auth:activation:${token}`;
const kSession = (/** @type {string} */ sid) => `simpy:auth:session:${sid}`;

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
	return scryptSync(mdp, sel, 64).toString('hex');
}

export async function listerUsers() {
	const emails = /** @type {string[]} */ (await redis.smembers(kUsers));
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
	return publicUser(user);
}

/** @param {string} email @param {string} mdp */
export async function verifierLogin(email, mdp) {
	const user = /** @type {UserRecord | null} */ (await redis.get(kUser(email)));
	if (!user) return { erreur: 'identifiants_invalides' };
	if (user.statut !== 'active' || !user.hash || !user.sel) return { erreur: 'compte_non_active' };
	const calc = scryptSync(mdp, user.sel, 64);
	const stored = Buffer.from(user.hash, 'hex');
	if (calc.length !== stored.length || !timingSafeEqual(calc, stored))
		return { erreur: 'identifiants_invalides' };
	return { user: publicUser(user) };
}

/** @param {import('@sveltejs/kit').Cookies} cookies @param {string} email */
export async function creerSession(cookies, email) {
	const sid = randomBytes(32).toString('hex');
	await redis.set(kSession(sid), email, { ex: SESSION_TTL_S });
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
	if (sid) await redis.del(kSession(sid));
	cookies.delete(SESSION_COOKIE, { path: '/' });
}
