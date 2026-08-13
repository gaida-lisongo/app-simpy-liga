<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';

	/**
	 * Panneau diagramme thermodynamique — types P-s / T-s / T-P, sélection d'un composant
	 * (segment du cycle) à mettre en évidence. Alimenté par resultats.etats_cycle (cycle de
	 * référence à valeurs nominales). Rendu Plotly.
	 * @type {{
	 *   etats: { point: string, T?: number, P?: number, h?: number, s?: number, x?: number }[] | undefined,
	 *   segments: { label: string, from: string, to: string }[],
	 *   accent: string
	 * }}
	 */
	let { etats, segments, accent } = $props();

	const TYPES = [
		{ id: 'Ts', label: 'T-s', xLabel: 's (kJ/kg·K)', yLabel: 'T (°C)' },
		{ id: 'Ps', label: 'P-s', xLabel: 's (kJ/kg·K)', yLabel: 'P (bar)', yLog: true },
		{ id: 'TP', label: 'T-P', xLabel: 'P (bar)', yLabel: 'T (°C)', xLog: true }
	];
	let type = $state('Ts');
	let composant = $state('');

	/** @param {{T?:number,P?:number,s?:number}} e */
	function coords(e) {
		if (type === 'Ts') return { x: e.s, y: e.T };
		if (type === 'Ps') return { x: e.s, y: e.P != null && e.P > 0 ? e.P : null };
		return { x: e.P != null && e.P > 0 ? e.P : null, y: e.T };
	}

	let pts = $derived.by(() => {
		if (!etats?.length) return null;
		const raw = etats.map((e) => ({ point: e.point, ...coords(e) }));
		const valid = raw.filter((p) => p.x != null && p.y != null);
		return valid.length >= 2 ? valid : null;
	});

	let segmentActif = $derived(segments.find((s) => s.label === composant));
	let typeInfo = $derived(TYPES.find((t) => t.id === type));

	let cycleTrace = $derived(
		pts
			? {
					x: pts.map((p) => p.x),
					y: pts.map((p) => p.y),
					text: pts.map((p) => p.point),
					mode: 'lines+markers+text',
					name: 'Cycle R718',
					line: { color: '#71717a', width: 2 },
					marker: { color: 'rgba(250,250,250,0.95)', size: 8, symbol: 'circle' },
					textposition: 'top right',
					textfont: { color: '#fafafa', size: 10 }
				}
			: null
	);

	let segmentTrace = $derived.by(() => {
		if (!pts || !segmentActif) return null;
		const a = pts.find((p) => p.point === segmentActif.from);
		const b = pts.find((p) => p.point === segmentActif.to);
		if (!a || !b) return null;
		return {
			x: [a.x, b.x],
			y: [a.y, b.y],
			mode: 'lines',
			name: segmentActif.label,
			line: { color: 'rgba(250,250,250,0.95)', width: 4 },
			showlegend: false,
			hoverinfo: 'skip'
		};
	});

	let plotData = $derived(
		cycleTrace ? (segmentTrace ? [cycleTrace, segmentTrace] : [cycleTrace]) : []
	);

	let plotLayout = $derived({
		margin: { t: 16, r: 12, b: 44, l: 56 },
		showlegend: true,
		xaxis: {
			title: { text: typeInfo?.xLabel ?? '', font: { size: 10, color: '#64748b' } },
			type: typeInfo?.xLog ? 'log' : '-'
		},
		yaxis: {
			title: { text: typeInfo?.yLabel ?? '', font: { size: 10, color: '#64748b' } },
			type: typeInfo?.yLog ? 'log' : '-'
		}
	});
</script>

<div class="flex h-full flex-col rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
		<h3 class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">Diagramme thermodynamique</h3>
		<div class="flex flex-wrap gap-2">
			<select
				bind:value={type}
				class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2 py-1 text-xs text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none"
			>
				{#each TYPES as t (t.id)}
					<option value={t.id}>{t.label}</option>
				{/each}
			</select>
			{#if segments.length}
				<select
					bind:value={composant}
					class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2 py-1 text-xs text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none"
				>
					<option value="">Cycle complet</option>
					{#each segments as s (s.label)}
						<option value={s.label}>{s.label}</option>
					{/each}
				</select>
			{/if}
		</div>
	</div>

	{#if pts}
		<div class="min-h-[280px] flex-1">
			<PlotlyChart data={plotData} layout={plotLayout} />
		</div>
		<div class="mt-2 flex flex-wrap items-center gap-4 text-[10px] text-[var(--text-muted)]">
			<span class="flex items-center gap-1.5"><span class="h-1.5 w-3 rounded-full bg-[#71717a]"></span> Cycle</span>
			{#if segmentActif}
				<span class="flex items-center gap-1.5"><span class="h-1.5 w-3 rounded-full bg-[var(--text-primary)]"></span> {segmentActif.label}</span>
			{/if}
		</div>
	{:else}
		<p class="flex-1 py-16 text-center text-sm text-[var(--text-muted)]">
			Non disponible — nécessite les points d'état du cycle. Lancez une campagne.
		</p>
	{/if}
</div>