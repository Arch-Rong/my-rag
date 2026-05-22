#!/usr/bin/env python3
"""创建本地开发用演示用户，上传接口需传 X-User-Id。"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select

from app.auth.security import hash_password
from app.db.session import engine
from app.models.user import User

DEMO_EMAIL = 'demo@medrag.local'
DEMO_PASSWORD = 'demo-pass-123'


def main() -> None:
	with Session(engine) as session:
		existing = session.exec(select(User).where(User.email == DEMO_EMAIL)).first()
		if existing:
			if not existing.password_hash:
				existing.password_hash = hash_password(DEMO_PASSWORD)
				session.add(existing)
				session.commit()
			print(existing.id)
			print(f'login: POST /api/v1/auth/login email={DEMO_EMAIL} password={DEMO_PASSWORD}')
			return
		user = User(
			id=uuid.uuid4(),
			email=DEMO_EMAIL,
			display_name='Demo User',
			password_hash=hash_password(DEMO_PASSWORD),
		)
		session.add(user)
		session.commit()
		print(user.id)
		print(f'login: POST /api/v1/auth/login email={DEMO_EMAIL} password={DEMO_PASSWORD}')


if __name__ == '__main__':
	main()
