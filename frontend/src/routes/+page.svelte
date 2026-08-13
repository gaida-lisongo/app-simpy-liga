<script>
	import { getDashboard } from '$lib/api.js';
	import KpiCard from '$lib/components/KpiCard.svelte';
	import StatCard from '$lib/components/StatCard.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import { CIRCUITS, apiCircuitOf } from '$lib/constants.js';

	let loading = $state(true);
	let error = $state('');
	let dash = $state(/** @type {any} */ (null));

	/** @param {boolean} [force] Ignore le cache Redis et relance les campagnes de synthèse. */
	async function load(force = false) {
		loading = true;
		error = '';
		try {
			if (!force) {
				const cached = await fetch('/db/dashboard').then((r) => r.json());
				if (cached) {
					dash = cached;
					return;
				}
			}
			dash = await getDashboard();
			fetch('/db/dashboard', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(dash)
			}).catch(() => {});
		} catch (/** @type {any} */ e) {
			error = e?.message ?? 'Erreur de chargement du dashboard.';
		} finally {
			loading = false;
		}
	}

	load();

	/** @param {number | null | undefined} v @param {number} [d] */
	function fmt(v, d = 3) {
		return v === undefined || v === null ? '—' : Number(v).toFixed(d);
	}

	let copMoyen = $derived.by(() => {
		if (!dash) return null;
		const vals = Object.values(dash.circuits)
			.map((c) => c.COP?.moyenne)
			.filter((v) => v !== undefined && v !== null);
		if (!vals.length) return null;
		return vals.reduce((a, b) => a + b, 0) / vals.length;
	});

	let rejetMax = $derived.by(() => {
		if (!dash) return null;
		const vals = Object.values(dash.circuits)
			.map((c) => c.taux_rejet_pct)
			.filter((v) => v !== undefined && v !== null);
		return vals.length ? Math.max(...vals) : null;
	});
</script>

<header class="mb-6 flex flex-wrap items-start justify-between gap-3">
	<div>
		<h1 class="text-2xl font-semibold text-[var(--text-primary)]">Dashboard</h1>
		<p class="mt-1 text-sm text-[var(--text-secondary)]">
			Synthèse globale — 4 circuits, dimensionnement inverse cible {dash?.cible_kW ?? 12} kW
		</p>
	</div>
	<div class="flex items-center gap-2">
		{#if dash?.coeur_physique_reel !== undefined}
			<Badge tone={dash.coeur_physique_reel ? 'good' : 'warning'}>
				{dash.coeur_physique_reel ? 'Cœur physique réel (CoolProp)' : 'Cœur physique indisponible'}
			</Badge>
		{:else if dash?.agrege_depuis_cache}
			<Badge tone="neutral">Synthèse agrégée (cache)</Badge>
		{/if}
		<Button variant="secondary" onclick={() => load(true)} disabled={loading}>
			{loading ? 'Campagne en cours…' : 'Rafraîchir'}
		</Button>
	</div>
</header>

{#if loading && !dash}
	<div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
		<p class="text-sm text-[var(--text-secondary)]">
			Campagnes de synthèse en cours sur les 4 circuits (LHS, 500 tirages chacune) — cela peut
			prendre jusqu'à quelques minutes.
		</p>
	</div>
{:else if error}
	<p class="text-sm text-[var(--critical)]">{error}</p>
{:else if dash}
	<section class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
		<KpiCard label="COP moyen (4 circuits)" value={fmt(copMoyen)} sub="Coefficient de performance" />
		<KpiCard
			label="μ moyen"
			value="—"
			sub="Taux d'entraînement — voir pages circuits"
			tone="neutral"
		/>
		<KpiCard
			label="Taux de rejet max"
			value={rejetMax !== null ? `${fmt(rejetMax, 1)}%` : '—'}
			sub="Tirages non-physiques"
			tone={rejetMax && rejetMax > 1 ? 'warning' : 'good'}
		/>
		<KpiCard label="Cible Q_evap" value={`${dash.cible_kW} kW`} sub="Imposée — dimensionnement inverse" tone="accent" />
	</section>

	<section>
		<h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
			Par circuit
		</h2>
		<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
			{#each CIRCUITS as circuit (circuit.slug)}
				{@const c = dash.circuits[apiCircuitOf(circuit)]}
				<div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5">
					<div class="mb-3 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<Badge tone="accent">{circuit.id}</Badge>
							<a href="/{circuit.slug}" class="text-sm font-medium text-[var(--text-primary)] hover:underline">
								{circuit.titre}
							</a>
						</div>
						{#if c}
							<Badge tone={(c.taux_rejet_pct ?? 0) > 1 ? 'warning' : 'good'}>
								Rejet {fmt(c.taux_rejet_pct, 1)}%
							</Badge>
						{/if}
					</div>
					{#if c}
						<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
							<StatCard label="COP" stat={c.COP} />
							<StatCard label="η_ex" stat={c.eta_ex} />
							<StatCard label="ṁ_p (kg/s)" stat={c.m_dot_pri} decimals={5} />
						</div>
					{:else}
						<p class="text-sm text-[var(--text-muted)]">Aucune donnée pour ce circuit.</p>
					{/if}
				</div>
			{/each}
		</div>
	</section>

	{#if dash.campagne_id}
		<p class="mt-6 text-xs text-[var(--text-muted)]">Campagne de synthèse : {dash.campagne_id}</p>
	{/if}
{/if}
