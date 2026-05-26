#!/usr/bin/env python3
"""独立进程执行单文档 ingest（上传后由 ingest_tasks 拉起，可躲过 uvicorn reload）。"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmodel import Session

from app.logging_setup import configure_app_logging
from app.db.session import engine
from app.services.ingest_service import ingest_document
from app.storage.factory import create_object_storage


def main() -> None:
	configure_app_logging()
	if len(sys.argv) < 2:
		print('usage: python scripts/ingest_one_document.py <document_uuid>', file=sys.stderr)
		raise SystemExit(2)
	doc_id = uuid.UUID(sys.argv[1])
	with Session(engine) as session:
		ingest_document(session, create_object_storage(), doc_id)
	print(f'ingest finished: {doc_id}')


if __name__ == '__main__':
	main()
