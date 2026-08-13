<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';
	import Tooltip from '$lib/components/ui/Tooltip.svelte';

	/**
	 * Sparkline = moyenne cumulée du tirage (convergence réelle sur la campagne),
	 * calculée à partir de resultats.tirages — pas de donnée fabriquée. Rendu Plotly.
	 * @type {{
	 *   label: string,
	 *   tooltip?: string,
	 *   stat: { moyenne?: number, ecart_type?: number, IC95?: [number, number] } | null,
	 *   serie: number[],
	 *   accent: string,
	 *   decimals?: number
	 * }}
	 */
	let { label, tooltip = '', stat, serie, accent, decimals = 3 } = $props();

	/** @param {number | null | undefined} v */
	function fmt(v) {
		return v === undefined || v === null ? '—' : Number(v).toFixed(decimals);
	}

	let cum = $derived.by(() => {
		if (!serie?.length) return [];
		let acc = 0;
		return serie.map((v, i) => (acc += v) / (i + 1));
	});

	let plotData = $derived(
		cum.length
			? [
					{
						x: cum.map((_, i) => i + 1),
						y: cum,
						type: 'scatter',
						mode: 'lines',
						fill: 'tozeroy',
						line: { color: '#06c167', width: 1.6 },
						fillcolor: 'rgba(6,193,103,0.14)',
						showlegend: false
					}
				]
			: []
	);

	let sparkLayout = $derived({
		margin: { t: 0, b: 0, l: 0, r: 0 },
		xaxis: { visible: false },
		yaxis: { visible: false },
		showlegend: false
	});

	let cv = $derived(
		stat?.moyenne ? Math.abs((stat.ecart_type ?? 0) / stat.moyenne) * 100 : null
	);
</script>

<div class="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="absolute inset-x-0 top-0 h-[3px] bg-[var(--accent)]"></div>

	<div class="flex items-center gap-1.5">
		<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">{label}</span>
		{#if tooltip}
			<Tooltip text={tooltip}>
				<span class="flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full border border-[var(--text-muted)] text-[9px] leading-none text-[var(--text-muted)]">?</span>
			</Tooltip>
		{/if}
	</div>

	{#if stat}
		<p class="tabular mt-1.5 text-2xl font-semibold text-[var(--text-primary)]">{fmt(stat.moyenne)}</p>
		{#if cv !== null}
			<p class="tabular text-xs text-[var(--text-secondary)]">CV {cv.toFixed(1)}%</p>
		{/if}

		{#if cum.length}
			<div style="height:48px" class="mt-2">
				<PlotlyChart data={plotData} layout={sparkLayout} />
			</div>
		{/if}

		{#if stat.IC95}
			<p class="tabular mt-1 text-[10px] text-[var(--text-muted)]">IC95 [{fmt(stat.IC95[0])}, {fmt(stat.IC95[1])}]</p>
		{/if}
	{:else}
		<p class="mt-2 text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
	{/if}
</div>