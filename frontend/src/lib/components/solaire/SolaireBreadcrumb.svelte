<script>
	import Badge from '$lib/components/ui/Badge.svelte';

	/**
	 * Fil d'ariane du circuit solaire (A4). Tags : article, N simulations,
	 * méthode, date dernière campagne (parsée depuis campagne_id).
	 * @type {{ result: any | null, apiStatus?: { statut: 'ok'|'error', coeur_physique_reel: boolean } | null }}
	 */
	let { result, apiStatus = null } = $props();

	let nIter = $derived(result?.simulation?.N_iterations ?? null);
	let methode = $derived(result?.simulation?.echantillonnage ?? 'LHS');

	/** @param {string | undefined} cid */
	function formatDate(cid) {
		const m = /^camp_(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/.exec(cid ?? '');
		if (!m) return null;
		return `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]} UTC`;
	}
	let dateCampagne = $derived(formatDate(result?.campagne_id));
</script>

<div class="mb-6">
	<p class="text-xs text-[var(--text-muted)]">SimPy-LIGA / Circuit Solaire — A4</p>
	<div class="mt-1 flex items-center gap-2">
		<Badge tone="accent">A4</Badge>
		<h1 class="text-2xl font-semibold text-[var(--text-primary)]">Circuit Solaire</h1>
	</div>
	<p class="mt-1 text-sm text-[var(--text-secondary)]">
		Source thermique de la machine — Concentrateur cylindro-parabolique
	</p>
	<div class="mt-3 flex flex-wrap gap-1.5">
		<span class="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--text-secondary)]">Article A4</span>
		<span class="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--text-secondary)]">
			{nIter !== null ? `${nIter.toLocaleString('fr-FR')} simulations` : '— simulations'}
		</span>
		<span class="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--text-secondary)]">Méthode {methode}</span>
		{#if dateCampagne}
			<span class="rounded-full border border-[var(--border)] bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--text-muted)]">{dateCampagne}</span>
		{/if}
	</div>
</div>