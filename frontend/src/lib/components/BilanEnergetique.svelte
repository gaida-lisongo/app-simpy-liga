<script>
	/**
	 * Bilan Q_evap / Q_cond / W_pompe / COP. Utilise result.resultats.bilan_energetique s'il existe
	 * (pas encore exposé par l'API), sinon reconstitue ce qui est disponible depuis les statistiques
	 * déjà renvoyées (COP, Q_gen) — le reste (Q_evap, Q_cond, W_pompe) reste marqué indisponible.
	 * @type {{
	 *   bilan: { Q_evap?: number, Q_cond?: number, W_pompe?: number, COP?: number } | undefined,
	 *   statistiques: Record<string, { moyenne?: number }>
	 * }}
	 */
	let { bilan, statistiques } = $props();

	let lignes = $derived([
		{ label: 'Q_evap', unite: 'kW', valeur: bilan?.Q_evap ?? null },
		{ label: 'Q_gen', unite: 'kW', valeur: bilan?.Q_evap == null ? (statistiques?.Q_gen?.moyenne ?? null) : null },
		{ label: 'Q_cond', unite: 'kW', valeur: bilan?.Q_cond ?? null },
		{ label: 'W_pompe', unite: 'kW', valeur: bilan?.W_pompe ?? null },
		{ label: 'COP', unite: '', valeur: bilan?.COP ?? statistiques?.COP?.moyenne ?? null }
	]);
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h3 class="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">Bilan énergétique</h3>
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
	{#if !bilan}
		<p class="mt-3 text-[11px] text-[var(--text-muted)]">
			Q_cond et W_pompe non disponibles — l'API ne renvoie pour l'instant que COP et Q_gen.
		</p>
	{/if}
</div>
