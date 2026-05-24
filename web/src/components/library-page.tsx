'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { FileText, Loader2, Trash2, Upload } from 'lucide-react';

import {
	ApiError,
	deleteDocument,
	listDocuments,
	uploadDocument,
	type DocumentDto,
	type DocumentStatus,
} from '@/api/index';
import { Button } from '@/components/ui/button';
import { PAGE_SHELL } from '@/lib/layout';
import { clearAccessToken, isLoggedIn } from '@/lib/auth';
import { formatDate, formatFileSize } from '@/lib/format';
import { cn } from '@/lib/utils';

type DocSource = 'user' | 'system';

type LibraryDoc = {
	id: string;
	name: string;
	size: string;
	chunks: number;
	status: DocumentStatus;
	uploadedAt: string;
	source: DocSource;
	errorMessage: string | null;
};

const STATUS_STYLE: Record<
	DocumentStatus,
	{ label: string; dot: string; bg: string; text: string }
> = {
	ready: {
		label: '已就绪',
		dot: 'bg-primary',
		bg: 'bg-primary/10',
		text: 'text-primary',
	},
	embedding: {
		label: '向量化中',
		dot: 'bg-amber-500',
		bg: 'bg-amber-500/10',
		text: 'text-amber-700',
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
	deleted: {
		label: '已删除',
		dot: 'bg-muted-foreground',
		bg: 'bg-muted',
		text: 'text-muted-foreground',
	},
};

const POLL_STATUSES: DocumentStatus[] = ['queued', 'parsing', 'embedding'];

function mapDto(row: DocumentDto): LibraryDoc {
	const source: DocSource = row.owner_type === 'system' ? 'system' : 'user';
	return {
		id: row.id,
		name: row.title || row.original_filename || '未命名',
		size: formatFileSize(row.file_size),
		chunks: row.chunk_count,
		status: row.status,
		uploadedAt: source === 'system' ? '系统预置' : formatDate(row.created_at),
		source,
		errorMessage: row.error_message,
	};
}

export function LibraryPage() {
	const router = useRouter();
	const [authed, setAuthed] = useState(() => isLoggedIn());
	const [docs, setDocs] = useState<LibraryDoc[]>([]);
	const [loading, setLoading] = useState(true);
	const [uploading, setUploading] = useState(false);
	const [dragOver, setDragOver] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const inputRef = useRef<HTMLInputElement>(null);

	const loadDocuments = useCallback(async () => {
		const data = await listDocuments();
		setDocs(data.items.map(mapDto));
	}, []);

	useEffect(() => {
		if (!isLoggedIn()) {
			router.replace('/login?from=/library');
			return;
		}
		setAuthed(true);
	}, [router]);

	useEffect(() => {
		if (!authed) return;

		let cancelled = false;

		(async () => {
			setLoading(true);
			setError(null);
			try {
				await loadDocuments();
			} catch (err) {
				if (!cancelled) {
					const msg =
						err instanceof ApiError ? err.message : '加载文档列表失败';
					setError(msg);
					if (err instanceof ApiError && err.status === 401) {
						clearAccessToken();
						router.replace('/login?from=/library');
					}
				}
			} finally {
				if (!cancelled) setLoading(false);
			}
		})();

		return () => {
			cancelled = true;
		};
	}, [authed, loadDocuments]);

	useEffect(() => {
		if (!authed) return;
		const needsPoll = docs.some((d) => POLL_STATUSES.includes(d.status));
		if (!needsPoll) return;

		const timer = window.setInterval(() => {
			loadDocuments().catch(() => {
				/* 轮询失败静默，避免打断用户操作 */
			});
		}, 3000);

		return () => window.clearInterval(timer);
	}, [authed, docs, loadDocuments]);

	async function handleFiles(files: FileList | null) {
		if (!files?.length || uploading) return;
		const file = files[0];
		setUploading(true);
		setError(null);
		try {
			await uploadDocument(file);
			await loadDocuments();
		} catch (err) {
			setError(err instanceof ApiError ? err.message : '上传失败');
		} finally {
			setUploading(false);
			if (inputRef.current) inputRef.current.value = '';
		}
	}

	async function handleDelete(id: string) {
		const doc = docs.find((d) => d.id === id);
		if (doc?.source === 'system') return;
		if (!confirm(`确定删除「${doc?.name}」？`)) return;

		setError(null);
		try {
			await deleteDocument(id);
			setDocs((prev) => prev.filter((d) => d.id !== id));
		} catch (err) {
			setError(err instanceof ApiError ? err.message : '删除失败');
		}
	}

	const userCount = docs.filter((d) => d.source === 'user').length;

	if (!authed) {
		return (
			<div className='text-muted-foreground flex flex-1 items-center justify-center gap-2 py-24 text-sm'>
				<Loader2 className='size-4 animate-spin' />
				跳转登录…
			</div>
		);
	}

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

			{error && (
				<p
					className='bg-destructive/10 text-destructive mb-6 rounded-lg px-4 py-3 text-sm'
					role='alert'
				>
					{error}
				</p>
			)}

			{/* 上传 */}
			<div
				role='button'
				tabIndex={0}
				aria-disabled={uploading}
				onDragOver={(e) => {
					e.preventDefault();
					if (!uploading) setDragOver(true);
				}}
				onDragLeave={() => setDragOver(false)}
				onDrop={(e) => {
					e.preventDefault();
					setDragOver(false);
					if (!uploading) void handleFiles(e.dataTransfer.files);
				}}
				onKeyDown={(e) =>
					e.key === 'Enter' && !uploading && inputRef.current?.click()
				}
				onClick={() => !uploading && inputRef.current?.click()}
				className={cn(
					'border-border bg-card/50 mb-10 flex cursor-pointer flex-col items-center gap-3 rounded-xl border border-dashed py-12 transition-colors',
					dragOver && 'border-primary/50 bg-primary/5',
					uploading && 'pointer-events-none opacity-60',
				)}
			>
				<input
					ref={inputRef}
					type='file'
					accept='.pdf,.md,.markdown'
					className='hidden'
					disabled={uploading}
					onChange={(e) => void handleFiles(e.target.files)}
				/>
				<div className='bg-primary/10 text-primary flex size-11 items-center justify-center rounded-full'>
					{uploading ? (
						<Loader2 className='size-5 animate-spin' />
					) : (
						<Upload className='size-5' />
					)}
				</div>
				<p className='text-foreground text-sm font-medium'>
					{uploading ? '上传中…' : '点击或拖拽上传'}
				</p>
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

				{loading ? (
					<div className='text-muted-foreground flex items-center justify-center gap-2 py-16 text-sm'>
						<Loader2 className='size-4 animate-spin' />
						加载中…
					</div>
				) : (
					<div className='border-border/80 bg-card overflow-hidden rounded-xl border shadow-sm'>
						<div className='bg-muted/50 text-muted-foreground hidden gap-4 border-b px-5 py-3 text-xs font-medium sm:grid sm:grid-cols-[1fr_5rem_6rem_5rem_4rem]'>
							<span>文档名称</span>
							<span>大小</span>
							<span>状态</span>
							<span>来源</span>
							<span className='text-right'>操作</span>
						</div>

						<ul className='divide-border/60 divide-y'>
							{docs.map((doc) => {
								const st = STATUS_STYLE[doc.status] ?? STATUS_STYLE.queued;
								return (
									<li key={doc.id}>
										<div className='group hover:bg-muted/30 grid gap-3 px-5 py-4 transition-colors sm:grid-cols-[1fr_5rem_6rem_5rem_4rem] sm:items-center sm:gap-4'>
											<div className='flex min-w-0 items-start gap-3 sm:items-center'>
												<FileText className='text-primary/70 mt-0.5 size-4 shrink-0 sm:mt-0' />
												<div className='min-w-0'>
													<p className='text-foreground truncate text-sm font-medium'>
														{doc.name}
													</p>
													{doc.status === 'failed' && doc.errorMessage && (
														<p
															className='text-destructive mt-1 line-clamp-2 text-xs'
															title={doc.errorMessage}
														>
															{doc.errorMessage}
														</p>
													)}
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
														onClick={() => void handleDelete(doc.id)}
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
				)}

				<p className='text-muted-foreground mt-4 text-xs'>
					系统预置教材不可删除 · 解析中状态每 3 秒自动刷新
				</p>
			</section>
		</div>
	);
}
