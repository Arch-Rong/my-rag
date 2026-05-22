import sys
from pathlib import Path

# 使 `from main import app` 在 server/ 根下可用
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 注册全部 SQLModel 表，避免 relationship 解析失败
import app.models  # noqa: F401
