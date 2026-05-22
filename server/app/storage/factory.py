from functools import lru_cache
from pathlib import Path

from app.config import Settings, get_settings
from app.storage.filesystem_storage import FilesystemObjectStorage
from app.storage.protocol import ObjectStorage
from app.storage.s3_storage import S3ObjectStorage


@lru_cache
def create_object_storage(settings: Settings | None = None) -> ObjectStorage:
	cfg = settings or get_settings()
	if cfg.storage_backend == 'filesystem':
		return FilesystemObjectStorage(Path(cfg.storage_local_root))
	return S3ObjectStorage(cfg)
