<script>
	import { getDashboard } from '$lib/api.js';
	import KpiCard from '$lib/components/KpiCard.svelte';
	import StatCard from '$lib/components/StatCard.svelte';
	import BilanEnergetique from '$lib/components/BilanEnergetique.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import { CIRCUITS, apiCircuitOf } from '$lib/constants.js';

	let loading = $state(true);
	let error = $state('');
	let dash = $state(/** @type {any} */ (null));
	let bilans = $state(/** @type {Record<string, { bilan: any, statistiques: any }>} */ ({}));

	/** @param {boolean} [force] Ignore le cache Redis et relance les campagnes de synthèse. */
	async function load(force = false) {
		loading = true;
		error = '';
		try {
			if (!force) {
				const cached = await fetch('/db/dashboard').then((r) => r.json());
				if (cached) {
					dash = cached;
				}
			}
			if (!dash || force) {
				dash = await getDashboard();
				fetch('/db/dashboard', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(dash)
				}).catch(() => {});
			}
			// Bilan énergétique par circuit — depuis les dernières campagnes persistées (Redis).
			loadBilans();
		} catch (/** @type {any} */ e) {
			error = e?.message ?? 'Erreur de chargement du dashboard.';
		} finally {
			loading = false;
		}
	}

	async function loadBilans() {
		try {
			const data = await fetch('/db/campagnes').then((r) => r.json());
			const out = {};
			for (const slug of Object.keys(data || {})) {
				const r = data[slug];
				if (r?.resultats) {
					out[slug] = { bilan: r.resultats.bilan_energetique, statistiques: r.resultats.statistiques };
				}
			}
			bilans = out;
		} catch {
			// Bilan indisponible (vide) — non bloquant, le reste du dashboard s'affiche.
		}
	}

	load();

	/** @param {number | null | undefined} v @param {number} [d] */
	function fmt(v, d = 3) {
		return v === undefined || v === null ? '—' : Number(v).toFixed(d);
	}

	let clearing = $state('');
	let clearError = $state('');

	/** @param {string} slug ou 'all' */
	async function clearCache(slug) {
		clearing = slug;
		clearError = '';
		try {
			const url = slug === 'all' ? '/db/campagnes' : `/db/campagnes?circuit=${slug}`;
			const res = await fetch(url, { method: 'DELETE' });
			if (!res.ok) throw new Error(`Erreur ${res.status}`);
			if (slug === 'all') {
				dash = null;
				bilans = {};
			} else {
				delete bilans[slug];
				bilans = { ...bilans };
			}
		} catch (/** @type {any} */ e) {
			clearError = e?.message ?? 'Erreur lors du nettoyage.';
		} finally {
			clearing = '';
		}
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
		<Button
			variant="ghost"
			onclick={() => clearCache('all')}
			disabled={clearing === 'all'}
			title="Supprimer l'historique de tous les circuits"
		>
			{#if clearing === 'all'}
				<span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--text-muted)]/40 border-t-[var(--text-muted)]"></span>
				Nettoyage…
			{:else}
				<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1m1 0v9a1 1 0 01-1 1H5a1 1 0 01-1-1V4" /><path d="M7 7v4M9 7v4" /></svg>
				Nettoyer le cache
			{/if}
		</Button>
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

	<section class="mb-8">
		<h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">
			Bilan énergétique — machine
		</h2>
		<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
			{#each CIRCUITS as circuit (circuit.slug)}
				{@const b = bilans[apiCircuitOf(circuit)]}
				<div
					class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5"
					style="--accent: {circuit.accent}; --accent-soft: {circuit.accent}22;"
				>
					<div class="mb-3 flex items-center justify-between gap-2">
						<div class="flex items-center gap-2">
							<Badge tone="accent">{circuit.id}</Badge>
							<a href="/{circuit.slug}" class="text-sm font-medium text-[var(--text-primary)] hover:underline">
								{circuit.titre}
							</a>
						</div>
						<button
							type="button"
							onclick={() => clearCache(circuit.slug)}
							disabled={clearing === circuit.slug || !b}
							title="Supprimer l'historique de ce circuit"
							class="flex h-7 w-7 items-center justify-center rounded-[var(--radius-sm)] border border-[var(--border)] text-[var(--text-muted)] transition-all duration-200 hover:scale-[1.05] hover:border-[var(--critical)] hover:text-[var(--critical)] active:scale-95 disabled:pointer-events-none disabled:opacity-30"
						>
							{#if clearing === circuit.slug}
								<span class="h-3 w-3 animate-spin rounded-full border-2 border-[var(--text-muted)]/40 border-t-[var(--text-muted)]"></span>
							{:else}
								<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1m1 0v9a1 1 0 01-1 1H5a1 1 0 01-1-1V4" /></svg>
							{/if}
						</button>
					</div>
					{#if b && b.bilan}
						<BilanEnergetique bilan={b.bilan} statistiques={b.statistiques} />
					{:else}
						<p class="text-sm text-[var(--text-muted)]">
							{clearing === circuit.slug ? 'Données supprimées.' : 'Aucun bilan — lancez une campagne sur ce circuit pour alimenter le bilan global.'}
						</p>
					{/if}
				</div>
			{/each}
		</div>
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
