<script>
	import { page } from '$app/state';
	import { User } from '@lucide/svelte';
	import { CIRCUITS } from '$lib/constants.js';

	/** @type {{ user?: { email: string, nom: string, role: string } | null }} */
	let { user = null } = $props();

	const nav = [{ slug: '', id: '—', titre: 'Dashboard' }, ...CIRCUITS];

	let open = $state(false);
	/** @type {HTMLDivElement | undefined} */
	let rootEl = $state();

	/** @param {MouseEvent} e */
	function onDocClick(e) {
		if (rootEl && !rootEl.contains(/** @type {Node} */ (e.target))) open = false;
	}

	/** @param {KeyboardEvent} e */
	function onKeydown(e) {
		if (e.key === 'Escape') open = false;
	}
</script>

<svelte:window onclick={onDocClick} onkeydown={onKeydown} />

<div class="relative" bind:this={rootEl}>
	<button
		type="button"
		class="flex items-center gap-2 rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-primary)] transition-colors hover:border-[var(--accent)]"
		aria-haspopup="menu"
		aria-expanded={open}
		onclick={() => (open = !open)}
	>
		<span
			class="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--accent-soft)] text-[11px] font-semibold text-[var(--accent)]"
		>
			☰
		</span>
		<span class="hidden sm:inline">Menu</span>
		<svg width="12" height="12" viewBox="0 0 12 12" fill="none" class="text-[var(--text-muted)]">
			<path d="M2.5 4.5 6 8l3.5-3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
		</svg>
	</button>

	{#if open}
		<div
			role="menu"
			class="absolute right-0 z-30 mt-2 w-72 overflow-hidden rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface)] shadow-xl"
		>
			<nav class="p-2">
				{#each nav as item (item.slug)}
					{@const href = `/${item.slug}`}
					{@const active = page.url.pathname === href}
					<a
						{href}
						role="menuitem"
						onclick={() => (open = false)}
						class="flex items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2.5 text-sm transition-colors {active
							? 'bg-[var(--accent-soft)] text-[var(--text-primary)]'
							: 'text-[var(--text-secondary)] hover:bg-white/5 hover:text-[var(--text-primary)]'}"
					>
						<span
							class="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] text-[11px] font-semibold {active
								? 'bg-[var(--accent)] text-white'
								: 'bg-white/5 text-[var(--text-muted)]'}"
						>
							{item.id}
						</span>
						<span class="font-medium">{item.titre}</span>
					</a>
				{/each}

				{#if user}
					<div class="my-2 border-t border-[var(--border)]"></div>
					{@const active = page.url.pathname === '/mon-compte'}
					<a
						href="/mon-compte"
						role="menuitem"
						onclick={() => (open = false)}
						class="flex items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2.5 text-sm transition-colors {active
							? 'bg-[var(--accent-soft)] text-[var(--text-primary)]'
							: 'text-[var(--text-secondary)] hover:bg-white/5 hover:text-[var(--text-primary)]'}"
					>
						<span
							class="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] {active
								? 'bg-[var(--accent)] text-white'
								: 'bg-white/5 text-[var(--text-muted)]'}"
						>
							<User size={14} />
						</span>
						<span class="font-medium">Mon compte</span>
					</a>
				{/if}
			</nav>
		</div>
	{/if}
</div>
