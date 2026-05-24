"""
入库分片「总入口」— Worker 只应调用本文件的 chunk_file_content。

流程：
  MinIO 读出 bytes + 文件名
       ↓
  chunk_file_content()  ← 你在这里
       ↓
  .md → splitters.chunk_markdown
  .pdf → splitters.chunk_pdf
       ↓
  list[ChunkDraft] → ingest_service 写入 chunks 表
"""

from app.ingest.splitters.langchain import chunk_markdown, chunk_pdf
from app.ingest.types import ChunkDraft
from app.storage.keys import allowed_extension


def chunk_file_content(
	data: bytes,
	filename: str,
	*,
	max_tokens: int = 512,
	overlap_tokens: int = 64,
) -> list[ChunkDraft]:
	"""
	根据文件类型选择分片方式（ingest 主入口）。

	参数：
	  data / filename：来自 MinIO 的文件内容与原始文件名
	  max_tokens / overlap_tokens：与 config.py / .env 中 CHUNK_* 一致

	返回：
	  可直接插入 chunks 表的 ChunkDraft 列表
	"""
	ext = allowed_extension(filename)
	if ext == '.md':
		return chunk_markdown(
			data.decode('utf-8'),
			max_tokens=max_tokens,
			overlap_tokens=overlap_tokens,
		)
	if ext == '.pdf':
		return chunk_pdf(
			data,
			max_tokens=max_tokens,
			overlap_tokens=overlap_tokens,
		)
	raise ValueError(f'不支持的文件类型: {ext}')
