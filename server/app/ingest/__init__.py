"""
app/ingest — 文档入库：解析 + 结构分片（LangChain）

目录结构：
  types.py           中间数据结构（ChunkDraft 等）
  tokens.py          token 估算（配置换算用）
  pipeline.py        ★ Worker 入口：chunk_file_content()
  loaders/           从文件读出文本
    pdf.py           PDF 按页抽字
  splitters/         把长文本切成块
    langchain.py     MarkdownHeader + RecursiveCharacter 分片

典型调用（在 ingest_service 里）：
  from app.ingest import chunk_file_content
  drafts = chunk_file_content(raw_bytes, "notes.md", max_tokens=512, ...)
"""

from app.ingest.pipeline import chunk_file_content
from app.ingest.splitters.langchain import chunk_markdown, chunk_pdf

__all__ = [
	'chunk_file_content',
	'chunk_markdown',
	'chunk_pdf',
]
