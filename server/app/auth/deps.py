import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.auth.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


def _user_from_token(
	session: Session, credentials: HTTPAuthorizationCredentials | None
) -> User | None:
	if credentials is None or credentials.scheme.lower() != 'bearer':
		return None
	try:
		payload = decode_access_token(credentials.credentials)
		user_id = uuid.UUID(payload['sub'])
	except (ValueError, KeyError):
		raise HTTPException(status_code=401, detail='invalid or expired token') from None

	user = session.get(User, user_id)
	if user is None:
		raise HTTPException(status_code=401, detail='user not found')
	return user


def get_current_user(
	session: Session = Depends(get_session),
	credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
	user = _user_from_token(session, credentials)
	if user is None:
		raise HTTPException(
			status_code=401,
			detail='authentication required',
			headers={'WWW-Authenticate': 'Bearer'},
		)
	return user


def get_optional_user(
	session: Session = Depends(get_session),
	credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User | None:
	return _user_from_token(session, credentials)
