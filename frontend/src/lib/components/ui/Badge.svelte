<script>
	/** @type {{ tone?: 'good' | 'warning' | 'critical' | 'neutral' | 'accent', children?: import('svelte').Snippet }} */
	let { tone = 'neutral', children } = $props();

	const tones = {
		good: 'bg-[color-mix(in_oklab,var(--good)_18%,transparent)] text-[var(--good)] border-[color-mix(in_oklab,var(--good)_40%,transparent)]',
		warning:
			'bg-[color-mix(in_oklab,var(--warning)_18%,transparent)] text-[var(--warning)] border-[color-mix(in_oklab,var(--warning)_40%,transparent)]',
		critical:
			'bg-[color-mix(in_oklab,var(--critical)_18%,transparent)] text-[var(--critical)] border-[color-mix(in_oklab,var(--critical)_40%,transparent)]',
		accent: 'bg-[var(--accent-soft)] text-[var(--accent)] border-transparent',
		neutral: 'bg-white/5 text-[var(--text-secondary)] border-[var(--border)]'
	};
</script>

<span
	class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium {tones[tone]}"
>
	{@render children?.()}
</span>
