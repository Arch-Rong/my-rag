/** 字节数 → 可读大小（如 2.1 MB） */
export function formatFileSize(bytes: number | null | undefined): string {
	if (bytes == null || bytes <= 0) return '—';
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** ISO 日期 → 本地 YYYY-MM-DD */
export function formatDate(iso: string | null | undefined): string {
	if (!iso) return '—';
	const d = new Date(iso);
	if (Number.isNaN(d.getTime())) return '—';
	return d.toLocaleDateString('zh-CN', {
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
	});
}
