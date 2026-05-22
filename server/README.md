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

### 0. 数据库（阶段 B + C）

```bash
# 仓库根目录
docker compose -f docker/docker-compose.yml up -d
cd server && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
curl http://127.0.0.1:8000/api/v1/health/db   # 需先启动 uvicorn
```

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
