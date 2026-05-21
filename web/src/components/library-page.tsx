'use client';

import Link from 'next/link';
import { useRef, useState } from 'react';
import { FileText, Trash2, Upload } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { PAGE_SHELL } from '@/lib/layout';
import { cn } from '@/lib/utils';

type DocStatus = 'ready' | 'parsing' | 'failed' | 'queued';

type Document = {
	id: string;
	name: string;
	size: string;
	chunks: number;
	status: DocStatus;
	uploadedAt: string;
	source: 'user' | 'system';
};

const STATUS_STYLE: Record<
	DocStatus,
	{ label: string; dot: string; bg: string; text: string }
> = {
	ready: {
		label: '已向量化',
		dot: 'bg-primary',
		bg: 'bg-primary/10',
		text: 'text-primary',
	},
	parsing: {
		label: '解析中',
		dot: 'bg-amber-500',
		bg: 'bg-amber-500/10',
		text: 'text-amber-700',
	},
	queued: {
		label: '排队中',
		dot: 'bg-muted-foreground',
		bg: 'bg-muted',
		text: 'text-muted-foreground',
	},
	failed: {
		label: '失败',
		dot: 'bg-destructive',
		bg: 'bg-destructive/10',
		text: 'text-destructive',
	},
};

const INITIAL_DOCS: Document[] = [
	{
		id: 'sys-1',
		name: '内科学（第 8 版）— 节选',
		size: '12.4 MB',
		chunks: 2840,
		status: 'ready',
		uploadedAt: '系统预置',
		source: 'system',
	},
	{
		id: 'user-1',
		name: '呼吸科期末复习笔记.pdf',
		size: '2.1 MB',
		chunks: 186,
		status: 'ready',
		uploadedAt: '2026-05-18',
		source: 'user',
	},
];

export function LibraryPage() {
	const [docs, setDocs] = useState<Document[]>(INITIAL_DOCS);
	const [dragOver, setDragOver] = useState(false);
	const inputRef = useRef<HTMLInputElement>(null);

	function handleFiles(files: FileList | null) {
		if (!files?.length) return;
		const file = files[0];
		const newDoc: Document = {
			id: `user-${Date.now()}`,
			name: file.name,
			size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
			chunks: 0,
			status: 'queued',
			uploadedAt: new Date().toISOString().slice(0, 10),
			source: 'user',
		};
		setDocs((prev) => [newDoc, ...prev]);
		setTimeout(() => {
			setDocs((prev) =>
				prev.map((d) =>
					d.id === newDoc.id ? { ...d, status: 'parsing' as const } : d,
				),
			);
		}, 400);
		setTimeout(() => {
			setDocs((prev) =>
				prev.map((d) =>
					d.id === newDoc.id
						? {
								...d,
								status: 'ready' as const,
								chunks: Math.floor(Math.random() * 200) + 50,
							}
						: d,
				),
			);
		}, 2200);
	}

	function handleDelete(id: string) {
		const doc = docs.find((d) => d.id === id);
		if (doc?.source === 'system') return;
		if (!confirm(`确定删除「${doc?.name}」？`)) return;
		setDocs((prev) => prev.filter((d) => d.id !== id));
	}

	const userCount = docs.filter((d) => d.source === 'user').length;

	return (
		<div className={cn(PAGE_SHELL, 'py-8 lg:py-10')}>
			<header className='mb-8'>
				<h1 className='text-foreground text-xl font-semibold tracking-tight'>
					知识库
				</h1>
				<p className='text-muted-foreground mt-2 text-sm leading-relaxed'>
					上传教材与笔记，入库后可在
					<Link
						href='/chat'
						className='text-primary mx-1 font-medium hover:underline'
					>
						智能问答
					</Link>
					中检索并引用。
				</p>
			</header>

			{/* 上传 */}
			<div
				role='button'
				tabIndex={0}
				onDragOver={(e) => {
					e.preventDefault();
					setDragOver(true);
				}}
				onDragLeave={() => setDragOver(false)}
				onDrop={(e) => {
					e.preventDefault();
					setDragOver(false);
					handleFiles(e.dataTransfer.files);
				}}
				onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
				onClick={() => inputRef.current?.click()}
				className={cn(
					'border-border bg-card/50 mb-10 flex cursor-pointer flex-col items-center gap-3 rounded-xl border border-dashed py-12 transition-colors',
					dragOver && 'border-primary/50 bg-primary/5',
				)}
			>
				<input
					ref={inputRef}
					type='file'
					accept='.pdf,.md,.markdown'
					className='hidden'
					onChange={(e) => handleFiles(e.target.files)}
				/>
				<div className='bg-primary/10 text-primary flex size-11 items-center justify-center rounded-full'>
					<Upload className='size-5' />
				</div>
				<p className='text-foreground text-sm font-medium'>点击或拖拽上传</p>
				<p className='text-muted-foreground text-xs'>
					PDF · Markdown · 单文件 ≤ 50 MB
				</p>
			</div>

			{/* 文档列表 */}
			<section>
				<div className='mb-4 flex items-end justify-between'>
					<h2 className='text-foreground text-sm font-medium'>文档列表</h2>
					<p className='text-muted-foreground text-xs'>
						共{' '}
						<span className='text-foreground font-medium'>{docs.length}</span>{' '}
						份 · 我的上传{' '}
						<span className='text-foreground font-medium'>{userCount}</span> 份
					</p>
				</div>

				<div className='border-border/80 bg-card overflow-hidden rounded-xl border shadow-sm'>
					{/* 表头 */}
					<div className='bg-muted/50 text-muted-foreground hidden gap-4 border-b px-5 py-3 text-xs font-medium sm:grid sm:grid-cols-[1fr_5rem_6rem_5rem_4rem]'>
						<span>文档名称</span>
						<span>大小</span>
						<span>状态</span>
						<span>来源</span>
						<span className='text-right'>操作</span>
					</div>

					<ul className='divide-border/60 divide-y'>
						{docs.map((doc) => {
							const st = STATUS_STYLE[doc.status];
							return (
								<li key={doc.id}>
									<div className='group hover:bg-muted/30 grid gap-3 px-5 py-4 transition-colors sm:grid-cols-[1fr_5rem_6rem_5rem_4rem] sm:items-center sm:gap-4'>
										<div className='flex min-w-0 items-start gap-3 sm:items-center'>
											<FileText className='text-primary/70 mt-0.5 size-4 shrink-0 sm:mt-0' />
											<div className='min-w-0'>
												<p className='text-foreground truncate text-sm font-medium'>
													{doc.name}
												</p>
												<p className='text-muted-foreground mt-1 text-xs sm:hidden'>
													{doc.size} · {st.label}
												</p>
											</div>
										</div>

										<span className='text-muted-foreground hidden text-sm sm:block'>
											{doc.size}
										</span>

										<span
											className={cn(
												'inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
												st.bg,
												st.text,
											)}
										>
											<span className={cn('size-1.5 rounded-full', st.dot)} />
											{st.label}
										</span>

										<span className='text-muted-foreground text-sm'>
											{doc.source === 'system' ? (
												<span className='text-primary/90'>系统教材</span>
											) : (
												'我的上传'
											)}
										</span>

										<div className='flex items-center justify-between gap-2 sm:justify-end'>
											<span className='text-muted-foreground text-xs sm:hidden'>
												{doc.chunks > 0 ? `${doc.chunks} 段` : '—'} ·{' '}
												{doc.uploadedAt}
											</span>
											<span className='text-muted-foreground hidden text-xs sm:block'>
												{doc.chunks > 0 ? `${doc.chunks} 段` : '—'}
											</span>
											{doc.source === 'user' ? (
												<Button
													type='button'
													variant='ghost'
													size='icon-sm'
													className='text-muted-foreground hover:text-destructive size-8'
													onClick={() => handleDelete(doc.id)}
													aria-label='删除'
												>
													<Trash2 className='size-4' />
												</Button>
											) : (
												<span className='text-muted-foreground hidden text-xs sm:inline'>
													—
												</span>
											)}
										</div>
									</div>
								</li>
							);
						})}
					</ul>

					{docs.length === 0 && (
						<p className='text-muted-foreground px-5 py-16 text-center text-sm'>
							暂无文档，请上传第一份学习资料
						</p>
					)}
				</div>

				<p className='text-muted-foreground mt-4 text-xs'>
					系统预置教材不可删除 · 演示数据，未连接后端
				</p>
			</section>
		</div>
	);
}
