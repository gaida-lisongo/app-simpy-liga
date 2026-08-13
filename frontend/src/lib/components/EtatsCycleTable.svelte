<script>
	import { fly } from 'svelte/transition';

	/**
	 * Carte "État du cycle" dynamisée : table des points d'état thermodynamiques
	 * (T, P, h, s, x) avec entrée animée (fly) des lignes, en-tête de flow du
	 * cycle (ordre 1 → 7 → 8 → 4) animé, et surbrillance au survol.
	 * @type {{
	 *   etats: { point: string|number, T?: number, P?: number, h?: number, s?: number, x?: number }[] | undefined,
	 *   ordre: string,
	 *   accent?: string
	 * }}
	 */
	let { etats, ordre, accent = '#4ade80' } = $props();

	// Points du flow extraits de l'ordre, ex. "1 → 7 → 8 → 4" → ["1","7","8","4"].
	let flowPoints = $derived(
		(ordre ?? '')
			.split('→')
			.map((s) => s.trim())
			.filter((p) => p.length && p !== 'Externe')
	);

	let hoverPoint = $state(/** @type {string | null} */ (null));
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="mb-3 flex items-center justify-between gap-2">
		<h3 class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">État du cycle</h3>
		{#if flowPoints.length > 1}
			<span class="font-mono text-xs text-[var(--text-muted)]">{ordre}</span>
		{/if}
	</div>

	<!-- Flow du cycle (pills reliées par flèches) -->
	{#if flowPoints.length > 1}
		<div class="mb-4 flex flex-wrap items-center gap-1.5">
			{#each flowPoints as p, i (p + i)}
				<span
					class="flex h-7 min-w-7 items-center justify-center rounded-full px-2 text-xs font-semibold transition-all duration-200 {hoverPoint === p
						? 'scale-110 bg-[var(--text-primary)] text-[var(--page)]'
						: 'bg-[var(--surface-raised)] text-[var(--text-secondary)]'}"
					role="img"
					aria-label="Point {p}"
				>
					{p}
				</span>
				{#if i < flowPoints.length - 1}
					<svg width="14" height="14" viewBox="0 0 14 14" fill="none" class="text-[var(--text-muted)]" aria-hidden="true">
						<path d="M2 7h8M7.5 4l3 3-3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
					</svg>
				{/if}
			{/each}
		</div>
	{/if}

	{#if etats && etats.length}
		<div class="overflow-x-auto">
			<table class="tabular w-full text-left text-sm">
				<thead>
					<tr class="border-b border-[var(--border)] text-[10px] uppercase tracking-wide text-[var(--text-muted)]">
						<th class="py-2 pr-3">Point</th>
						<th class="py-2 pr-3">T (°C)</th>
						<th class="py-2 pr-3">P (bar)</th>
						<th class="py-2 pr-3">h (kJ/kg)</th>
						<th class="py-2 pr-3">s (kJ/kg·K)</th>
						<th class="py-2 pr-3">x</th>
					</tr>
				</thead>
				<tbody>
					{#each etats as e, i (e.point)}
						<tr
							class="border-b border-[var(--border)]/60 text-[var(--text-secondary)] transition-colors duration-150 last:border-0 hover:bg-white/5 {hoverPoint === String(e.point) ? 'bg-white/5' : ''}"
							onmouseenter={() => (hoverPoint = String(e.point))}
							onmouseleave={() => (hoverPoint = null)}
							transition:fly={{ y: 10, duration: 220, delay: i * 50 }}
						>
							<td class="py-2 pr-3">
								<span
									class="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--surface-raised)] px-1.5 text-[10px] font-semibold text-[var(--text-primary)]"
								>
									{e.point}
								</span>
							</td>
							<td class="py-2 pr-3">{e.T?.toFixed(2) ?? '—'}</td>
							<td class="py-2 pr-3">{e.P?.toFixed(3) ?? '—'}</td>
							<td class="py-2 pr-3">{e.h?.toFixed(1) ?? '—'}</td>
							<td class="py-2 pr-3">{e.s?.toFixed(3) ?? '—'}</td>
							<td class="py-2 pr-3">{e.x !== undefined && e.x !== null ? e.x.toFixed(3) : '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<div class="flex flex-col items-center gap-2 py-8 text-center">
			<div class="h-8 w-8 rounded-full bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
			<p class="text-sm text-[var(--text-muted)]">Aucun point d'état — lancez une campagne.</p>
		</div>
	{/if}
</div>