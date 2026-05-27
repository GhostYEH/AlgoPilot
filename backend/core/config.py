import os
import re
from pathlib import Path
from typing import Self

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env 示例占位符，勿当作真实密钥
_LLM_PLACEHOLDER_RE = re.compile(
    r"请替换|你的星火|你的百炼|changeme|replace.?me|xxx+",
    re.IGNORECASE,
)

_DEFAULT_SILICONFLOW_CHAT_URL = "https://api.siliconflow.cn/v1/chat/completions"
_DEFAULT_SILICONFLOW_MODEL = "Qwen/Qwen2.5-7B-Instruct"


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
    jwt_expire_minutes: int = 60 * 24 * 7  # 可通过环境变量 JWT_EXPIRE_MINUTES 覆盖

    # 大模型（OpenAI 兼容）：讯飞星火 或 硅基流动 SiliconFlow，二选一或混填时自动择优
    spark_api_password: str = Field(default="", validation_alias="SPARK_API_PASSWORD")
    siliconflow_api_key: str = Field(default="", validation_alias="SILICONFLOW_API_KEY")
    spark_model: str = Field(default="lite", validation_alias="SPARK_MODEL")
    siliconflow_model: str = Field(
        default=_DEFAULT_SILICONFLOW_MODEL,
        validation_alias="SILICONFLOW_MODEL",
    )
    spark_chat_url: str = Field(
        default="https://spark-api-open.xf-yun.com/v1/chat/completions",
        validation_alias=AliasChoices("SPARK_CHAT_URL", "LLM_CHAT_URL"),
    )
    siliconflow_chat_url: str = Field(
        default=_DEFAULT_SILICONFLOW_CHAT_URL,
        validation_alias=AliasChoices("SILICONFLOW_CHAT_URL", "LLM_CHAT_URL"),
    )

    @model_validator(mode="after")
    def _resolve_llm_endpoint(self) -> Self:
        """合并密钥并修正「SiliconFlow sk- 密钥 + 星火默认 URL/模型」导致的 401。"""
        spark_key = self.spark_api_password.strip()
        sf_key = self.siliconflow_api_key.strip()
        if spark_key and not _is_llm_placeholder(spark_key):
            api_key = spark_key
        elif sf_key and not _is_llm_placeholder(sf_key):
            api_key = sf_key
        else:
            return self

        object.__setattr__(self, "spark_api_password", api_key)

        if api_key.startswith("sk-"):
            url = self.spark_chat_url.strip()
            if "xf-yun.com" in url or _is_llm_placeholder(url):
                object.__setattr__(
                    self,
                    "spark_chat_url",
                    os.environ.get("SILICONFLOW_CHAT_URL", self.siliconflow_chat_url).strip()
                    or _DEFAULT_SILICONFLOW_CHAT_URL,
                )
            model = self.spark_model.strip()
            if model in ("", "lite") or model.startswith("general"):
                object.__setattr__(
                    self,
                    "spark_model",
                    os.environ.get("SILICONFLOW_MODEL", self.siliconflow_model).strip()
                    or _DEFAULT_SILICONFLOW_MODEL,
                )
        return self

    @property
    def llm_configured(self) -> bool:
        return bool(self.spark_api_password.strip()) and not _is_llm_placeholder(
            self.spark_api_password
        )

    @property
    def llm_provider(self) -> str:
        key = self.spark_api_password.strip()
        if key.startswith("sk-"):
            return "siliconflow"
        if "xf-yun.com" in self.spark_chat_url:
            return "spark"
        return "openai_compatible"

    # 阿里云百炼 DashScope · CosyVoice 语音合成
    dashscope_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("DASHSCOPE_API_KEY", "BAILIAN_API_KEY"),
    )
    tts_model: str = Field(
        default="cosyvoice-v3-flash",
        validation_alias=AliasChoices("TTS_MODEL", "COSYVOICE_MODEL"),
    )
    tts_voice: str = Field(
        default="longanyang",
        validation_alias=AliasChoices("TTS_VOICE", "COSYVOICE_VOICE"),
    )

    @property
    def tts_configured(self) -> bool:
        return bool(self.dashscope_api_key.strip())


settings = Settings()
