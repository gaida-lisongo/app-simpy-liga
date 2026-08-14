<script>
	import { enhance } from '$app/forms';
	import { fade, fly } from 'svelte/transition';
	import {
		Users,
		UserPlus,
		Mail,
		MailWarning,
		RefreshCw,
		Copy,
		Check,
		LoaderCircle,
		Link
	} from '@lucide/svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	/** @type {{ form: any, data: { users: Array<{ email: string, nom: string, role: string, statut: string, created_at: string }> } }} */
	let { form, data } = $props();

	let pendingCreer = $state(false);
	/** @type {string | null} */
	let pendingRenvoi = $state(null);
	let lienCopie = $state(false);

	const inputClass =
		'w-full rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-colors focus:border-[var(--accent)] focus:outline-none';

	const feedbackCreer = $derived(
		form?.ok && form.section === 'creer' ? form : form?.section === 'creer' ? form : null
	);
	const feedbackRenvoi = $derived(form?.ok && form.section === 'renvoyer' ? form : null);

	/** @param {string} lien */
	async function copierLien(lien) {
		await navigator.clipboard.writeText(lien);
		lienCopie = true;
		setTimeout(() => (lienCopie = false), 2000);
	}
</script>

<div class="mx-auto max-w-5xl">
	<header class="mb-8 flex items-center gap-3">
		<span
			class="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-soft)] text-[var(--accent)]"
		>
			<Users size={20} />
		</span>
		<div>
			<h1 class="text-lg font-semibold text-[var(--text-primary)]">Utilisateurs</h1>
			<p class="text-sm text-[var(--text-muted)]">
				Déclarez les comptes et gérez les accès à la plateforme
			</p>
		</div>
	</header>

	<div class="grid grid-cols-1 gap-6 lg:grid-cols-5">
		<section class="lg:col-span-2" in:fly={{ y: 8, duration: 200 }}>
			<div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-5">
				<h2 class="mb-4 flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
					<UserPlus size={16} class="text-[var(--accent)]" />
					Déclarer un utilisateur
				</h2>

				<form
					method="post"
					action="?/creer"
					use:enhance={() => {
						pendingCreer = true;
						return ({ update }) => {
							pendingCreer = false;
							update();
						};
					}}
					class="flex flex-col gap-3"
				>
					<label class="flex flex-col gap-1.5">
						<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]"
							>Nom complet</span
						>
						<input name="nom" type="text" required placeholder="Prénom Nom" class={inputClass} />
					</label>

					<label class="flex flex-col gap-1.5">
						<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]"
							>Email</span
						>
						<input
							name="email"
							type="email"
							required
							placeholder="utilisateur@exemple.cd"
							class={inputClass}
						/>
					</label>

					<label class="flex flex-col gap-1.5">
						<span class="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]"
							>Rôle</span
						>
						<select name="role" class={inputClass}>
							<option value="chercheur">Chercheur</option>
							<option value="admin">Admin</option>
						</select>
					</label>

					<label class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
						<input
							name="envoyer"
							type="checkbox"
							checked
							class="h-4 w-4 accent-[var(--accent)]"
						/>
						Envoyer le magic link par email
					</label>

					{#if feedbackCreer?.error}
						<p
							in:fade={{ duration: 150 }}
							role="alert"
							class="rounded-[var(--radius-sm)] bg-[color-mix(in_oklab,var(--critical)_14%,transparent)] px-3 py-2 text-sm text-[var(--critical)]"
						>
							{feedbackCreer.error}
						</p>
					{/if}

					{#if feedbackCreer?.ok}
						<div
							in:fade={{ duration: 150 }}
							class="flex flex-col gap-2 rounded-[var(--radius-sm)] bg-[var(--accent-soft)] px-3 py-2 text-sm text-[var(--text-primary)]"
						>
							{#if feedbackCreer.mailEnvoye}
								<p class="flex items-center gap-2">
									<Mail size={14} class="shrink-0 text-[var(--accent)]" />
									Magic link envoyé à {feedbackCreer.email}
								</p>
							{:else}
								{#if feedbackCreer.mailErreur}
									<p class="flex items-center gap-2 text-[var(--warning)]">
										<MailWarning size={14} class="shrink-0" />
										Envoi email impossible — partagez ce lien manuellement :
									</p>
								{/if}
								{#if feedbackCreer.lien}
									<div class="flex items-center gap-2">
										<Link size={14} class="shrink-0 text-[var(--accent)]" />
										<code class="min-w-0 flex-1 truncate text-xs">{feedbackCreer.lien}</code>
										<button
											type="button"
											aria-label="Copier le lien"
											onclick={() => copierLien(feedbackCreer.lien)}
											class="shrink-0 rounded-[var(--radius-sm)] p-1 text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
										>
											{#if lienCopie}
												<Check size={14} class="text-[var(--accent)]" />
											{:else}
												<Copy size={14} />
											{/if}
										</button>
									</div>
								{/if}
							{/if}
						</div>
					{/if}

					<Button type="submit" disabled={pendingCreer}>
						{#if pendingCreer}
							<LoaderCircle size={16} class="animate-spin" />
							Création…
						{:else}
							<UserPlus size={16} />
							Créer l'utilisateur
						{/if}
					</Button>
				</form>
			</div>
		</section>

		<section class="lg:col-span-3" in:fly={{ y: 8, duration: 200, delay: 60 }}>
			<div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)]">
				<div class="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
					<h2 class="text-sm font-semibold text-[var(--text-primary)]">
						Comptes déclarés
					</h2>
					<Badge tone="neutral">{data.users.length}</Badge>
				</div>

				{#if feedbackRenvoi}
					<div
						in:fade={{ duration: 150 }}
						class="mx-5 mt-4 flex flex-col gap-1 rounded-[var(--radius-sm)] bg-[var(--accent-soft)] px-3 py-2 text-sm"
					>
						{#if feedbackRenvoi.mailEnvoye}
							<p class="flex items-center gap-2">
								<Mail size={14} class="shrink-0 text-[var(--accent)]" />
								Magic link renvoyé à {feedbackRenvoi.email}
							</p>
						{:else}
							<p class="flex items-center gap-2 text-[var(--warning)]">
								<MailWarning size={14} class="shrink-0" />
								Envoi email impossible — partagez ce lien manuellement :
							</p>
							{#if feedbackRenvoi.lien}
								<div class="flex items-center gap-2">
									<code class="min-w-0 flex-1 truncate text-xs">{feedbackRenvoi.lien}</code>
									<button
										type="button"
										aria-label="Copier le lien"
										onclick={() => copierLien(feedbackRenvoi.lien)}
										class="shrink-0 rounded-[var(--radius-sm)] p-1 text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
									>
										<Copy size={14} />
									</button>
								</div>
							{/if}
						{/if}
					</div>
				{/if}

				{#if data.users.length === 0}
					<div class="flex flex-col items-center gap-3 px-5 py-12 text-center">
						<Users size={28} class="text-[var(--text-muted)]" />
						<p class="text-sm text-[var(--text-muted)]">
							Aucun utilisateur déclaré pour le moment.
						</p>
					</div>
				{:else}
					<ul class="divide-y divide-[var(--border)]">
						{#each data.users as user (user.email)}
							<li class="flex flex-col gap-3 px-5 py-4 transition-colors hover:bg-white/[0.02] sm:flex-row sm:items-center">
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-medium text-[var(--text-primary)]">
										{user.nom}
									</p>
									<p class="truncate text-xs text-[var(--text-muted)]">{user.email}</p>
								</div>

								<div class="flex items-center gap-2">
									<Badge tone={user.role === 'admin' ? 'accent' : 'neutral'}>
										{user.role}
									</Badge>
									<Badge tone={user.statut === 'active' ? 'good' : 'warning'}>
										{user.statut === 'active' ? 'actif' : 'en attente'}
									</Badge>
								</div>

								<form
									method="post"
									action="?/renvoyer"
									use:enhance={() => {
										pendingRenvoi = user.email;
										return ({ update }) => {
											pendingRenvoi = null;
											update();
										};
									}}
								>
									<input type="hidden" name="email" value={user.email} />
									<input type="hidden" name="nom" value={user.nom} />
									<input
										type="hidden"
										name="reinitialisation"
										value={user.statut === 'active' ? '1' : '0'}
									/>
									<button
										type="submit"
										disabled={pendingRenvoi === user.email}
										class="inline-flex items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--border-strong)] px-2.5 py-1.5 text-xs font-medium text-[var(--text-secondary)] transition-all duration-200 hover:border-[var(--accent)] hover:text-[var(--text-primary)] active:scale-[0.98] disabled:opacity-50"
									>
										{#if pendingRenvoi === user.email}
											<LoaderCircle size={12} class="animate-spin" />
										{:else}
											<RefreshCw size={12} />
										{/if}
										{user.statut === 'active' ? 'Réinitialiser' : 'Renvoyer'}
									</button>
								</form>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</section>
	</div>
</div>
