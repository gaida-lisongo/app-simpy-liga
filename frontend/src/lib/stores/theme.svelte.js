import { browser } from '$app/environment';

let theme = $state(/** @type {'light' | 'dark'} */ ('dark'));

function apply(/** @type {'light' | 'dark'} */ value) {
	if (!browser) return;
	document.documentElement.setAttribute('data-theme', value);
	try {
		localStorage.setItem('theme', value);
	} catch (_) {}
}

export const themeStore = {
	get value() {
		return theme;
	},
	set(/** @type {'light' | 'dark'} */ next) {
		if (next !== 'light' && next !== 'dark') return;
		theme = next;
		apply(next);
	},
	toggle() {
		const next = theme === 'dark' ? 'light' : 'dark';
		theme = next;
		apply(next);
	},
	syncFromDom() {
		if (!browser) return;
		const attr = document.documentElement.getAttribute('data-theme');
		if ((attr === 'light' || attr === 'dark') && theme !== attr) {
			theme = attr;
		}
	}
};