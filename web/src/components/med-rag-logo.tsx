import { cn } from '@/lib/utils';

/** 简约书本标识：实心主色底 + 单色线稿 */
export function MedRagLogoMark({ className }: { className?: string }) {
	return (
		<span
			className={cn(
				'bg-primary text-primary-foreground',
				'flex size-8 shrink-0 items-center justify-center rounded-sm',
				'transition-opacity duration-200 ease-out group-hover:opacity-90',
				className,
			)}
			aria-hidden
		>
			<svg viewBox='0 0 24 24' fill='none' className='size-4' aria-hidden>
				<path
					d='M12 6 7.25 7.25V17.75L12 16.25M12 6l4.75 1.25v10.5L12 16.25'
					stroke='currentColor'
					strokeWidth='1.5'
					strokeLinecap='round'
					strokeLinejoin='round'
				/>
			</svg>
		</span>
	);
}
