<script>
	import { onMount } from 'svelte';
	import { getCircuitConfig } from '$lib/api.js';
	import { apiCircuitOf, SORTIE_LABELS } from '$lib/constants.js';
	import { simulationStore } from '$lib/stores/simulationStore.svelte.js';

	import Badge from '$lib/components/ui/Badge.svelte';
	import SimulationDrawer from '$lib/components/features/SimulationDrawer.svelte';
	import HistorySelector from '$lib/components/HistorySelector.svelte';
	import KpiCardSpark from '$lib/components/KpiCardSpark.svelte';
	import ThermoDiagramPanel from '$lib/components/ThermoDiagramPanel.svelte';
	import EtatsCycleTable from '$lib/components/EtatsCycleTable.svelte';
	import McDonutChart from '$lib/components/McDonutChart.svelte';
	import DensityTabs from '$lib/components/DensityTabs.svelte';
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
	let drawerOpen = $state(false);

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
		const n = Number(nIterations);
		if (!Number.isInteger(n) || n < 1 || n > 10000) {
			st.error = `Nombre d'itérations invalide (${nIterations ?? 'vide'}) — entrez un entier entre 1 et 10000.`;
			return;
		}
		try {
			await simulationStore.run(circuit.slug, {
				circuit: apiCircuit,
				parametres_incertains: params,
				simulation: { N_iterations: n, seed, echantillonnage: methode }
			});
		} catch {
			// L'erreur est déjà portée par le store (st.error) et affichée dans le drawer.
		}
	}

	let tauxRejet = $derived(st.result?.resultats?.taux_rejet_non_physique_pct ?? null);
	let tirages = $derived(/** @type {Record<string, number>[]} */ (st.result?.resultats?.tirages ?? []));
	let etatsCycle = $derived(st.result?.resultats?.etats_cycle ?? undefined);
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
	<!-- SECTION 1 — Fil d'ariane + bouton Simuler -->
	<header class="mb-6">
		<p class="text-xs text-[var(--text-muted)]">SimPy-LIGA / Circuit {circuit.titre} — {circuit.id}</p>
		<div class="mt-1 flex flex-wrap items-center justify-between gap-3">
			<div class="flex flex-wrap items-center gap-2">
				<Badge tone="accent">{circuit.id}</Badge>
				<h1 class="text-2xl font-semibold text-[var(--text-primary)]">{circuit.titre}</h1>
			</div>
			<div class="flex flex-wrap items-center gap-2">
				<HistorySelector slug={circuit.slug} campaigns={st.campaigns} />
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

		<!-- SECTION 3 — diagramme thermo ( gauche) + donut + histogrammes (droite) -->
		<section class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-stretch">
			<div class="flex min-h-[420px] flex-col gap-4">
				<ThermoDiagramPanel etats={etatsCycle} segments={circuit.segments} accent={circuit.accent} />
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
				<DensityTabs {params} {tirages} />
			</div>
		</section>

		<!-- SECTION 4 — données brutes (gauche) + états du cycle dynamisés (droite) -->
		<section class="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
			<RawDataTable {tirages} campagneId={st.result.campagne_id} />
			<EtatsCycleTable etats={etatsCycle} ordre={circuit.etats} accent={circuit.accent} />
		</section>
	{:else}
		<div class="mb-6 flex flex-col items-center gap-4 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-10 text-center">
			<div class="h-12 w-12 rounded-full bg-[var(--accent-soft)] animate-pulse" aria-hidden="true"></div>
			<p class="text-sm text-[var(--text-muted)]">
				Aucune campagne pour ce circuit — ouvrez le panneau de simulation pour configurer et lancer.
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