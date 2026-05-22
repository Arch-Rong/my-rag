"""文档上传 / 删除 API（JWT + Postgres + 本地文件存储）。"""

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from app.db.session import get_session
from main import app
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.storage.deps import get_object_storage
from app.storage.filesystem_storage import FilesystemObjectStorage

pytestmark = pytest.mark.skipif(
	not __import__('os').getenv('DATABASE_URL'),
	reason='DATABASE_URL 未设置，跳过需 Postgres 的 API 测试',
)


def _register_and_token(client: TestClient) -> str:
	email = f'doc-{uuid.uuid4()}@example.com'
	reg = client.post(
		'/api/v1/auth/register',
		json={'email': email, 'password': 'test-pass-123'},
	)
	assert reg.status_code == 201, reg.text
	return reg.json()['access_token']


@pytest.fixture
def api_client(tmp_path: Path) -> Generator[TestClient, None, None]:
	engine = create_engine(
		__import__('os').environ['DATABASE_URL'],
		pool_pre_ping=True,
	)
	storage = FilesystemObjectStorage(tmp_path)

	def override_session() -> Generator[Session, None, None]:
		with Session(engine) as session:
			yield session

	app.dependency_overrides[get_session] = override_session
	app.dependency_overrides[get_object_storage] = lambda: storage

	with TestClient(app) as client:
		yield client

	app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(api_client: TestClient) -> dict[str, str]:
	token = _register_and_token(api_client)
	return {'Authorization': f'Bearer {token}'}


def test_upload_requires_auth(api_client: TestClient) -> None:
	response = api_client.post(
		'/api/v1/documents',
		files={'file': ('sample.md', b'# hi', 'text/markdown')},
	)
	assert response.status_code == 401


def test_upload_document_returns_metadata(
	api_client: TestClient, auth_headers: dict[str, str]
) -> None:
	response = api_client.post(
		'/api/v1/documents',
		files={'file': ('sample.md', b'# Title\n\nBody', 'text/markdown')},
		data={'title': 'My Notes'},
		headers=auth_headers,
	)
	assert response.status_code == 201, response.text
	body = response.json()
	assert body['title'] == 'My Notes'
	assert body['status'] == DocumentStatus.queued.value
	assert body['file_path'].startswith('uploads/')


def test_delete_document_removes_db_record_and_storage_file(
	api_client: TestClient,
	auth_headers: dict[str, str],
	tmp_path: Path,
) -> None:
	upload = api_client.post(
		'/api/v1/documents',
		files={'file': ('to-delete.pdf', b'%PDF-1.4', 'application/pdf')},
		headers=auth_headers,
	)
	assert upload.status_code == 201
	doc_id = upload.json()['id']
	file_path = upload.json()['file_path']

	delete = api_client.delete(
		f'/api/v1/documents/{doc_id}',
		headers=auth_headers,
	)
	assert delete.status_code == 204

	engine = create_engine(__import__('os').environ['DATABASE_URL'])
	with Session(engine) as session:
		doc = session.get(Document, uuid.UUID(doc_id))
		assert doc is not None
		assert doc.status == DocumentStatus.deleted

	storage = FilesystemObjectStorage(tmp_path)
	assert not storage.exists(file_path)
