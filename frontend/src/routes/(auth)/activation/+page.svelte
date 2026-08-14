<script>
	import { enhance } from '$app/forms';
	import { fade } from 'svelte/transition';
	import { KeyRound, LoaderCircle, ShieldAlert } from '@lucide/svelte';
	import AuthShell from '$lib/components/features/auth/AuthShell.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	/** @type {{ form: any, data: { token: string, valide: boolean, user: any } }} */
	let { form, data } = $props();

	let pending = $state(false);

	const reinitialisation = $derived(data.user?.statut === 'active');
	const titre = $derived(reinitialisation ? 'Nouveau mot de passe' : 'Activation du compte');
	const sousTitre = $derived(
		reinitialisation
			? `Réinitialisation du mot de passe pour ${data.user?.email}`
			: `Bienvenue ${data.user?.nom ?? ''} — définissez votre mot de passe pour commencer.`
	);

	const inputClass =
		'w-full rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-colors focus:border-[var(--accent)] focus:outline-none';
</script>

{#if data.valide}
	<AuthShell {titre} sousTitre={sousTitre}>
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
			<input type="hidden" name="token" value={data.token} />

			<label class="flex flex-col gap-1.5">
				<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]"
					>Mot de passe</span
				>
				<input
					name="password"
					type="password"
					required
					minlength="8"
					autocomplete="new-password"
					placeholder="8 caractères minimum"
					class={inputClass}
				/>
			</label>

			<label class="flex flex-col gap-1.5">
				<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]"
					>Confirmation</span
				>
				<input
					name="confirm"
					type="password"
					required
					minlength="8"
					autocomplete="new-password"
					placeholder="Répétez le mot de passe"
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
					Enregistrement…
				{:else}
					<KeyRound size={16} />
					{reinitialisation ? 'Définir le mot de passe' : 'Activer mon compte'}
				{/if}
			</Button>
		</form>
	</AuthShell>
{:else}
	<AuthShell titre="Lien invalide">
		<div class="flex flex-col items-center gap-4 text-center">
			<span
				class="flex h-12 w-12 items-center justify-center rounded-full bg-[color-mix(in_oklab,var(--critical)_14%,transparent)] text-[var(--critical)]"
			>
				<ShieldAlert size={24} />
			</span>
			<p class="text-sm text-[var(--text-secondary)]">
				Ce lien d'activation est invalide ou a expiré. Demandez un nouveau lien à un
				administrateur de la plateforme.
			</p>
			<a
				href="/connexion"
				class="text-sm font-medium text-[var(--accent)] transition-opacity hover:opacity-80"
			>
				Aller à la connexion
			</a>
		</div>
	</AuthShell>
{/if}
