<script>
	import Tooltip from '$lib/components/ui/Tooltip.svelte';

	/**
	 * @type {{
	 *   label: string,
	 *   tooltip?: string,
	 *   stat: { moyenne?: number, ecart_type?: number, IC95?: [number, number] } | null,
	 *   decimals?: number
	 * }}
	 */
	let { label, tooltip = '', stat, decimals = 3 } = $props();

	/** @param {number | null | undefined} v */
	function fmt(v) {
		return v === undefined || v === null ? '—' : Number(v).toFixed(decimals);
	}
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="flex items-center gap-1.5">
		<span class="text-xs font-medium text-[var(--text-secondary)]">{label}</span>
		{#if tooltip}
			<Tooltip text={tooltip}>
				<span
					class="flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full border border-[var(--text-muted)] text-[9px] leading-none text-[var(--text-muted)]"
					>?</span
				>
			</Tooltip>
		{/if}
	</div>

	{#if stat}
		<dl class="tabular mt-2 grid grid-cols-2 gap-x-3 gap-y-2">
			<div>
				<dt class="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">Moyenne</dt>
				<dd class="text-lg font-semibold text-[var(--text-primary)]">{fmt(stat.moyenne)}</dd>
			</div>
			<div>
				<dt class="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">Écart-type</dt>
				<dd class="text-lg font-semibold text-[var(--text-primary)]">{fmt(stat.ecart_type)}</dd>
			</div>
			<div>
				<dt class="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">IC95 bas</dt>
				<dd class="text-sm text-[var(--text-secondary)]">{fmt(stat.IC95?.[0])}</dd>
			</div>
			<div>
				<dt class="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">IC95 haut</dt>
				<dd class="text-sm text-[var(--text-secondary)]">{fmt(stat.IC95?.[1])}</dd>
			</div>
		</dl>
	{:else}
		<p class="mt-2 text-sm text-[var(--text-muted)]">Aucune donnée — lancez une campagne.</p>
	{/if}
</div>
