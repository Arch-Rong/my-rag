# MedRAG Server（FastAPI + LangChain Agent）

## 目录结构

```
server/
├── main.py
├── requirements.txt
├── alembic/                # 数据库迁移
├── app/
│   ├── config.py
│   ├── db/                 # engine、get_session
│   ├── models/             # User、Document、Chunk（SQLModel）
│   ├── agents/
│   ├── tools/
│   └── api/v1/
└── scripts/
```

数据库 Docker 与迁移说明见仓库根目录 [`doc/database-setup.md`](../doc/database-setup.md)。

## 安装与运行

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env：ARK_API_KEY、DATABASE_URL 等
```

### 0. 数据库与 MinIO（阶段 B + C）

```bash
# 仓库根目录
docker compose -f docker/docker-compose.yml up -d
cd server && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 含 S3_ENDPOINT 等
alembic upgrade head
python scripts/seed_demo_user.py   # 演示账号 demo@medrag.local / demo-pass-123
curl http://127.0.0.1:8000/api/v1/health/db   # 需先启动 uvicorn
```

### 认证（JWT）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册，返回 `access_token` |
| POST | `/api/v1/auth/login` | 登录 |
| GET | `/api/v1/auth/me` | 当前用户（需 `Authorization: Bearer`） |

**文档上传 / 下载 / 删除**（需登录 Bearer）：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/documents` | multipart：`file`（pdf/md），可选 `title` |
| GET | `/api/v1/documents/{id}/file` | 下载源文件（仅本人） |
| DELETE | `/api/v1/documents/{id}` | 软删记录、删 MinIO 对象与 chunks |

**聊天** `POST /api/v1/agent/chat`：`scope` 默认 `system_only`（未登录可用）；`user_only` / `all` 需登录。

### 1. 命令行跑 Agent 示例

```bash
python scripts/run_agent_demo.py
```

### 2. 启动 API

```bash
uvicorn main:app --reload --port 8000
```

- 健康检查：<http://127.0.0.1:8000/health>
- Swagger：<http://127.0.0.1:8000/docs>
- Agent 对话：`POST /api/v1/agent/chat`

```json
{ "message": "What's the weather in San Francisco?" }
```

## 模型配置（火山方舟 / 豆包）

默认使用 [火山方舟](https://console.volcengine.com/ark) OpenAI 兼容 Chat API：

```env
ARK_API_KEY=你的密钥
ARK_API_BASE=https://ark.cn-beijing.volces.com/api/v3
AGENT_MODEL=doubao-seed-1-6-flash-250715
```

- `ARK_API_KEY`：与 curl 里 `Authorization: Bearer $ARK_API_KEY` 相同。
- `AGENT_MODEL`：控制台 **推理接入点 ID**（你 curl 里 `"model": ""` 需填这里，不能留空）。

说明：文档里的 `POST /api/v3/responses` 多模态接口与 Agent 文本问答不同；本项目通过 LangChain 走 **`/chat/completions`** 兼容路径。

参考：<https://www.volcengine.com/docs/82379/1099455>
