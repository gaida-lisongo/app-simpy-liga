<script>
	import Tooltip from '$lib/components/ui/Tooltip.svelte';
	import { PARAM_INFO, LOI_LABELS } from '$lib/constants.js';

	/**
	 * @type {{ param: { nom: string, symbole: string, unite: string, loi: string,
	 *   min?: number, mode?: number, max?: number, sigma?: number, valeur?: number } }}
	 */
	let { param } = $props();

	let info = $derived(PARAM_INFO[param.nom] ?? { label: param.symbole, tooltip: '' });

	const inputCls =
		'w-full rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2.5 py-1.5 text-sm text-[var(--text-primary)] tabular focus:border-[var(--accent)] focus:outline-none';
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="flex items-start justify-between gap-2">
		<div class="flex items-center gap-1.5">
			<span class="text-sm font-medium text-[var(--text-primary)]">{info.label}</span>
			{#if info.tooltip}
				<Tooltip text={info.tooltip}>
					<span
						class="flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full border border-[var(--text-muted)] text-[9px] leading-none text-[var(--text-muted)]"
						>?</span
					>
				</Tooltip>
			{/if}
		</div>
		<span class="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-[var(--text-muted)]">
			{param.symbole}{param.unite && param.unite !== '-' ? ` (${param.unite})` : ''}
		</span>
	</div>

	<p class="mt-1 text-[11px] text-[var(--text-muted)]">{LOI_LABELS[param.loi] ?? param.loi}</p>

	<div class="mt-3 grid grid-cols-3 gap-2">
		{#if param.loi === 'uniforme'}
			<label class="col-span-1 flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
				min
				<input class={inputCls} type="number" step="any" bind:value={param.min} />
			</label>
			<label class="col-span-1 col-start-3 flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
				max
				<input class={inputCls} type="number" step="any" bind:value={param.max} />
			</label>
		{:else if param.loi === 'triangulaire'}
			<label class="flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
				min
				<input class={inputCls} type="number" step="any" bind:value={param.min} />
			</label>
			<label class="flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
				mode
				<input class={inputCls} type="number" step="any" bind:value={param.mode} />
			</label>
			<label class="flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
				max
				<input class={inputCls} type="number" step="any" bind:value={param.max} />
			</label>
		{:else if param.loi === 'normale'}
			<label class="flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
				μ (moyenne)
				<input class={inputCls} type="number" step="any" bind:value={param.mode} />
			</label>
			<label class="flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
				σ (écart-type)
				<input class={inputCls} type="number" step="any" bind:value={param.sigma} />
			</label>
		{:else}
			<label class="flex flex-col gap-1 text-[11px] text-[var(--text-muted)]">
				valeur
				<input class={inputCls} type="number" step="any" bind:value={param.valeur} />
			</label>
		{/if}
	</div>
</div>
