<script>
	import ThemeToggle from '$lib/components/ui/ThemeToggle.svelte';

	let { children } = $props();
</script>

<div class="relative isolate">
	<ThemeToggle floating={true} />
	{@render children()}
</div>
