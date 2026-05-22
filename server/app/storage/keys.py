"""对象存储键名与文件名规范化。"""

import re
import uuid

_ALLOWED_EXTENSIONS = {'.pdf', '.md'}
_EXTENSION_TO_MIME = {
	'.pdf': 'application/pdf',
	'.md': 'text/markdown',
}


def sanitize_filename(name: str) -> str:
	"""只保留文件名本体，去掉路径成分。"""
	base = name.replace('\\', '/').split('/')[-1].strip()
	return base or 'upload.bin'


def allowed_extension(filename: str) -> str:
	lower = filename.lower()
	for ext in _ALLOWED_EXTENSIONS:
		if lower.endswith(ext):
			return ext
	raise ValueError(f'unsupported file type: {filename!r} (allowed: pdf, md)')


def mime_for_filename(filename: str) -> str:
	ext = allowed_extension(filename)
	return _EXTENSION_TO_MIME[ext]


def build_upload_key(user_id: uuid.UUID, document_id: uuid.UUID, filename: str) -> str:
	safe = sanitize_filename(filename)
	safe = re.sub(r'[^\w.\-]+', '_', safe)
	return f'uploads/{user_id}/{document_id}/{safe}'
