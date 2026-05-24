"""
Token 数量估算。

LangChain 的 RecursiveCharacterTextSplitter 按「字符数」切分，
我们用本模块把配置里的 max_tokens 换算成 chunk_size（字符），便于中英文混排文档。
"""


def estimate_tokens(text: str) -> int:
	"""
	粗算一段文字有多少 token。

	经验：中英文混合时约 2 个字符 ≈ 1 个 token。
	只用于控制分片大小和写入 chunk_count，不必与模型计费完全一致。
	"""
	if not text:
		return 0
	return max(1, (len(text) + 1) // 2)
