'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { MedRagLogoMark } from '@/components/med-rag-logo';
import { GithubIcon } from '@/components/github-icon';
import { ThemeToggle } from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';
import { APP_HEADER_HEIGHT, PAGE_SHELL } from '@/lib/layout';
import { clearAccessToken, isLoggedIn } from '@/lib/auth';
import { GITHUB_REPO_URL } from '@/lib/site';
import { cn } from '@/lib/utils';

const links = [
	{ href: '/chat', label: '智能问答' },
	{ href: '/library', label: '知识库', requiresAuth: true },
] as const;

export function AppNav() {
	const pathname = usePathname();
	const router = useRouter();
	const [loggedIn, setLoggedIn] = useState(false);

	useEffect(() => {
		setLoggedIn(isLoggedIn());
	}, [pathname]);

	function handleLogout() {
		clearAccessToken();
		setLoggedIn(false);
		router.push('/login');
	}

	return (
		<header className='border-border bg-background/95 supports-[backdrop-filter]:bg-background/80 sticky top-0 z-50 border-b backdrop-blur-sm'>
			<div
				className={cn(PAGE_SHELL, 'flex items-center justify-between gap-4')}
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

				<div className='flex items-center gap-1.5 sm:gap-2'>
					<nav className='flex items-center gap-1' aria-label='主导航'>
						{links.map(({ href, label, ...rest }) => {
							const requiresAuth = 'requiresAuth' in rest && rest.requiresAuth;
							const targetHref =
								requiresAuth && !loggedIn
									? `/login?from=${encodeURIComponent(href)}`
									: href;
							const active =
								pathname === href || pathname.startsWith(`${href}/`);

							return (
								<Link
									key={href}
									href={targetHref}
									className={cn(
										'rounded-md px-3 py-1.5 text-sm transition-[color,background-color] duration-150',
										active
											? 'bg-primary/12 text-primary dark:bg-muted dark:text-primary font-medium'
											: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground',
									)}
								>
									{label}
								</Link>
							);
						})}
					</nav>

					<div className='bg-border/80 hidden h-5 w-px sm:block' aria-hidden />

					{loggedIn ? (
						<Button
							type='button'
							variant='ghost'
							size='sm'
							className='text-muted-foreground hover:text-foreground'
							onClick={handleLogout}
						>
							退出
						</Button>
					) : (
						<div className='flex items-center gap-1'>
							<Button
								variant='ghost'
								size='sm'
								className='text-muted-foreground'
								asChild
							>
								<Link href='/login'>登录</Link>
							</Button>
							<Button size='sm' className='hidden sm:inline-flex' asChild>
								<Link href='/register'>注册</Link>
							</Button>
						</div>
					)}

					<div className='bg-border/80 hidden h-5 w-px sm:block' aria-hidden />

					<div className='flex items-center gap-0.5'>
						<Button
							variant='ghost'
							size='icon-sm'
							className='text-muted-foreground hover:text-foreground size-8'
							asChild
						>
							<a
								href={GITHUB_REPO_URL}
								target='_blank'
								rel='noopener noreferrer'
								aria-label='GitHub 仓库'
							>
								<GithubIcon />
							</a>
						</Button>
						<ThemeToggle />
					</div>
				</div>
			</div>
		</header>
	);
}
