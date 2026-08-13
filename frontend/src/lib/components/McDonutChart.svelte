<script>
	/**
	 * Donut de distribution Monte Carlo : part des tirages sous μ-σ, dans μ±σ, au-dessus de μ+σ,
	 * calculée directement sur resultats.tirages (pas de fabrication statistique).
	 * @type {{
	 *   label: string, serie: number[], stat: { moyenne?: number, ecart_type?: number } | null, accent: string,
	 *   convergence?: { N_stable?: number | null, stabilise?: boolean | null } | null,
	 *   tauxRejetPct?: number | null
	 * }}
	 */
	let { label, serie, stat, accent, convergence = null, tauxRejetPct = null } = $props();

	const R = 60, CX = 70, CY = 70, STROKE = 22;

	let buckets = $derived.by(() => {
		if (!serie?.length || !stat?.moyenne || !stat?.ecart_type) return null;
		const { moyenne: mu, ecart_type: sigma } = stat;
		let bas = 0, dans = 0, haut = 0;
		for (const v of serie) {
			if (v < mu - sigma) bas++;
			else if (v > mu + sigma) haut++;
			else dans++;
		}
		const n = serie.length;
		return [
			{ label: 'μ − σ', n: bas, pct: (bas / n) * 100, opacity: 0.45 },
			{ label: 'μ ± σ', n: dans, pct: (dans / n) * 100, opacity: 1 },
			{ label: 'μ + σ', n: haut, pct: (haut / n) * 100, opacity: 0.7 }
		];
	});

	/** @param {number} startPct @param {number} pct */
	function arc(startPct, pct) {
		const c = 2 * Math.PI * R;
		return {
			dasharray: `${(pct / 100) * c} ${c}`,
			dashoffset: -((startPct / 100) * c)
		};
	}

	let arcs = $derived.by(() => {
		if (!buckets) return [];
		let acc = 0;
		return buckets.map((b) => {
			const a = arc(acc, b.pct);
			acc += b.pct;
			return { ...b, ...a };
		});
	});
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h3 class="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Distribution Monte Carlo — {label}
	</h3>

	{#if buckets}
		<div class="flex flex-col items-center gap-4 sm:flex-row">
			<svg viewBox="0 0 140 140" width="140" height="140" role="img" aria-label="Répartition des tirages autour de la moyenne">
				<circle cx={CX} cy={CY} r={R} fill="none" stroke="var(--border)" stroke-width={STROKE} />
				{#each arcs as a (a.label)}
					<circle
						cx={CX} cy={CY} r={R} fill="none" stroke={accent} stroke-width={STROKE}
						stroke-opacity={a.opacity}
						stroke-dasharray={a.dasharray}
						stroke-dashoffset={a.dashoffset}
						transform="rotate(-90 {CX} {CY})"
					/>
				{/each}
				<text x={CX} y={CY - 4} text-anchor="middle" font-size="20" fill="var(--text-primary)" font-weight="600">{serie.length}</text>
				<text x={CX} y={CY + 14} text-anchor="middle" font-size="9" fill="var(--text-muted)">tirages</text>
			</svg>

			<ul class="flex-1 space-y-1.5 text-xs">
				{#each buckets as b (b.label)}
					<li class="flex items-center justify-between gap-3">
						<span class="flex items-center gap-2 text-[var(--text-secondary)]">
							<span class="h-2.5 w-2.5 rounded-full" style="background:{accent}; opacity:{b.opacity}"></span>
							{b.label}
						</span>
						<span class="tabular text-[var(--text-primary)]">{b.pct.toFixed(1)}% ({b.n})</span>
					</li>
				{/each}
			</ul>
		</div>
		{#if convergence || tauxRejetPct !== null}
			<p class="tabular mt-3 text-[10px] text-[var(--text-muted)]">
				{#if convergence?.N_stable}N_stable = {convergence.N_stable} ({convergence.stabilise ? 'stabilisée' : 'non stabilisée'}){/if}
				{#if tauxRejetPct !== null} · rejet non-physique {tauxRejetPct.toFixed(1)}%{/if}
			</p>
		{/if}
	{:else}
		<p class="text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
	{/if}
</div>
