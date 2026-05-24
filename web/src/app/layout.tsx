import Script from 'next/script';
import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

import { THEME_INIT_SCRIPT } from '@/lib/theme-preference';

const geistSans = Geist({
	variable: '--font-geist-sans',
	subsets: ['latin'],
});

const geistMono = Geist_Mono({
	variable: '--font-geist-mono',
	subsets: ['latin'],
});

export const metadata: Metadata = {
	title: 'MedRAG — 医学生智能知识助手',
	description: '基于医学知识库的可溯源 RAG 学习助手',
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html
			lang='zh-CN'
			className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
			suppressHydrationWarning
		>
			<body className='flex min-h-full flex-col'>
				<Script id='theme-init' strategy='beforeInteractive'>
					{THEME_INIT_SCRIPT}
				</Script>
				{children}
			</body>
		</html>
	);
}
