<script>
	import { fly } from 'svelte/transition';
	import favicon from '$lib/assets/favicon.svg';

	/**
	 * @type {{
	 *   titre: string,
	 *   sousTitre?: string,
	 *   children: import('svelte').Snippet,
	 *   pitch?: import('svelte').Snippet
	 * }}
	 */
	let { titre, sousTitre = '', children, pitch } = $props();
</script>

<div class="grid min-h-screen w-full grid-cols-1 lg:grid-cols-2">
	<aside
		class="relative hidden overflow-hidden border-r border-[var(--border)] bg-[var(--auth-panel-bg)] lg:flex"
		aria-hidden="true"
	>
		<div
			class="absolute inset-0 opacity-60"
			style="background: radial-gradient(60% 50% at 30% 30%, var(--auth-glow), transparent 70%);"
		></div>

		<div
			class="relative z-10 flex h-full w-full flex-col justify-between p-10 xl:p-14"
			in:fly={{ x: -16, duration: 320, delay: 80 }}
		>
			<div class="flex items-center gap-2.5">
				<img src={favicon} alt="" class="h-8 w-8" />
				<span class="text-sm font-semibold tracking-wide text-[var(--text-primary)]">
					SimpyLIGA
				</span>
			</div>

			{#if pitch}
				<div class="max-w-md">
					{@render pitch()}
				</div>
			{:else}
				<div class="max-w-md">
					<h2 class="text-2xl font-semibold leading-tight text-[var(--text-primary)] xl:text-3xl">
						Simulations thermodynamiques <br />propulsées par Monte Carlo.
					</h2>
					<p class="mt-4 text-sm leading-relaxed text-[var(--text-secondary)]">
						Plateforme interne pour la modélisation énergétique des circuits solaire, couplage,
						frigorifique et moteur. Campagnes paramétriques, KPIs et bilans en temps réel.
					</p>
					<ul class="mt-6 space-y-2.5 text-sm text-[var(--text-secondary)]">
						<li class="flex items-center gap-2">
							<span class="h-1.5 w-1.5 rounded-full bg-[var(--accent)]"></span>
							Campagnes LHS / Monte Carlo haute fidélité
						</li>
						<li class="flex items-center gap-2">
							<span class="h-1.5 w-1.5 rounded-full bg-[var(--accent)]"></span>
							Bilans énergétiques par circuit
						</li>
						<li class="flex items-center gap-2">
							<span class="h-1.5 w-1.5 rounded-full bg-[var(--accent)]"></span>
							Caches Redis et résultats reproductibles
						</li>
					</ul>
				</div>
			{/if}

			<p class="text-xs text-[var(--text-muted)]">
				© {new Date().getFullYear()} SimpyLIGA — Usage interne réservé.
			</p>
		</div>
	</aside>

	<section
		class="relative flex min-h-screen items-center justify-center bg-[var(--page)] px-5 py-10 sm:px-8"
	>
		<div class="w-full max-w-md" in:fly={{ y: 12, duration: 240 }}>
			<div class="mb-7 flex flex-col items-center gap-3 text-center lg:items-start lg:text-left">
				<img src={favicon} alt="" class="h-10 w-10 lg:hidden" />
				<div>
					<h1 class="text-xl font-semibold text-[var(--text-primary)]">{titre}</h1>
					{#if sousTitre}
						<p class="mt-1 text-sm text-[var(--text-muted)]">{sousTitre}</p>
					{/if}
				</div>
			</div>
			<div
				class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-sm sm:p-8"
			>
				{@render children()}
			</div>
		</div>
	</section>
</div>
