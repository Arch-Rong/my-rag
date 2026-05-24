"""
_loaders：从原始文件「读出可切分的文本」。

不负责分片，只负责解析/抽取。
"""

from app.ingest.loaders.pdf import extract_pdf_pages

__all__ = ['extract_pdf_pages']
