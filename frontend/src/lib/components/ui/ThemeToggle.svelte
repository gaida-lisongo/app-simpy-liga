<script>
	import { Sun, Moon } from '@lucide/svelte';
	import { themeStore } from '$lib/stores/theme.svelte.js';

	let { floating = false } = $props();

	function toggle() {
		themeStore.toggle();
	}
</script>

<button
	type="button"
	onclick={toggle}
	aria-label={themeStore.value === 'dark' ? 'Passer en thème clair' : 'Passer en thème sombre'}
	title={themeStore.value === 'dark' ? 'Thème clair' : 'Thème sombre'}
	class={[
		'inline-flex h-9 w-9 items-center justify-center rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface)] text-[var(--text-secondary)] transition-all duration-200',
		'hover:border-[var(--accent)] hover:text-[var(--text-primary)] active:scale-[0.96]',
		floating ? 'fixed top-4 right-4 z-50 shadow-lg backdrop-blur' : ''
	]
		.filter(Boolean)
		.join(' ')}
>
	{#if themeStore.value === 'dark'}
		<span class="block transition-transform duration-300 hover:rotate-45">
			<Sun size={16} />
		</span>
	{:else}
		<span class="block transition-transform duration-300 hover:-rotate-12">
			<Moon size={16} />
		</span>
	{/if}
</button>
