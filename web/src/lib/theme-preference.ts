export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'medrag-theme';

export function getStoredTheme(): Theme | null {
	if (typeof window === 'undefined') return null;
	const value = localStorage.getItem(STORAGE_KEY);
	return value === 'light' || value === 'dark' ? value : null;
}

export function resolveTheme(): Theme {
	const stored = getStoredTheme();
	if (stored) return stored;
	if (
		typeof window !== 'undefined' &&
		window.matchMedia('(prefers-color-scheme: dark)').matches
	) {
		return 'dark';
	}
	return 'light';
}

export function applyTheme(theme: Theme): void {
	document.documentElement.classList.toggle('dark', theme === 'dark');
}

export function setTheme(theme: Theme): void {
	localStorage.setItem(STORAGE_KEY, theme);
	applyTheme(theme);
}

export function toggleTheme(): Theme {
	const next: Theme = document.documentElement.classList.contains('dark')
		? 'light'
		: 'dark';
	setTheme(next);
	return next;
}

/** 供 layout 内联脚本使用，避免首屏主题闪烁 */
export const THEME_INIT_SCRIPT = `(function(){try{var k='${STORAGE_KEY}';var t=localStorage.getItem(k);if(t==='dark'||(t!=='light'&&window.matchMedia('(prefers-color-scheme: dark)').matches))document.documentElement.classList.add('dark')}catch(e){}})();`;
