from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file='.env',
		env_file_encoding='utf-8',
		extra='ignore',
	)

	# 火山方舟 Ark（豆包）— 推荐用 ARK_*，见 https://console.volcengine.com/ark
	ark_api_key: str = ''
	ark_api_base: str = 'https://ark.cn-beijing.volces.com/api/v3'

	# 推理接入点 ID，与控制台一致，如 doubao-seed-1-6-flash-250715
	agent_model: str = 'doubao-seed-1-6-flash-250715'
	agent_system_prompt: str = 'You are a helpful assistant'

	# 兼容旧配置（未填 ARK_API_KEY 时回退）
	openai_api_key: str = ''
	openai_api_base: str | None = None

	# PostgreSQL + pgvector（阶段 B/C）
	database_url: str = (
		'postgresql+psycopg://medrag:medrag@127.0.0.1:5432/medrag'
	)
	embedding_dim: int = 1024
	database_echo: bool = False

	@property
	def llm_api_key(self) -> str:
		return self.ark_api_key or self.openai_api_key

	@property
	def llm_api_base(self) -> str:
		base = self.openai_api_base or self.ark_api_base
		return base.rstrip('/')


@lru_cache
def get_settings() -> Settings:
	return Settings()
