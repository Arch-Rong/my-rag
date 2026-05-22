-- 首次启动 Postgres 时自动执行
-- 启用 pgvector：向量存在同库的 chunks.embedding 列（见 Alembic 迁移），不是单独向量库服务
CREATE EXTENSION IF NOT EXISTS vector;
