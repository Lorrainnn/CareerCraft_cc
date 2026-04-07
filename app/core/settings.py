from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Auth
    jwt_secret: str = "CHANGE_ME"
    jwt_access_token_expiration: int = 7200  # seconds

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6334
    qdrant_collection_name: str = "resumes"

    # OSS (Aliyun)
    oss_endpoint: str = ""
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_bucket_name: str = ""

    # LLM provider
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    dashscope_rerank_model: str = "qwen3-vl-rerank"

    # Database (MySQL)
    # Example:
    #   mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4
    database_url: str = ""

    # SMTP (optional): used by "忘记密码"验证码
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_ssl: bool = True

    optimization_sse_timeout_seconds: int = 600


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
