#!/usr/bin/env bash
# 仓库根目录先起 Docker，再在 server 目录执行本脚本
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SERVER="$(cd "$(dirname "$0")/.." && pwd)"

echo "1/3 启动 Postgres（Docker）..."
docker compose -f "$REPO_ROOT/docker/docker-compose.yml" up -d

echo "等待数据库就绪..."
for i in $(seq 1 30); do
	if docker exec medrag-postgres pg_isready -U medrag -d medrag >/dev/null 2>&1; then
		echo "Postgres 已就绪"
		break
	fi
	sleep 1
	if [[ "$i" -eq 30 ]]; then
		echo "超时：请检查 docker compose ps 与 Docker Desktop"
		exit 1
	fi
done

cd "$SERVER"
source .venv/bin/activate
pip install -r requirements.txt -q

echo "2/3 执行迁移 alembic upgrade head..."
alembic upgrade head

echo "3/3 验证表..."
docker exec medrag-postgres psql -U medrag -d medrag -c '\dt'

echo "完成。可启动 API：./scripts/dev.sh"
