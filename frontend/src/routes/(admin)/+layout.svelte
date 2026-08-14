<script>
	import AppHeader from '$lib/components/features/chrome/AppHeader.svelte';

	let { children, data } = $props();
</script>

<div class="min-h-screen bg-[var(--page)]">
	<AppHeader user={data.user} />
	<main class="w-full px-4 py-6 sm:px-6 lg:px-8">
		{@render children()}
	</main>
</div>
