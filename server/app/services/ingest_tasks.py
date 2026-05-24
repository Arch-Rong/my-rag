"""后台执行 ingest（供 FastAPI BackgroundTasks 或脚本调用）。"""

import logging
import uuid

from sqlmodel import Session

from app.db.session import engine
from app.services.ingest_service import ingest_document
from app.storage.factory import create_object_storage

logger = logging.getLogger(__name__)


def run_ingest_for_document(document_id: uuid.UUID) -> None:
	"""失败只记日志，不抛到 HTTP 层（上传接口已返回 201）。"""
	try:
		with Session(engine) as session:
			ingest_document(session, create_object_storage(), document_id)
	except Exception:
		logger.exception('background ingest failed for document %s', document_id)
