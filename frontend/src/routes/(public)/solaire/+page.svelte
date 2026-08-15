<script>
	import { onMount } from 'svelte';
	import { getCircuitConfig } from '$lib/api.js';
	import { simulationStore } from '$lib/stores/simulationStore.svelte.js';

	import SimulationDrawer from '$lib/components/features/SimulationDrawer.svelte';
	import SolaireBreadcrumb from '$lib/components/solaire/SolaireBreadcrumb.svelte';
	import SolaireKpiGrid from '$lib/components/solaire/SolaireKpiGrid.svelte';
	import SolaireDiagramme from '$lib/components/solaire/SolaireDiagramme.svelte';
	import SolaireEtatCycle from '$lib/components/solaire/SolaireEtatCycle.svelte';
	import SolaireProfilTube from '$lib/components/solaire/SolaireProfilTube.svelte';
	import SolaireCourbesCPC from '$lib/components/solaire/SolaireCourbesCPC.svelte';
	import SolaireSankey from '$lib/components/solaire/SolaireSankey.svelte';
	import RawDataTable from '$lib/components/RawDataTable.svelte';
	import McDonutChart from '$lib/components/McDonutChart.svelte';
	import DensityTabs from '$lib/components/DensityTabs.svelte';
	import HistorySelector from '$lib/components/HistorySelector.svelte';
	import { CIRCUITS } from '$lib/constants.js';

	let circuit = $derived(CIRCUITS.find((c) => c.slug === 'solaire'));
	let st = $derived(simulationStore.state.solaire);

	let params = $state(/** @type {any[]} */ ([]));
	let nIterations = $state(10000);
	let seed = $state(42);
	let methode = $state('LHS');

	let configLoading = $state(true);
	let configError = $state('');
	let drawerOpen = $state(false);

	async function loadConfig() {
		configLoading = true;
		configError = '';
		try {
			const cfg = await getCircuitConfig('solaire');
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
		const n = Number(nIterations);
		if (!Number.isInteger(n) || n < 1 || n > 10000) {
			st.error = `Nombre d'itérations invalide (${nIterations ?? 'vide'}) — entrez un entier entre 1 et 10000.`;
			return;
		}
		try {
			await simulationStore.run('solaire', {
				circuit: 'solaire',
				parametres_incertains: params,
				simulation: { N_iterations: n, seed, echantillonnage: methode }
			});
		} catch {
			// erreur portée par le store
		}
	}

	let r = $derived(st.result?.resultats ?? null);
	let tirages = $derived(r?.tirages ?? []);
	let etatsCycle = $derived(r?.etats_cycle ?? undefined);
	let stats = $derived(r?.statistiques ?? null);
	let convergence = $derived(r?.convergence ?? null);
	let tauxRejet = $derived(r?.taux_rejet_non_physique_pct ?? null);
	let profilTube = $derived(r?.profil_tube ?? null);
	let courbesCpc = $derived(r?.courbes_cpc ?? null);
	let sankey = $derived(r?.sankey_solaire ?? null);
	let strSerie = $derived(tirages.map((t) => t['STR']).filter((v) => typeof v === 'number'));
</script>

<div style="--accent: {circuit.accent}; --accent-soft: {circuit.accent}22; --circuit-accent: {circuit.accent};">
	<!-- SECTION 1 — Fil d'ariane + bouton Simuler -->
	<header class="mb-6 flex flex-wrap items-start justify-between gap-3">
		<SolaireBreadcrumb result={st.result} />
		<div class="flex flex-wrap items-center gap-2 mt-1">
			<HistorySelector slug="solaire" campaigns={st.campaigns} />
			<button
				type="button"
				onclick={() => (drawerOpen = true)}
				disabled={st.loading}
				class="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] transition-all duration-200 hover:scale-[1.01] hover:border-[var(--text-primary)] active:scale-[0.99] disabled:pointer-events-none disabled:opacity-60"
			>
				<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M5 3.5v9l7-4.5z" /></svg>
				Simuler
			</button>
		</div>
	</header>

	{#if st.result}
		<!-- SECTION 2 — 4 KPI solaires -->
		<SolaireKpiGrid result={st.result} />

		<!-- SECTION 3 — diagramme thermo & état du cycle (50/50) -->
		<section class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2 lg:items-stretch">
			<div class="flex min-h-[420px] flex-col">
				<SolaireDiagramme etats={etatsCycle} />
			</div>
			<div class="flex min-h-[420px] flex-col">
				<SolaireEtatCycle etats={etatsCycle} />
			</div>
		</section>

		<!-- SECTION 4 — profil tube absorbeur + courbes CPC (50/50) -->
		<section class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2 lg:items-stretch">
			<SolaireProfilTube profil={profilTube} />
			<SolaireCourbesCPC courbes={courbesCpc} />
		</section>

		<!-- SECTION 5 — Sankey + donut MC (50/50) -->
		<section class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2 lg:items-stretch">
			<SolaireSankey sankey={sankey} />
			<McDonutChart
				label="STR"
				serie={strSerie}
				stat={stats?.['STR'] ?? null}
				accent={circuit.accent}
				{convergence}
				tauxRejetPct={tauxRejet}
			/>
		</section>

		<!-- SECTION 6 — densités VA + données brutes -->
		<section class="mb-6">
			<DensityTabs {params} {tirages} />
		</section>

		<section class="mb-6">
			<RawDataTable {tirages} campagneId={st.result.campagne_id} />
		</section>
	{:else}
		<div class="mb-6 flex flex-col items-center gap-4 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-10 text-center">
			<div class="h-12 w-12 rounded-full bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
			<p class="text-sm text-[var(--text-muted)]">
				Aucune campagne pour le circuit solaire — ouvrez le panneau de simulation pour configurer et lancer.
			</p>
			<button
				type="button"
				onclick={() => (drawerOpen = true)}
				class="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] transition-all duration-200 hover:scale-[1.01] hover:border-[var(--text-primary)]"
			>
				<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M5 3.5v9l7-4.5z" /></svg>
				Simuler
			</button>
		</div>
	{/if}
</div>

<SimulationDrawer
	bind:open={drawerOpen}
	{circuit}
	bind:nIterations
	bind:seed
	bind:methode
	{params}
	{configLoading}
	configError={configError}
	running={st.loading}
	progress={st.progress}
	error={st.error}
	onLancer={lancerCampagne}
/>