import { popEvents } from '$lib/server/redis.js';

// GET /db/campagne/[id]/events — pont Server-Sent Events entre la file Redis
// (RPOP simpy:campagne:{id}:events) et le navigateur. L'UI ouvre un EventSource
// sur cette route et se met à jour en temps réel (progression, puis résultat/done
// ou erreur). Boucle de polling (Upstash REST ne supporte pas SUBSCRIBE persistant).
/** @param {{ params: { id: string } }} */
export async function GET({ params }) {
	const id = params.id;
	const enc = (/** @type {string} */ s) => new TextEncoder().encode(s);

	const stream = new ReadableStream({
		async start(controller) {
			let finished = false;
			const deadline = Date.now() + 35 * 60 * 1000; // garde-fou 35 min
			try {
				while (!finished && Date.now() < deadline) {
					const events = await popEvents(id);
					for (const ev of events) {
						controller.enqueue(enc(`data: ${JSON.stringify(ev)}\n\n`));
						if (ev.type === 'done' || ev.type === 'error') finished = true;
					}
					if (!finished) await new Promise((r) => setTimeout(r, 700));
				}
				if (!finished) {
					controller.enqueue(enc(`data: ${JSON.stringify({ type: 'error', message: 'Délai dépassé.' })}\n\n`));
				}
			} catch (/** @type {any} */ e) {
				try {
					controller.enqueue(enc(`data: ${JSON.stringify({ type: 'error', message: e?.message ?? 'Erreur de flux.' })}\n\n`));
				} catch {
					// le contrôleur est peut-être déjà fermé
				}
			} finally {
				controller.close();
			}
		}
	});

	return new Response(stream, {
		headers: {
			'content-type': 'text/event-stream; charset=utf-8',
			'cache-control': 'no-cache, no-transform',
			connection: 'keep-alive',
			'x-accel-buffering': 'no'
		}
	});
}