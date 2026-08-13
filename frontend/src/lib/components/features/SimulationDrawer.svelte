<script>
	import Drawer from '$lib/components/ui/Drawer.svelte';
	import ParamEditor from '$lib/components/ParamEditor.svelte';

	/**
	 * Tiroir latéral de simulation — par circuit. Contient les paramètres
	 * incertains (éditables), la configuration de campagne (N, seed, méthode)
	 * et le bouton de lancement + progression temps réel.
	 * @type {{
	 *   open?: boolean,
	 *   circuit: { id: string, titre: string, accent: string, etats: string },
	 *   nIterations: number,
	 *   seed: number,
	 *   methode: string,
	 *   params: any[],
	 *   configLoading: boolean,
	 *   configError?: string,
	 *   running: boolean,
	 *   progress?: number,
	 *   error?: string,
	 *   onLancer: () => void,
	 *   onClose?: () => void
	 * }}
	 */
	let {
		open = $bindable(false),
		circuit,
		nIterations = $bindable(),
		seed = $bindable(),
		methode = $bindable(),
		params,
		configLoading,
		configError = '',
		running,
		progress = 0,
		error = '',
		onLancer,
		onClose
	} = $props();

	const inputCls =
		'w-full rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2.5 py-1.5 text-sm tabular text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none transition-colors duration-150';
</script>

<Drawer bind:open title="Simulation — {circuit.id}" onClose={onClose} width="440px">
	<div class="flex flex-col gap-6">
		<!-- En-tête circuit -->
		<div>
			<div class="flex items-center gap-2">
				<span
					class="flex h-7 w-7 items-center justify-center rounded-[var(--radius-sm)] text-[11px] font-semibold text-white"
					style="background:{circuit.accent}"
				>
					{circuit.id}
				</span>
				<div>
					<p class="text-sm font-semibold text-[var(--text-primary)]">{circuit.titre}</p>
					<p class="text-[11px] text-[var(--text-muted)]">États {circuit.etats}</p>
				</div>
			</div>
		</div>

		<!-- Paramètres incertains -->
		<section>
			<h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
				Paramètres incertains
			</h3>
			{#if configLoading}
				<div class="space-y-2">
					{#each Array(3) as _, i (i)}
						<div class="h-14 rounded-[var(--radius-sm)] bg-[var(--surface-raised)] animate-pulse" aria-hidden="true"></div>
					{/each}
				</div>
			{:else if configError}
				<p class="text-sm text-[var(--critical)]">{configError}</p>
			{:else if params.length === 0}
				<p class="text-sm text-[var(--text-muted)]">Aucun paramètre incertain pour ce circuit.</p>
			{:else}
				<div class="grid grid-cols-1 gap-2.5">
					{#each params as param (param.nom)}
						<ParamEditor {param} />
					{/each}
				</div>
			{/if}
		</section>

		<!-- Configuration de campagne -->
		<section>
			<h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
				Configuration de campagne
			</h3>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
				<label class="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
					Itérations
					<input type="number" min="1" max="10000" step="1" bind:value={nIterations} class={inputCls} />
				</label>
				<label class="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
					Seed
					<input type="number" step="1" bind:value={seed} class={inputCls} />
				</label>
				<label class="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
					Méthode
					<select bind:value={methode} class={inputCls}>
						<option value="LHS">LHS</option>
						<option value="MonteCarlo">Monte Carlo</option>
					</select>
				</label>
			</div>
			<p class="mt-2 text-[10px] text-[var(--text-muted)]">
				Plafond serveur : 10 000 tirages (dimensionnement inverse, cible 12 kW).
			</p>
		</section>
	</div>

	{#snippet footer()}
		<div class="flex flex-col gap-3">
			<button
				type="button"
				onclick={onLancer}
				disabled={running}
				class="flex w-full items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--text-primary)] bg-[var(--text-primary)] px-4 py-2.5 text-sm font-medium text-[var(--page)] transition-all duration-200 hover:scale-[1.01] hover:bg-[var(--text-secondary)] active:scale-[0.99] disabled:pointer-events-none disabled:opacity-60"
			>
				{#if running}
					<span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--page)]/40 border-t-[var(--page)]"></span>
					Simulation en cours…
				{:else}
					<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M5 3.5v9l7-4.5z" /></svg>
					Lancer la simulation
				{/if}
			</button>

			{#if running}
				<div class="flex items-center gap-2">
					<div class="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--border)]">
						<div
							class="h-full rounded-full transition-all duration-300"
							style="width:{Math.max(2, progress)}%; background:var(--text-primary)"
						></div>
					</div>
					<span class="tabular text-xs text-[var(--text-muted)]">{progress.toFixed(0)}%</span>
				</div>
			{:else if progress === 100}
				<p class="text-center text-xs text-[var(--good)]">Campagne terminée — données disponibles.</p>
			{/if}

			{#if error}
				<p class="text-sm text-[var(--critical)]">{error}</p>
			{/if}
		</div>
	{/snippet}
</Drawer>