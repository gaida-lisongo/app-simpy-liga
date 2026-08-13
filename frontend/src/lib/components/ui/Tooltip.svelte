<script>
	/** @type {{ text: string, children?: import('svelte').Snippet }} */
	let { text, children } = $props();
</script>

<span class="group relative inline-flex items-center">
	{@render children?.()}
	<span
		role="tooltip"
		class="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 w-56 -translate-x-1/2 rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-3 py-2 text-xs leading-snug text-[var(--text-secondary)] opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100"
	>
		{text}
	</span>
</span>
