"""
LangChain 结构分片实现。

整体思路：把「一整篇 MD / 一本 PDF」切成多段 ChunkDraft，每段将来对应数据库里的一行 chunks。

Markdown 两步：
  1. MarkdownHeaderTextSplitter — 按 # / ## / ### 按章节切
  2. RecursiveCharacterTextSplitter — 某一节太长时，再按段落/句号切，并加 overlap

PDF 两步：
  1. loaders.pdf 按页抽出文字（TextBlock）
  2. 每页转成 LangChain Document，再 RecursiveCharacterTextSplitter 切小块
"""

# LangChain 的「文档」类型：page_content=正文，metadata=章节/页码等
from langchain_core.documents import Document

# 两个分片器：按标题切、按字符递归切
from langchain_text_splitters import (
	MarkdownHeaderTextSplitter,
	RecursiveCharacterTextSplitter,
)

# PDF 专用：从二进制读出每一页文字
from app.ingest.loaders.pdf import extract_pdf_pages

# 估算每段有多少 token（写入 chunk_count）
from app.ingest.tokens import estimate_tokens

# 分片结果草稿，稍后由 ingest_service 写入 chunks 表
from app.ingest.types import ChunkDraft

# ---------------------------------------------------------------------------
# Markdown 标题级别 与 数据库 metadata 字段名的对应关系
# 例如 ## 高血压 → metadata["section"] = "高血压"
# ---------------------------------------------------------------------------
_MD_HEADERS = [
	('#', 'chapter'),       # 一级标题 → chapter
	('##', 'section'),      # 二级标题 → section
	('###', 'subsection'),  # 三级标题 → subsection
]


def _tokens_to_chars(max_tokens: int, overlap_tokens: int) -> tuple[int, int]:
	"""
	把配置里的 token 数换成 LangChain 使用的「字符数」。

	LangChain 的 RecursiveCharacterTextSplitter 参数叫 chunk_size（字符），
	不是 token；我们用 estimate_tokens 的逆推：约 2 字符 ≈ 1 token。
	"""
	chunk_size = max(1, max_tokens * 2)       # 单段最多大约多少字符
	chunk_overlap = max(0, overlap_tokens * 2)  # 相邻两段重叠多少字符
	return chunk_size, chunk_overlap


def _make_recursive_splitter(
	max_tokens: int, overlap_tokens: int
) -> RecursiveCharacterTextSplitter:
	"""
	创建「递归字符分片器」：超长文本时继续切，并保留 overlap。

	separators 顺序很重要：先尝试按双换行（段落）切，再单换行，再中文句号等。
	"""
	chunk_size, chunk_overlap = _tokens_to_chars(max_tokens, overlap_tokens)
	return RecursiveCharacterTextSplitter(
		chunk_size=chunk_size,           # 每段最大字符数
		chunk_overlap=chunk_overlap,     # 段与段之间重叠，避免句子正好被截断在边界
		separators=[
			'\n\n',   # 优先：空行（段落）
			'\n',     # 其次：换行
			'。', '！', '？',  # 中文句末
			'. ', '; ', ' ', '',  # 英文句号、空格、硬切
		],
	)


def _documents_to_drafts(
	docs: list[Document],
	*,
	source_format: str,
	start_index: int = 0,
) -> tuple[list[ChunkDraft], int]:
	"""
	把 LangChain 分片后的 Document 列表，转成我们项目里的 ChunkDraft。

	同时统一补上 source_format、chunk_index，方便落库和前端展示。
	"""
	drafts: list[ChunkDraft] = []
	idx = start_index  # 全局块序号，写入 metadata.chunk_index

	for doc in docs:
		content = doc.page_content.strip()  # 这一段正文
		if not content:
			continue  # 跳过空段

		# 复制 LangChain 带来的 metadata（如 section、page），去掉 None
		meta = {k: v for k, v in doc.metadata.items() if v is not None}
		meta.setdefault('source_format', source_format)  # markdown 或 pdf
		meta['chunk_index'] = idx  # 第几块，从 0 递增

		drafts.append(
			ChunkDraft(
				content=content,
				token_count=estimate_tokens(content),  # 粗算 token，给 RAG 控上下文用
				metadata=meta,
			)
		)
		idx += 1

	return drafts, idx  # 返回草稿列表和下一个可用序号


def chunk_markdown(
	text: str,
	*,
	max_tokens: int = 512,
	overlap_tokens: int = 64,
) -> list[ChunkDraft]:
	"""
	对 Markdown 全文做结构分片（对外暴露，pipeline 里 .md 会调这个）。

	参数 max_tokens / overlap_tokens 来自 config.py 或 .env 的 CHUNK_*。
	"""
	# --- 第一步：按 # ## ### 标题切成若干「节」---
	header_splitter = MarkdownHeaderTextSplitter(
		headers_to_split_on=_MD_HEADERS,  # 见文件顶部 _MD_HEADERS
		strip_headers=False,  # False：标题文字仍留在正文里，引用时可读
	)
	header_docs = header_splitter.split_text(text)  # 得到 list[Document]

	# 没有任何标题的纯文本：整篇当作一节
	if not header_docs and text.strip():
		header_docs = [
			Document(
				page_content=text.strip(),
				metadata={'source_format': 'markdown'},
			)
		]

	# --- 第二步：某一节仍然太长 → 递归字符分片 ---
	recursive = _make_recursive_splitter(max_tokens, overlap_tokens)
	split_docs = recursive.split_documents(header_docs)  # 可能一节变多段

	# --- 转成 ChunkDraft，准备写数据库 ---
	drafts, _ = _documents_to_drafts(split_docs, source_format='markdown')
	return drafts


def chunk_pdf(
	data: bytes,
	*,
	max_tokens: int = 512,
	overlap_tokens: int = 64,
) -> list[ChunkDraft]:
	"""
	对 PDF 二进制做分片（pipeline 里 .pdf 会调这个）。

	data 来自 MinIO 的 get_bytes，不是本地路径。
	"""
	# --- 第一步：按页抽文本（pymupdf）---
	page_blocks = extract_pdf_pages(data)  # 每页一个 TextBlock，带 page 页码

	# 转成 LangChain Document，后面 split_documents 只吃这种类型
	page_docs = [
		Document(
			page_content=block.text,
			metadata=dict(block.metadata),  # 含 page、source_format 等
		)
		for block in page_blocks
	]

	# --- 第二步：单页文字若仍超长，继续递归切 ---
	recursive = _make_recursive_splitter(max_tokens, overlap_tokens)
	split_docs = recursive.split_documents(page_docs)

	# --- 转成 ChunkDraft ---
	drafts, _ = _documents_to_drafts(split_docs, source_format='pdf')
	return drafts
