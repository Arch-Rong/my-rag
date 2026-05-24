'use client';

import { Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
	applyTheme,
	resolveTheme,
	toggleTheme,
	type Theme,
} from '@/lib/theme-preference';

export function ThemeToggle() {
	const [theme, setTheme] = useState<Theme>('light');
	const [mounted, setMounted] = useState(false);

	useEffect(() => {
		const current = resolveTheme();
		applyTheme(current);
		setTheme(current);
		setMounted(true);
	}, []);

	function handleToggle() {
		setTheme(toggleTheme());
	}

	return (
		<Button
			type='button'
			variant='ghost'
			size='icon-sm'
			className='text-muted-foreground hover:text-foreground size-8'
			onClick={handleToggle}
			disabled={!mounted}
			aria-label={theme === 'dark' ? '切换浅色模式' : '切换深色模式'}
		>
			{theme === 'dark' ? (
				<Moon className='size-4' />
			) : (
				<Sun className='size-4' />
			)}
		</Button>
	);
}
