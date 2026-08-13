<script>
	import SolaireKpiCard from '$lib/components/solaire/SolaireKpiCard.svelte';
	import { SOLAIRE_KPI_LABELS } from '$lib/utils/labels.js';

	/**
	 * Section 2 — 4 métriques clés du circuit solaire (COP, mu, Q_gen, eta_ex).
	 * Skeletons animés si aucune campagne n'est chargée. Q_gen est récupéré depuis
	 * bilan_energetique si absent des statistiques (le défaut sorties_suivies de
	 * l'API ne l'inclut pas toujours).
	 * @type {{ result: any | null }}
	 */
	let { result } = $props();

	const KEYS = ['COP', 'mu', 'Q_gen', 'eta_ex'];
	const DECIMALS = { COP: 3, mu: 3, Q_gen: 2, eta_ex: 3 };

	let stats = $derived(result?.resultats?.statistiques ?? null);
	let bilan = $derived(result?.resultats?.bilan_energetique ?? null);
	let tirages = $derived(result?.resultats?.tirages ?? []);

	/** @param {string} key */
	function serieDe(key) {
		if (key === 'Q_gen') {
			const vals = tirages.map((t) => t['Q_gen']).filter((v) => typeof v === 'number');
			if (vals.length) return vals;
			return tirages.map((t) => t['Q_gen']).filter((v) => typeof v === 'number');
		}
		return tirages.map((t) => t[key]).filter((v) => typeof v === 'number');
	}

	/** @param {string} key */
	function statDe(key) {
		if (stats?.[key]) return stats[key];
		if (key === 'Q_gen' && bilan?.Q_gen != null) {
			return { moyenne: bilan.Q_gen, ecart_type: 0, IC95: null };
		}
		return null;
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
			stat={statDe(key)}
			serie={serieDe(key)}
			decimals={DECIMALS[key]}
			index={i}
		/>
	{/each}
</section>