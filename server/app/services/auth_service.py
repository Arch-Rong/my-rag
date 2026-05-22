from fastapi import HTTPException
from sqlmodel import Session, select

from app.auth.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, RegisterRequest


def register_user(session: Session, body: RegisterRequest) -> AuthResponse:
	email = body.email.strip().lower()
	existing = session.exec(select(User).where(User.email == email)).first()
	if existing is not None:
		raise HTTPException(status_code=409, detail='email already registered')

	user = User(
		email=email,
		display_name=body.display_name,
		password_hash=hash_password(body.password),
	)
	session.add(user)
	session.commit()
	session.refresh(user)
	token = create_access_token(user.id)
	return AuthResponse(
		access_token=token,
		id=user.id,
		email=user.email or email,
		display_name=user.display_name,
	)


def login_user(session: Session, email: str, password: str) -> AuthResponse:
	normalized = email.strip().lower()
	user = session.exec(select(User).where(User.email == normalized)).first()
	if user is None or not user.password_hash:
		raise HTTPException(status_code=401, detail='invalid email or password')
	if not verify_password(password, user.password_hash):
		raise HTTPException(status_code=401, detail='invalid email or password')

	token = create_access_token(user.id)
	return AuthResponse(
		access_token=token,
		id=user.id,
		email=user.email or normalized,
		display_name=user.display_name,
	)
