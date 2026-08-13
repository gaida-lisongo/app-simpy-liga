<script>
	import { PARAM_INFO, LOI_LABELS } from '$lib/constants.js';

	/**
	 * Histogramme réel (pas une approximation) construit depuis resultats.tirages —
	 * une tab par paramètre incertain variable du circuit.
	 * @type {{ params: any[], tirages: Record<string, number>[] }}
	 */
	let { params, tirages } = $props();

	let variables = $derived(params.filter((p) => p.loi !== 'fixe'));
	let actif = $state(/** @type {string | null} */ (null));
	$effect(() => {
		if (!actif && variables.length) actif = variables[0].nom;
	});

	const BINS = 20;
	const W = 320, H = 140, PAD_L = 6, PAD_B = 20;

	/** @param {string} nom */
	function bars(nom) {
		const vals = tirages.map((t) => t[nom]).filter((v) => typeof v === 'number' && Number.isFinite(v));
		if (vals.length < 2) return null;
		const lo = Math.min(...vals), hi = Math.max(...vals);
		if (!(hi > lo)) return null;
		const step = (hi - lo) / BINS;
		const counts = new Array(BINS).fill(0);
		for (const v of vals) counts[Math.min(BINS - 1, Math.floor((v - lo) / step))]++;
		const max = Math.max(...counts) || 1;
		const barW = (W - PAD_L) / BINS;
		return {
			lo, hi,
			bars: counts.map((c, i) => ({
				x: PAD_L + i * barW,
				w: Math.max(barW - 2, 1),
				h: (c / max) * (H - PAD_B - 6)
			}))
		};
	}

	let courant = $derived(actif ? bars(actif) : null);
	let paramActif = $derived(variables.find((p) => p.nom === actif));
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h3 class="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Variables aléatoires
	</h3>

	{#if variables.length === 0}
		<p class="text-sm text-[var(--text-muted)]">Aucun paramètre incertain variable pour ce circuit.</p>
	{:else}
		<div class="mb-3 flex flex-wrap gap-1">
			{#each variables as p (p.nom)}
				<button
					type="button"
					onclick={() => (actif = p.nom)}
					class="rounded-full border px-2.5 py-1 text-xs font-medium transition-colors {actif === p.nom
						? 'border-[#4ade80] bg-[#4ade8022] text-[#4ade80]'
						: 'border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-secondary)]'}"
				>
					{p.symbole}
				</button>
			{/each}
		</div>

		{#if courant}
			<svg viewBox="0 0 {W} {H}" class="w-full" role="img" aria-label="Histogramme de {paramActif?.symbole}">
				<line x1={PAD_L} y1={H - PAD_B} x2={W} y2={H - PAD_B} stroke="var(--border)" stroke-width="1" />
				{#each courant.bars as b, i (i)}
					<rect x={b.x} y={H - PAD_B - b.h} width={b.w} height={b.h} rx="2" fill="#4ade80" opacity="0.85" />
				{/each}
			</svg>
			<div class="tabular mt-1 flex justify-between text-[10px] text-[var(--text-muted)]">
				<span>{courant.lo.toFixed(3)}</span>
				<span>{courant.hi.toFixed(3)}</span>
			</div>
			<p class="mt-1 text-[10px] text-[var(--text-muted)]">
				{PARAM_INFO[paramActif?.nom]?.label ?? paramActif?.symbole} — {LOI_LABELS[paramActif?.loi] ?? paramActif?.loi}
			</p>
		{:else}
			<p class="text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
		{/if}
	{/if}
</div>
