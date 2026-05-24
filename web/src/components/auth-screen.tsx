import Link from 'next/link';
import type { ReactNode } from 'react';

import { MedRagLogoMark } from '@/components/med-rag-logo';
import { cn } from '@/lib/utils';

type AuthScreenProps = {
	title: string;
	subtitle: string;
	children: ReactNode;
	footer?: ReactNode;
	className?: string;
};

/** 登录 / 注册页共用布局：留白、轻渐变、居中卡片 */
export function AuthScreen({
	title,
	subtitle,
	children,
	footer,
	className,
}: AuthScreenProps) {
	return (
		<div
			className={cn(
				'relative flex min-h-dvh flex-col items-center justify-center px-6 py-16',
				className,
			)}
		>
			<div
				className='pointer-events-none absolute inset-0 overflow-hidden'
				aria-hidden
			>
				<div className='bg-primary/[0.07] dark:bg-muted/40 absolute -top-40 left-1/2 size-[32rem] -translate-x-1/2 rounded-full blur-3xl' />
				<div className='bg-primary/[0.04] dark:bg-muted/25 absolute -right-20 bottom-0 size-72 rounded-full blur-3xl' />
				<div className='absolute inset-0 bg-[linear-gradient(to_bottom,transparent_0%,oklch(1_0_0/0.4)_100%)] dark:bg-[linear-gradient(to_bottom,transparent_0%,oklch(0.165_0.006_265)_100%)]' />
			</div>

			<div className='relative w-full max-w-[26rem]'>
				<Link
					href='/chat'
					className='group mb-10 flex flex-col items-center gap-3 outline-none'
				>
					<MedRagLogoMark className='size-10 rounded-lg' />
					<span className='text-foreground text-lg font-semibold tracking-tight transition-opacity group-hover:opacity-80'>
						MedRAG
					</span>
					<span className='text-muted-foreground text-xs tracking-wide'>
						医学生学习助手
					</span>
				</Link>

				<div className='border-border/70 bg-card/90 rounded-2xl border p-8 shadow-[0_1px_0_0_rgba(0,0,0,0.04),0_12px_48px_-16px_rgba(0,0,0,0.1)] backdrop-blur-md'>
					<header className='mb-8 text-center'>
						<h1 className='text-foreground text-2xl font-semibold tracking-tight'>
							{title}
						</h1>
						<p className='text-muted-foreground mt-2 text-sm leading-relaxed'>
							{subtitle}
						</p>
					</header>
					{children}
				</div>

				{footer ? (
					<div className='text-muted-foreground mt-8 text-center text-sm'>
						{footer}
					</div>
				) : null}
			</div>
		</div>
	);
}

type AuthFieldProps = {
	id: string;
	label: string;
	children: ReactNode;
	hint?: string;
};

export function AuthField({ id, label, children, hint }: AuthFieldProps) {
	return (
		<div className='space-y-2'>
			<label htmlFor={id} className='text-foreground text-sm font-medium'>
				{label}
			</label>
			{children}
			{hint ? <p className='text-muted-foreground text-xs'>{hint}</p> : null}
		</div>
	);
}
