'use client';

import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

import { AppNav } from '@/components/app-nav';
import { isAuthPath } from '@/lib/auth-routes';

export function AppShell({ children }: { children: ReactNode }) {
	const pathname = usePathname();
	const hideNav = isAuthPath(pathname);

	return (
		<div className='bg-background flex min-h-dvh flex-col'>
			{!hideNav ? <AppNav /> : null}
			<main className='flex min-h-0 flex-1 flex-col'>{children}</main>
		</div>
	);
}
