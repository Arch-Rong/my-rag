# MedRAG 服务端入门（FastAPI / Python）

> 面向当前仓库：前端在 `web/`（Next.js），后端计划在 **`api/`**（Python FastAPI）。  
> 与产品需求、API 约定见 [`prd.md`](./prd.md) 第四、五、十一章。

---

## 总览：建议做到哪一步

| 阶段 | 目标 | 建议顺序 |
|------|------|----------|
| **0** | 虚拟环境 + 目录骨架 | 本文 **第一步～第三步** |
| **1** | 跑通 `GET /health` | 第四步 |
| **2** | 对话 / 文档 API 占位 + CORS | 第五步 |
| **3** | PostgreSQL、Redis、Worker | 见 PRD，后续单独文档 |

---

## 第一步：要不要配置虚拟环境？

**要。强烈建议作为第一件事。**

| 做法 | 说明 |
|------|------|
| **推荐：`venv` 项目内虚拟环境** | 依赖隔离、可复现、不污染系统 Python |
| 不推荐：全局 `pip install` | 多项目版本冲突，难以对齐协作与部署 |
| 可选进阶：`uv` / `poetry` | 更快或锁版本更严；MVP 用标准库 `venv` 即可 |

### 环境要求

- **Python 3.11+**（与 PRD 一致；3.12 也可）
- macOS 可先检查：

```bash
python3 --version
# 建议 >= 3.11
```

若版本过低，用 Homebrew 安装：

```bash
brew install python@3.12
```

### 创建并启用虚拟环境（在 `api/` 目录下）

后续会在仓库根目录创建 `api/`，虚拟环境放在 **`api/.venv`**（已加入 `.gitignore`，不要提交）。

```bash
cd /path/to/my-rag

# 1. 创建 api 目录（若尚未创建）
mkdir -p api

# 2. 进入并创建虚拟环境
cd api
python3 -m venv .venv

# 3. 激活（macOS / Linux）
source .venv/bin/activate

# 激活成功后，命令行前会出现 (.venv)
which python   # 应指向 api/.venv/bin/python
which pip      # 应指向 api/.venv/bin/pip
```

**Windows（PowerShell）：**

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 每次开发前

```bash
cd my-rag/api
source .venv/bin/activate
```

退出虚拟环境：

```bash
deactivate
```

### VS Code / Cursor

在仓库 `.vscode/settings.json` 中可指定解释器（路径按本机调整）：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/api/.venv/bin/python"
}
```

打开 `api/` 下任意 `.py` 文件时，右下角选择 **Python: api/.venv**。

---

## 第二步：目录骨架（建议）

与 PRD 第十一章对齐；当前前端在 `web/`，后端用同级 **`api/`** 即可（不必立刻改成 `apps/api/`）。

```
my-rag/
├── web/                 # 已有：Next.js 前端
├── api/                 # 新建：FastAPI
│   ├── .venv/           # 虚拟环境（不提交 Git）
│   ├── .env             # 本地密钥（不提交，见 .env.example）
│   ├── .env.example
│   ├── .gitignore
│   ├── requirements.txt # 或 pyproject.toml
│   ├── README.md        # api 专属启动说明（可选，简短）
│   └── app/
│       ├── __init__.py
│       ├── main.py      # FastAPI 入口
│       ├── config.py    # 配置（读环境变量）
│       ├── api/
│       │   └── v1/
│       │       ├── router.py
│       │       ├── chat.py
│       │       └── documents.py
│       ├── services/    # RAG、LLM 等业务
│       └── models/      # Pydantic schema
├── doc/
│   ├── prd.md
│   └── backend-setup.md # 本文档
└── docker/              # 后期：postgres、redis、compose
```

---

## 第三步：安装依赖

在 **已激活** 的虚拟环境中：

```bash
cd api
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" python-dotenv pydantic-settings

# 后期按需追加，不必第一天全装：
# pip install langchain langchain-openai httpx sqlalchemy asyncpg pgvector ...
```

建议生成锁定文件，便于复现：

```bash
pip freeze > requirements.txt
```

**`api/.gitignore` 建议至少包含：**

```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
.ruff_cache/
```

**`api/.env.example` 示例：**

```env
# 服务
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# 后期
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/medrag
# REDIS_URL=redis://localhost:6379/0
# DEEPSEEK_API_KEY=
```

---

## 第四步：最小可运行 FastAPI

`app/main.py` 示例（第一步跑通即可）：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MedRAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "medrag-api"}
```

启动（在 `api/` 且 venv 已激活）：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：

- 浏览器打开：<http://127.0.0.1:8000/health>
- 自动文档：<http://127.0.0.1:8000/docs>

---

## 第五步：和前端 `web/` 怎么连

1. **本地**：Next.js 默认 `http://localhost:3000`，API `http://localhost:8000`。
2. **CORS**：已在 `main.py` 放行 3000；生产再改 `CORS_ORIGINS`。
3. **环境变量**（`web/.env.local` 示例，后续接真实接口时用）：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

4. **API 路径**：与 PRD 一致，建议统一前缀 **`/api/v1`**，例如：
   - `POST /api/v1/chat` — 问答（流式 SSE）
   - `GET /api/v1/documents` — 知识库列表
   - `POST /api/v1/documents` — 上传

前端 `chat-page` / `library-page` 目前是 mock，后端就绪后改为 `fetch(NEXT_PUBLIC_API_BASE_URL + '/api/v1/...')`。

---

## 常见问题

### 1. `python3` 找不到或版本不对

- macOS：`brew install python@3.12`，用 `python3.12 -m venv .venv` 创建环境。

### 2. 终端里没有 `(.venv)`

- 未执行 `source .venv/bin/activate`，或路径不对。

### 3. `pip install` 装到了系统里

- 先 `which pip`，必须显示 `api/.venv/bin/pip`。

### 4. 要不要用 Docker？

- **开发初期**：本机 venv + uvicorn 即可。
- **接 PostgreSQL / Redis 后**：再用 `docker/docker-compose.yml`（PRD 4.4），与 venv 不冲突：Python 仍在宿主机 venv 里跑，数据库在容器里。

---

## 推荐执行清单（今天就可以做）

- [ ] 安装 Python 3.11+
- [ ] `mkdir api && cd api && python3 -m venv .venv && source .venv/bin/activate`
- [ ] `pip install fastapi uvicorn[standard] python-dotenv pydantic-settings`
- [ ] 按上文创建 `app/main.py` 与 `.gitignore`
- [ ] `uvicorn app.main:app --reload --port 8000`，确认 `/health` 返回 ok
- [ ] （可选）在 Cursor 里选中 `api/.venv` 解释器

完成以上步骤后，再进入 **文档 CRUD、RAG 检索、异步 Worker**（见 PRD Phase 1）。

---

## 下一步文档（可后续补充）

| 文档 | 内容 |
|------|------|
| `doc/api-design.md` | `/api/v1` 请求/响应 JSON 与错误码 |
| `doc/database.md` | PostgreSQL + pgvector 表结构 |
| `api/README.md` | 一键启动、测试命令 |

---

*文档版本：v0.1 · MedRAG 后端第一步：虚拟环境与 FastAPI 骨架*
