import re
from pathlib import Path
from typing import Self

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env 示例占位符，勿当作真实密钥
_LLM_PLACEHOLDER_RE = re.compile(
    r"请替换|你的星火|你的百炼|你的讯飞|changeme|replace.?me|xxx+",
    re.IGNORECASE,
)


def _is_llm_placeholder(value: str) -> bool:
    text = value.strip()
    return not text or bool(_LLM_PLACEHOLDER_RE.search(text))


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
    jwt_expire_minutes: int = 60 * 24 * 7

    # 讯飞星火 Spark 大模型（OpenAI 兼容接口）
    spark_api_password: str = Field(default="", validation_alias="SPARK_API_PASSWORD")
    spark_model: str = Field(default="lite", validation_alias="SPARK_MODEL")
    spark_chat_url: str = Field(
        default="https://spark-api-open.xf-yun.com/v1/chat/completions",
        validation_alias=AliasChoices("SPARK_CHAT_URL", "LLM_CHAT_URL"),
    )

    @model_validator(mode="after")
    def _validate_llm_config(self) -> Self:
        """验证讯飞星火配置是否有效。"""
        api_password = self.spark_api_password.strip()
        if api_password and not _is_llm_placeholder(api_password):
            return self
        return self

    @property
    def llm_configured(self) -> bool:
        password = self.spark_api_password.strip()
        return bool(password) and not _is_llm_placeholder(password)

    @property
    def llm_provider(self) -> str:
        return "spark"

    # 科大讯飞在线语音合成（流式 WebAPI v2）
    iflytek_tts_app_id: str = Field(
        default="",
        validation_alias=AliasChoices("IFLYTEK_TTS_APP_ID", "XFYUN_APP_ID"),
    )
    iflytek_tts_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("IFLYTEK_TTS_API_KEY", "XFYUN_API_KEY"),
    )
    iflytek_tts_api_secret: str = Field(
        default="",
        validation_alias=AliasChoices("IFLYTEK_TTS_API_SECRET", "XFYUN_API_SECRET"),
    )
    tts_voice: str = Field(
        default="x4_xiaoyan",
        validation_alias=AliasChoices("TTS_VOICE", "TTS_VCN", "IFLYTEK_TTS_VCN"),
    )

    @property
    def tts_configured(self) -> bool:
        app_id = self.iflytek_tts_app_id.strip()
        api_key = self.iflytek_tts_api_key.strip()
        api_secret = self.iflytek_tts_api_secret.strip()
        if not (app_id and api_key and api_secret):
            return False
        return not any(_is_llm_placeholder(v) for v in (app_id, api_key, api_secret))


settings = Settings()
