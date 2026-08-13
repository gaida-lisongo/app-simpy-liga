<script>
	import CircuitPage from '$lib/components/CircuitPage.svelte';
	import { circuitBySlug } from '$lib/constants.js';
</script>

<CircuitPage circuit={circuitBySlug('solaire')} />
