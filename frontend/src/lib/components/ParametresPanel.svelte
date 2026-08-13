<script>
	import ParamEditor from '$lib/components/ParamEditor.svelte';

	/**
	 * @type {{
	 *   params: any[],
	 *   loading: boolean,
	 *   error?: string
	 * }}
	 */
	let { params, loading, error = '' } = $props();
</script>

<section>
	<h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
		Paramètres incertains
	</h2>

	{#if loading}
		<p class="text-sm text-[var(--text-muted)]">Chargement de la configuration…</p>
	{:else if error}
		<p class="text-sm text-[var(--critical)]">{error}</p>
	{:else if params.length === 0}
		<p class="text-sm text-[var(--text-muted)]">Aucun paramètre incertain pour ce circuit.</p>
	{:else}
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
			{#each params as param (param.nom)}
				<ParamEditor {param} />
			{/each}
		</div>
	{/if}
</section>
