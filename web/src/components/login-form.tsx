'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

import { ApiError, login } from '@/api/index';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AuthField } from '@/components/auth-screen';
import { getSafeRedirect } from '@/lib/auth-routes';
import { isLoggedIn, setAccessToken } from '@/lib/auth';

export function LoginForm() {
	const router = useRouter();
	const searchParams = useSearchParams();
	const from = getSafeRedirect(searchParams.get('from'));

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
			const res = await login({ email, password });
			setAccessToken(res.access_token);
			router.replace(from);
		} catch (err) {
			setError(err instanceof ApiError ? err.message : '登录失败，请重试');
		} finally {
			setLoading(false);
		}
	}

	return (
		<form onSubmit={handleSubmit} className='space-y-5'>
			<AuthField id='email' label='邮箱'>
				<Input
					id='email'
					type='email'
					autoComplete='email'
					placeholder='you@example.com'
					className='bg-background/60 h-11'
					value={email}
					onChange={(e) => setEmail(e.target.value)}
					required
				/>
			</AuthField>

			<AuthField id='password' label='密码'>
				<Input
					id='password'
					type='password'
					autoComplete='current-password'
					placeholder='••••••••'
					className='bg-background/60 h-11'
					value={password}
					onChange={(e) => setPassword(e.target.value)}
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
						登录中…
					</>
				) : (
					'登录'
				)}
			</Button>

			<p className='text-muted-foreground border-border/60 border-t pt-5 text-center text-xs leading-relaxed'>
				演示账号{' '}
				<button
					type='button'
					className='text-primary hover:underline'
					onClick={() => {
						setEmail('admin@qq.com');
						setPassword('12345678');
					}}
				>
					一键填入
				</button>
			</p>
		</form>
	);
}

export function LoginPageFooter() {
	const searchParams = useSearchParams();
	const from = searchParams.get('from');
	const registerHref = from
		? `/register?from=${encodeURIComponent(from)}`
		: '/register';

	return (
		<p>
			还没有账号？{' '}
			<Link
				href={registerHref}
				className='text-foreground hover:text-primary font-medium transition-colors'
			>
				注册
			</Link>
		</p>
	);
}
