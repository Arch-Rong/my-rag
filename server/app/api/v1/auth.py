from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import (
	AuthResponse,
	LoginRequest,
	RegisterRequest,
	UserResponse,
)
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=AuthResponse, status_code=201)
def register(
	body: RegisterRequest,
	session: Session = Depends(get_session),
) -> AuthResponse:
	return register_user(session, body)


@router.post('/login', response_model=AuthResponse)
def login(
	body: LoginRequest,
	session: Session = Depends(get_session),
) -> AuthResponse:
	return login_user(session, body.email, body.password)


@router.get('/me', response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
	return current_user
