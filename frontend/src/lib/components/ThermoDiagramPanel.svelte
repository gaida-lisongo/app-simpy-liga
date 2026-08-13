<script>
	/**
	 * Panneau diagramme thermodynamique — types P-s / T-s / T-P, sélection d'un composant
	 * (segment du cycle) à mettre en évidence. Alimenté par resultats.etats_cycle (cycle de
	 * référence à valeurs nominales).
	 * @type {{
	 *   etats: { point: string, T?: number, P?: number, h?: number, s?: number, x?: number }[] | undefined,
	 *   segments: { label: string, from: string, to: string }[],
	 *   accent: string
	 * }}
	 */
	let { etats, segments, accent } = $props();

	const TYPES = [
		{ id: 'Ts', label: 'T-s', xLabel: 's (kJ/kg·K)', yLabel: 'T (°C)' },
		{ id: 'Ps', label: 'P-s', xLabel: 's (kJ/kg·K)', yLabel: 'log P (bar)' },
		{ id: 'TP', label: 'T-P', xLabel: 'log P (bar)', yLabel: 'T (°C)' }
	];
	let type = $state('Ts');
	let composant = $state('');

	const W = 420, H = 260, PAD = 40;

	/** @param {{T?:number,P?:number,s?:number}} e */
	function coords(e) {
		if (type === 'Ts') return { x: e.s, y: e.T };
		if (type === 'Ps') return { x: e.s, y: e.P != null && e.P > 0 ? Math.log10(e.P) : null };
		return { x: e.P != null && e.P > 0 ? Math.log10(e.P) : null, y: e.T };
	}

	let pts = $derived.by(() => {
		if (!etats?.length) return null;
		const raw = etats.map((e) => ({ point: e.point, ...coords(e) }));
		const valid = raw.filter((p) => p.x != null && p.y != null);
		if (valid.length < 2) return null;

		const xs = valid.map((p) => /** @type {number} */ (p.x));
		const ys = valid.map((p) => /** @type {number} */ (p.y));
		const xMin = Math.min(...xs), xMax = Math.max(...xs);
		const yMin = Math.min(...ys), yMax = Math.max(...ys);
		const sx = (/** @type {number} */ x) => PAD + ((x - xMin) / (xMax - xMin || 1)) * (W - 2 * PAD);
		const sy = (/** @type {number} */ y) => H - PAD - ((y - yMin) / (yMax - yMin || 1)) * (H - 2 * PAD);

		return valid.map((p) => ({ point: p.point, x: sx(/** @type {number} */ (p.x)), y: sy(/** @type {number} */ (p.y)) }));
	});

	let segmentActif = $derived(segments.find((s) => s.label === composant));

	/** @param {string} point */
	function estSurSegment(point) {
		return segmentActif && (point === segmentActif.from || point === segmentActif.to);
	}

	let typeInfo = $derived(TYPES.find((t) => t.id === type));
</script>

<div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4">
	<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
		<h3 class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">Diagramme thermodynamique</h3>
		<div class="flex flex-wrap gap-2">
			<select
				bind:value={type}
				class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2 py-1 text-xs text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none"
			>
				{#each TYPES as t (t.id)}
					<option value={t.id}>{t.label}</option>
				{/each}
			</select>
			{#if segments.length}
				<select
					bind:value={composant}
					class="rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-2 py-1 text-xs text-[var(--text-primary)] focus:border-[var(--accent)] focus:outline-none"
				>
					<option value="">Cycle complet</option>
					{#each segments as s (s.label)}
						<option value={s.label}>{s.label}</option>
					{/each}
				</select>
			{/if}
		</div>
	</div>

	{#if pts}
		<svg viewBox="0 0 {W} {H}" class="w-full" role="img" aria-label="Diagramme {typeInfo?.label} du cycle">
			<line x1={PAD} y1={PAD} x2={PAD} y2={H - PAD} stroke="var(--border)" />
			<line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="var(--border)" />
			<text x={PAD} y={H - 10} font-size="10" fill="var(--text-muted)">{typeInfo?.xLabel}</text>
			<text x="6" y={PAD - 6} font-size="10" fill="var(--text-muted)">{typeInfo?.yLabel}</text>

			<polyline
				points={pts.map((p) => `${p.x},${p.y}`).join(' ')}
				fill="none"
				stroke="var(--border-strong)"
				stroke-width="1.5"
				stroke-linejoin="round"
			/>
			{#each segmentActif ? [segmentActif] : [] as seg (seg.label)}
				{@const a = pts.find((p) => p.point === seg.from)}
				{@const b = pts.find((p) => p.point === seg.to)}
				{#if a && b}
					<line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={accent} stroke-width="3" stroke-linecap="round" />
				{/if}
			{/each}
			{#each pts as p (p.point)}
				<circle cx={p.x} cy={p.y} r="4" fill={estSurSegment(p.point) ? accent : 'var(--text-muted)'} stroke="var(--surface)" stroke-width="2" />
				<text x={p.x + 6} y={p.y - 6} font-size="10" fill="var(--text-secondary)">{p.point}</text>
			{/each}
		</svg>
		<div class="mt-2 flex items-center gap-4 text-[10px] text-[var(--text-muted)]">
			<span class="flex items-center gap-1.5"><span class="h-1.5 w-3 rounded-full" style="background:var(--border-strong)"></span> Cycle</span>
			{#if segmentActif}
				<span class="flex items-center gap-1.5"><span class="h-1.5 w-3 rounded-full" style="background:{accent}"></span> {segmentActif.label}</span>
			{/if}
		</div>
	{:else}
		<p class="py-12 text-center text-sm text-[var(--text-muted)]">
			Non disponible — nécessite les points d'état du cycle. Lancez une campagne.
		</p>
	{/if}
</div>
