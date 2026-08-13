<script>
	import { fade, fly } from 'svelte/transition';

	/**
	 * Side drawer (tiroir latéral) — primitive UI réutilisable.
	 * Backdrop en `fade`, panneau en `fly` (droite→gauche), fermeture par Échap
	 * ou clic hors du panneau. Verrouille le scroll body quand ouvert.
	 * @type {{
	 *   open?: boolean,
	 *   title?: string,
	 *   side?: 'right' | 'left',
	 *   width?: string,
	 *   onClose?: () => void,
	 *   children?: import('svelte').Snippet,
	 *   footer?: import('svelte').Snippet
	 * }}
	 */
	let { open = $bindable(false), title = '', side = 'right', width = '420px', onClose, children, footer } = $props();

	function close() {
		open = false;
		onClose?.();
	}

	/** @param {KeyboardEvent} e */
	function onKeydown(e) {
		if (e.key === 'Escape' && open) close();
	}

	// Verrouille le scroll du body tant que le drawer est ouvert.
	$effect(() => {
		if (open) {
			document.body.style.overflow = 'hidden';
			return () => (document.body.style.overflow = '');
		}
	});
</script>

<svelte:window onkeydown={onKeydown} />

{#if open}
	<div class="fixed inset-0 z-50">
		<!-- Backdrop -->
		<button
			type="button"
			aria-label="Fermer le panneau"
			class="absolute inset-0 cursor-default bg-black/60 backdrop-blur-sm"
			onclick={close}
			transition:fade={{ duration: 180 }}
		></button>

		<!-- Panel -->
		<aside
			role="dialog"
			aria-modal="true"
			aria-label={title}
			class="absolute top-0 flex h-full flex-col border-[var(--border-strong)] bg-[var(--surface)] shadow-2xl {side === 'right' ? 'right-0 border-l' : 'left-0 border-r'}"
			style="width:{width}; max-width:92vw;"
			transition:fly={{ x: side === 'right' ? 420 : -420, duration: 220, opacity: 1 }}
		>
			<header class="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
				<h2 class="text-sm font-semibold uppercase tracking-wide text-[var(--text-muted)]">{title}</h2>
				<button
					type="button"
					onclick={close}
					aria-label="Fermer"
					class="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] text-[var(--text-muted)] transition-all duration-200 hover:scale-[1.06] hover:bg-white/5 hover:text-[var(--text-primary)] active:scale-95"
				>
					<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
						<path d="M4 4l8 8M12 4l-8 8" />
					</svg>
				</button>
			</header>

			<div class="flex-1 overflow-y-auto px-5 py-4">
				{@render children?.()}
			</div>

			{#if footer}
				<footer class="border-t border-[var(--border)] px-5 py-4">
					{@render footer()}
				</footer>
			{/if}
		</aside>
	</div>
{/if}