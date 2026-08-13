<script>
	import { fly } from 'svelte/transition';

	/**
	 * Table paginée des tirages solaires (G, eta_col, T_0, A_col, COP, mu) — labels UI
	 * français, export CSV/JSON en notation technique. Pagination 20 lignes/page.
	 * @type {{ tirages: Record<string, number>[], campagneId?: string }}
	 */
	let { tirages, campagneId = '' } = $props();

	const PAGE_SIZE = 20;
	let page = $state(1);

	const COLS = [
		{ cle: null, label: '#', cls: 'text-[var(--text-muted)] tabular' },
		{ cle: 'G', label: 'Rayonnement solaire', cls: 'text-[var(--text-secondary)]' },
		{ cle: 'eta_col', label: 'Efficacité concentrateur', cls: 'text-[var(--text-secondary)]' },
		{ cle: 'T_0', label: 'Température ambiante', cls: 'text-[var(--text-secondary)]' },
		{ cle: 'A_col', label: 'Surface captante', cls: 'text-[var(--text-secondary)]' },
		{ cle: 'COP', label: 'Performance globale', cls: 'text-[var(--text-primary)] font-semibold' },
		{ cle: 'mu', label: "Taux d'entraînement", cls: 'text-[var(--text-secondary)]' }
	];

	const CSV_COLS = ['id', 'G_W_m2', 'eta_col', 'T0_degC', 'A_col_m2', 'COP', 'mu'];

	let nPages = $derived(Math.max(1, Math.ceil(tirages.length / PAGE_SIZE)));
	let pageClampee = $derived(Math.min(Math.max(1, page), nPages));
	let lignesPage = $derived(
		tirages.slice((pageClampee - 1) * PAGE_SIZE, pageClampee * PAGE_SIZE)
	);

	let pages = $derived.by(() => {
		const n = nPages;
		const cur = pageClampee;
		/** @type {(number | string)[]} */
		const out = [];
		if (n <= 7) {
			for (let p = 1; p <= n; p++) out.push(p);
		} else {
			out.push(1);
			const start = Math.max(2, cur - 1);
			const end = Math.min(n - 1, cur + 1);
			if (start > 2) out.push('…');
			for (let p = start; p <= end; p++) out.push(p);
			if (end < n - 1) out.push('…');
			out.push(n);
		}
		return out;
	});

	/** @param {number | null | undefined} v */
	function fmt(v) {
		if (v === undefined || v === null || typeof v !== 'number' || !isFinite(v)) return '—';
		let s = v.toFixed(4);
		if (s.indexOf('.') !== -1) s = s.replace(/0+$/, '').replace(/\.$/, '');
		return s;
	}

	/** @param {string | number | null | undefined} v */
	function csvCell(v) {
		if (v === undefined || v === null) return '';
		if (typeof v === 'number') return String(v);
		const s = String(v);
		if (/[",\n\r]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
		return s;
	}

	function exporterCsv() {
		const lines = [CSV_COLS.join(',')];
		tirages.forEach((row, i) => {
			const id = String(i + 1).padStart(5, '0');
			const vals = [id, row.G, row.eta_col, row.T_0, row.A_col, row.COP, row.mu];
			lines.push(vals.map(csvCell).join(','));
		});
		telecharger(lines.join('\n'), 'text/csv;charset=utf-8;', 'csv');
	}

	function exporterJson() {
		telecharger(JSON.stringify(tirages, null, 2), 'application/json', 'json');
	}

	/** @param {string} contenu @param {string} mime @param {string} ext */
	function telecharger(contenu, mime, ext) {
		const blob = new Blob([contenu], { type: mime });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `tirages_${campagneId || 'solaire'}.${ext}`;
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="mb-4 flex flex-wrap items-start justify-between gap-3">
		<div>
			<h3 class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
				Résultats détaillés de la simulation
			</h3>
			<p class="mt-1 text-xs text-[var(--text-secondary)]">
				{tirages.length} lignes · Compatible avec R, Python, Excel
			</p>
		</div>
		<div class="flex gap-2">
			<button
				type="button"
				onclick={exporterCsv}
				disabled={!tirages.length}
				class="border border-[var(--border-strong)] bg-[var(--surface-raised)] px-3 py-1.5 rounded-[var(--radius-sm)] text-xs text-[var(--text-primary)] transition-all duration-200 hover:scale-[1.02] hover:border-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-40"
			>
				Télécharger CSV
			</button>
			<button
				type="button"
				onclick={exporterJson}
				disabled={!tirages.length}
				class="border border-[var(--border-strong)] bg-[var(--surface-raised)] px-3 py-1.5 rounded-[var(--radius-sm)] text-xs text-[var(--text-primary)] transition-all duration-200 hover:scale-[1.02] hover:border-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-40"
			>
				Télécharger JSON
			</button>
		</div>
	</div>

	{#if !tirages.length}
		<div class="flex flex-col items-center gap-3 py-10 text-center">
			<div
				class="h-8 w-8 rounded-full bg-[var(--surface-raised)] animate-pulse"
				aria-hidden="true"
			></div>
			<p class="text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
		</div>
	{:else}
		<div class="overflow-x-auto">
			<table class="tabular w-full min-w-[680px] text-left text-sm">
				<thead>
					<tr
						class="border-b border-[var(--border)] text-[10px] uppercase tracking-wide text-[var(--text-muted)]"
					>
						{#each COLS as c (c.cle ?? '__index')}
							<th class="py-2 px-3 whitespace-nowrap">{c.label}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each lignesPage as row, i (pageClampee + '-' + i)}
						<tr
							class="border-b border-[var(--border)]/60 last:border-0 transition-colors hover:bg-white/5"
							transition:fly={{ y: 10, duration: 200, delay: Math.min(i, 10) * 40 }}
						>
							{#each COLS as c (c.cle ?? '__index')}
								<td class="py-2 px-3 whitespace-nowrap {c.cls}">
									{#if c.cle === null}
										{(pageClampee - 1) * PAGE_SIZE + i + 1}
									{:else}
										{fmt(row[c.cle])}
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		{#if nPages > 1}
			<div class="mt-3 flex items-center gap-3 text-xs text-[var(--text-muted)]">
				<button
					type="button"
					onclick={() => (page = pageClampee - 1)}
					disabled={pageClampee <= 1}
					class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2.5 py-1 text-[var(--text-secondary)] transition-all duration-200 hover:border-[var(--text-primary)] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-40"
				>
					← Préc.
				</button>
				{#each pages as p, idx (p + '-' + idx)}
					{#if p === '…'}
						<span class="px-1 text-[var(--text-muted)]">…</span>
					{:else if typeof p === 'number'}
						<button
							type="button"
							onclick={() => (page = p)}
							class="h-7 min-w-7 rounded-[var(--radius-sm)] px-2 transition-colors {p === pageClampee
								? 'border border-[var(--border-strong)] bg-[var(--surface-raised)] font-semibold text-[var(--text-primary)]'
								: 'text-[var(--text-secondary)] hover:bg-white/5 hover:text-[var(--text-primary)]'}"
						>
							{p}
						</button>
					{/if}
				{/each}
				<button
					type="button"
					onclick={() => (page = pageClampee + 1)}
					disabled={pageClampee >= nPages}
					class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2.5 py-1 text-[var(--text-secondary)] transition-all duration-200 hover:border-[var(--text-primary)] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-40"
				>
					Suiv. →
				</button>
				<span class="ml-auto">Compatible R · Python · Excel</span>
			</div>
		{/if}
	{/if}
</div>