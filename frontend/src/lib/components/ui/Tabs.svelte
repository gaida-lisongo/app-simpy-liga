<script>
	/**
	 * @type {{
	 *   tabs: { id: string, label: string }[],
	 *   active: string
	 * }}
	 */
	let { tabs, active = $bindable() } = $props();
</script>

<div role="tablist" class="flex gap-1 border-b border-[var(--border)]">
	{#each tabs as t (t.id)}
		<button
			type="button"
			role="tab"
			aria-selected={active === t.id}
			onclick={() => (active = t.id)}
			class="relative px-4 py-2.5 text-sm font-medium transition-colors {active === t.id
				? 'text-[var(--text-primary)]'
				: 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'}"
		>
			{t.label}
			{#if active === t.id}
				<span class="absolute inset-x-0 -bottom-px h-[2px] rounded-full bg-[var(--accent)]"></span>
			{/if}
		</button>
	{/each}
</div>
