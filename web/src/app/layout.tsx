import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

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
		>
			<body className='flex min-h-full flex-col'>{children}</body>
		</html>
	);
}
