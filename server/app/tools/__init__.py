from app.tools.weather import get_weather

# 演示脚本可用；聊天接口使用 build_knowledge_tools 按 scope 动态注册
ALL_TOOLS = [get_weather]

__all__ = ['ALL_TOOLS', 'get_weather']
