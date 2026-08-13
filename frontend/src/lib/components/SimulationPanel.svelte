<script>
	import Button from '$lib/components/ui/Button.svelte';

	/**
	 * @type {{
	 *   nIterations: number,
	 *   seed: number,
	 *   methode: string,
	 *   running: boolean,
	 *   progress?: number,
	 *   error?: string,
	 *   onLancer: () => void
	 * }}
	 */
	let {
		nIterations = $bindable(10000),
		seed = $bindable(42),
		methode = $bindable('LHS'),
		running,
		progress = 0,
		error = '',
		onLancer
	} = $props();

	const inputCls =
		'w-full rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2.5 py-1.5 text-sm tabular text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none';
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Campagne Monte Carlo
	</h2>

	<div class="flex flex-col gap-3">
		<label class="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
			N_iterations
			<input type="number" min="1" step="1" bind:value={nIterations} class={inputCls} />
		</label>

		<label class="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
			seed
			<input type="number" step="1" bind:value={seed} class={inputCls} />
		</label>

		<label class="flex flex-col gap-1 text-xs text-[var(--text-muted)]">
			Méthode d'échantillonnage
			<select bind:value={methode} class={inputCls}>
				<option value="LHS">LHS (Latin Hypercube Sampling)</option>
				<option value="MonteCarlo">Monte Carlo pur</option>
			</select>
		</label>

<Button onclick={onLancer} disabled={running} type="button">
		{#if running}
			<span
				class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white"
			></span>
			Simulation en cours…
		{:else}
			Lancer la simulation
		{/if}
	</Button>

	{#if running}
		<div class="flex items-center gap-2">
			<div class="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--border)]">
				<div
					class="h-full rounded-full transition-all duration-300"
					style="width:{Math.max(2, progress)}%; background:var(--accent)"
				></div>
			</div>
			<span class="tabular text-xs text-[var(--text-muted)]">{progress.toFixed(0)}%</span>
		</div>
	{:else if progress === 100}
		<p class="text-xs text-[var(--text-muted)]">Campagne terminée — données disponibles.</p>
	{/if}

	{#if error}
		<p class="text-sm text-[var(--critical)]">{error}</p>
	{/if}
	</div>
</div>
