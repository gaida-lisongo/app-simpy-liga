<script>
	/**
	 * @type {{
	 *   variant?: 'primary' | 'secondary' | 'ghost',
	 *   disabled?: boolean,
	 *   type?: 'button' | 'submit',
	 *   onclick?: (e: MouseEvent) => void,
	 *   children?: import('svelte').Snippet
	 * }}
	 */
	let { variant = 'primary', disabled = false, type = 'button', onclick, children, ...rest } =
		$props();

	const base =
		'inline-flex items-center justify-center gap-2 rounded-[var(--radius-sm)] px-4 py-2 text-sm font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2';

	const variants = {
		primary: 'bg-[var(--accent)] text-white hover:bg-[#4f96e8] focus-visible:outline-[var(--accent)]',
		secondary:
			'bg-[var(--surface-raised)] text-[var(--text-primary)] border border-[var(--border-strong)] hover:border-[var(--accent)]',
		ghost: 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/5'
	};
</script>

<button {type} {disabled} {onclick} class="{base} {variants[variant]}" {...rest}>
	{@render children?.()}
</button>
