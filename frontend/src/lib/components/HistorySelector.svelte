<script>
	import { simulationStore } from '$lib/stores/simulationStore.svelte.js';

	/**
	 * Sélecteur d'historique — liste les campagnes passées d'un circuit
	 * (cache Redis qui accumule). L'utilisateur peut revenir à n'importe quelle
	 * campagne précédente. La plus récente est en tête.
	 * @type {{ slug: string, campaigns: any[] }}
	 */
	let { slug, campaigns } = $props();

	function onSelect(/** @type {Event} */ e) {
		const id = /** @type {HTMLSelectElement} */ (e.currentTarget).value;
		if (id) simulationStore.selectCampaign(slug, id);
	}

	/** @param {string | undefined} cid */
	function fmtDate(cid) {
		const m = /^camp_(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/.exec(cid ?? '');
		if (!m) return cid ?? '';
		return `${m[3]}/${m[2]} ${m[4]}:${m[5]}`;
	}

	const selectCls =
		'rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2.5 py-1.5 text-xs text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none transition-colors';
</script>

{#if campaigns?.length}
	<div class="flex items-center gap-2">
		<label for="hist-{slug}" class="text-xs text-[var(--text-muted)]">Historique</label>
		<select id={`hist-${slug}`} onchange={onSelect} class={selectCls} aria-label="Campagnes passées">
			{#each campaigns as cg (cg.id)}
				<option value={cg.id}>
					{fmtDate(cg.campagne_id)} · N={cg.N_iterations ?? '?'}
					{cg.STR != null ? ` · STR=${Number(cg.STR).toFixed(3)}` : (cg.COP != null ? ` · COP=${Number(cg.COP).toFixed(3)}` : '')}
				</option>
			{/each}
		</select>
	</div>
{/if}