import { apiClient } from '../client';

export type DocumentStatus =
	| 'queued'
	| 'parsing'
	| 'embedding'
	| 'ready'
	| 'failed'
	| 'deleted';

export type DocumentDto = {
	id: string;
	user_id: string | null;
	owner_type: 'system' | 'user';
	title: string;
	original_filename: string | null;
	source_type: string;
	mime_type: string | null;
	file_size: number | null;
	file_path: string | null;
	content_hash: string | null;
	chunk_count: number;
	status: DocumentStatus;
	error_message: string | null;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
};

export type DocumentListResponse = {
	items: DocumentDto[];
	total: number;
};

/** 知识库文档列表（系统教材 + 我的上传） */
export function listDocuments(limit = 100) {
	return apiClient.get<DocumentListResponse>('/api/v1/documents', {
		params: { limit },
	});
}

/** 上传 PDF / Markdown */
export function uploadDocument(file: File, title?: string) {
	const form = new FormData();
	form.append('file', file);
	if (title?.trim()) {
		form.append('title', title.trim());
	}
	return apiClient.request<DocumentDto>({
		path: '/api/v1/documents',
		method: 'POST',
		rawBody: form,
	});
}

/** 删除我的上传（软删 + 清 MinIO + chunks） */
export function deleteDocument(documentId: string) {
	return apiClient.delete<void>(`/api/v1/documents/${documentId}`);
}
