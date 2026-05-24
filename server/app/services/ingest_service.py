"""
文档入库 Worker 逻辑：读 MinIO → 解析 → 结构分片 → 写 chunks → 向量化。
"""

import logging
import uuid  # 文档主键 document_id 的类型

logger = logging.getLogger(__name__)

from sqlmodel import Session, delete, select  # ORM 会话；delete/select 写 SQL

from app.config import get_settings  # 读取分片参数 chunk_max_tokens 等
from app.ingest.pipeline import chunk_file_content  # 字节流 → 分片草稿列表
from app.models.chunk import Chunk  # chunks 表模型
from app.models.document import Document  # documents 表模型
from app.models.enums import DocumentStatus  # queued / parsing / ready / failed ...
from app.storage.protocol import ObjectStorage  # 对象存储抽象（MinIO 等）


def ingest_document(
	session: Session,  # 数据库会话，由调用方创建（如 ingest_tasks）
	storage: ObjectStorage,  # 用来按 file_path 下载原始文件
	document_id: uuid.UUID,  # 要处理的文档 ID
) -> Document:
	"""
	处理单份 queued / failed 文档：解析 + 分片 + 落库。

	失败时 status=failed，error_message 记录原因。
	"""
	settings = get_settings()  # 全局配置（分片大小、重叠等）
	document = session.get(Document, document_id)  # 按主键查一行 Document
	if document is None:  # 不存在则无法继续
		raise ValueError(f'document not found: {document_id}')
	if document.status == DocumentStatus.deleted:  # 软删文档不再入库
		raise ValueError('document is deleted')
	if not document.file_path:  # MinIO/S3 上的对象键，没有则读不了文件
		raise ValueError('document has no file_path')
	if not document.original_filename:  # 分片管道靠扩展名选解析器（pdf/docx/...）
		raise ValueError('document has no original_filename')

	# --- 阶段 1：尽早把状态写成 parsing 并提交，便于轮询与崩溃排查 ---
	document.status = DocumentStatus.parsing  # 内存中改为「解析中」
	document.error_message = None  # 重试时清空旧错误文案
	session.add(document)  # 确保变更挂在当前 Session（get 出的对象通常已挂上）
	session.commit()  # 立即落库；后面读文件/分片耗时长，别让别人一直看到 queued

	try:
		# --- 阶段 2：读对象存储 + 解析并分片（尚未写 chunks 表）---
		raw = storage.get_bytes(document.file_path)  # 下载整文件为 bytes
		drafts = chunk_file_content(  # 按格式解析，切成带 token 数的草稿
			raw,
			document.original_filename,
			max_tokens=settings.chunk_max_tokens,
			overlap_tokens=settings.chunk_overlap_tokens,
		)
		if not drafts:  # 空文档或解析不出任何块
			raise ValueError('no chunks produced from document')

		# --- 阶段 3：替换旧分片（重跑 ingest 时先删再插）---
		session.exec(delete(Chunk).where(Chunk.document_id == document_id))

		for draft in drafts:  # 每个草稿落一条 Chunk 行
			session.add(
				Chunk(
					document_id=document.id,  # 外键指向当前文档
					content=draft.content,  # 分片正文
					token_count=draft.token_count,  # 估算 token 数
					chunk_metadata=draft.metadata,  # 页码、标题等 JSON
					embedding=None,  # 向量下一步再填
				)
			)

		# --- 阶段 4：更新文档汇总字段（仍在 try 内，尚未 commit）---
		document.chunk_count = len(drafts)  # 分片总数
		document.status = DocumentStatus.ready  # 分片成功，可检索（embedding 另说）
		document.error_message = None  # 成功路径再次确保无错误信息
	except Exception as exc:
		# 任意步骤失败：记 failed + 截断错误信息，先 commit 再向上抛
		document.status = DocumentStatus.failed
		document.error_message = str(exc)[:2000]  # 防止 error_message 字段过长
		session.add(document)
		session.commit()  # 失败状态也要立刻可见
		session.refresh(document)  # 从库重载（updated_at 等由 DB 生成的字段）
		raise  # 交给 ingest_tasks 记日志

	# --- 阶段 5：成功路径一次性提交 chunks + document ---
	session.add(document)
	session.commit()  # 写入新 Chunk 行 + ready 状态
	session.refresh(document)

	# --- 阶段 6：向量化（pgvector），失败不阻断 ready，可后续脚本补跑 ---
	if settings.embed_on_ingest and settings.llm_api_key.strip():
		try:
			from app.services.embedding_service import embed_document_chunks

			embed_document_chunks(session, document_id)
		except Exception:
			logger.exception(
				'embedding failed for document %s; sparse search still available',
				document_id,
			)

	return document


def list_queued_document_ids(session: Session, limit: int = 50) -> list[uuid.UUID]:
	"""扫描待处理文档 ID，供 Worker 批量拉取（每次最多 limit 条）。"""
	rows = session.exec(
		select(Document.id)  # 只查 id，减轻负载
		.where(Document.status == DocumentStatus.queued)  # 仅排队中的
		.limit(limit)  # 防止一次拉太多
	).all()
	return list(rows)  # exec 可能返回可迭代对象，转成 list[UUID]
