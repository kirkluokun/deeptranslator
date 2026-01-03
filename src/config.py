"""配置加载模块"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"


def load_env() -> None:
    """加载环境变量"""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # 尝试加载 .env.example 作为警告
        example_path = PROJECT_ROOT / ".env.example"
        if example_path.exists():
            print("⚠️  未找到 .env 文件，请复制 .env.example 并填入 API Key")


def load_yaml(filename: str) -> dict[str, Any]:
    """加载 YAML 配置文件"""
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"配置文件不存在: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Config:
    """配置管理类"""
    
    _instance = None
    _models: dict | None = None
    _settings: dict | None = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            load_env()
        return cls._instance
    
    @property
    def models(self) -> dict[str, Any]:
        """获取模型配置"""
        if self._models is None:
            self._models = load_yaml("models.yaml")
        return self._models
    
    @property
    def settings(self) -> dict[str, Any]:
        """获取全局设置"""
        if self._settings is None:
            self._settings = load_yaml("settings.yaml")
        return self._settings
    
    @property
    def api_key(self) -> str:
        """获取 Gemini API Key"""
        key = os.getenv("GEMINI_API_KEY")
        if not key or key == "your_api_key_here":
            raise ValueError("请在 .env 文件中配置 GEMINI_API_KEY")
        return key
    
    def get_model(self, purpose: str) -> dict[str, Any]:
        """获取指定用途的模型配置
        
        Args:
            purpose: segment | translate | review
        """
        models = self.models.get("models", {})
        if purpose not in models:
            raise ValueError(f"未知的模型用途: {purpose}")
        return models[purpose]
    
    @property
    def segment_chars(self) -> int:
        """每段目标字符数"""
        return self.settings.get("translation", {}).get("segment_chars", 5000)
    
    @property
    def parallel_workers(self) -> int:
        """并行 worker 数量"""
        return self.settings.get("translation", {}).get("parallel_workers", 10)
    
    @property
    def max_review_rounds(self) -> int:
        """最大审核轮次"""
        return self.settings.get("translation", {}).get("max_review_rounds", 2)
    
    @property
    def retry_config(self) -> dict[str, int]:
        """重试配置"""
        return self.settings.get("retry", {
            "max_attempts": 3,
            "backoff_base": 2,
            "backoff_max": 60
        })
    
    @property
    def checkpoint_enabled(self) -> bool:
        """是否启用断点续传"""
        return self.settings.get("checkpoint", {}).get("enabled", True)
    
    @property
    def source_language(self) -> str:
        """源语言代码"""
        return self.settings.get("language", {}).get("source", "en")
    
    @property
    def target_language(self) -> str:
        """目标语言代码"""
        return self.settings.get("language", {}).get("target", "zh")
    
    def get_language_name(self, code: str) -> str:
        """获取语言名称"""
        names = {
            "en": ("English", "英语"),
            "zh": ("Chinese", "中文"),
            "ja": ("Japanese", "日语"),
            "ko": ("Korean", "韩语"),
            "de": ("German", "德语"),
            "fr": ("French", "法语"),
            "es": ("Spanish", "西班牙语"),
            "ru": ("Russian", "俄语"),
        }
        return names.get(code, (code, code))


# 全局配置实例
config = Config()
