from collections.abc import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

engine = create_engine(
	get_settings().database_url,
	echo=get_settings().database_echo,
	pool_pre_ping=True,
)


def init_db() -> None:
	"""开发用：按模型建表（生产请用 Alembic migrate）。"""
	SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
	"""FastAPI Depends(get_session) 注入数据库会话。"""
	with Session(engine) as session:
		yield session


def check_db_connection() -> bool:
	with Session(engine) as session:
		session.execute(text('SELECT 1'))
	return True
