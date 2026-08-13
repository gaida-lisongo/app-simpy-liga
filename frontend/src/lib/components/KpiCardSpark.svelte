<script>
	import Tooltip from '$lib/components/ui/Tooltip.svelte';

	/**
	 * Sparkline = moyenne cumulée du tirage (convergence réelle sur la campagne),
	 * calculée à partir de resultats.tirages — pas de donnée fabriquée.
	 * @type {{
	 *   label: string,
	 *   tooltip?: string,
	 *   stat: { moyenne?: number, ecart_type?: number, IC95?: [number, number] } | null,
	 *   serie: number[],
	 *   accent: string,
	 *   decimals?: number
	 * }}
	 */
	let { label, tooltip = '', stat, serie, accent, decimals = 3 } = $props();

	/** @param {number | null | undefined} v */
	function fmt(v) {
		return v === undefined || v === null ? '—' : Number(v).toFixed(decimals);
	}

	const W = 160;
	const H = 40;

	let path = $derived.by(() => {
		if (!serie?.length) return null;
		let acc = 0;
		const cum = serie.map((v, i) => (acc += v) / (i + 1));
		const min = Math.min(...cum), max = Math.max(...cum);
		const sx = (/** @type {number} */ i) => (i / (cum.length - 1 || 1)) * W;
		const sy = (/** @type {number} */ v) => H - 2 - ((v - min) / (max - min || 1)) * (H - 4);
		return cum.map((v, i) => `${i === 0 ? 'M' : 'L'}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(' ');
	});

	let cv = $derived(
		stat?.moyenne ? Math.abs((stat.ecart_type ?? 0) / stat.moyenne) * 100 : null
	);
</script>

<div class="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="absolute inset-x-0 top-0 h-[3px]" style="background:{accent}"></div>

	<div class="flex items-center gap-1.5">
		<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">{label}</span>
		{#if tooltip}
			<Tooltip text={tooltip}>
				<span class="flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full border border-[var(--text-muted)] text-[9px] leading-none text-[var(--text-muted)]">?</span>
			</Tooltip>
		{/if}
	</div>

	{#if stat}
		<p class="tabular mt-1.5 text-2xl font-semibold text-[var(--text-primary)]">{fmt(stat.moyenne)}</p>
		{#if cv !== null}
			<p class="tabular text-xs" style="color:{accent}">CV {cv.toFixed(1)}%</p>
		{/if}

		{#if path}
			<svg viewBox="0 0 {W} {H}" class="mt-2 w-full" preserveAspectRatio="none" role="img" aria-label="Convergence de {label} sur la campagne">
				<path d={path} fill="none" stroke={accent} stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
			</svg>
		{/if}

		{#if stat.IC95}
			<p class="tabular mt-1 text-[10px] text-[var(--text-muted)]">IC95 [{fmt(stat.IC95[0])}, {fmt(stat.IC95[1])}]</p>
		{/if}
	{:else}
		<p class="mt-2 text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
	{/if}
</div>
