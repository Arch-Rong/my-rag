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
	agent_system_prompt: str = (
		'你是 MedRAG 学习助手，知识库包含医学教材与用户上传的个人资料（如简历、报告）。'
		'回答应基于检索到的资料；若资料中有工作经历、项目或技能，请据实归纳，'
		'不要声称「只有医学资料」而忽略用户上传的非教材文档。'
	)

	# 向量化（火山方舟 Embedding，OpenAI 兼容 /embeddings）
	embedding_model: str = 'doubao-embedding-large-text-250515'

	# 兼容旧配置（未填 ARK_API_KEY 时回退）
	openai_api_key: str = ''
	openai_api_base: str | None = None

	# PostgreSQL + pgvector（阶段 B/C）
	database_url: str = (
		'postgresql+psycopg://medrag:medrag@127.0.0.1:5432/medrag'
	)
	embedding_dim: int = 1024
	database_echo: bool = False

	# 对象存储：s3 = MinIO（默认），filesystem = 本地目录（测试）
	storage_backend: str = 's3'
	storage_local_root: str = './data/object-storage'

	s3_endpoint: str = 'http://127.0.0.1:9000'
	s3_access_key: str = 'medrag'
	s3_secret_key: str = 'medrag_dev'
	s3_bucket: str = 'medrag-uploads'
	s3_region: str = 'us-east-1'
	s3_use_ssl: bool = False

	# 上传限制
	max_upload_bytes: int = 52_428_800  # 50 MiB

	# JWT 登录（生产务必改 JWT_SECRET_KEY）
	jwt_secret_key: str = 'dev-change-me-use-openssl-rand-hex-32'
	jwt_algorithm: str = 'HS256'
	jwt_expire_minutes: int = 60 * 24 * 7  # 7 天

	# 结构分片（Worker ingest）
	chunk_max_tokens: int = 512
	chunk_overlap_tokens: int = 64
	# 上传成功后是否后台自动分片（pytest 可在 conftest 设为 false）
	ingest_on_upload: bool = True
	# 入库后自动写入 chunk 向量（需 ARK_API_KEY）
	embed_on_ingest: bool = True

	# 混合检索 Top-K / RRF
	retrieval_dense_top_k: int = 12
	retrieval_sparse_top_k: int = 12
	retrieval_final_top_k: int = 6
	retrieval_rrf_k: int = 60

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
