from fastapi import APIRouter, HTTPException

from app.db.session import check_db_connection

router = APIRouter(tags=['health'])


@router.get('/health/db')
def health_db():
	"""检查 PostgreSQL 是否可连接。"""
	try:
		ok = check_db_connection()
	except Exception as exc:
		raise HTTPException(status_code=503, detail=str(exc)) from exc
	if not ok:
		raise HTTPException(status_code=503, detail='database unreachable')
	return {'status': 'ok', 'database': 'postgresql'}
