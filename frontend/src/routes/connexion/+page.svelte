<script>
	import { enhance } from '$app/forms';
	import { fade } from 'svelte/transition';
	import { LogIn, LoaderCircle } from '@lucide/svelte';
	import AuthShell from '$lib/components/features/auth/AuthShell.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	/** @type {{ form: any }} */
	let { form } = $props();

	let pending = $state(false);

	const inputClass =
		'w-full rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-colors focus:border-[var(--accent)] focus:outline-none';
</script>

<AuthShell titre="Connexion" sousTitre="Accédez à votre environnement SimpyLIGA">
	<form
		method="post"
		use:enhance={() => {
			pending = true;
			return ({ update }) => {
				pending = false;
				update();
			};
		}}
		class="flex flex-col gap-4"
	>
		<label class="flex flex-col gap-1.5">
			<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">Email</span>
			<input
				name="email"
				type="email"
				required
				autocomplete="email"
				value={form?.email ?? ''}
				placeholder="vous@exemple.cd"
				class={inputClass}
			/>
		</label>

		<label class="flex flex-col gap-1.5">
			<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]"
				>Mot de passe</span
			>
			<input
				name="password"
				type="password"
				required
				autocomplete="current-password"
				placeholder="••••••••"
				class={inputClass}
			/>
		</label>

		{#if form?.error}
			<p
				in:fade={{ duration: 150 }}
				role="alert"
				class="rounded-[var(--radius-sm)] bg-[color-mix(in_oklab,var(--critical)_14%,transparent)] px-3 py-2 text-sm text-[var(--critical)]"
			>
				{form.error}
			</p>
		{/if}

		<Button type="submit" disabled={pending}>
			{#if pending}
				<LoaderCircle size={16} class="animate-spin" />
				Connexion en cours…
			{:else}
				<LogIn size={16} />
				Se connecter
			{/if}
		</Button>
	</form>
</AuthShell>
