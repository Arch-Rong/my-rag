# functools.lru_cache：缓存函数返回值，相同参数只执行一次（这里用于 Agent 只创建一份）
from functools import lru_cache

# FastAPI 的路由器，用来定义一组 HTTP 接口
from fastapi import APIRouter, Depends, HTTPException
# Pydantic：校验请求体、定义响应 JSON 结构
from pydantic import BaseModel, Field
from openai import APIConnectionError, APIError, AuthenticationError
from sqlmodel import Session

from app.auth.deps import get_optional_user
from app.agents.base import create_chat_agent, format_agent_reply, invoke_agent
from app.config import get_settings
from app.db.session import get_session
from app.models.enums import RetrievalScope
from app.models.user import User
from app.rag.gate import should_activate_rag
from app.services.retrieval_service import (
	format_rag_context,
	hits_to_citations,
	search_chunks,
)

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


class CitationItem(BaseModel):
	id: str
	label: str
	excerpt: str


# ---------- 请求体：客户端 POST 时要传的 JSON ----------
class AgentChatRequest(BaseModel):
	# 用户问题，必填，至少 1 个字符
	message: str = Field(..., min_length=1, description='用户问题')
	# 可选：同一会话 ID，用于 LangChain 多轮记忆（不传则每次当新对话）
	thread_id: str | None = Field(default=None, description='可选，多轮会话 ID')
	# 检索范围：对应前端 全部 / 教材 / 我的；默认全部（未登录会降级为教材）
	scope: RetrievalScope = Field(
		default=RetrievalScope.all,
		description='all | system_only | user_only',
	)


# ---------- 响应体：接口返回给前端的 JSON ----------
class AgentChatResponse(BaseModel):
	# 助手最终回复的文本
	reply: str
	# 本轮结束后消息列表里有几条（便于调试，看 Agent 调了几轮工具）
	raw_message_count: int
	# 实际使用的检索范围（RAG 接入后按 scope 过滤文档）
	scope: RetrievalScope
	citations: list[CitationItem] = Field(default_factory=list)


def _resolve_scope(
	body: AgentChatRequest, current_user: User | None
) -> RetrievalScope:
	if body.scope == RetrievalScope.user_only and current_user is None:
		raise HTTPException(
			status_code=401,
			detail='login required for user_only scope',
		)
	# 未登录时「全部」降级为仅系统教材，避免 401
	if body.scope == RetrievalScope.all and current_user is None:
		return RetrievalScope.system_only
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
	session: Session = Depends(get_session),
) -> AgentChatResponse:
	scope = _resolve_scope(body, current_user)
	user_id = current_user.id if current_user else None
	_ensure_llm_configured()

	# 1. 预检索 + 门控：仅 kb_intent 或分数够高时启用 RAG
	hits = search_chunks(
		session,
		body.message,
		scope=scope,
		user_id=user_id,
	)
	use_rag = should_activate_rag(body.message, hits)
	rag_context = format_rag_context(hits) if use_rag else ''
	citations = (
		[CitationItem(**c) for c in hits_to_citations(hits)] if use_rag else []
	)

	# 2. 按门控创建 Agent（RAG 模式带工具，否则通用对话）
	agent = create_chat_agent(
		session, scope=scope, user_id=user_id, use_rag=use_rag
	)
	try:
		result = invoke_agent(
			agent,
			body.message,
			thread_id=body.thread_id,
			rag_context=rag_context or None,
		)
	except (AuthenticationError, APIConnectionError, APIError) as exc:
		_raise_llm_http_error(exc)
	except Exception as exc:
		_raise_llm_http_error(exc)

	return AgentChatResponse(
		reply=format_agent_reply(result),
		raw_message_count=len(result.get('messages') or []),
		scope=scope,
		citations=citations,
	)
