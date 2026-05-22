"""
登录相关的「密码」和「令牌」工具（不碰 HTTP、不碰数据库表结构）。

可以把它理解成：
  - 注册时：把明文密码变成不可逆的哈希存进 users.password_hash
  - 登录时：校验密码对不对，对了就发一张「通行证」JWT
  - 每次请求：从 JWT 里读出是哪个用户（user_id）
"""

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings


def hash_password(plain: str) -> str:
	"""
	注册时用：把用户输入的明文密码变成哈希字符串。

	特点：数据库里不存真实密码，就算库泄露别人也很难反推出原密码。
	同一个密码每次 hash 结果也不同（盐值随机），所以用 verify_password 来比对。
	"""
	digest = bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt())
	return digest.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
	"""
	登录时用：用户输入的密码 和 库里存的 password_hash 是否匹配。

	返回 True = 密码正确，可以发 token；False = 密码错误，返回 401。
	"""
	return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: uuid.UUID) -> str:
	"""
	登录/注册成功后：签发 JWT（前端常说的 access_token）。

	令牌里主要带：
	  - sub：用户 UUID（subject，主体是谁）
	  - exp：过期时间（默认 7 天，见配置 JWT_EXPIRE_MINUTES）

	前端之后请求带上：Authorization: Bearer <这一长串字符串>
	"""
	settings = get_settings()
	expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
	payload = {
		'sub': str(user_id),
		'exp': expire,
	}
	return jwt.encode(
		payload,
		settings.jwt_secret_key,
		algorithm=settings.jwt_algorithm,
	)


def decode_access_token(token: str) -> dict:
	"""
	校验并解析 JWT：签名对不对、有没有过期。

	成功返回 payload 字典（至少含 sub、exp）；
	失败抛 ValueError，上层会转成 HTTP 401「token 无效或过期」。
	"""
	settings = get_settings()
	try:
		return jwt.decode(
			token,
			settings.jwt_secret_key,
			algorithms=[settings.jwt_algorithm],
		)
	except JWTError as exc:
		raise ValueError('invalid token') from exc
