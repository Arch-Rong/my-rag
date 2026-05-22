from app.storage.factory import create_object_storage
from app.storage.protocol import ObjectStorage


def get_object_storage() -> ObjectStorage:
	return create_object_storage()
