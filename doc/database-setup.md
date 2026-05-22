# 数据库阶段 B + C（PostgreSQL + pgvector + SQLModel）

## B：启动 Postgres

在仓库根目录：

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml ps
```

- 镜像：`pgvector/pgvector:pg16`
- 端口：`5432`
- 账号：`medrag` / `medrag`，库名：`medrag`
- 首次启动会自动执行 `docker/init/01-pgvector.sql` 安装 `vector` 扩展

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
