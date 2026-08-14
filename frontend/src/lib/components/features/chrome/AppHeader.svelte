<script>
	import favicon from '$lib/assets/favicon.svg';
	import { Users, LogOut } from '@lucide/svelte';
	import UserMenuDropdown from '$lib/components/UserMenuDropdown.svelte';
	import CircuitPills from '$lib/components/CircuitPills.svelte';
	import ApiStatusBadge from '$lib/components/ApiStatusBadge.svelte';
	import ThemeToggle from '$lib/components/ui/ThemeToggle.svelte';

	/** @type {{ user: { email: string, nom: string, role: string } | null }} */
	let { user } = $props();
</script>

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
		{#if user?.role === 'admin'}
			<a
				href="/utilisateurs"
				class="inline-flex items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--border-strong)] px-3 py-2 text-sm text-[var(--text-secondary)] transition-all duration-200 hover:border-[var(--accent)] hover:text-[var(--text-primary)] active:scale-[0.98]"
			>
				<Users size={15} />
				<span class="hidden sm:inline">Utilisateurs</span>
			</a>
		{/if}
		<ApiStatusBadge />
		<ThemeToggle />
		{#if user}
			<div class="flex items-center gap-2">
				<span
					class="hidden max-w-32 truncate text-sm text-[var(--text-secondary)] md:inline"
					title={user.email}
				>
					{user.nom}
				</span>
				<form method="post" action="/logout">
					<button
						type="submit"
						aria-label="Se déconnecter"
						class="inline-flex items-center rounded-[var(--radius-sm)] p-2 text-[var(--text-muted)] transition-all duration-200 hover:bg-white/5 hover:text-[var(--text-primary)] active:scale-[0.98]"
					>
						<LogOut size={16} />
					</button>
				</form>
			</div>
		{/if}
		<UserMenuDropdown user={user} />
	</div>
</header>
