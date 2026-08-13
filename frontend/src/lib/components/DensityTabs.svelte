<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';
	import { PARAM_INFO, LOI_LABELS } from '$lib/constants.js';
	import { PARAM_LABELS } from '$lib/utils/labels.js';

	/**
	 * Densité par noyau (KDE gaussien) des variables aléatoires d'une campagne.
	 * Affiche une **courbe pleine** (estimateur de densité lissé) plutôt qu'un
	 * histogramme à bâtons — adapté aux variables continues issues du tirage LHS.
	 * Une tab par paramètre incertain variable du circuit.
	 * @type {{ params: any[], tirages: Record<string, number>[] }}
	 */
	let { params, tirages } = $props();

	let variables = $derived(params.filter((p) => p.loi !== 'fixe'));
	let actif = $state(/** @type {string | null} */ (null));
	$effect(() => {
		if (!actif && variables.length) actif = variables[0].nom;
	});

	let paramActif = $derived(variables.find((p) => p.nom === actif));

	let vals = $derived(
		actif
			? tirages.map((t) => t[actif]).filter((v) => typeof v === 'number' && Number.isFinite(v))
			: []
	);

	// KDE gaussien (règle de Silverman pour la largeur de bande).
	let density = $derived.by(() => {
		const n = vals.length;
		if (n < 2) return null;
		const lo = Math.min(...vals);
		const hi = Math.max(...vals);
		const range = hi - lo || 1;
		const pad = range * 0.15;
		const xMin = lo - pad;
		const xMax = hi + pad;
		const mean = vals.reduce((a, b) => a + b, 0) / n;
		const variance = vals.reduce((a, v) => a + (v - mean) ** 2, 0) / Math.max(1, n - 1);
		const sigma = Math.sqrt(variance) || range * 0.1 || 1;
		const h = 1.06 * sigma * Math.pow(n, -0.2);
		const grid = 200;
		const xs = new Array(grid);
		const ys = new Array(grid);
		const norm = 1 / (n * h * Math.sqrt(2 * Math.PI));
		for (let i = 0; i < grid; i++) {
			const x = xMin + (i / (grid - 1)) * (xMax - xMin);
			let y = 0;
			for (const v of vals) {
				const u = (x - v) / h;
				y += Math.exp(-0.5 * u * u);
			}
			y *= norm;
			xs[i] = x;
			ys[i] = y;
		}
		return { x: xs, y: ys };
	});

	let plotData = $derived(
		density
			? [
					{
						x: density.x,
						y: density.y,
						type: 'scatter',
						mode: 'lines',
						name: 'Densité estimée',
						fill: 'tozeroy',
						line: { color: '#06c167', width: 1.6, shape: 'spline', smoothing: 1.2 },
						fillcolor: 'rgba(6,193,103,0.16)',
						hovertemplate: '%{x:.3f}<br>densité %{y:.4f}<extra></extra>'
					}
				]
			: []
	);

	let plotLayout = $derived({
		margin: { t: 10, r: 12, b: 40, l: 44 },
		showlegend: false,
		xaxis: {
			title: {
				text: PARAM_INFO[paramActif?.nom]?.label ?? PARAM_LABELS[paramActif?.nom]?.label ?? paramActif?.symbole ?? '',
				font: { size: 10, color: '#71717a' }
			}
		},
		yaxis: {
			title: { text: 'Densité', font: { size: 10, color: '#71717a' } },
			zeroline: true
		}
	});
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h3 class="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Variables aléatoires
	</h3>

	{#if variables.length === 0}
		<p class="text-sm text-[var(--text-muted)]">Aucun paramètre incertain variable pour ce circuit.</p>
	{:else}
		<div class="mb-3 flex flex-wrap gap-1">
			{#each variables as p (p.nom)}
				<button
					type="button"
					onclick={() => (actif = p.nom)}
					class="rounded-full border px-2.5 py-1 text-xs font-medium transition-all duration-200 hover:scale-[1.02] {actif === p.nom
						? 'border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent)]'
						: 'border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-secondary)]'}"
				>
					{PARAM_LABELS[p.nom]?.label ?? p.symbole}
				</button>
			{/each}
		</div>

		{#if density}
			<div style="height:220px">
				<PlotlyChart data={plotData} layout={plotLayout} />
			</div>
			<p class="mt-2 text-[10px] text-[var(--text-muted)]">
				{PARAM_LABELS[paramActif?.nom]?.label ?? PARAM_INFO[paramActif?.nom]?.label ?? paramActif?.symbole} — {LOI_LABELS[paramActif?.loi] ?? paramActif?.loi} · {vals.length} tirages · KDE gaussien (Silverman)
			</p>
		{:else}
			<div class="flex flex-col items-center gap-2 py-12 text-center">
				<div class="h-8 w-8 rounded-full bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
				<p class="text-sm text-[var(--text-muted)]">Pas assez de tirages — lancez une campagne.</p>
			</div>
		{/if}
	{/if}
</div>