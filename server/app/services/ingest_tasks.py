"""
上传后异步入库。

为何不用进程内 BackgroundTasks  alone：
  uvicorn --reload 会重启整个 Python 进程，进程内的后台任务会被杀掉，
  导致「上传 201 成功但从未向量化」。

默认改为拉起独立子进程执行 ingest（start_new_session），reload 不会中断子进程。
"""

from __future__ import annotations

import logging
import subprocess
import sys
import uuid
from pathlib import Path

from sqlmodel import Session

from app.config import get_settings
from app.db.session import engine
from app.services.ingest_service import ingest_document
from app.storage.factory import create_object_storage

logger = logging.getLogger(__name__)

_SERVER_ROOT = Path(__file__).resolve().parent.parent.parent
_INGEST_SCRIPT = _SERVER_ROOT / 'scripts' / 'ingest_one_document.py'


def _run_ingest_inprocess(document_id: uuid.UUID) -> None:
	try:
		with Session(engine) as session:
			ingest_document(session, create_object_storage(), document_id)
	except Exception:
		logger.exception('ingest failed for document %s', document_id)


def _run_ingest_subprocess(document_id: uuid.UUID) -> None:
	"""独立子进程跑 ingest，与 uvicorn 主进程解耦。"""
	if not _INGEST_SCRIPT.is_file():
		logger.error('ingest script missing: %s', _INGEST_SCRIPT)
		_run_ingest_inprocess(document_id)
		return
	cmd = [sys.executable, str(_INGEST_SCRIPT), str(document_id)]
	logger.info('spawn ingest subprocess: %s', ' '.join(cmd))
	subprocess.Popen(
		cmd,
		cwd=str(_SERVER_ROOT),
		start_new_session=True,
	)
	# 不 wait：上传接口立即返回；进度看日志或知识库 status


def run_ingest_for_document(document_id: uuid.UUID) -> None:
	"""
	上传接口 BackgroundTasks 入口。

	失败在子进程内记日志，不抛到 HTTP 层（上传已 201）。
	"""
	if get_settings().ingest_spawn_subprocess:
		_run_ingest_subprocess(document_id)
	else:
		_run_ingest_inprocess(document_id)
