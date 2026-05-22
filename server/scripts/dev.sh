#!/usr/bin/env bash
# 在 server 目录执行：./scripts/dev.sh
# 或：bash scripts/dev.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
	echo "未找到 .venv，请先：python3 -m venv .venv"
	exit 1
fi

# 必须用项目虚拟环境，不要用 conda 全局的 uvicorn
source .venv/bin/activate

pip install -r requirements.txt -q

echo "→ 使用 Python: $(which python)"
echo "→ 使用 uvicorn: $(which uvicorn)"

exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
