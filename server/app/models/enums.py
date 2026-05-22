"""
枚举：字段只能取下面列出的几个固定字符串之一。

在 PostgreSQL 里会建成 ENUM 类型，避免乱填「readyy」这种脏数据。
在 Python 里写 DocumentStatus.ready 比手写字符串更安全。
"""

from enum import Enum


class OwnerType(str, Enum):
	"""这份文档属于谁 / 哪类库"""

	system = 'system'  # 系统预置教材（开发者批量导入，无 user_id）
	user = 'user'  # 用户自己上传的


class SourceType(str, Enum):
	"""资料类型（展示、筛选、统计用）"""

	textbook = 'textbook'  # 教材
	guideline = 'guideline'  # 指南
	lecture = 'lecture'  # 讲义
	user_upload = 'user_upload'  # 用户上传（默认）


class RetrievalScope(str, Enum):
	"""RAG 检索范围（聊天接口用）"""

	system_only = 'system_only'  # 仅系统预置库（未登录默认）
	user_only = 'user_only'  # 仅当前用户上传库（需登录）
	all = 'all'  # 系统 + 当前用户（需登录）


class DocumentStatus(str, Enum):
	"""文档入库流水线状态（知识库列表页显示「解析中」「已向量化」等）"""

	queued = 'queued'  # 排队等待处理
	parsing = 'parsing'  # 正在解析 PDF/MD 抽文本
	embedding = 'embedding'  # 正在分块并写入向量
	ready = 'ready'  # 可向量化检索，问答可用
	failed = 'failed'  # 失败（error_message 里看原因）
	deleted = 'deleted'  # 已删除（软删，检索要排除）
