'use client';

import Link from 'next/link';
import { Library, LogOut, MessageCircle } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { fetchMe, type UserResponse } from '@/api/endpoints/auth';
import { MedRagLogoMark } from '@/components/med-rag-logo';
import { GithubIcon } from '@/components/github-icon';
import { ThemeToggle } from '@/components/theme-toggle';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from '@/components/ui/tooltip';
import { APP_HEADER_HEIGHT, PAGE_SHELL } from '@/lib/layout';
import { clearAccessToken, isLoggedIn } from '@/lib/auth';
import { GITHUB_REPO_URL } from '@/lib/site';
import { getUserDisplayName, getUserInitials } from '@/lib/user-display';
import { cn } from '@/lib/utils';

const links = [
	{ href: '/chat', label: '智能问答', icon: MessageCircle },
	{ href: '/library', label: '知识库', icon: Library, requiresAuth: true },
] as const;

export function AppNav() {
	const pathname = usePathname();
	const router = useRouter();
	const [loggedIn, setLoggedIn] = useState(false);
	const [user, setUser] = useState<UserResponse | null>(null);

	useEffect(() => {
		const authed = isLoggedIn();
		setLoggedIn(authed);
		if (!authed) {
			setUser(null);
			return;
		}
		let cancelled = false;
		fetchMe()
			.then((me) => {
				if (!cancelled) setUser(me);
			})
			.catch(() => {
				if (!cancelled) setUser(null);
			});
		return () => {
			cancelled = true;
		};
	}, [pathname]);

	function handleLogout() {
		clearAccessToken();
		setLoggedIn(false);
		setUser(null);
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
					<TooltipProvider>
						<nav className='flex items-center gap-0.5' aria-label='主导航'>
							{links.map(({ href, label, icon: Icon, ...rest }) => {
								const requiresAuth =
									'requiresAuth' in rest && rest.requiresAuth;
								const targetHref =
									requiresAuth && !loggedIn
										? `/login?from=${encodeURIComponent(href)}`
										: href;
								const active =
									pathname === href || pathname.startsWith(`${href}/`);

								return (
									<Tooltip key={href}>
										<TooltipTrigger asChild>
											<Button
												variant='ghost'
												size='icon-sm'
												className={cn(
													'size-8',
													active
														? 'bg-primary/12 text-primary dark:bg-muted dark:text-primary'
														: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground',
												)}
												asChild
											>
												<Link href={targetHref} aria-label={label}>
													<Icon className='size-4' />
												</Link>
											</Button>
										</TooltipTrigger>
										<TooltipContent side='bottom'>{label}</TooltipContent>
									</Tooltip>
								);
							})}
						</nav>
					</TooltipProvider>

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
						<div
							className='bg-border/80 hidden h-5 w-px sm:block'
							aria-hidden
						/>
						{loggedIn ? (
							<DropdownMenu>
								<DropdownMenuTrigger asChild>
									<Button
										type='button'
										variant='ghost'
										size='icon-sm'
										className='size-8 rounded-full p-0'
										aria-label='账户菜单'
									>
										<Avatar className='size-8'>
											<AvatarFallback className='bg-primary/12 text-primary text-xs font-medium'>
												{getUserInitials(user)}
											</AvatarFallback>
										</Avatar>
									</Button>
								</DropdownMenuTrigger>
								<DropdownMenuContent align='end' className='w-56'>
									<DropdownMenuLabel className='font-normal'>
										<div className='flex flex-col gap-0.5'>
											<span className='text-foreground font-medium'>
												{getUserDisplayName(user)}
											</span>
											{user?.email ? (
												<span className='text-muted-foreground text-xs'>
													{user.email}
												</span>
											) : null}
										</div>
									</DropdownMenuLabel>
									<DropdownMenuSeparator />
									<DropdownMenuItem
										variant='destructive'
										onClick={handleLogout}
									>
										<LogOut className='size-4' />
										退出登录
									</DropdownMenuItem>
								</DropdownMenuContent>
							</DropdownMenu>
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
							</div>
						)}

						<div
							className='bg-border/80 hidden h-5 w-px sm:block'
							aria-hidden
						/>
					</div>
				</div>
			</div>
		</header>
	);
}
