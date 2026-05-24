import { Suspense } from 'react';

import { AuthScreen } from '@/components/auth-screen';
import { LoginForm, LoginPageFooter } from '@/components/login-form';

export default function LoginPage() {
	return (
		<AuthScreen
			title='欢迎回来'
			subtitle='登录后管理知识库，上传教材与笔记'
			footer={
				<Suspense fallback={null}>
					<LoginPageFooter />
				</Suspense>
			}
		>
			<Suspense
				fallback={
					<p className='text-muted-foreground py-8 text-center text-sm'>
						加载中…
					</p>
				}
			>
				<LoginForm />
			</Suspense>
		</AuthScreen>
	);
}
