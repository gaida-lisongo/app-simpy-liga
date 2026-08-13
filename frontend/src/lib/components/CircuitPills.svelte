<script>
	import { page } from '$app/state';
	import { CIRCUITS } from '$lib/constants.js';
</script>

<nav class="hidden items-center gap-1 md:flex">
	{#each CIRCUITS as c (c.slug)}
		{@const href = `/${c.slug}`}
		{@const active = page.url.pathname === href}
		<a
			{href}
			class="rounded-full border px-3 py-1.5 text-xs font-medium transition-colors"
			style={active
				? 'background:rgba(250,250,250,0.10); border-color:rgba(250,250,250,0.40); color:var(--text-primary)'
				: 'background:transparent; border-color:transparent; color:var(--text-muted)'}
		>
			{c.id}
		</a>
	{/each}
</nav>
