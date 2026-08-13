<script>
	/**
	 * Bilan Q_evap / Q_cond / W_pompe / COP — contenu (sans enveloppe de carte).
	 * Utilise result.resultats.bilan_energetique s'il existe, sinon reconstitue
	 * ce qui est disponible depuis les statistiques (COP, Q_gen).
	 * @type {{
	 *   bilan: { Q_evap?: number, Q_cond?: number, W_pompe?: number, Q_gen?: number, COP?: number } | undefined,
	 *   statistiques: Record<string, { moyenne?: number }>
	 * }}
	 */
	let { bilan, statistiques } = $props();

	let lignes = $derived.by(() => [
		{ label: 'Q_evap', unite: 'kW', valeur: bilan?.Q_evap ?? null },
		{ label: 'Q_gen', unite: 'kW', valeur: bilan?.Q_gen ?? statistiques?.Q_gen?.moyenne ?? null },
		{ label: 'Q_cond', unite: 'kW', valeur: bilan?.Q_cond ?? null },
		{ label: 'W_pompe', unite: 'kW', valeur: bilan?.W_pompe ?? null },
		{ label: 'COP', unite: '', valeur: bilan?.COP ?? statistiques?.COP?.moyenne ?? null }
	]);

	let dispo = $derived(lignes.some((l) => l.valeur !== null));
</script>

<div>
	<dl class="tabular grid grid-cols-2 gap-3 sm:grid-cols-3">
		{#each lignes as l (l.label)}
			{#if l.valeur !== null}
				<div>
					<dt class="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">{l.label}</dt>
					<dd class="text-lg font-semibold text-[var(--text-primary)]">
						{l.valeur.toFixed(3)}<span class="ml-1 text-xs text-[var(--text-muted)]">{l.unite}</span>
					</dd>
				</div>
			{/if}
		{/each}
	</dl>
	{#if !dispo}
		<p class="text-sm text-[var(--text-muted)]">Bilan indisponible — lancez une campagne sur ce circuit.</p>
	{:else if !bilan?.Q_cond}
		<p class="mt-3 text-[11px] text-[var(--text-muted)]">
			Q_cond et W_pompe non disponibles sur cette campagne.
		</p>
	{/if}
</div>