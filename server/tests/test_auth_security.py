"""密码哈希与 JWT 编解码（无数据库）。"""

from uuid import UUID

from app.auth.security import (
	create_access_token,
	decode_access_token,
	hash_password,
	verify_password,
)


def test_hash_and_verify_password() -> None:
	hashed = hash_password('secret-pass')
	assert hashed != 'secret-pass'
	assert verify_password('secret-pass', hashed)
	assert not verify_password('wrong', hashed)


def test_jwt_roundtrip() -> None:
	user_id = UUID('62ef44b1-f4ad-4801-95cc-fad55631043d')
	token = create_access_token(user_id)
	payload = decode_access_token(token)
	assert payload['sub'] == str(user_id)
