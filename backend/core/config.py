"""
配置管理模块
使用pydantic-settings管理应用配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import json


class APISettings(BaseSettings):
    """API服务配置"""

    host: str = Field(default="0.0.0.0", description="API服务地址")
    port: int = Field(default=8000, description="API服务端口")
    reload: bool = Field(default=True, description="是否自动重载")

    model_config = SettingsConfigDict(env_prefix="API_")


class LLMSettings(BaseSettings):
    """LLM配置"""

    provider: str = Field(default="openai", description="LLM提供商")
    model: str = Field(default="qwen-plus", description="模型名称", alias="LLM_MODEL")
    temperature: float = Field(default=0.7, description="生成温度", alias="LLM_TEMPERATURE")
    max_tokens: int = Field(default=2000, description="最大token数", alias="LLM_MAX_TOKENS")
    api_key: str = Field(default="", description="API密钥", alias="OPENAI_API_KEY")
    api_base: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="API基础URL",
        alias="OPENAI_API_BASE"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True  # 允许使用别名填充
    )

    def get_model_kwargs(self) -> dict:
        """获取模型参数"""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


class ExperimentSettings(BaseSettings):
    """实验配置"""

    memory_size: int = Field(default=1000, description="记忆缓冲区大小")
    total_rounds: int = Field(default=500, description="实验总轮次")
    short_term_weight: float = Field(
        default=0.7,
        description="短期奖励权重"
    )
    long_term_weight: float = Field(
        default=0.3,
        description="长期奖励权重"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class LogSettings(BaseSettings):
    """日志配置"""

    level: str = Field(default="INFO", description="日志级别")
    file: str = Field(default="logs/backend.log", description="日志文件路径")

    model_config = SettingsConfigDict(env_prefix="LOG_")


class AppSettings(BaseSettings):
    """应用总配置"""

    api: APISettings = Field(default_factory=APISettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    experiment: ExperimentSettings = Field(default_factory=ExperimentSettings)
    log: LogSettings = Field(default_factory=LogSettings)

    # 跨域配置
    cors_origins: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        description="允许的跨域来源"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 允许额外字段，忽略不匹配的
    )

    @classmethod
    def load(cls) -> "AppSettings":
        """加载配置"""
        return cls()


# 全局配置实例
settings = AppSettings.load()


# 导出配置
__all__ = [
    "APISettings",
    "LLMSettings",
    "ExperimentSettings",
    "LogSettings",
    "AppSettings",
    "settings",
]
