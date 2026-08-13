<script>
	import { fly, fade } from 'svelte/transition';
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';

	/**
	 * Panneau diagramme thermodynamique du circuit solaire (R718). Trois paires
	 * d'axes (T-s, P-h, P-s) et deux composants (vue d'ensemble du cycle 7→8,
	 * générateur entrée → sortie). Dôme de saturation illustratif + segment
	 * mis en évidence par une zone rectangulaire. Rendu Plotly via le wrapper.
	 * @type {{
	 *   etats: { point: string, T?: number, P?: number, h?: number, s?: number, x?: number }[] | undefined
	 * }}
	 */
	let { etats } = $props();

	const TYPES = [
		{
			id: 'Ts',
			label: 'Température-Entropie',
			xKey: 's',
			yKey: 'T',
			xLabel: 'Entropie (kJ/kg·K)',
			yLabel: 'Température (°C)',
			yLog: false
		},
		{
			id: 'Ph',
			label: 'Pression-Enthalpie',
			xKey: 'h',
			yKey: 'P',
			xLabel: 'Enthalpie (kJ/kg)',
			yLabel: 'Pression (bar)',
			yLog: true
		},
		{
			id: 'Ps',
			label: 'Pression-Entropie',
			xKey: 's',
			yKey: 'P',
			xLabel: 'Entropie (kJ/kg·K)',
			yLabel: 'Pression (bar)',
			yLog: true
		}
	];

	const COMPOSANTS = [
		{ id: 'overview', label: "Vue d'ensemble" },
		{ id: 'generateur', label: 'Générateur (entrée → sortie)' }
	];

	// Dôme de saturation R718 (illustratif) — ancrages fournis par le cycle.
	// Liquide saturé (s_f, h_f, T, P) et vapeur saturée (s_g, h_g, T, P) approchés.
	const SAT_LIQ = [
		{ T: -10, P: 0.0029, hf: -42, sf: 0.296 },
		{ T: 0, P: 0.0061, hf: 0, sf: 0.367 },
		{ T: 35, P: 0.056, hf: 147, sf: 0.504 },
		{ T: 95, P: 0.846, hf: 398, sf: 1.25 }
	];
	const SAT_VAP = [
		{ T: 95, P: 0.846, hg: 2668, sg: 7.42 },
		{ T: 10, P: 0.0123, hg: 2519, sg: 8.75 },
		{ T: -10, P: 0.0029, hg: 2485, sg: 9.1 }
	];

	let type = $state('Ts');
	let composant = $state('overview');

	let typeInfo = $derived(TYPES.find((t) => t.id === type));

	/** Coordonnées (x,y) d'un état selon la paire d'axes courante ; null si invalide. */
	function coordOf(
		/** @type {{ point: string, T?: number, P?: number, h?: number, s?: number, x?: number } | undefined} */ e,
		/** @type {'s'|'h'} */ xKey,
		/** @type {'T'|'P'} */ yKey
	) {
		if (!e) return null;
		const x = e[xKey];
		const y = e[yKey];
		if (x == null || y == null) return null;
		if (yKey === 'P' && y <= 0) return null;
		return { x, y };
	}

	let pt7 = $derived(etats?.find((e) => String(e.point) === '7'));
	let pt8 = $derived(etats?.find((e) => String(e.point) === '8'));
	let c7 = $derived(pt7 && typeInfo ? coordOf(pt7, typeInfo.xKey, typeInfo.yKey) : null);
	let c8 = $derived(pt8 && typeInfo ? coordOf(pt8, typeInfo.xKey, typeInfo.yKey) : null);
	let hasData = $derived(!!(c7 && c8));

	let satTraces = $derived.by(() => {
		if (!typeInfo) return [];
		const { xKey, yKey } = typeInfo;
		const liqKey = xKey === 'h' ? 'hf' : 'sf';
		const vapKey = xKey === 'h' ? 'hg' : 'sg';
		const ySat = yKey === 'P' ? 'P' : 'T';
		return [
			{
				x: SAT_LIQ.map((p) => p[liqKey]),
				y: SAT_LIQ.map((p) => p[ySat]),
				mode: 'lines',
				name: 'Saturation R718',
				line: { color: '#52525b', width: 1.5, dash: 'dot' },
				showlegend: true,
				hoverinfo: 'skip'
			},
			{
				x: SAT_VAP.map((p) => p[vapKey]),
				y: SAT_VAP.map((p) => p[ySat]),
				mode: 'lines',
				name: 'Saturation R718 (vapeur)',
				line: { color: '#52525b', width: 1.5, dash: 'dot' },
				showlegend: false,
				hoverinfo: 'skip'
			}
		];
	});

	let cycleTrace = $derived.by(() => {
		if (!hasData || !c7 || !c8 || composant !== 'overview') return null;
		return {
			x: [c7.x, c8.x, c7.x],
			y: [c7.y, c8.y, c7.y],
			text: ['7', '8', ''],
			mode: 'lines+markers+text',
			name: 'Cycle solaire',
			line: { color: '#06c167', width: 2 },
			marker: { color: '#06c167', size: [8, 8, 0], symbol: 'circle' },
			textposition: 'top right',
			textfont: { color: '#06c167', size: 9 },
			showlegend: true
		};
	});

	let generateurTrace = $derived.by(() => {
		if (!hasData || !c7 || !c8 || composant !== 'generateur') return null;
		return {
			x: [c7.x, c8.x],
			y: [c7.y, c8.y],
			text: ['7', '8'],
			mode: 'lines+markers+text',
			name: 'Générateur (7→8)',
			line: { color: '#06c167', width: 2.5 },
			marker: { color: '#06c167', size: 8, symbol: 'circle' },
			textposition: 'top right',
			textfont: { color: '#06c167', size: 9 },
			showlegend: true
		};
	});

	let plotData = $derived(
		[...satTraces, cycleTrace, generateurTrace].filter(
			(/** @type {any} */ t) => t !== null
		)
	);

	let shapes = $derived.by(() => {
		if (composant !== 'generateur' || !c7 || !c8 || !typeInfo) return [];
		const xs = [c7.x, c8.x];
		const ys = [c7.y, c8.y];
		const x0 = Math.min(...xs);
		const x1 = Math.max(...xs);
		let y0;
		let y1;
		if (typeInfo.yLog) {
			const pn = Math.min(...ys) || 0.001;
			const px = Math.max(...ys) || 0.001;
			y0 = pn * 0.6;
			y1 = px * 1.6;
		} else {
			const span = Math.max(1, Math.max(...ys) - Math.min(...ys));
			y0 = Math.min(...ys) - span * 0.15;
			y1 = Math.max(...ys) + span * 0.15;
		}
		return [
			{
				type: 'rect',
				x0,
				x1,
				y0,
				y1,
				fillcolor: 'rgba(6,193,103,0.07)',
				line: { width: 0 },
				layer: 'below'
			}
		];
	});

	let annotations = $derived.by(() => {
		if (!c7 || !c8) return [];
		/** @type {any[]} */
		const anns = [
			{
				x: c7.x,
				y: c7.y,
				text: 'Entrée générateur',
				showarrow: true,
				arrowhead: 2,
				arrowsize: 0.6,
				arrowwidth: 1,
				arrowcolor: '#a1a1aa',
				ax: -32,
				ay: -28,
				font: { color: '#a1a1aa', size: 9 },
				bgcolor: 'rgba(24,24,27,0.85)',
				bordercolor: '#27272a',
				borderwidth: 1
			},
			{
				x: c8.x,
				y: c8.y,
				text: 'Sortie générateur',
				showarrow: true,
				arrowhead: 2,
				arrowsize: 0.6,
				arrowwidth: 1,
				arrowcolor: '#a1a1aa',
				ax: 32,
				ay: -28,
				font: { color: '#a1a1aa', size: 9 },
				bgcolor: 'rgba(24,24,27,0.85)',
				bordercolor: '#27272a',
				borderwidth: 1
			}
		];
		if (composant === 'generateur') {
			anns.push({
				x: (c7.x + c8.x) / 2,
				y: (c7.y + c8.y) / 2,
				text: 'Générateur — vaporisation isobare',
				showarrow: false,
				font: { color: '#06c167', size: 10 },
				bgcolor: 'rgba(9,9,11,0.65)',
				bordercolor: 'rgba(250,250,250,0.12)',
				borderwidth: 1
			});
		}
		return anns;
	});

	let plotLayout = $derived({
		margin: { t: 16, r: 16, b: 44, l: 52 },
		showlegend: false,
		xaxis: {
			title: { text: typeInfo?.xLabel ?? '', font: { size: 10, color: '#a1a1aa' } },
			type: '-'
		},
		yaxis: {
			title: { text: typeInfo?.yLabel ?? '', font: { size: 10, color: '#a1a1aa' } },
			type: typeInfo?.yLog ? 'log' : '-'
		},
		shapes,
		annotations
	});
</script>

<div
	class="flex h-full flex-col rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4"
>
	<div class="mb-3 flex flex-wrap items-start justify-between gap-3">
		<div class="min-w-0">
			<h3
				class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]"
			>
				Diagramme thermodynamique
			</h3>
			<p class="mt-0.5 text-xs text-[var(--text-muted)]">
				Cycle R718 · Circuit solaire (source externe)
			</p>
		</div>
		<div class="flex flex-wrap items-center gap-2">
			<label class="flex items-center gap-1.5">
				<span class="text-[10px] uppercase tracking-wide text-[var(--text-muted)]"
					>Type</span
				>
				<select
					bind:value={type}
					class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2 py-1.5 text-xs text-[var(--text-primary)] transition-colors duration-150 hover:border-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none"
					aria-label="Type de diagramme"
				>
					{#each TYPES as t (t.id)}
						<option value={t.id}>{t.label}</option>
					{/each}
				</select>
			</label>
			<label class="flex items-center gap-1.5">
				<span class="text-[10px] uppercase tracking-wide text-[var(--text-muted)]"
					>Composant</span
				>
				<select
					bind:value={composant}
					class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2 py-1.5 text-xs text-[var(--text-primary)] transition-colors duration-150 hover:border-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none"
					aria-label="Composant du cycle"
				>
					{#each COMPOSANTS as c (c.id)}
						<option value={c.id}>{c.label}</option>
					{/each}
				</select>
			</label>
		</div>
	</div>

	{#if hasData}
		<div class="flex-1 min-h-[340px]" transition:fade={{ duration: 180 }}>
			<PlotlyChart data={plotData} layout={plotLayout} className="h-full w-full" />
		</div>
		<div
			class="mt-2 flex flex-wrap items-center gap-4 text-[10px] text-[var(--text-muted)]"
		>
			<span class="flex items-center gap-1.5">
				<span class="h-1.5 w-3 rounded-full bg-[var(--text-primary)]"></span>
				Cycle R718
			</span>
			<span class="flex items-center gap-1.5">
				<span
					class="inline-block h-0 w-4 border-t-2 border-dotted border-[#52525b]"
				></span>
				Saturation
			</span>
			{#if composant === 'generateur'}
				<span class="flex items-center gap-1.5">
					<span class="h-1.5 w-3 rounded-full bg-[var(--text-primary)]"></span>
					Générateur (7→8)
				</span>
			{/if}
		</div>
	{:else}
		<div
			class="flex flex-1 flex-col items-center justify-center gap-3 py-12 text-center"
			transition:fly={{ y: 10, duration: 200 }}
		>
			<div
				class="h-10 w-10 rounded-full bg-[var(--surface-raised)] animate-pulse"
				aria-hidden="true"
			></div>
			<p class="text-sm text-[var(--text-muted)]">
				Aucun point d'état — lancez une campagne.
			</p>
		</div>
	{/if}
</div>