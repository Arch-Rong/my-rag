'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
	BookMarked,
	ChevronDown,
	Loader2,
	PanelRightClose,
	PanelRightOpen,
	Send,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { APP_HEADER_HEIGHT, PAGE_SHELL } from '@/lib/layout';
import { cn } from '@/lib/utils';

type Scope = 'all' | 'system' | 'user';

type Message = {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	citations?: { label: string; excerpt: string }[];
};

const MOCK_ANSWER: Message = {
	id: 'a1',
	role: 'assistant',
	content:
		'肺栓塞（PE）是指内源性或外源性栓子阻塞肺动脉或其分支，导致肺循环障碍的临床综合征。典型表现包括突发呼吸困难、胸痛、咯血，严重者可出现休克或猝死。',
	citations: [
		{
			label: '《内科学》第 8 版 · 第 3 章 · p.128',
			excerpt:
				'肺栓塞是由于内源性或外源性栓子堵塞肺动脉或其分支，引起肺循环障碍的临床综合征。',
		},
		{
			label: '《诊断学》第 8 版 · 呼吸系统 · p.42',
			excerpt: '常见症状为呼吸困难、胸痛、咯血，称为「三联征」。',
		},
	],
};

const SCOPE_OPTIONS: { key: Scope; label: string }[] = [
	{ key: 'all', label: '全部' },
	{ key: 'system', label: '教材' },
	{ key: 'user', label: '我的' },
];

function CitationItem({
	index,
	citation,
}: {
	index: number;
	citation: { label: string; excerpt: string };
}) {
	const [open, setOpen] = useState(index === 1);

	return (
		<li className='border-border border-b last:border-0'>
			<Collapsible open={open} onOpenChange={setOpen}>
				<CollapsibleTrigger asChild>
					<button
						type='button'
						className='hover:bg-muted/50 flex w-full items-start gap-2 py-3 text-left text-sm'
					>
						<span className='text-primary w-4 shrink-0 text-xs font-medium'>
							{index}
						</span>
						<span className='text-foreground flex-1 leading-snug'>
							{citation.label}
						</span>
						<ChevronDown
							className={cn(
								'text-muted-foreground size-4 shrink-0 transition-transform',
								open && 'rotate-180',
							)}
						/>
					</button>
				</CollapsibleTrigger>
				<CollapsibleContent>
					<p className='text-muted-foreground pb-3 pl-6 text-xs leading-relaxed'>
						{citation.excerpt}
					</p>
				</CollapsibleContent>
			</Collapsible>
		</li>
	);
}

function CitationsSidebar({
	open,
	onOpenChange,
	citations,
	className,
}: {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	citations?: { label: string; excerpt: string }[];
	className?: string;
}) {
	return (
		<aside
			className={cn(
				'border-border bg-card flex shrink-0 flex-col overflow-hidden border-l transition-[width] duration-300',
				open ? 'w-64' : 'w-0 border-l-0',
				className,
			)}
		>
			<div className='flex h-full w-64 flex-col'>
				<div className='border-border flex items-center justify-between border-b px-4 py-3'>
					<span className='text-foreground text-sm font-medium'>引用来源</span>
					<button
						type='button'
						onClick={() => onOpenChange(false)}
						className='text-muted-foreground hover:text-foreground'
						aria-label='收起'
					>
						<PanelRightClose className='size-4' />
					</button>
				</div>
				<ScrollArea className='flex-1'>
					{citations?.length ? (
						<ul>
							{citations.map((c, i) => (
								<CitationItem key={c.label} index={i + 1} citation={c} />
							))}
						</ul>
					) : (
						<p className='text-muted-foreground px-4 py-8 text-xs'>
							提问后显示文献片段
						</p>
					)}
				</ScrollArea>
			</div>
		</aside>
	);
}

export function ChatPage() {
	const [scope, setScope] = useState<Scope>('all');
	const [input, setInput] = useState('');
	const [sidebarOpen, setSidebarOpen] = useState(false);
	const [messages, setMessages] = useState<Message[]>([
		{
			id: 'welcome',
			role: 'assistant',
			content:
				'你好，我是 MedRAG。基于知识库检索作答，并标注引用来源。（演示）',
		},
	]);
	const [loading, setLoading] = useState(false);

	const lastCitations = [...messages]
		.reverse()
		.find((m) => m.role === 'assistant' && m.citations)?.citations;

	useEffect(() => {
		if (lastCitations?.length) setSidebarOpen(true);
	}, [lastCitations]);

	function handleSend() {
		const text = input.trim();
		if (!text || loading) return;
		setMessages((prev) => [
			...prev,
			{ id: `u-${Date.now()}`, role: 'user', content: text },
		]);
		setInput('');
		setLoading(true);
		setTimeout(() => {
			setMessages((prev) => [
				...prev,
				{ ...MOCK_ANSWER, id: `a-${Date.now()}` },
			]);
			setLoading(false);
		}, 800);
	}

	return (
		<div
			className='relative flex w-full'
			style={{ height: `calc(100dvh - ${APP_HEADER_HEIGHT})` }}
		>
			{/* 与 header 同宽：PAGE_SHELL */}
			<div className={cn(PAGE_SHELL, 'flex min-w-0 flex-1 py-5')}>
				{/* 主栏：占满 shell 宽度（侧栏除外） */}
				<div className='flex min-w-0 flex-1 flex-col'>
					<div className='mb-5 flex items-center justify-between gap-4'>
						<div
							className='border-border bg-muted/50 inline-flex rounded-md border p-0.5'
							role='tablist'
							aria-label='检索范围'
						>
							{SCOPE_OPTIONS.map(({ key, label }) => (
								<Button
									key={key}
									type='button'
									role='tab'
									aria-selected={scope === key}
									variant='ghost'
									size='sm'
									onClick={() => setScope(key)}
									className={cn(
										'h-7 px-3 shadow-none',
										scope === key
											? 'bg-background text-primary font-medium shadow-sm'
											: 'text-muted-foreground',
									)}
								>
									{label}
								</Button>
							))}
						</div>
						<Button
							type='button'
							variant='ghost'
							size='sm'
							className='text-muted-foreground gap-1 lg:hidden'
							onClick={() => setSidebarOpen(true)}
						>
							<BookMarked className='size-4' />
							引用{lastCitations?.length ? ` ${lastCitations.length}` : ''}
						</Button>
					</div>

					<ScrollArea className='min-h-0 flex-1'>
						<div className='space-y-8 pb-4'>
							{messages.map((msg) => (
								<article
									key={msg.id}
									className={cn(
										'flex w-full',
										msg.role === 'user' ? 'justify-end' : 'justify-start',
									)}
								>
									<div
										className={cn(
											'text-[0.9375rem] leading-[1.8]',
											msg.role === 'user'
												? 'border-primary/15 bg-primary/8 text-foreground max-w-[78%] rounded-2xl border px-4 py-3'
												: 'text-foreground max-w-full',
										)}
									>
										{msg.content}
									</div>
								</article>
							))}
							{loading && (
								<p className='text-muted-foreground flex items-center gap-2 text-sm'>
									<Loader2 className='text-primary size-4 animate-spin' />
									检索中…
								</p>
							)}
							{messages.some((m) => m.citations) && (
								<button
									type='button'
									className='text-primary text-xs hover:underline lg:hidden'
									onClick={() => setSidebarOpen(true)}
								>
									查看引用来源
								</button>
							)}
						</div>
					</ScrollArea>

					<div className='border-border mt-4 space-y-2 border-t pt-4'>
						<div className='flex gap-2'>
							<Input
								value={input}
								onChange={(e) => setInput(e.target.value)}
								onKeyDown={(e) =>
									e.key === 'Enter' && !e.shiftKey && handleSend()
								}
								placeholder='输入医学问题…'
								className='h-10 flex-1'
								disabled={loading}
							/>
							<Button
								type='button'
								size='icon'
								className='size-10 shrink-0'
								onClick={handleSend}
								disabled={loading || !input.trim()}
								aria-label='发送'
							>
								{loading ? (
									<Loader2 className='size-4 animate-spin' />
								) : (
									<Send className='size-4' />
								)}
							</Button>
						</div>
						<p className='text-muted-foreground text-xs'>
							仅供学习，不替代诊疗 ·{' '}
							<Link href='/library' className='text-primary hover:underline'>
								知识库
							</Link>
						</p>
					</div>
				</div>

				<CitationsSidebar
					open={sidebarOpen}
					onOpenChange={setSidebarOpen}
					citations={lastCitations}
					className='hidden lg:flex'
				/>
			</div>

			{!sidebarOpen && (
				<Button
					type='button'
					variant='outline'
					size='icon-sm'
					className='bg-card absolute top-20 right-6 z-10 hidden lg:inline-flex'
					onClick={() => setSidebarOpen(true)}
					aria-label='展开引用'
				>
					<PanelRightOpen className='size-4' />
				</Button>
			)}

			<div className='lg:hidden'>
				<div
					className={cn(
						'fixed inset-y-0 right-0 z-30 transition-transform duration-300',
						sidebarOpen
							? 'translate-x-0'
							: 'pointer-events-none translate-x-full',
					)}
				>
					<CitationsSidebar
						open
						onOpenChange={setSidebarOpen}
						citations={lastCitations}
						className='bg-card h-full w-64 border-l shadow-lg'
					/>
				</div>
				{sidebarOpen && (
					<button
						type='button'
						className='bg-foreground/15 fixed inset-0 z-20'
						aria-label='关闭'
						onClick={() => setSidebarOpen(false)}
					/>
				)}
			</div>
		</div>
	);
}
