<script>
	import SolaireKpiCard from '$lib/components/solaire/SolaireKpiCard.svelte';
	import { SOLAIRE_KPI_LABELS } from '$lib/utils/labels.js';

	/**
	 * Section 2 — 4 métriques clés du circuit solaire (STR, eta_th, eta_ex, Q_utile).
	 * Skeletons animés si aucune campagne n'est chargée.
	 * @type {{ result: any | null }}
	 */
	let { result } = $props();

	const KEYS = ['STR', 'eta_th', 'eta_ex', 'Q_utile'];
	const DECIMALS = { STR: 3, eta_th: 3, eta_ex: 3, Q_utile: 2 };

	let stats = $derived(result?.resultats?.statistiques ?? null);
	let tirages = $derived(result?.resultats?.tirages ?? []);

	/** @param {string} key */
	function serieDe(key) {
		return tirages.map((t) => t[key]).filter((v) => typeof v === 'number');
	}
</script>

<section class="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
	{#each KEYS as key, i (key)}
		{@const info = SOLAIRE_KPI_LABELS[key]}
		<SolaireKpiCard
			label={info.label}
			unite={info.unite}
			tooltip={info.tooltip}
			litterature={info.litterature}
			stat={stats?.[key] ?? null}
			serie={serieDe(key)}
			decimals={DECIMALS[key]}
			index={i}
		/>
	{/each}
</section>