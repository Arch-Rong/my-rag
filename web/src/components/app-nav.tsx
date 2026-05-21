'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { MedRagLogoMark } from '@/components/med-rag-logo';
import { APP_HEADER_HEIGHT, PAGE_SHELL } from '@/lib/layout';
import { cn } from '@/lib/utils';

const links = [
	{ href: '/chat', label: '智能问答' },
	{ href: '/library', label: '知识库' },
] as const;

export function AppNav() {
	const pathname = usePathname();

	return (
		<header className='border-border bg-background/95 supports-[backdrop-filter]:bg-background/80 sticky top-0 z-50 border-b backdrop-blur-sm'>
			<div
				className={cn(PAGE_SHELL, 'flex items-center justify-between')}
				style={{ height: APP_HEADER_HEIGHT }}
			>
				<Link
					href='/chat'
					className={cn(
						'group focus-visible:ring-ring/60 -ml-1 flex items-center gap-2.5 rounded-lg px-1.5 py-1',
						'transition-colors outline-none focus-visible:ring-2',
					)}
					aria-label='MedRAG 首页，前往智能问答'
				>
					<MedRagLogoMark />
					<span className='hidden min-w-0 flex-col leading-tight sm:flex'>
						MedRAG
					</span>
				</Link>

				<nav className='flex items-center gap-1' aria-label='主导航'>
					{links.map(({ href, label }) => {
						const active = pathname === href || pathname.startsWith(`${href}/`);
						return (
							<Link
								key={href}
								href={href}
								className={cn(
									'rounded-md px-3 py-1.5 text-sm transition-[color,background-color] duration-150',
									active
										? 'bg-primary/12 text-primary font-medium'
										: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground',
								)}
							>
								{label}
							</Link>
						);
					})}
				</nav>
			</div>
		</header>
	);
}
