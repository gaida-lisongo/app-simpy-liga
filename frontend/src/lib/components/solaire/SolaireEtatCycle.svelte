<script>
	import { fly } from 'svelte/transition';

	/**
	 * Carte "État du cycle" — valeurs numériques des points (T, P, h, s, x) du
	 * cycle de référence, affichée à côté du diagramme thermodynamique. Entrée
	 * animée des lignes (fly décalé), hover, et export CSV/JSON en notation
	 * technique (thèse/recherche).
	 * @type {{ etats: { point: string, T?: number, P?: number, h?: number, s?: number, x?: number }[] | undefined }}
	 */
	let { etats } = $props();

	const COLS_UI = [
		{ key: 'point', label: 'Point', cls: 'text-[var(--text-primary)] font-medium' },
		{ key: 'T', label: 'T (°C)', cls: 'text-[var(--text-secondary)]' },
		{ key: 'P', label: 'P (bar)', cls: 'text-[var(--text-secondary)]' },
		{ key: 'h', label: 'h (kJ/kg)', cls: 'text-[var(--text-secondary)]' },
		{ key: 's', label: 's (kJ/kg·K)', cls: 'text-[var(--text-secondary)]' },
		{ key: 'x', label: 'Titre x', cls: 'text-[var(--accent)]' }
	];
	const CSV_HEADER = ['point', 'T_degC', 'P_bar', 'h_kJ_kg', 's_kJ_kgK', 'x'];

	/** @param {number | null | undefined} v @param {number} [d] */
	function fmt(v, d = 3) {
		return v === undefined || v === null ? '—' : Number(v).toFixed(d);
	}

	function exporterCsv() {
		if (!etats?.length) return;
		const lines = [CSV_HEADER.join(',')];
		for (const e of etats) {
			lines.push([
				e.point,
				e.T ?? '',
				e.P ?? '',
				e.h ?? '',
				e.s ?? '',
				e.x ?? ''
			].join(','));
		}
		download(lines.join('\n'), 'text/csv', 'csv');
	}

	function exporterJson() {
		if (!etats?.length) return;
		download(JSON.stringify(etats, null, 2), 'application/json', 'json');
	}

	/** @param {string} content @param {string} mime @param {string} ext */
	function download(content, mime, ext) {
		const blob = new Blob([content], { type: mime });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `etats_cycle_solaire.${ext}`;
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<div class="flex h-full flex-col rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="mb-3 flex items-center justify-between gap-2">
		<h3 class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">État du cycle</h3>
		<div class="flex gap-1.5">
			<button
				type="button"
				onclick={exporterCsv}
				disabled={!etats?.length}
				aria-label=" exporter CSV"
				class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2.5 py-1 text-[10px] text-[var(--text-secondary)] transition-all duration-200 hover:scale-[1.02] hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:pointer-events-none disabled:opacity-40"
			>CSV</button>
			<button
				type="button"
				onclick={exporterJson}
				disabled={!etats?.length}
				aria-label="Exporter JSON"
				class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2.5 py-1 text-[10px] text-[var(--text-secondary)] transition-all duration-200 hover:scale-[1.02] hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:pointer-events-none disabled:opacity-40"
			>JSON</button>
		</div>
	</div>

	{#if etats && etats.length}
		<div class="flex-1 overflow-y-auto">
			<table class="tabular w-full text-left text-sm">
				<thead class="sticky top-0 bg-[var(--surface)]">
					<tr class="border-b border-[var(--border)] text-[10px] uppercase tracking-wide text-[var(--text-muted)]">
						{#each COLS_UI as c (c.key)}
							<th class="py-2 pr-3">{c.label}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each etats as e, i (e.point)}
						<tr
							class="border-b border-[var(--border)]/60 text-[var(--text-secondary)] transition-colors duration-150 last:border-0 hover:bg-white/5"
							transition:fly={{ y: 8, duration: 200, delay: Math.min(i, 8) * 45 }}
						>
							<td class="py-2 pr-3">
								<span class="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--accent)] px-1.5 text-[10px] font-semibold text-black">
									{e.point}
								</span>
							</td>
							<td class="py-2 pr-3">{fmt(e.T)}</td>
							<td class="py-2 pr-3">{fmt(e.P)}</td>
							<td class="py-2 pr-3">{fmt(e.h, 1)}</td>
							<td class="py-2 pr-3">{fmt(e.s, 4)}</td>
							<td class="py-2 pr-3 {COLS_UI[5].cls}">{e.x !== undefined && e.x !== null ? fmt(e.x) : '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<div class="flex flex-1 flex-col items-center justify-center gap-2 py-8 text-center">
			<div class="h-8 w-8 rounded-full bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
			<p class="text-sm text-[var(--text-muted)]">Aucun point d'état — lancez une campagne.</p>
		</div>
	{/if}
</div>