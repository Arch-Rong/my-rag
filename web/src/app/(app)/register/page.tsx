import { Suspense } from 'react';

import { AuthScreen } from '@/components/auth-screen';
import { RegisterForm, RegisterPageFooter } from '@/components/register-form';

export default function RegisterPage() {
	return (
		<AuthScreen
			title='创建账号'
			subtitle='加入 MedRAG，开始你的智能学习之旅'
			footer={
				<Suspense fallback={null}>
					<RegisterPageFooter />
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
				<RegisterForm />
			</Suspense>
		</AuthScreen>
	);
}
