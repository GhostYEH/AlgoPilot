import logging
import re
import sys
from pathlib import Path
from typing import Literal, Self

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)

# .env 示例占位符，勿当作真实密钥
_LLM_PLACEHOLDER_RE = re.compile(
    r"请替换|你的星火|你的百炼|你的讯飞|changeme|replace.?me|xxx+"
    r"|your[-_]?spark|your[-_]?iflytek|your[-_]?api[-_]?password"
    r"|your[-_]?app[-_]?id|your[-_]?api[-_]?key|your[-_]?api[-_]?secret",
    re.IGNORECASE,
)


def _is_llm_placeholder(value: str) -> bool:
    text = value.strip()
    return not text or bool(_LLM_PLACEHOLDER_RE.search(text))


def _app_root() -> Path:
    """打包后使用可执行文件所在目录，开发时使用 backend 目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _default_database_url() -> str:
    """默认使用应用根目录/data/ 下的 SQLite 文件，无需单独安装数据库服务。"""
    data_dir = _app_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / 'alp_learning.db').as_posix()}"


def _default_env_file() -> str:
    """打包后从可执行文件目录读取 .env，开发时从 backend 目录读取。"""
    return str(_app_root() / ".env")


class Settings(BaseSettings):
    """从环境变量或 `.env` 读取配置。"""

    model_config = SettingsConfigDict(env_file=_default_env_file(), env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(default_factory=_default_database_url)
    app_env: Literal["development", "test", "production"] = Field(
        default="development",
        validation_alias="APP_ENV",
    )
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
    spark_max_tokens_limit: int = Field(
        default=4096,
        validation_alias="SPARK_MAX_TOKENS_LIMIT",
    )
    spark_timeout: float = Field(
        default=90.0,
        validation_alias="SPARK_TIMEOUT",
    )
    spark_stream_timeout: float = Field(
        default=180.0,
        validation_alias="SPARK_STREAM_TIMEOUT",
    )

    @model_validator(mode="after")
    def _validate_llm_config(self) -> Self:
        """验证讯飞星火配置是否有效，占位符时发出警告。"""
        api_password = self.spark_api_password.strip()
        if api_password and _is_llm_placeholder(api_password):
            _logger.warning(
                "SPARK_API_PASSWORD 仍为示例占位符，AI 功能将不可用，请在 .env 中填入真实密钥"
            )
        if not api_password:
            _logger.info("SPARK_API_PASSWORD 未设置，AI 功能将不可用")
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
    tts_timeout: int = Field(
        default=30,
        validation_alias="TTS_TIMEOUT",
    )
    tts_ssl_verify: bool = Field(
        default=True,
        validation_alias="TTS_SSL_VERIFY",
    )

    cors_origins: str = Field(
        default="http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000",
        validation_alias="CORS_ORIGINS",
    )
    oj_max_code_chars: int = Field(default=20_000, ge=1_000, le=200_000, validation_alias="OJ_MAX_CODE_CHARS")
    oj_run_requests_per_minute: int = Field(
        default=20, ge=1, le=600, validation_alias="OJ_RUN_REQUESTS_PER_MINUTE"
    )
    oj_ai_requests_per_minute: int = Field(
        default=5, ge=1, le=120, validation_alias="OJ_AI_REQUESTS_PER_MINUTE"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        """环境必须显式声明，绝不能从 CORS 配置反推安全策略。"""
        return self.app_env == "production"

    @property
    def tts_configured(self) -> bool:
        app_id = self.iflytek_tts_app_id.strip()
        api_key = self.iflytek_tts_api_key.strip()
        api_secret = self.iflytek_tts_api_secret.strip()
        if not (app_id and api_key and api_secret):
            return False
        return not any(_is_llm_placeholder(v) for v in (app_id, api_key, api_secret))


settings = Settings()
