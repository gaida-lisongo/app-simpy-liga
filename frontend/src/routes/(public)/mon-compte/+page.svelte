<script>
	import { enhance } from '$app/forms';
	import { fade, scale } from 'svelte/transition';
	import { User, Mail, ShieldAlert, Trash2, AlertTriangle, LoaderCircle } from '@lucide/svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	/** @type {{ form: any, data: { user: { email: string, nom: string, role: string, statut: string } } }} */
	let { form, data } = $props();

	let confirmOuvert = $state(false);
	let confirmationTexte = $state('');
	let pendingSuppression = $state(false);

	const peutConfirmer = $derived(confirmationTexte === 'SUPPRIMER');

	const inputClass =
		'w-full rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-colors focus:border-[var(--accent)] focus:outline-none';
</script>

<div class="mx-auto max-w-2xl">
	<header class="mb-8 flex items-center gap-3">
		<span
			class="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-soft)] text-[var(--accent)]"
		>
			<User size={20} />
		</span>
		<div>
			<h1 class="text-lg font-semibold text-[var(--text-primary)]">Mon compte</h1>
			<p class="text-sm text-[var(--text-muted)]">
				Consultez vos informations et gérez votre compte
			</p>
		</div>
	</header>

	<section
		in:fade={{ duration: 200 }}
		class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5"
	>
		<h2 class="mb-4 text-sm font-semibold text-[var(--text-primary)]">Informations</h2>
		<dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
			<div class="flex flex-col gap-1">
				<dt class="text-xs uppercase tracking-wide text-[var(--text-muted)]">Nom</dt>
				<dd class="text-sm text-[var(--text-primary)]">{data.user.nom}</dd>
			</div>
			<div class="flex flex-col gap-1">
				<dt class="text-xs uppercase tracking-wide text-[var(--text-muted)]">Email</dt>
				<dd class="flex items-center gap-2 text-sm text-[var(--text-primary)]">
					<Mail size={14} class="text-[var(--text-muted)]" />
					<span class="truncate">{data.user.email}</span>
				</dd>
			</div>
			<div class="flex flex-col gap-1">
				<dt class="text-xs uppercase tracking-wide text-[var(--text-muted)]">Rôle</dt>
				<dd>
					<Badge tone={data.user.role === 'admin' ? 'accent' : 'neutral'}>
						{data.user.role}
					</Badge>
				</dd>
			</div>
		</dl>
	</section>

	<section
		in:fade={{ duration: 200, delay: 60 }}
		class="mt-6 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5"
	>
		<h2 class="mb-1 flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
			<ShieldAlert size={16} class="text-[var(--critical)]" />
			Zone sensible
		</h2>
		<p class="mb-4 text-sm text-[var(--text-muted)]">
			La suppression de votre compte est définitive. Toutes vos sessions actives
			seront révoquées et votre adresse email redeviendra disponible.
		</p>

		<button
			type="button"
			onclick={() => (confirmOuvert = true)}
			class="inline-flex items-center gap-2 rounded-[var(--radius-sm)] border border-[var(--critical)]/40 px-4 py-2 text-sm font-medium text-[var(--critical)] transition-all duration-150 hover:bg-[color-mix(in_oklab,var(--critical)_10%,transparent)] active:scale-[0.98]"
		>
			<Trash2 size={14} />
			Supprimer mon compte
		</button>
	</section>
</div>

{#if confirmOuvert}
	<div
		role="dialog"
		aria-modal="true"
		aria-labelledby="auto-suppression-titre"
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
		transition:fade={{ duration: 150 }}
	>
		<div
			class="w-full max-w-md rounded-[var(--radius-lg)] border border-[var(--border-strong)] bg-[var(--surface)] p-6 shadow-2xl"
			transition:scale={{ duration: 180, start: 0.96 }}
		>
			<div class="mb-4 flex items-start gap-3">
				<span
					class="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[color-mix(in_oklab,var(--critical)_18%,transparent)] text-[var(--critical)]"
				>
					<AlertTriangle size={18} />
				</span>
				<div class="min-w-0">
					<h2
						id="auto-suppression-titre"
						class="text-base font-semibold text-[var(--text-primary)]"
					>
						Supprimer votre compte ?
					</h2>
					<p class="mt-1 text-sm text-[var(--text-muted)]">
						Vous serez déconnecté immédiatement. Cette action est irréversible.
					</p>
				</div>
			</div>

			<form
				method="post"
				action="?/supprimer"
				use:enhance={() => {
					pendingSuppression = true;
					return ({ update }) => {
						pendingSuppression = false;
						update();
					};
				}}
				class="flex flex-col gap-3"
			>
				<label class="flex flex-col gap-1.5">
					<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
						Tapez <code class="font-mono">SUPPRIMER</code> pour confirmer
					</span>
					<input
						type="text"
						name="confirmation"
						bind:value={confirmationTexte}
						autocomplete="off"
						class={inputClass}
						placeholder="SUPPRIMER"
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

				<div class="mt-2 flex justify-end gap-2">
					<button
						type="button"
						onclick={() => {
							confirmOuvert = false;
							confirmationTexte = '';
						}}
						class="inline-flex items-center justify-center rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] transition-all duration-150 hover:border-[var(--text-primary)] active:scale-[0.98]"
					>
						Annuler
					</button>
					<button
						type="submit"
						disabled={!peutConfirmer || pendingSuppression}
						class="inline-flex items-center justify-center gap-2 rounded-[var(--radius-sm)] px-4 py-2 text-sm font-medium text-white transition-all duration-150 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
						style="background:var(--critical)"
					>
						{#if pendingSuppression}
							<LoaderCircle size={14} class="animate-spin" />
							Suppression…
						{:else}
							<Trash2 size={14} />
							Supprimer définitivement
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}