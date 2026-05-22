# 数据库与对象存储（PostgreSQL + pgvector + MinIO）

## B：启动 Postgres 与 MinIO

在仓库根目录：

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml ps
```

| 服务 | 说明 |
|------|------|
| **postgres** | `pgvector/pgvector:pg16`，端口 `5432`，账号 `medrag` / `medrag`，库 `medrag` |
| **minio** | S3 兼容对象存储，API `9000`，控制台 http://127.0.0.1:9001（`medrag` / `medrag_dev`） |

Postgres 首次启动会执行 `docker/init/01-pgvector.sql` 安装 `vector` 扩展。

**MinIO bucket**：在控制台新建 `medrag-uploads`（与 `server/.env` 的 `S3_BUCKET` 一致）；不建也可以，后端首次上传时会尝试自动创建。

## C：Python 依赖与迁移

```bash
cd server
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 确认 .env 中 DATABASE_URL 与上面一致
alembic upgrade head
```

## 验证

```bash
# API 健康检查（需 uvicorn 已启动）
curl http://127.0.0.1:8000/api/v1/health/db

# 进入数据库
docker exec -it medrag-postgres psql -U medrag -d medrag -c '\dt'

# 注册 / 登录（或使用 seed 演示账号）
cd server && source .venv/bin/activate
alembic upgrade head
python scripts/seed_demo_user.py
# 演示：demo@medrag.local / demo-pass-123

TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@medrag.local","password":"demo-pass-123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 上传 PDF / MD（Bearer）
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/notes.md" \
  -F "title=我的笔记"

# 下载源文件
curl -OJ http://127.0.0.1:8000/api/v1/documents/<document_id>/file

# 删除（软删 DB + 删 MinIO 对象 + 删 chunks）
curl -X DELETE http://127.0.0.1:8000/api/v1/documents/<document_id>
```

应看到表：`users`、`documents`、`chunks`。

## 表结构（MVP）

| 表 | 说明 |
|----|------|
| `users` | 用户（MVP 可先单用户） |
| `documents` | 知识库文档元数据、状态、文件路径 |
| `chunks` | 分块正文 + `metadata` JSON + `embedding` 向量 |

枚举：`owner_type`、`source_type`、`document_status`（见 `app/models/enums.py`）。

向量维度默认 **1024**（`.env` 的 `EMBEDDING_DIM`，与 Alembic 迁移一致）。

## 常用命令

```bash
# 新建迁移（改模型后）
alembic revision --autogenerate -m "describe change"
alembic upgrade head

# 回滚一步
alembic downgrade -1

# 开发快捷建表（不用 Alembic，仅本地试）
python -c "from app.db import init_db; init_db()"
```

## 在 FastAPI 里用会话

```python
from fastapi import Depends
from sqlmodel import Session
from app.db.session import get_session

@router.get("/example")
def example(session: Session = Depends(get_session)):
    ...
```

## 目录

```
docker/
  docker-compose.yml
  init/01-pgvector.sql
server/
  app/models/     # SQLModel 表
  app/db/         # engine、get_session
  alembic/        # 迁移
```
