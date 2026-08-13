<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';
	import { SOLAIRE_KPI_LABELS, fmtVal, fmtIC95 } from '$lib/utils/labels.js';

	/**
	 * @type {{ label: string, unite: string, tooltip?: string, litterature?: string,
	 *   stat: { moyenne?: number, ecart_type?: number, IC95?: [number, number] } | null,
	 *   serie?: number[], decimals?: number, index?: number }}
	 */
	let { label, unite = '', tooltip = '', litterature = '', stat, serie = [], decimals = 3, index = 0 } = $props();

	let sigmaNul = $derived(stat?.ecart_type === 0 || stat?.ecart_type == null && stat?.moyenne != null);
	let constT = $derived(serie.length >= 2 && serie.every((v) => v === serie[0]));

	// Moyenne cumulée pour la sparkline (convergence réelle).
	let cum = $derived.by(() => {
		if (!serie?.length) return [];
		let acc = 0;
		return serie.map((v, i) => (acc += v) / (i + 1));
	});

	let plotData = $derived(
		cum.length >= 2 && !constT
			? [
					{
						x: cum.map((_, i) => i + 1),
						y: cum,
						type: 'scatter',
						mode: 'lines',
						fill: 'tozeroy',
						line: { color: '#06c167', width: 1.5 },
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

	let deltaTone = $derived(sigmaNul ? 'text-[var(--text-muted)]' : 'text-[var(--text-secondary)]');
	let deltaText = $derived(sigmaNul
		? 'σ = 0 — sortie non sensible aux paramètres'
		: `σ = ${fmtVal(stat?.ecart_type, 4)}`);
</script>

<div class="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5">
	<div class="absolute inset-x-0 top-0 h-[3px] bg-[var(--accent)]"></div>

	<p class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]" title={tooltip}>{label}</p>

	{#if stat}
		<p class="tabular mt-2 text-3xl font-semibold text-[var(--text-primary)]">
			{fmtVal(stat.moyenne, decimals)}<span class="ml-1 text-sm text-[var(--text-muted)]">{unite}</span>
		</p>
		<p class="tabular mt-1 text-xs {deltaTone}">{deltaText}</p>

		{#if plotData.length}
			<div style="height:44px" class="mt-2">
				<PlotlyChart data={plotData} layout={sparkLayout} />
			</div>
		{/if}

		<p class="tabular mt-2 text-[10px] text-[var(--text-muted)]">{fmtIC95(stat.IC95)}</p>
		{#if litterature}
			<p class="mt-1 text-[10px] text-[var(--text-muted)]">{litterature}</p>
		{/if}
	{:else}
		<div class="mt-2 space-y-2">
			<div class="h-7 w-24 rounded bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
			<div class="h-3 w-32 rounded bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
			<div class="h-11 w-full rounded bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
		</div>
	{/if}
</div>