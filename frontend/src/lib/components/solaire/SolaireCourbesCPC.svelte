<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';

	/**
	 * Courbes de performance du CPC : η_th = f(G) et STR = f(T_gen).
	 * @type {{ courbes: { G_range: number[], eta_th_vs_G: number[], T_gen_range: number[], STR_vs_Tgen: number[] } | null }}
	 */
	let { courbes } = $props();

	let etaThData = $derived(
		courbes?.G_range?.length
			? [{
					x: courbes.G_range, y: courbes.eta_th_vs_G,
					type: 'scatter', mode: 'lines',
					name: 'η_th = f(G)',
					line: { color: '#06c167', width: 2 },
					fill: 'tozeroy', fillcolor: 'rgba(6,193,103,0.10)',
					hovertemplate: 'G=%{x:.0f} W/m²<br>η_th=%{y:.4f}<extra></extra>'
				}]
			: []
	);
	let etaThLayout = $derived({
		margin: { t: 10, r: 12, b: 44, l: 48 },
		showlegend: false,
		xaxis: { title: { text: 'Rayonnement solaire (W/m²)', font: { size: 10, color: '#71717a' } } },
		yaxis: { title: { text: 'Rendement thermique', font: { size: 10, color: '#71717a' } } }
	});

	let strData = $derived(
		courbes?.T_gen_range?.length
			? [{
					x: courbes.T_gen_range, y: courbes.STR_vs_Tgen,
					type: 'scatter', mode: 'lines',
					name: 'STR = f(T_gen)',
					line: { color: '#06c167', width: 2 },
					fill: 'tozeroy', fillcolor: 'rgba(6,193,103,0.10)',
					hovertemplate: 'T_gen=%{x:.0f} °C<br>STR=%{y:.4f}<extra></extra>'
				}]
			: []
	);
	let strLayout = $derived({
		margin: { t: 10, r: 12, b: 44, l: 48 },
		showlegend: false,
		xaxis: { title: { text: 'Température de génération (°C)', font: { size: 10, color: '#71717a' } } },
		yaxis: { title: { text: 'Performance solaire (STR)', font: { size: 10, color: '#71717a' } } }
	});
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h3 class="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Performance du concentrateur CPC
	</h3>
	{#if etaThData.length}
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div>
				<div style="height:200px">
					<PlotlyChart data={etaThData} layout={etaThLayout} />
				</div>
				<p class="mt-1 text-[10px] text-[var(--text-muted)] text-center">Rendement thermique selon le rayonnement</p>
			</div>
			<div>
				<div style="height:200px">
					<PlotlyChart data={strData} layout={strLayout} />
				</div>
				<p class="mt-1 text-[10px] text-[var(--text-muted)] text-center">Performance solaire (STR) selon T_gen</p>
			</div>
		</div>
	{:else}
		<div class="flex h-56 flex-col items-center justify-center gap-2">
			<div class="h-8 w-8 rounded-full bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
			<p class="text-sm text-[var(--text-muted)]">Aucune courbe — lancez une campagne.</p>
		</div>
	{/if}
</div>