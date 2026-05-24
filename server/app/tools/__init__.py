from app.tools.weather import get_weather

# 全局基础工具；聊天接口可再叠加 build_knowledge_tools
ALL_TOOLS = [get_weather]


def _tool_key(tool: object) -> str:
	name = getattr(tool, 'name', None)
	if name:
		return str(name)
	return getattr(tool, '__name__', repr(tool))


def merge_tools(extra: list | None = None) -> list:
	"""
	合并工具列表：始终包含 ALL_TOOLS，再追加 extra（按工具名去重）。

	extra=None → 仅 ALL_TOOLS；extra=[] → 同上；extra=[...] → 并集。
	"""
	if extra is None:
		return list(ALL_TOOLS)
	seen: set[str] = set()
	merged: list = []
	for tool in [*ALL_TOOLS, *extra]:
		key = _tool_key(tool)
		if key in seen:
			continue
		seen.add(key)
		merged.append(tool)
	return merged


__all__ = ['ALL_TOOLS', 'get_weather', 'merge_tools']
