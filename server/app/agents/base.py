# os.environ：把 .env 里的配置写进「环境变量」，LangChain / OpenAI SDK 会从这里读 Key
import os
# Any：表示「任意类型」，用于 invoke 返回的复杂字典
import uuid
from typing import Any

# LangChain 官方：用「模型 + 工具 + 系统提示」拼出一个可执行的 Agent（底层是 LangGraph）
from langchain.agents import create_agent
# 火山方舟提供 OpenAI 兼容 Chat API（base_url 为 ark.cn-beijing.volces.com/api/v3）
from langchain_openai import ChatOpenAI
from sqlmodel import Session

# 读 .env 配置（API Key、模型名、系统提示等）
from app.config import get_settings
# 演示脚本用的天气工具
from app.models.enums import RetrievalScope
from app.tools import merge_tools

_SCOPE_HINT = {
	RetrievalScope.all: '全部（系统教材 + 我的上传）',
	RetrievalScope.system_only: '教材（系统预置）',
	RetrievalScope.user_only: '我的上传',
}


def create_base_agent(
	*,
	# 下面的参数都可省略；省略时用 config.py / .env 里的默认值
	model: str | None = None,
	tools: list | None = None,
	system_prompt: str | None = None,
):
	"""创建基础 Agent（LangChain create_agent）。"""
	# 加载配置（带缓存，全进程共用一份）
	settings = get_settings()

	# 同步到环境变量，供 LangChain / OpenAI SDK 读取
	api_key = settings.llm_api_key
	api_base = settings.llm_api_base
	if api_key:
		os.environ.setdefault('OPENAI_API_KEY', api_key)
	if api_base:
		os.environ.setdefault('OPENAI_API_BASE', api_base)

	# 模型 ID = 火山控制台「推理接入点」名称；去掉误写的 openai: 前缀
	model_id = model or settings.agent_model
	if model_id.startswith('openai:'):
		model_id = model_id.split(':', 1)[1]

	# 火山方舟 OpenAI 兼容：/chat/completions（Agent 文本问答走这条，不是 /responses 多模态）
	chat_model = ChatOpenAI(
		model=model_id,
		api_key=api_key,
		base_url=api_base,
		temperature=0.6,
	)

	return create_agent(
		model=chat_model,
		tools=merge_tools(tools),
		system_prompt=system_prompt or settings.agent_system_prompt,
	)


def create_chat_agent(
	session: Session,
	*,
	scope: RetrievalScope,
	user_id: uuid.UUID | None = None,
	use_rag: bool = True,
) -> Any:
	"""
	聊天专用 Agent。

	use_rag=True：注册知识库工具，要求基于检索资料作答；
	use_rag=False：无工具，通用对话（检索门控关闭时）。
	"""
	settings = get_settings()
	scope_hint = _SCOPE_HINT[scope]

	if not use_rag:
		system_prompt = (
			f'{settings.agent_general_prompt}\n\n'
			f'（用户界面当前检索范围为 {scope_hint}，但本轮未命中知识库，未注入参考资料。）'
		)
		return create_base_agent(tools=[], system_prompt=system_prompt)

	from app.tools.knowledge_base import build_knowledge_tools

	tools = build_knowledge_tools(session, scope=scope, user_id=user_id)
	system_prompt = (
		f'{settings.agent_system_prompt}\n\n'
		f'当前知识库检索范围：{scope_hint}。\n'
		'工具说明：\n'
		'- search_knowledge：混合检索（向量+关键词）资料片段；\n'
		'- list_knowledge_documents：列出当前范围内的文档。\n'
		'请优先依据已注入的参考资料或工具检索结果作答，并注明来源；'
		'若资料中无相关内容，如实说明，不要用「整个知识库只有医学资料」这类笼统拒答。'
	)
	return create_base_agent(tools=tools, system_prompt=system_prompt)


def invoke_agent(
	agent,
	user_content: str,
	*,
	thread_id: str | None = None,
	rag_context: str | None = None,
) -> dict[str, Any]:
	"""调用 Agent：传入用户一句话，返回包含整段对话 messages 的字典。"""
	messages: list[dict[str, str]] = []
	if rag_context:
		messages.append(
			{
				'role': 'user',
				'content': f'【系统自动检索到的参考资料】\n{rag_context}',
			}
		)
		messages.append(
			{
				'role': 'assistant',
				'content': '已阅读参考资料，我会在回答中结合这些内容。',
			}
		)
	messages.append({'role': 'user', 'content': user_content})

	payload: dict[str, Any] = {'messages': messages}
	# 若传了 thread_id，同 ID 的多轮请求会共用记忆（需 LangGraph checkpointer 等才完整生效）
	if thread_id:
		payload['thread_id'] = thread_id
	# invoke = 同步跑完整个 Agent 循环（可能多轮：模型 → 调工具 → 再模型 → …）
	return agent.invoke(payload)


def format_agent_reply(result: dict[str, Any]) -> str:
	"""
	从 invoke 的返回值里，取出「助手最后一条」的纯文字，给 API 返回给前端。

	参数 result：agent.invoke(...) 的完整返回值（字典）。
	返回值 str：只给前端展示的最终回答文字。
	"""

	# result.get('messages')：从字典里取键名为 messages 的列表；没有则返回 None
	# `or []`：若是 None，改成空列表 []，避免后面报错
	# 变量 messages：整段对话里所有消息的列表（用户、工具、助手…按时间顺序排列）
	messages = result.get('messages') or []

	# 若列表为空，说明 Agent 没产生任何消息，直接返回空字符串
	if not messages:
		return ''

	# messages[-1]：列表最后一个元素（Python 负数索引表示从后往前数）
	# 变量 last：通常是大模型给用户的「最终回复」那条消息对象（不是 dict，是 LangChain 的 Message）
	last = messages[-1]

	# getattr(对象, '属性名', 默认值)：读取 last.content_blocks；没有该属性则得到 None
	# 变量 content_blocks：可能是「多块内容」的列表（新版 API），例如 [{type:'text', text:'...'}, ...]
	content_blocks = getattr(last, 'content_blocks', None)

	# 若存在 content_blocks，走「按块拼接文字」这条分支
	if content_blocks is not None:
		# 变量 parts：先建一个空列表，用来收集每一段文字
		parts: list[str] = []

		# block：content_blocks 里的每一块（可能是一个 dict、字符串或对象）
		for block in content_blocks:
			# isinstance(变量, 类型)：判断 block 是不是字典
			if isinstance(block, dict):
				# text：从字典里取键 'text' 的值（没有则 None）
				text = block.get('text')
				# 只有 text 有内容时才放进 parts
				if text:
					parts.append(str(text))
			# 若这一块本身就是字符串，直接加入列表
			elif isinstance(block, str):
				parts.append(block)
			else:
				# 其他对象类型：尝试读 .text 属性
				text = getattr(block, 'text', None)
				if text:
					parts.append(str(text))

		# 若 parts 里收集到了至少一段文字
		if parts:
			# '\n'.join(parts)：用换行符把多段拼成一个大字符串并返回
			return '\n'.join(parts)

	# 若没有 content_blocks，或上面没拼出文字，再尝试最常见的 .content 字段
	# 变量 content：通常是 str，有时也可能是别的类型（列表等）
	content = getattr(last, 'content', None)

	# 若 content 已经是普通字符串，直接当作最终回复返回
	if isinstance(content, str):
		return content

	# content 不是 str 但也不是 None（例如列表），强制转成字符串返回
	if content is not None:
		return str(content)

	# 以上都失败：把整条 last 消息对象转成字符串兜底（调试用，正常很少走到）
	return str(last)
