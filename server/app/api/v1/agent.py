# functools.lru_cache：缓存函数返回值，相同参数只执行一次（这里用于 Agent 只创建一份）
from functools import lru_cache

# FastAPI 的路由器，用来定义一组 HTTP 接口
from fastapi import APIRouter, Depends, HTTPException
# Pydantic：校验请求体、定义响应 JSON 结构
from pydantic import BaseModel, Field
from openai import APIConnectionError, APIError, AuthenticationError

from app.auth.deps import get_optional_user
from app.config import get_settings
from app.models.enums import RetrievalScope
from app.models.user import User

# 从业务层引入：创建 Agent、调用 Agent、把结果转成纯文本
from app.agents.base import create_base_agent, format_agent_reply, invoke_agent

# 本文件的路由前缀是 /agent；在 router.py 里还会再挂一层 /api/v1
# 最终完整路径：POST /api/v1/agent/chat
router = APIRouter(prefix='/agent', tags=['agent'])

_PLACEHOLDER_API_KEYS = frozenset(
	{
		'',
		'your-ark-api-key',
		'your-api-key',
		'changeme',
	}
)


# ---------- 请求体：客户端 POST 时要传的 JSON ----------
class AgentChatRequest(BaseModel):
	# 用户问题，必填，至少 1 个字符
	message: str = Field(..., min_length=1, description='用户问题')
	# 可选：同一会话 ID，用于 LangChain 多轮记忆（不传则每次当新对话）
	thread_id: str | None = Field(default=None, description='可选，多轮会话 ID')
	# 检索范围：未登录仅允许 system_only
	scope: RetrievalScope = Field(
		default=RetrievalScope.system_only,
		description='system_only | user_only | all',
	)


# ---------- 响应体：接口返回给前端的 JSON ----------
class AgentChatResponse(BaseModel):
	# 助手最终回复的文本
	reply: str
	# 本轮结束后消息列表里有几条（便于调试，看 Agent 调了几轮工具）
	raw_message_count: int
	# 实际使用的检索范围（RAG 接入后按 scope 过滤文档）
	scope: RetrievalScope


# 带缓存的工厂：进程内只调用一次 create_base_agent()，避免每个请求都重建 Agent
@lru_cache
def _get_agent():
	return create_base_agent()


# 注册 POST 接口；response_model 会让 FastAPI 按 AgentChatResponse 生成 OpenAPI 文档
def _resolve_scope(
	body: AgentChatRequest, current_user: User | None
) -> RetrievalScope:
	if body.scope in (RetrievalScope.user_only, RetrievalScope.all) and current_user is None:
		raise HTTPException(
			status_code=401,
			detail='login required for user_only or all scope',
		)
	return body.scope


def _ensure_llm_configured() -> None:
	key = get_settings().llm_api_key.strip()
	if key.lower() in _PLACEHOLDER_API_KEYS:
		raise HTTPException(
			status_code=503,
			detail=(
				'大模型未配置：请在 server/.env 设置有效的 ARK_API_KEY '
				'（火山方舟控制台 → API Key 管理）'
			),
		)


def _raise_llm_http_error(exc: Exception) -> None:
	if isinstance(exc, AuthenticationError):
		raise HTTPException(
			status_code=502,
			detail='大模型 API Key 无效或格式错误，请检查 server/.env 中的 ARK_API_KEY',
		) from exc
	if isinstance(exc, APIConnectionError):
		raise HTTPException(
			status_code=502,
			detail='无法连接大模型服务，请检查网络与 ARK_API_BASE',
		) from exc
	if isinstance(exc, APIError):
		raise HTTPException(status_code=502, detail=str(exc)) from exc
	raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post('/chat', response_model=AgentChatResponse)
def agent_chat(
	body: AgentChatRequest,
	current_user: User | None = Depends(get_optional_user),
) -> AgentChatResponse:
	scope = _resolve_scope(body, current_user)
	_ensure_llm_configured()
	# 1. 拿到（或复用缓存的）LangChain Agent 实例
	agent = _get_agent()
	# 2. 把用户 message 交给 Agent，得到包含 messages 列表的字典
	try:
		result = invoke_agent(agent, body.message, thread_id=body.thread_id)
	except (AuthenticationError, APIConnectionError, APIError) as exc:
		_raise_llm_http_error(exc)
	except Exception as exc:
		_raise_llm_http_error(exc)
	# TODO: RAG 检索时按 scope + current_user.id 过滤 documents/chunks
	# 3. 封装成 API 响应：提取最后一条助手文字 + 消息条数
	return AgentChatResponse(
		reply=format_agent_reply(result),
		raw_message_count=len(result.get('messages') or []),
		scope=scope,
	)
