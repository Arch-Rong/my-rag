"""
_splitters：把长文本切成适合检索的 ChunkDraft（基于 LangChain）。
"""

from app.ingest.splitters.langchain import chunk_markdown, chunk_pdf

__all__ = ['chunk_markdown', 'chunk_pdf']
