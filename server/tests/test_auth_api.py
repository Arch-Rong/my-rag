"""注册 / 登录 / me API。"""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select

from app.db.session import get_session
from app.models.user import User
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


def _unique_email() -> str:
	return f'user-{uuid.uuid4()}@example.com'


def test_register_login_and_me(api_client: TestClient) -> None:
	email = _unique_email()
	password = 'test-pass-123'

	reg = api_client.post(
		'/api/v1/auth/register',
		json={'email': email, 'password': password, 'display_name': 'Tester'},
	)
	assert reg.status_code == 201, reg.text
	reg_body = reg.json()
	assert reg_body['email'] == email
	assert 'access_token' in reg_body
	token = reg_body['access_token']

	login = api_client.post(
		'/api/v1/auth/login',
		json={'email': email, 'password': password},
	)
	assert login.status_code == 200
	assert login.json()['access_token']

	me = api_client.get(
		'/api/v1/auth/me',
		headers={'Authorization': f'Bearer {token}'},
	)
	assert me.status_code == 200
	assert me.json()['email'] == email


def test_register_duplicate_email_returns_409(api_client: TestClient) -> None:
	email = _unique_email()
	payload = {'email': email, 'password': 'test-pass-123'}
	assert api_client.post('/api/v1/auth/register', json=payload).status_code == 201
	dup = api_client.post('/api/v1/auth/register', json=payload)
	assert dup.status_code == 409


def test_login_wrong_password_returns_401(api_client: TestClient) -> None:
	email = _unique_email()
	api_client.post(
		'/api/v1/auth/register',
		json={'email': email, 'password': 'correct-pass'},
	)
	bad = api_client.post(
		'/api/v1/auth/login',
		json={'email': email, 'password': 'wrong-pass'},
	)
	assert bad.status_code == 401
