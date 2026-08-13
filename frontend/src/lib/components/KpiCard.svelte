<script>
	/**
	 * @type {{
	 *   label: string,
	 *   value: string,
	 *   sub?: string,
	 *   tone?: 'accent' | 'good' | 'warning' | 'critical' | 'neutral'
	 * }}
	 */
	let { label, value, sub = '', tone = 'accent' } = $props();

	const rings = {
		accent: 'var(--accent)',
		good: 'var(--good)',
		warning: 'var(--warning)',
		critical: 'var(--critical)',
		neutral: 'var(--text-muted)'
	};
</script>

<div
	class="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5"
>
	<div
		class="absolute inset-x-0 top-0 h-[3px]"
		style="background:{rings[tone]}"
	></div>
	<p class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">{label}</p>
	<p class="tabular mt-2 text-3xl font-semibold text-[var(--text-primary)]">{value}</p>
	{#if sub}
		<p class="tabular mt-1 text-xs text-[var(--text-secondary)]">{sub}</p>
	{/if}
</div>
