#!/usr/bin/env python3
"""
消费 queued 文档：解析 + 结构分片 + 写入 chunks。

用法（server 目录）：
  python scripts/run_ingest.py              # 处理全部 queued
  python scripts/run_ingest.py <document_uuid>
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session

from app.db.session import engine
from app.services.ingest_service import ingest_document, list_queued_document_ids
from app.storage.factory import create_object_storage


def main() -> None:
	storage = create_object_storage()
	if len(sys.argv) > 1:
		doc_ids = [uuid.UUID(sys.argv[1])]
	else:
		with Session(engine) as session:
			doc_ids = list_queued_document_ids(session)
		if not doc_ids:
			print('no queued documents')
			return

	for doc_id in doc_ids:
		print(f'ingesting {doc_id} ...')
		with Session(engine) as session:
			try:
				doc = ingest_document(session, storage, doc_id)
				print(f'  -> {doc.status.value}, chunks={doc.chunk_count}')
			except Exception as exc:
				print(f'  -> failed: {exc}')


if __name__ == '__main__':
	main()
