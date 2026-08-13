<script>
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import UserMenuDropdown from '$lib/components/UserMenuDropdown.svelte';
	import CircuitPills from '$lib/components/CircuitPills.svelte';
	import ApiStatusBadge from '$lib/components/ApiStatusBadge.svelte';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="min-h-screen bg-[var(--page)]">
	<header
		class="sticky top-0 z-40 flex h-16 w-full items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--surface)]/95 px-4 backdrop-blur sm:px-6"
	>
		<a href="/" class="flex items-center gap-2 shrink-0">
			<img src={favicon} alt="" class="h-7 w-7" />
			<span class="hidden text-sm font-semibold tracking-wide text-[var(--text-primary)] sm:inline">
				SimpyLIGA
			</span>
		</a>

		<CircuitPills />

		<div class="ml-auto flex items-center gap-3">
			<ApiStatusBadge />
			<UserMenuDropdown />
		</div>
	</header>

	<main class="w-full px-4 py-6 sm:px-6 lg:px-8">
		{@render children()}
	</main>
</div>
