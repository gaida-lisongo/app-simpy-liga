<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';

	/**
	 * Donut de distribution Monte Carlo : part des tirages sous μ-σ, dans μ±σ, au-dessus de μ+σ,
	 * calculée directement sur resultats.tirages (pas de fabrication statistique). Rendu Plotly.
	 * @type {{
	 *   label: string, serie: number[], stat: { moyenne?: number, ecart_type?: number } | null, accent: string,
	 *   convergence?: { N_stable?: number | null, stabilise?: boolean | null } | null,
	 *   tauxRejetPct?: number | null
	 * }}
	 */
	let { label, serie, stat, accent, convergence = null, tauxRejetPct = null } = $props();

	let buckets = $derived.by(() => {
		if (!serie?.length || stat?.moyenne == null) return null;
		const { moyenne: mu, ecart_type: sigma } = stat;
		// Cas dégénéré : σ nul (tirages identiques — ex. paramètres non couplés au cycle).
		// On ne peut pas bucketing autour de μ±σ ; on signale l'état au rendu.
		if (!sigma || sigma === 0) return { degenerate: true, mu, n: serie.length };
		let bas = 0, dans = 0, haut = 0;
		for (const v of serie) {
			if (v < mu - sigma) bas++;
			else if (v > mu + sigma) haut++;
			else dans++;
		}
		const n = serie.length;
		return [
			{ label: 'μ − σ', n: bas, pct: (bas / n) * 100, opacity: 0.30 },
			{ label: 'μ ± σ', n: dans, pct: (dans / n) * 100, opacity: 0.95 },
			{ label: 'μ + σ', n: haut, pct: (haut / n) * 100, opacity: 0.55 }
		];
	});

	let degenerate = $derived(buckets && /** @type {any} */ (buckets).degenerate === true);
	let bucketList = $derived(buckets && !degenerate ? /** @type {any[]} */ (buckets) : []);

	let plotData = $derived(
		bucketList.length
			? [
					{
						values: bucketList.map((b) => b.pct),
						labels: bucketList.map((b) => b.label),
						type: 'pie',
						hole: 0.55,
						marker: { colors: ['rgba(250,250,250,0.25)', '#06c167', 'rgba(250,250,250,0.50)'] },
						textfont: { color: '#09090b', size: 9 },
						hovertemplate: '%{label}: %{value:.1f}%<extra></extra>',
						showlegend: true
					}
				]
			: degenerate
				? [
						{
							values: [100],
							labels: ['Tous identiques'],
							type: 'pie',
							hole: 0.55,
							marker: { colors: ['rgba(250,250,250,0.55)'] },
							textfont: { color: '#09090b', size: 9 },
							hovertemplate: 'σ = 0 — tirages identiques<extra></extra>',
							showlegend: false
						}
					]
				: []
	);

	let plotLayout = $derived({
		showlegend: !degenerate,
		margin: { t: 0, b: 0, l: 0, r: 0 },
		annotations: [
			{
				x: 0.5, y: 0.5, showarrow: false,
				text: `<b>${serie?.length ?? 0}</b><br><span style="font-size:9px;color:#71717a">tirages</span>`,
				font: { color: '#fafafa', size: 18 }
			}
		]
	});
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h3 class="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Distribution Monte Carlo — {label}
	</h3>

	{#if buckets}
		<div class="flex flex-col items-center gap-4 sm:flex-row">
			<div style="width:200px;height:200px;flex:0 0 auto">
				<PlotlyChart data={plotData} layout={plotLayout} />
			</div>

			{#if degenerate}
				<div class="flex-1 space-y-2 text-xs">
					<p class="text-[var(--text-secondary)]">
						<span class="tabular font-medium text-[var(--text-primary)]">σ = 0</span> — tous les tirages sont identiques.
					</p>
					<p class="text-[10px] leading-relaxed text-[var(--text-muted)]">
						Les paramètres incertains de ce circuit ne sont pas couplés au solveur du cycle :
						la grandeur de sortie est constante quelle que soit la valeur tirée.
					</p>
					<p class="tabular text-[10px] text-[var(--text-muted)]">μ = {buckets.mu.toFixed(4)} · {buckets.n} tirages</p>
				</div>
			{:else}
				<ul class="flex-1 space-y-1.5 text-xs">
					{#each bucketList as b (b.label)}
						<li class="flex items-center justify-between gap-3">
							<span class="flex items-center gap-2 text-[var(--text-secondary)]">
								<span class="h-2.5 w-2.5 rounded-full bg-[var(--text-primary)]" style="opacity:{b.opacity}"></span>
								{b.label}
							</span>
							<span class="tabular text-[var(--text-primary)]">{b.pct.toFixed(1)}% ({b.n})</span>
						</li>
					{/each}
				</ul>
			{/if}
		</div>
		{#if convergence || tauxRejetPct !== null}
			<p class="tabular mt-3 text-[10px] text-[var(--text-muted)]">
				{#if convergence?.N_stable}N_stable = {convergence.N_stable} ({convergence.stabilise ? 'stabilisée' : 'non stabilisée'}){/if}
				{#if tauxRejetPct !== null} · rejet non-physique {tauxRejetPct.toFixed(1)}%{/if}
			</p>
		{/if}
	{:else}
		<p class="py-10 text-center text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
	{/if}
</div>