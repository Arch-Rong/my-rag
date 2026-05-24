"""
PDF 加载：用 pymupdf 按页抽出纯文本。

说明：
  - 图表、扫描版 PDF 可能抽不到字，MVP 只处理可选中复制的文本层
  - 抽完后交给 splitters/langchain.py 做分片
"""

from app.ingest.types import TextBlock


def extract_pdf_pages(data: bytes) -> list[TextBlock]:
	"""
	读取 PDF 二进制，每一页生成一个 TextBlock。

	metadata 示例：page=3, source_format=pdf, block_type=page
	"""
	try:
		import fitz  # pymupdf
	except ImportError as exc:
		raise RuntimeError(
			'处理 PDF 需要安装 pymupdf：pip install pymupdf'
		) from exc

	blocks: list[TextBlock] = []
	with fitz.open(stream=data, filetype='pdf') as doc:
		for page_index, page in enumerate(doc, start=1):
			text = page.get_text('text').strip()
			if not text:
				continue
			blocks.append(
				TextBlock(
					text=text,
					metadata={
						'source_format': 'pdf',
						'page': page_index,
						'block_type': 'page',
					},
				)
			)

	if not blocks:
		raise ValueError('PDF 中未提取到可读文本（可能是扫描件或纯图片）')
	return blocks
