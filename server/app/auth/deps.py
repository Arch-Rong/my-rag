"""
FastAPI「依赖注入」：从请求头里取出登录用户。

用法示例（在路由里）：
  current_user: User = Depends(get_current_user)   # 必须登录，否则 401
  user: User | None = Depends(get_optional_user)  # 有 token 就解析，没有就 None

请求头格式：Authorization: Bearer eyJhbGciOiJ...
"""

import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.auth.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

# 自动从 Header 读取 Authorization；auto_error=False 表示没带头也不立刻报错，交给下面函数判断
_bearer = HTTPBearer(auto_error=False)


def _user_from_token(
	session: Session, credentials: HTTPAuthorizationCredentials | None
) -> User | None:
	"""
	内部共用逻辑：把 Bearer token 换成数据库里的 User 行。

	流程：
	  1. 没有 Authorization 或不是 Bearer → 返回 None（表示未登录）
	  2. 解码 JWT，取出 sub（用户 id）
	  3. 用 id 查 users 表
	  4. token 坏了 / 用户被删了 → 抛 401

	上传文档等接口不要直接调这个，用 get_current_user 或 get_optional_user。
	"""
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
	"""
	「必须登录」依赖：挂在上传文档、删除文档、/auth/me 等接口上。

	- 没带 token → 401 authentication required
	- token 有效 → 返回当前 User，路由里用 current_user.id 即可

	在路由参数里写：current_user: User = Depends(get_current_user)
	"""
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
	"""
	「可选登录」依赖：主要给聊天接口用。

	- 没登录 → None，允许只用 system_only 查系统库
	- 已登录 → User，允许 scope=user_only / all

	在路由参数里写：current_user: User | None = Depends(get_optional_user)
	"""
	return _user_from_token(session, credentials)
