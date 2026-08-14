<script>
	import { fly } from 'svelte/transition';
	import favicon from '$lib/assets/favicon.svg';

	/** @type {{ titre: string, sousTitre?: string, children: import('svelte').Snippet }} */
	let { titre, sousTitre = '', children } = $props();
</script>

<div class="flex min-h-[70vh] items-center justify-center px-4 py-10">
	<div class="w-full max-w-md" in:fly={{ y: 12, duration: 220 }}>
		<div class="mb-6 flex flex-col items-center gap-3 text-center">
			<img src={favicon} alt="" class="h-10 w-10" />
			<div>
				<h1 class="text-xl font-semibold text-[var(--text-primary)]">{titre}</h1>
				{#if sousTitre}
					<p class="mt-1 text-sm text-[var(--text-muted)]">{sousTitre}</p>
				{/if}
			</div>
		</div>
		<div
			class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8"
		>
			{@render children()}
		</div>
	</div>
</div>
