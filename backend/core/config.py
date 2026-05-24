from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    """默认使用后端目录下的 SQLite 文件，无需单独安装数据库服务。"""
    backend_root = Path(__file__).resolve().parent.parent
    data_dir = backend_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / 'alp_learning.db').as_posix()}"


class Settings(BaseSettings):
    """从环境变量或 `.env` 读取配置。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(default_factory=_default_database_url)
    jwt_secret: str = "dev-change-me-use-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 可通过环境变量 JWT_EXPIRE_MINUTES 覆盖

    siliconflow_api_key: str = ""
    siliconflow_model: str = "Qwen/Qwen2.5-7B-Instruct"


settings = Settings()
