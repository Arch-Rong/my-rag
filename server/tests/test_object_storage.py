"""对象存储：键名规则与本地后端行为（不依赖 MinIO）。"""

import uuid
from pathlib import Path

import pytest

from app.storage.filesystem_storage import FilesystemObjectStorage
from app.storage.keys import build_upload_key, sanitize_filename


def test_sanitize_filename_strips_path_components() -> None:
	assert sanitize_filename('../../etc/passwd') == 'passwd'
	assert sanitize_filename('notes.md') == 'notes.md'


def test_build_upload_key_includes_user_and_document() -> None:
	user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
	doc_id = uuid.UUID('00000000-0000-0000-0000-000000000002')
	key = build_upload_key(user_id, doc_id, 'report.pdf')
	assert key == 'uploads/00000000-0000-0000-0000-000000000001/00000000-0000-0000-0000-000000000002/report.pdf'


def test_filesystem_storage_put_get_delete_roundtrip(tmp_path: Path) -> None:
	storage = FilesystemObjectStorage(tmp_path)
	key = 'uploads/u/d/file.md'
	storage.put_bytes(key, b'# hello', 'text/markdown')
	assert storage.get_bytes(key) == b'# hello'
	assert storage.exists(key)
	storage.delete(key)
	assert not storage.exists(key)


def test_filesystem_storage_delete_missing_is_noop(tmp_path: Path) -> None:
	storage = FilesystemObjectStorage(tmp_path)
	storage.delete('uploads/none/missing.pdf')
