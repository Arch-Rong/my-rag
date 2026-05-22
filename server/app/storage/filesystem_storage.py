from pathlib import Path

from app.storage.protocol import ObjectStorage


class FilesystemObjectStorage:
	"""本地目录存储，用于测试或 STORAGE_BACKEND=filesystem。"""

	def __init__(self, root: Path) -> None:
		self._root = root
		self._root.mkdir(parents=True, exist_ok=True)

	def _path(self, key: str) -> Path:
		path = (self._root / key).resolve()
		root = self._root.resolve()
		if not str(path).startswith(str(root)):
			raise ValueError('invalid storage key')
		return path

	def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
		path = self._path(key)
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_bytes(data)

	def get_bytes(self, key: str) -> bytes:
		path = self._path(key)
		if not path.is_file():
			raise FileNotFoundError(key)
		return path.read_bytes()

	def delete(self, key: str) -> None:
		path = self._path(key)
		if path.is_file():
			path.unlink()

	def exists(self, key: str) -> bool:
		return self._path(key).is_file()
