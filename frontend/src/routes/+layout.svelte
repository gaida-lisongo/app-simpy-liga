<script>
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { themeStore } from '$lib/stores/theme.svelte.js';

	let { children } = $props();

	$effect(() => {
		themeStore.syncFromDom();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children()}
