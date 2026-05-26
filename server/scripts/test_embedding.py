#!/usr/bin/env python3
"""
测试火山方舟 Embedding 是否可用（与入库向量化同一配置）。

用法：
  cd server
  source .venv/bin/activate
  python scripts/test_embedding.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings


def main() -> int:
	settings = get_settings()
	model = settings.embedding_model
	key = settings.llm_api_key.strip()
	base = settings.llm_api_base

	print('--- Embedding 配置 ---')
	print(f'ARK_API_BASE     = {base}')
	print(f'EMBEDDING_MODEL  = {model}')
	print(f'EMBEDDING_DIM    = {settings.embedding_dim}')
	print(f'ARK_API_KEY      = {"已设置" if key and key != "your-ark-api-key" else "未设置/占位符"}')

	if not key or key.lower() in ('your-ark-api-key', 'changeme'):
		print('\n请在 server/.env 配置有效的 ARK_API_KEY')
		return 1

	try:
		from app.embeddings.client import embed_query

		vec = embed_query('MedRAG embedding test')
		print(f'\n成功：向量维度 = {len(vec)}')
		return 0
	except Exception as exc:
		err = str(exc)
		print(f'\n失败：{err[:500]}')
		if '404' in err or 'NotFound' in err or 'InvalidEndpointOrModel' in err:
			print(
				'\n常见原因：EMBEDDING_MODEL 在账号下未开通，或应使用「推理接入点 ID」。'
				'\n处理步骤：'
				'\n  1. 打开 https://console.volcengine.com/ark'
				'\n  2. 模型广场 → 向量化 → 开通 Doubao Embedding 模型'
				'\n     或：推理接入点 → 创建接入点 → 选择 Embedding 模型'
				'\n  3. 将控制台显示的「模型名」或「ep-xxxxxxxx」写入 .env：'
				'\n     EMBEDDING_MODEL=ep-你的接入点ID'
				'\n  4. 重启后端，再执行：python scripts/backfill_embeddings.py'
			)
		return 1


if __name__ == '__main__':
	raise SystemExit(main())
