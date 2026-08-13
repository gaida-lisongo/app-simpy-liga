<script>
	import PlotlyChart from '$lib/components/ui/PlotlyChart.svelte';
	import { PARAM_INFO, LOI_LABELS } from '$lib/constants.js';

	/**
	 * Histogramme réel (pas une approximation) construit depuis resultats.tirages —
	 * une tab par paramètre incertain variable du circuit. Rendu via Plotly.js.
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

	let plotData = $derived([
		{
			x: vals,
			type: 'histogram',
			name: 'Distribution simulée',
			marker: { color: '#4ade80', opacity: 0.85 },
			histnorm: 'probability density'
		}
	]);

	let plotLayout = $derived({
		margin: { t: 8, r: 8, b: 40, l: 44 },
		bargap: 0.03,
		showlegend: false,
		xaxis: {
			title: {
				text: PARAM_INFO[paramActif?.nom]?.label ?? paramActif?.symbole ?? '',
				font: { size: 10, color: '#64748b' }
			}
		},
		yaxis: {
			title: { text: 'Densité', font: { size: 10, color: '#64748b' } }
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
					class="rounded-full border px-2.5 py-1 text-xs font-medium transition-colors {actif === p.nom
						? 'border-[#4ade80] bg-[#4ade8022] text-[#4ade80]'
						: 'border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-secondary)]'}"
				>
					{p.symbole}
				</button>
			{/each}
		</div>

		{#if vals.length >= 2}
			<div style="height:220px">
				<PlotlyChart data={plotData} layout={plotLayout} />
			</div>
			<p class="mt-2 text-[10px] text-[var(--text-muted)]">
				{PARAM_INFO[paramActif?.nom]?.label ?? paramActif?.symbole} — {LOI_LABELS[paramActif?.loi] ?? paramActif?.loi} · {vals.length} tirages valides
			</p>
		{:else}
			<p class="py-10 text-center text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
		{/if}
	{/if}
</div>