# MedRAG Server（FastAPI + LangChain Agent）

## 目录结构

```
server/
├── main.py                 # FastAPI 入口
├── requirements.txt
├── .env.example
├── app/
│   ├── config.py           # 环境变量 / 模型配置
│   ├── agents/
│   │   └── base.py         # create_base_agent、invoke_agent
│   ├── tools/
│   │   └── weather.py      # 示例 Tool
│   └── api/v1/
│       ├── router.py
│       └── agent.py        # POST /api/v1/agent/chat
└── scripts/
    └── run_agent_demo.py   # 本地跑 Agent 示例
```

## 安装与运行

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入智谱 OPENAI_API_KEY（见 .env.example）
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
