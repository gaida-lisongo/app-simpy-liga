// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			user: {
				email: string;
				nom: string;
				role: 'admin' | 'chercheur';
				statut: 'declared' | 'active';
				created_at: string;
				activated_at: string | null;
			} | null;
		}
		interface PageData {
			user: Locals['user'];
		}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
