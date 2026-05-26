"""为 app.* 配置终端日志（uvicorn 默认不会打印应用 logger.info）。"""

from __future__ import annotations

import logging
import os
import sys


def configure_app_logging() -> None:
	level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
	level = getattr(logging, level_name, logging.INFO)

	handler = logging.StreamHandler(sys.stderr)
	handler.setFormatter(
		logging.Formatter(
			'%(asctime)s %(levelname)s [%(name)s] %(message)s',
			datefmt='%H:%M:%S',
		)
	)

	app_logger = logging.getLogger('app')
	app_logger.setLevel(level)
	app_logger.handlers.clear()
	app_logger.addHandler(handler)
	app_logger.propagate = False
