<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';

	/**
	 * Diagramme Sankey des flux d'énergie du circuit solaire.
	 * @type {{ sankey: { labels: string[], values_kW: number[], source: number[], target: number[] } | null }}
	 */
	let { sankey } = $props();

	let plotData = $derived.by(() => {
		if (!sankey?.labels?.length || !sankey.values_kW?.length) return [];
		const maxAbs = Math.max(...sankey.values_kW.map(Math.abs)) || 1;
		return [{
			type: 'sankey',
			orientation: 'h',
			node: {
				label: sankey.labels,
				color: sankey.labels.map((_, i) => {
					const isLoss = sankey.labels[i].toLowerCase().includes('perte');
					return isLoss ? '#f5a623' : '#06c167';
				}),
				pad: 14, thickness: 18,
				line: { color: '#27272a', width: 0.5 }
			},
			link: {
				source: sankey.source ?? [],
				target: sankey.target ?? [],
				value: sankey.values_kW,
				color: 'rgba(6,193,103,0.25)'
			}
		}];
	});

	let plotLayout = $derived({
		margin: { t: 10, r: 12, b: 10, l: 12 },
		font: { color: '#a1a1aa', size: 10 },
		paper_bgcolor: 'transparent',
		plot_bgcolor: 'transparent'
	});
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h3 class="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Flux d'énergie — circuit solaire
	</h3>
	{#if plotData.length}
		<div style="height:240px">
			<PlotlyChart data={plotData} layout={plotLayout} />
		</div>
		<div class="mt-2 grid grid-cols-2 gap-2 text-[10px] text-[var(--text-muted)] sm:grid-cols-3">
			{#each sankey.labels as label, i (label)}
				<span class="flex items-center justify-between gap-2 rounded-[var(--radius-sm)] bg-[var(--surface-raised)] px-2 py-1">
					<span>{label}</span>
					<span class="tabular font-medium text-[var(--text-secondary)]">{sankey.values_kW[i]?.toFixed(2)} kW</span>
				</span>
			{/each}
		</div>
	{:else}
		<div class="flex h-48 flex-col items-center justify-center gap-2">
			<div class="h-8 w-8 rounded-full bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
			<p class="text-sm text-[var(--text-muted)]">Aucune donnée Sankey — lancez une campagne.</p>
		</div>
	{/if}
</div>