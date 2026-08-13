<script>
	import { onMount } from 'svelte';
	import { getHealth } from '$lib/api.js';
	import Badge from '$lib/components/ui/Badge.svelte';

	let health = $state(/** @type {{statut:string, coeur_physique_reel:boolean}|null} */ (null));
	let healthError = $state(false);

	onMount(async () => {
		try {
			health = await getHealth();
		} catch {
			healthError = true;
		}
	});
</script>

{#if health}
	<Badge tone={health.coeur_physique_reel ? 'good' : 'warning'}>
		<span class="h-1.5 w-1.5 rounded-full bg-current"></span>
		<span class="hidden md:inline">
			{health.coeur_physique_reel ? 'Cœur physique réel' : 'Cœur physique indisponible'}
		</span>
	</Badge>
{:else if healthError}
	<Badge tone="critical">API injoignable</Badge>
{:else}
	<Badge tone="neutral">Connexion…</Badge>
{/if}
