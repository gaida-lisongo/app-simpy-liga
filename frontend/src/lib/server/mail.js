import nodemailer from 'nodemailer';
import {
	MAIL_HOST,
	MAIL_PORT,
	MAIL_SECURE,
	MAIL_USER,
	MAIL_PASS,
	MAIL_FROM
} from '$env/static/private';

/** @type {ReturnType<typeof nodemailer.createTransport> | null} */
let transporter = null;

function getTransporter() {
	if (!transporter) {
		transporter = nodemailer.createTransport({
			host: MAIL_HOST,
			port: Number(MAIL_PORT || 587),
			secure: String(MAIL_SECURE || 'false').toLowerCase() === 'true',
			connectionTimeout: 10000,
			greetingTimeout: 10000,
			socketTimeout: 20000,
			auth: { user: MAIL_USER, pass: MAIL_PASS },
			tls: { servername: MAIL_HOST }
		});
	}
	return transporter;
}

/**
 * @param {{ to: string, subject: string, html: string }} input
 */
export async function sendMail({ to, subject, html }) {
	return getTransporter().sendMail({
		from: MAIL_FROM || MAIL_USER,
		to,
		subject,
		html
	});
}

/**
 * @param {{ nom: string, circuit: string, campagneId: string, lien: string }} input
 */
export function mailCampagneTermineeHtml({ nom, circuit, campagneId, lien }) {
	return `
	<div style="font-family:system-ui,-apple-system,'Segoe UI',sans-serif;background:#0d0d0d;padding:24px;color:#1f2937;">
		<div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:14px;border:1px solid #e5e7eb;padding:32px;">
			<h1 style="margin:0 0 8px;font-size:20px;color:#111111;">Votre campagne est terminée</h1>
			<p style="margin:0 0 16px;color:#4b5563;">Bonjour <strong>${nom || ''}</strong>,</p>
			<p style="margin:0 0 24px;color:#4b5563;">
				La campagne de simulation lancée sur le circuit <strong>${circuit}</strong>
				(${campagneId}) est terminée et ses résultats sont disponibles.
				Actualisez la page pour les retrouver.
			</p>
			<a href="${lien}" style="display:inline-block;background:#06c167;color:#ffffff;text-decoration:none;font-weight:600;padding:12px 24px;border-radius:8px;">
				Voir les résultats
			</a>
			<p style="margin:24px 0 0;color:#9ca3af;font-size:13px;">
				Ou copiez ce lien dans votre navigateur :<br />
				<a href="${lien}" style="color:#06c167;word-break:break-all;">${lien}</a>
			</p>
		</div>
	</div>`;
}

/**
 * @param {{ nom: string, lien: string, reinitialisation?: boolean }} input
 */
export function mailActivationHtml({ nom, lien, reinitialisation = false }) {
	const titre = reinitialisation
		? 'Réinitialisez votre mot de passe'
		: 'Activez votre compte SimpyLIGA';
	const intro = reinitialisation
		? "Un administrateur a demandé la réinitialisation de votre mot de passe. Définissez-en un nouveau via le bouton ci-dessous."
		: "Votre compte SimpyLIGA a été créé. Définissez votre mot de passe via le bouton ci-dessous pour commencer à travailler.";
	return `
	<div style="font-family:system-ui,-apple-system,'Segoe UI',sans-serif;background:#0d0d0d;padding:24px;color:#1f2937;">
		<div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:14px;border:1px solid #e5e7eb;padding:32px;">
			<h1 style="margin:0 0 8px;font-size:20px;color:#111111;">${titre}</h1>
			<p style="margin:0 0 16px;color:#4b5563;">Bonjour <strong>${nom}</strong>,</p>
			<p style="margin:0 0 24px;color:#4b5563;">${intro}</p>
			<a href="${lien}" style="display:inline-block;background:#06c167;color:#ffffff;text-decoration:none;font-weight:600;padding:12px 24px;border-radius:8px;">
				${reinitialisation ? 'Définir un nouveau mot de passe' : 'Activer mon compte'}
			</a>
			<p style="margin:24px 0 0;color:#9ca3af;font-size:13px;">
				Ou copiez ce lien dans votre navigateur :<br />
				<a href="${lien}" style="color:#06c167;word-break:break-all;">${lien}</a>
			</p>
			<p style="margin:24px 0 0;color:#9ca3af;font-size:13px;">
				Ce lien est personnel et expire après 7 jours. Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.
			</p>
		</div>
	</div>`;
}
