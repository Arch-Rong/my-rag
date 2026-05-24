'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

import { ApiError, register } from '@/api/index';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AuthField } from '@/components/auth-screen';
import { getSafeRedirect } from '@/lib/auth-routes';
import { isLoggedIn, setAccessToken } from '@/lib/auth';

export function RegisterForm() {
	const router = useRouter();
	const searchParams = useSearchParams();
	const from = getSafeRedirect(searchParams.get('from'));
	const [displayName, setDisplayName] = useState('');
	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	useEffect(() => {
		if (isLoggedIn()) {
			router.replace(from);
		}
	}, [router, from]);

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault();
		setLoading(true);
		setError(null);
		try {
			const res = await register({
				email,
				password,
				display_name: displayName.trim() || undefined,
			});
			setAccessToken(res.access_token);
			router.replace(from);
		} catch (err) {
			setError(err instanceof ApiError ? err.message : '注册失败，请重试');
		} finally {
			setLoading(false);
		}
	}

	return (
		<form onSubmit={handleSubmit} className='space-y-5'>
			<AuthField id='displayName' label='昵称' hint='选填，用于展示'>
				<Input
					id='displayName'
					type='text'
					autoComplete='name'
					placeholder='例如：张同学'
					className='h-11 bg-background/60'
					value={displayName}
					onChange={(e) => setDisplayName(e.target.value)}
					maxLength={128}
				/>
			</AuthField>

			<AuthField id='email' label='邮箱'>
				<Input
					id='email'
					type='email'
					autoComplete='email'
					placeholder='you@example.com'
					className='h-11 bg-background/60'
					value={email}
					onChange={(e) => setEmail(e.target.value)}
					required
				/>
			</AuthField>

			<AuthField id='password' label='密码' hint='至少 8 位字符'>
				<Input
					id='password'
					type='password'
					autoComplete='new-password'
					placeholder='••••••••'
					className='h-11 bg-background/60'
					value={password}
					onChange={(e) => setPassword(e.target.value)}
					minLength={8}
					required
				/>
			</AuthField>

			{error ? (
				<p className='text-destructive text-center text-sm' role='alert'>
					{error}
				</p>
			) : null}

			<Button type='submit' className='h-11 w-full' disabled={loading}>
				{loading ? (
					<>
						<Loader2 className='size-4 animate-spin' />
						注册中…
					</>
				) : (
					'创建账号'
				)}
			</Button>
		</form>
	);
}

export function RegisterPageFooter() {
	const searchParams = useSearchParams();
	const from = searchParams.get('from');
	const loginHref = from
		? `/login?from=${encodeURIComponent(from)}`
		: '/login';

	return (
		<p>
			已有账号？{' '}
			<Link
				href={loginHref}
				className='text-foreground font-medium transition-colors hover:text-primary'
			>
				登录
			</Link>
		</p>
	);
}
