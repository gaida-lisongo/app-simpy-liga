<script>
	import { onMount } from 'svelte';
	import { getCircuitConfig } from '$lib/api.js';
	import { apiCircuitOf, SORTIE_LABELS } from '$lib/constants.js';
	import { simulationStore } from '$lib/stores/simulationStore.svelte.js';

	import Badge from '$lib/components/ui/Badge.svelte';
	import SimulationPanel from '$lib/components/SimulationPanel.svelte';
	import ParametresPanel from '$lib/components/ParametresPanel.svelte';
	import KpiCardSpark from '$lib/components/KpiCardSpark.svelte';
	import ThermoDiagramPanel from '$lib/components/ThermoDiagramPanel.svelte';
	import EtatsCycleTable from '$lib/components/EtatsCycleTable.svelte';
	import BilanEnergetique from '$lib/components/BilanEnergetique.svelte';
	import McDonutChart from '$lib/components/McDonutChart.svelte';
	import HistogrammeTabs from '$lib/components/HistogrammeTabs.svelte';
	import RawDataTable from '$lib/components/RawDataTable.svelte';

	/**
	 * @type {{ circuit: { slug: string, id: string, titre: string, accent: string,
	 *   sousTitre: string, etats: string, composants: string[], kpis: string[],
	 *   segments: { label: string, from: string, to: string }[] } }}
	 */
	let { circuit } = $props();

	let apiCircuit = $derived(apiCircuitOf(circuit));
	let st = $derived(simulationStore.state[circuit.slug]);

	let params = $state(/** @type {any[]} */ ([]));
	let nIterations = $state(10000);
	let seed = $state(42);
	let methode = $state('LHS');

	let configLoading = $state(true);
	let configError = $state('');

	async function loadConfig() {
		configLoading = true;
		configError = '';
		try {
			const cfg = await getCircuitConfig(apiCircuit);
			params = cfg?.parametres_incertains ?? [];
		} catch (/** @type {any} */ e) {
			configError = e?.message ?? 'Erreur de chargement de la configuration.';
		} finally {
			configLoading = false;
		}
	}

	onMount(() => {
		simulationStore.hydrate();
		loadConfig();
	});

	async function lancerCampagne() {
		try {
			await simulationStore.run(circuit.slug, {
				circuit: apiCircuit,
				parametres_incertains: params,
				simulation: { N_iterations: nIterations, seed, echantillonnage: methode }
			});
		} catch {
			// L'erreur est déjà portée par le store (st.error) et affichée dans SimulationPanel.
		}
	}

	let tauxRejet = $derived(st.result?.resultats?.taux_rejet_non_physique_pct ?? null);
	let tirages = $derived(/** @type {Record<string, number>[]} */ (st.result?.resultats?.tirages ?? []));
	let principal = $derived(circuit.kpis[0]);
	let principalInfo = $derived(SORTIE_LABELS[principal] ?? { label: principal, tooltip: '' });

	/** @param {string} key */
	function serieDe(key) {
		return tirages.map((t) => t[key]).filter((v) => typeof v === 'number');
	}

	/** @param {string | undefined} campagneId */
	function formatDate(campagneId) {
		const m = /^camp_(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/.exec(campagneId ?? '');
		if (!m) return null;
		return `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}:${m[6]} UTC`;
	}
</script>

<div style="--accent: {circuit.accent}; --accent-soft: {circuit.accent}22; --circuit-accent: {circuit.accent};">
	<!-- SECTION 1 — Fil d'ariane -->
	<header class="mb-6">
		<p class="text-xs text-[var(--text-muted)]">SimPy-LIGA / Circuit {circuit.titre} — {circuit.id}</p>
		<div class="mt-1 flex flex-wrap items-center gap-2">
			<Badge tone="accent">{circuit.id}</Badge>
			<h1 class="text-2xl font-semibold text-[var(--text-primary)]">{circuit.titre}</h1>
		</div>
		<p class="mt-1 text-sm text-[var(--text-secondary)]">{circuit.sousTitre} · états {circuit.etats}</p>
		<div class="mt-3 flex flex-wrap gap-1.5">
			{#each circuit.composants as c (c)}
				<span class="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--text-secondary)]">
					{c}
				</span>
			{/each}
			{#if st.result}
				<span class="rounded-full border border-[var(--border)] px-2.5 py-1 text-xs text-[var(--text-muted)]">
					N={st.result.simulation?.N_iterations}
				</span>
				<span class="rounded-full border border-[var(--border)] px-2.5 py-1 text-xs text-[var(--text-muted)]">
					{st.result.simulation?.echantillonnage}
				</span>
				{#if formatDate(st.result.campagne_id)}
					<span class="rounded-full border border-[var(--border)] px-2.5 py-1 text-xs text-[var(--text-muted)]">
						{formatDate(st.result.campagne_id)}
					</span>
				{/if}
			{/if}
		</div>
	</header>

	{#if st.result}
		<!-- SECTION 2 — 4 KPI cards -->
		<section class="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
			{#each circuit.kpis as key (key)}
				{@const info = SORTIE_LABELS[key] ?? { label: key, tooltip: '' }}
				<KpiCardSpark
					label={info.label}
					tooltip={info.tooltip}
					stat={st.result.resultats.statistiques[key]}
					serie={serieDe(key)}
					accent={circuit.accent}
					decimals={key === 'm_dot_pri' || key === 'm_dot_sec' ? 5 : 3}
				/>
			{/each}
		</section>

		<!-- SECTION 3 (diagramme) + 4A/4B (donut + histogrammes) -->
		<section class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
			<div class="flex flex-col gap-4">
				<ThermoDiagramPanel etats={st.result.resultats.etats_cycle} segments={circuit.segments} accent={circuit.accent} />
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<EtatsCycleTable etats={st.result.resultats.etats_cycle} ordre={circuit.etats} />
					<BilanEnergetique bilan={st.result.resultats.bilan_energetique} statistiques={st.result.resultats.statistiques} />
				</div>
			</div>
			<div class="flex flex-col gap-4">
				<McDonutChart
					label={principalInfo.label}
					serie={serieDe(principal)}
					stat={st.result.resultats.statistiques[principal]}
					accent={circuit.accent}
					convergence={st.result.resultats.convergence}
					tauxRejetPct={tauxRejet}
				/>
				<HistogrammeTabs {params} {tirages} />
			</div>
		</section>

		<!-- SECTION 5 — données brutes -->
		<section class="mb-6">
			<RawDataTable {tirages} campagneId={st.result.campagne_id} />
		</section>
	{:else}
		<p class="mb-6 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-6 text-center text-sm text-[var(--text-muted)]">
			Aucune campagne pour ce circuit — configurez et lancez une simulation ci-dessous.
		</p>
	{/if}

	<!-- SECTION 6 — panneau simulation -->
	<section class="grid grid-cols-1 gap-4 lg:grid-cols-2">
		<SimulationPanel
			bind:nIterations
			bind:seed
			bind:methode
			running={st.loading}
			error={st.error}
			onLancer={lancerCampagne}
		/>
		<ParametresPanel {params} loading={configLoading} error={configError} />
	</section>
</div>
