"""Agent 聊天 scope：未登录仅 system_only。"""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from app.db.session import get_session
from main import app

pytestmark = pytest.mark.skipif(
	not __import__('os').getenv('DATABASE_URL'),
	reason='DATABASE_URL 未设置',
)


@pytest.fixture
def api_client() -> Generator[TestClient, None, None]:
	engine = create_engine(__import__('os').environ['DATABASE_URL'], pool_pre_ping=True)

	def override_session() -> Generator[Session, None, None]:
		with Session(engine) as session:
			yield session

	app.dependency_overrides[get_session] = override_session
	with TestClient(app) as client:
		yield client
	app.dependency_overrides.clear()


def test_anonymous_user_only_scope_rejected(api_client: TestClient) -> None:
	response = api_client.post(
		'/api/v1/agent/chat',
		json={'message': 'hello', 'scope': 'user_only'},
	)
	assert response.status_code == 401


def test_anonymous_system_only_allowed(api_client: TestClient) -> None:
	# 无 ARK_API_KEY 时 Agent 可能失败；此处只验证鉴权通过
	response = api_client.post(
		'/api/v1/agent/chat',
		json={'message': 'hello', 'scope': 'system_only'},
	)
	assert response.status_code != 401


def test_anonymous_all_scope_downgrades(api_client: TestClient) -> None:
	response = api_client.post(
		'/api/v1/agent/chat',
		json={'message': 'hello', 'scope': 'all'},
	)
	assert response.status_code != 401
	if response.status_code == 200:
		assert response.json()['scope'] == 'system_only'
