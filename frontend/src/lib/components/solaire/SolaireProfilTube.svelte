<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';

	/**
	 * Profil axial du tube absorbeur — T_fluide, T_absorbeur, T_vitre le long
	 * du tube. 2 zones (préchauffage + vaporisation) colorées en arrière-plan.
	 * @type {{ profil: { x_m: number[], T_fluide: number[], T_absorbeur: number[], T_vitre: number[], zones: string[] } | null }}
	 */
	let { profil } = $props();

	let plotData = $derived.by(() => {
		if (!profil?.x_m?.length) return [];
		return [
			{
				x: profil.x_m, y: profil.T_fluide,
				type: 'scatter', mode: 'lines',
				name: 'Fluide R718',
				line: { color: '#06c167', width: 2 },
				hovertemplate: 'x=%{x:.2f} m<br>T=%{y:.1f} °C<extra>Fluide</extra>'
			},
			{
				x: profil.x_m, y: profil.T_absorbeur,
				type: 'scatter', mode: 'lines',
				name: 'Absorbeur',
				line: { color: '#f5a623', width: 1.5, dash: 'dot' },
				hovertemplate: 'x=%{x:.2f} m<br>T=%{y:.1f} °C<extra>Absorbeur</extra>'
			},
			{
				x: profil.x_m, y: profil.T_vitre,
				type: 'scatter', mode: 'lines',
				name: 'Vitre',
				line: { color: '#8e8e93', width: 1.5, dash: 'dash' },
				hovertemplate: 'x=%{x:.2f} m<br>T=%{y:.1f} °C<extra>Vitre</extra>'
			}
		];
	});

	// Zones colorées (shapes) selon profil.zones
	let shapes = $derived.by(() => {
		if (!profil?.x_m?.length || !profil.zones?.length) return [];
		const out = [];
		let i = 0;
		while (i < profil.zones.length) {
			const zone = profil.zones[i];
			let j = i;
			while (j < profil.zones.length && profil.zones[j] === zone) j++;
			const fill = zone === 'préchauffage' ? 'rgba(6,193,103,0.06)' : 'rgba(245,166,35,0.06)';
			out.push({
				type: 'rect', x0: profil.x_m[i], x1: profil.x_m[j - 1] ?? profil.x_m[i],
				y0: 0, y1: 1, yref: 'paper',
				fillcolor: fill, line: { width: 0 }
			});
			i = j;
		}
		return out;
	});

	let plotLayout = $derived({
		margin: { t: 10, r: 12, b: 44, l: 48 },
		showlegend: true,
		xaxis: { title: { text: 'Position le long du tube (m)', font: { size: 10, color: '#71717a' } } },
		yaxis: { title: { text: 'Température (°C)', font: { size: 10, color: '#71717a' } } },
		shapes,
		annotations: shapes.length >= 2 ? [
			{ x: (shapes[0].x0 + shapes[0].x1) / 2, y: 1.02, yref: 'paper', showarrow: false,
				text: 'Préchauffage', font: { size: 8, color: '#06c167' } },
			{ x: (shapes[1]?.x0 + shapes[1]?.x1) / 2, y: 1.02, yref: 'paper', showarrow: false,
				text: 'Vaporisation', font: { size: 8, color: '#f5a623' } }
		] : []
	});
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h3 class="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Profil axial du tube absorbeur
	</h3>
	{#if plotData.length}
		<div style="height:280px">
			<PlotlyChart data={plotData} layout={plotLayout} />
		</div>
		<div class="mt-2 flex flex-wrap gap-4 text-[10px] text-[var(--text-muted)]">
			<span class="flex items-center gap-1.5"><span class="h-1.5 w-3 rounded-full bg-[#06c167]"></span> Fluide R718</span>
			<span class="flex items-center gap-1.5"><span class="h-1.5 w-3 rounded-full bg-[#f5a623]"></span> Absorbeur</span>
			<span class="flex items-center gap-1.5"><span class="h-1.5 w-3 rounded-full bg-[#8e8e93]"></span> Vitre</span>
		</div>
	{:else}
		<div class="flex h-56 flex-col items-center justify-center gap-2">
			<div class="h-8 w-8 rounded-full bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
			<p class="text-sm text-[var(--text-muted)]">Aucun profil — lancez une campagne.</p>
		</div>
	{/if}
</div>