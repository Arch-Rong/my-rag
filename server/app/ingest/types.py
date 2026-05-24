"""
入库流水线用到的「中间数据结构」。

这些类不会直接映射数据库表，只在 Worker 内存里传递：
  读文件 → TextBlock（可选）→ ChunkDraft → 写入 chunks 表
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextBlock:
	"""
	从 PDF 按页拆出的一段原文（带页码等元数据）。

	Markdown 已直接用 LangChain 分片，一般不再经过 TextBlock。
	"""

	text: str
	metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkDraft:
	"""
	分片完成、准备落库的一行。

	对应数据库 chunks 表：
	  - content      → chunks.content
	  - token_count  → chunks.token_count
	  - metadata     → chunks.metadata（JSON，含 chapter / page / chunk_index 等）
	"""

	content: str
	token_count: int
	metadata: dict[str, Any] = field(default_factory=dict)
