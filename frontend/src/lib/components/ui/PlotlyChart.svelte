<script>
	import { onMount, onDestroy } from 'svelte';

	/**
	 * Wrapper Svelte générique pour Plotly.js — mode sombre.
	 * @type {{
	 *   data?: any[],
	 *   layout?: any,
	 *   config?: any,
	 *   className?: string
	 * }}
	 */
	let { data = [], layout = {}, config = { responsive: true, displayModeBar: false }, className = '' } = $props();

	let container = $state(null);
	let PlotlyInstance = $state(null);
	let plotError = $state('');

	const darkLayout = {
		paper_bgcolor: 'transparent',
		plot_bgcolor: 'transparent',
		font: { color: '#a1a1aa', size: 11 },
		xaxis: {
			gridcolor: '#27272a', linecolor: '#3f3f46',
			zerolinecolor: '#27272a', tickfont: { color: '#71717a', size: 9 }
		},
		yaxis: {
			gridcolor: '#27272a', linecolor: '#3f3f46',
			zerolinecolor: '#27272a', tickfont: { color: '#71717a', size: 9 }
		},
		margin: { t: 10, r: 10, b: 36, l: 42 },
		legend: {
			bgcolor: '#111113', bordercolor: '#27272a',
			borderwidth: 1, font: { color: '#a1a1aa', size: 9 }
		}
	};

	/** Fusionne le layout dark avec le layout passé en props (merge peu profond par axe). */
	function mergeLayout() {
		const merged = { ...darkLayout, ...layout };
		for (const axis of ['xaxis', 'yaxis']) {
			if (layout?.[axis]) merged[axis] = { ...darkLayout[axis], ...layout[axis] };
		}
		return merged;
	}

	function draw(/** @type {any[]} */ d) {
		if (!PlotlyInstance || !container) return;
		try {
			PlotlyInstance.react(container, d, mergeLayout(), config);
			plotError = '';
		} catch (/** @type {any} */ e) {
			plotError = `Plotly.react: ${e?.message ?? e}`;
			console.error('[PlotlyChart] react error', e);
		}
	}

	onMount(async () => {
		try {
			const mod = await import('$lib/plotly.js');
			// Interop CJS robuste : le default peut être niché selon le bundler.
			PlotlyInstance = mod.default ?? mod?.default?.default ?? mod;
			if (!PlotlyInstance || typeof PlotlyInstance.newPlot !== 'function') {
				throw new Error(`export Plotly invalide (type=${typeof PlotlyInstance})`);
			}
			PlotlyInstance.newPlot(container, data, mergeLayout(), config);
			plotError = '';
		} catch (/** @type {any} */ e) {
			plotError = `Plotly chargement: ${e?.message ?? e}`;
			console.error('[PlotlyChart] load/newPlot error', e);
		}
	});

	// Re-render réactif quand data/layout changent (et une fois Plotly prêt).
	$effect(() => {
		if (PlotlyInstance && container && data) draw(data);
	});

	// Responsive : recale le graphique quand la taille du conteneur change (flex,
	// grid, redimensionnement fenêtre). Plotly `responsive:true` ne gère que le
	// resize de fenêtre ; un ResizeObserver couvre aussi les changements de hauteur
	// flex/grid qui ne déclenchent pas l'événement window resize.
	/** @type {ResizeObserver | null} */
	let ro = null;

	onMount(() => {
		if (typeof ResizeObserver !== 'undefined' && container) {
			ro = new ResizeObserver(() => {
				if (PlotlyInstance && container && !plotError) {
					try { PlotlyInstance.Plots?.resize?.(container); } catch { /* best-effort */ }
				}
			});
			ro.observe(container);
		}
		window.addEventListener('resize', onResize);
	});

	function onResize() {
		if (PlotlyInstance && container && !plotError) {
			try { PlotlyInstance.Plots?.resize?.(container); } catch { /* best-effort */ }
		}
	}

	onDestroy(() => {
		if (ro) ro.disconnect();
		window.removeEventListener('resize', onResize);
		if (PlotlyInstance && container) {
			try { PlotlyInstance.purge(container); } catch { /* déjà démonté */ }
		}
	});
</script>

{#if plotError}
	<div class="flex h-full min-h-24 flex-col items-center justify-center rounded-[var(--radius-sm)] border border-[var(--critical)] bg-[var(--surface)] p-3 text-center">
		<p class="text-xs text-[var(--critical)]">Graphique indisponible</p>
		<p class="mt-1 max-w-full break-words text-[10px] text-[var(--text-muted)]">{plotError}</p>
	</div>
{:else}
	<div bind:this={container} class={className} style="width:100%;height:100%;"></div>
{/if}