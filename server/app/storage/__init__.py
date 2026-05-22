from app.storage.deps import get_object_storage
from app.storage.factory import create_object_storage
from app.storage.protocol import ObjectStorage

__all__ = ['ObjectStorage', 'create_object_storage', 'get_object_storage']
