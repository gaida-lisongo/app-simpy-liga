import { readFileSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
import { Redis } from '@upstash/redis';
import nodemailer from 'nodemailer';

const envPath = new URL('../.env', import.meta.url);
const env = Object.fromEntries(
	readFileSync(envPath, 'utf8')
		.split('\n')
		.map((l) => l.trim())
		.filter((l) => l && !l.startsWith('#'))
		.map((l) => {
			const i = l.indexOf('=');
			return [l.slice(0, i), l.slice(i + 1).replace(/^"|"$/g, '')];
		})
);

const ADMIN = {
	email: 'inbtpkinshasa@gmail.com',
	nom: 'Gaïda LISONGO',
	role: 'admin'
};

const baseUrl = process.argv[2] || env.SEED_BASE_URL || 'https://simpy-liga.elmes-solution.site';
const redis = new Redis({ url: env.UPSTASH_REDIS_REST_URL, token: env.UPSTASH_REDIS_REST_TOKEN });

const kUser = `simpy:auth:user:${ADMIN.email}`;
const kUsers = 'simpy:auth:users';

const existing = await redis.get(kUser);
if (existing) {
	console.log(`L'utilisateur ${ADMIN.email} existe déjà — génération d'un nouveau magic link.`);
}

const user = existing ?? {
	email: ADMIN.email,
	nom: ADMIN.nom,
	role: ADMIN.role,
	statut: 'declared',
	created_at: new Date().toISOString(),
	activated_at: null
};
const token = randomBytes(32).toString('hex');

await Promise.all([
	redis.set(kUser, user),
	redis.sadd(kUsers, ADMIN.email),
	redis.set(`simpy:auth:activation:${token}`, ADMIN.email, { ex: 7 * 24 * 3600 })
]);

const lien = `${baseUrl}/activation?token=${token}`;

const html = `
	<div style="font-family:system-ui,-apple-system,'Segoe UI',sans-serif;background:#0d0d0d;padding:24px;color:#1f2937;">
		<div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:14px;border:1px solid #e5e7eb;padding:32px;">
			<h1 style="margin:0 0 8px;font-size:20px;color:#111111;">Activez votre compte SimpyLIGA</h1>
			<p style="margin:0 0 16px;color:#4b5563;">Bonjour <strong>${ADMIN.nom}</strong>,</p>
			<p style="margin:0 0 24px;color:#4b5563;">Votre compte administrateur SimpyLIGA a été créé. Définissez votre mot de passe via le bouton ci-dessous pour commencer à travailler.</p>
			<a href="${lien}" style="display:inline-block;background:#06c167;color:#ffffff;text-decoration:none;font-weight:600;padding:12px 24px;border-radius:8px;">Activer mon compte</a>
			<p style="margin:24px 0 0;color:#9ca3af;font-size:13px;">
				Ou copiez ce lien dans votre navigateur :<br />
				<a href="${lien}" style="color:#06c167;word-break:break-all;">${lien}</a>
			</p>
			<p style="margin:24px 0 0;color:#9ca3af;font-size:13px;">Ce lien est personnel et expire après 7 jours.</p>
		</div>
	</div>`;

const transporter = nodemailer.createTransport({
	host: env.MAIL_HOST,
	port: Number(env.MAIL_PORT || 587),
	secure: String(env.MAIL_SECURE || 'false').toLowerCase() === 'true',
	connectionTimeout: 10000,
	greetingTimeout: 10000,
	socketTimeout: 20000,
	auth: { user: env.MAIL_USER, pass: env.MAIL_PASS },
	tls: { servername: env.MAIL_HOST }
});

try {
	const info = await transporter.sendMail({
		from: env.MAIL_FROM || env.MAIL_USER,
		to: ADMIN.email,
		subject: 'Activez votre compte SimpyLIGA',
		html
	});
	console.log(`Compte admin créé pour ${ADMIN.email}.`);
	console.log(`Magic link envoyé (messageId: ${info.messageId}).`);
	console.log(`Lien : ${lien}`);
} catch (e) {
	console.error(`Compte admin créé, mais l'envoi de l'email a échoué : ${e.message}`);
	console.log(`Partagez ce lien manuellement : ${lien}`);
	process.exit(1);
}
