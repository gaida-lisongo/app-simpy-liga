<script>
	import { onMount } from 'svelte';
	import { getCircuitConfig } from '$lib/api.js';
	import { simulationStore } from '$lib/stores/simulationStore.svelte.js';

	import SimulationDrawer from '$lib/components/features/SimulationDrawer.svelte';
	import SolaireBreadcrumb from '$lib/components/solaire/SolaireBreadcrumb.svelte';
	import SolaireKpiGrid from '$lib/components/solaire/SolaireKpiGrid.svelte';
	import SolaireDiagramme from '$lib/components/solaire/SolaireDiagramme.svelte';
	import SolaireEtatCycle from '$lib/components/solaire/SolaireEtatCycle.svelte';
	import SolaireDonneesBrutes from '$lib/components/solaire/SolaireDonneesBrutes.svelte';
	import McDonutChart from '$lib/components/McDonutChart.svelte';
	import DensityTabs from '$lib/components/DensityTabs.svelte';
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
		try {
			await simulationStore.run('solaire', {
				circuit: 'solaire',
				parametres_incertains: params,
				simulation: { N_iterations: nIterations, seed, echantillonnage: methode }
			});
		} catch {
			// erreur portée par le store
		}
	}

	let tirages = $derived(st.result?.resultats?.tirages ?? []);
	let etatsCycle = $derived(st.result?.resultats?.etats_cycle ?? undefined);
	let stats = $derived(st.result?.resultats?.statistiques ?? null);
	let convergence = $derived(st.result?.resultats?.convergence ?? null);
	let tauxRejet = $derived(st.result?.resultats?.taux_rejet_non_physique_pct ?? null);
	let principalSerie = $derived(tirages.map((t) => t['COP']).filter((v) => typeof v === 'number'));
</script>

<div style="--accent: {circuit.accent}; --accent-soft: {circuit.accent}22; --circuit-accent: {circuit.accent};">
	<!-- SECTION 1 — Fil d'ariane + bouton Simuler -->
	<header class="mb-6 flex flex-wrap items-start justify-between gap-3">
		<SolaireBreadcrumb result={st.result} />
		<button
			type="button"
			onclick={() => (drawerOpen = true)}
			disabled={st.loading}
			class="mt-1 flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] transition-all duration-200 hover:scale-[1.01] hover:border-[var(--text-primary)] active:scale-[0.99] disabled:pointer-events-none disabled:opacity-60"
		>
			<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M5 3.5v9l7-4.5z" /></svg>
			Simuler
		</button>
	</header>

	{#if st.result}
		<!-- SECTION 2 — 4 KPI -->
		<SolaireKpiGrid result={st.result} />

		<!-- SECTION 3 + 4 — diagramme thermo & état du cycle (50/50) + donut MC + densités VA -->
		<section class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2 lg:items-stretch">
			<!-- Gauche : diagramme thermo -->
			<div class="flex min-h-[420px] flex-col">
				<SolaireDiagramme etats={etatsCycle} />
			</div>
			<!-- Droite : carte valeurs numériques des états (côte à cote) -->
			<div class="flex min-h-[420px] flex-col">
				<SolaireEtatCycle etats={etatsCycle} />
			</div>
		</section>

		<!-- SECTION 4 — donut MC + densités VA (50/50) -->
		<section class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2 lg:items-stretch">
			<McDonutChart
				label={circuit.titre}
				serie={principalSerie}
				stat={stats?.['COP'] ?? null}
				accent={circuit.accent}
				{convergence}
				tauxRejetPct={tauxRejet}
			/>
			<DensityTabs {params} {tirages} />
		</section>

		<!-- SECTION 5 — données brutes (pleine largeur) -->
		<section class="mb-6">
			<SolaireDonneesBrutes {tirages} campagneId={st.result.campagne_id} />
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