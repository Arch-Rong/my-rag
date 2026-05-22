"""
本地运行基础 Agent 示例（与 LangChain 官方 Quickstart 一致）。

用法：
  cd server
  source .venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env   # 填入 OPENAI_API_KEY
  python scripts/run_agent_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / '.env')

from langchain.agents import create_agent

from app.config import get_settings
from app.tools import get_weather


def main() -> None:
	settings = get_settings()

	agent = create_agent(
		model=settings.agent_model,
		tools=[get_weather],
		system_prompt=settings.agent_system_prompt,
	)

	result = agent.invoke(
		{
			'messages': [
				{
					'role': 'user',
					'content': "What's the weather in San Francisco?",
				},
			],
		},
	)

	last = result['messages'][-1]
	if hasattr(last, 'content_blocks'):
		print(last.content_blocks)
	else:
		print(getattr(last, 'content', last))


if __name__ == '__main__':
	main()
