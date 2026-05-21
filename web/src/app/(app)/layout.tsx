import { AppNav } from '@/components/app-nav';

export default function AppLayout({ children }: { children: React.ReactNode }) {
	return (
		<div className='bg-background flex min-h-dvh flex-col'>
			<AppNav />
			<main className='flex min-h-0 flex-1 flex-col'>{children}</main>
		</div>
	);
}
