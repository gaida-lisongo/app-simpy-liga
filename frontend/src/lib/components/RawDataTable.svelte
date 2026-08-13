<script>
	import Button from '$lib/components/ui/Button.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';

	/**
	 * Table paginée des tirages Monte Carlo bruts (jusqu'à 10 000 lignes) — pagination
	 * côté client sur le tableau déjà en mémoire (hydraté depuis le cache Redis).
	 * @type {{ tirages: Record<string, number>[], campagneId?: string }}
	 */
	let { tirages, campagneId = '' } = $props();

	const PAGE_SIZE = 25;
	let page = $state(1);

	let colonnes = $derived(tirages.length ? Object.keys(tirages[0]) : []);
	let nPages = $derived(Math.max(1, Math.ceil(tirages.length / PAGE_SIZE)));
	let pageClampee = $derived(Math.min(page, nPages));
	let lignesPage = $derived(tirages.slice((pageClampee - 1) * PAGE_SIZE, pageClampee * PAGE_SIZE));

	function exporterJson() {
		telecharger(JSON.stringify(tirages, null, 2), 'application/json', 'json');
	}

	function exporterCsv() {
		const lignes = [colonnes.join(',')];
		for (const row of tirages) lignes.push(colonnes.map((c) => row[c] ?? '').join(','));
		telecharger(lignes.join('\n'), 'text/csv;charset=utf-8;', 'csv');
	}

	/** @param {string} contenu @param {string} mime @param {string} ext */
	function telecharger(contenu, mime, ext) {
		const blob = new Blob([contenu], { type: mime });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `tirages_${campagneId || 'campagne'}.${ext}`;
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
		<div class="flex items-center gap-2">
			<h3 class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">Données brutes</h3>
			<Badge tone="neutral">Compatible R · Jupyter · Excel</Badge>
		</div>
		<div class="flex gap-2">
			<Button variant="secondary" onclick={exporterCsv} disabled={!tirages.length}>CSV</Button>
			<Button variant="secondary" onclick={exporterJson} disabled={!tirages.length}>JSON</Button>
		</div>
	</div>

	{#if !tirages.length}
		<p class="text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
	{:else}
		<div class="overflow-x-auto">
			<table class="tabular w-full text-left text-sm">
				<thead>
					<tr class="border-b border-[var(--border)] text-[10px] uppercase tracking-wide text-[var(--text-muted)]">
						{#each colonnes as c (c)}
							<th class="py-2 pr-3 whitespace-nowrap">{c}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each lignesPage as row, i (i)}
						<tr class="border-b border-[var(--border)]/60 text-[var(--text-secondary)] last:border-0">
							{#each colonnes as c (c)}
								<td class="py-1.5 pr-3 whitespace-nowrap">{typeof row[c] === 'number' ? row[c].toFixed(4) : row[c]}</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<div class="mt-3 flex items-center justify-between text-xs text-[var(--text-muted)]">
			<span>{tirages.length} lignes</span>
			<div class="flex items-center gap-2">
				<button
					type="button"
					class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] px-2 py-1 disabled:opacity-40"
					onclick={() => (page = pageClampee - 1)}
					disabled={pageClampee <= 1}
				>
					←
				</button>
				<span class="tabular">Page {pageClampee} / {nPages}</span>
				<button
					type="button"
					class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] px-2 py-1 disabled:opacity-40"
					onclick={() => (page = pageClampee + 1)}
					disabled={pageClampee >= nPages}
				>
					→
				</button>
			</div>
		</div>
	{/if}
</div>
