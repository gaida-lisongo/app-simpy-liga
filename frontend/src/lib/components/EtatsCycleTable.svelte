<script>
	/**
	 * Attend result.resultats.etats_cycle: { point: string|number, T, P, h, s, x }[].
	 * Champ pas encore exposé par l'API (les états sont calculés dans le cœur physique
	 * mais interrompus à app/adapters/physics_adapter.py::run_cycle) — état vide en attendant.
	 * @type {{ etats: {point: string|number, T?: number, P?: number, h?: number, s?: number, x?: number}[] | undefined, ordre: string }}
	 */
	let { etats, ordre } = $props();
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="mb-3 flex items-center justify-between">
		<h3 class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">États du cycle</h3>
		<span class="text-xs text-[var(--text-muted)]">Ordre {ordre}</span>
	</div>

	{#if etats && etats.length}
		<div class="overflow-x-auto">
			<table class="tabular w-full text-left text-sm">
				<thead>
					<tr class="border-b border-[var(--border)] text-[10px] uppercase tracking-wide text-[var(--text-muted)]">
						<th class="py-2 pr-3">Point</th>
						<th class="py-2 pr-3">T (°C)</th>
						<th class="py-2 pr-3">P (bar)</th>
						<th class="py-2 pr-3">h (kJ/kg)</th>
						<th class="py-2 pr-3">s (kJ/kg·K)</th>
						<th class="py-2 pr-3">x</th>
					</tr>
				</thead>
				<tbody>
					{#each etats as e (e.point)}
						<tr class="border-b border-[var(--border)]/60 text-[var(--text-secondary)] last:border-0">
							<td class="py-2 pr-3 font-medium text-[var(--text-primary)]">{e.point}</td>
							<td class="py-2 pr-3">{e.T?.toFixed(2) ?? '—'}</td>
							<td class="py-2 pr-3">{e.P?.toFixed(3) ?? '—'}</td>
							<td class="py-2 pr-3">{e.h?.toFixed(1) ?? '—'}</td>
							<td class="py-2 pr-3">{e.s?.toFixed(3) ?? '—'}</td>
							<td class="py-2 pr-3">{e.x !== undefined && e.x !== null ? e.x.toFixed(3) : '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<p class="text-sm text-[var(--text-muted)]">
			Non disponible — l'API ne renvoie pas encore les points d'état détaillés pour ce circuit.
		</p>
	{/if}
</div>
