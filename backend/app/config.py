"""应用配置：全部经环境变量注入（12-factor），本地开发与容器共用一套代码。

环境变量与 deploy/.env.example 一一对应：
- DATABASE_URL        生产=MySQL（mysql+pymysql://...），测试/本地默认 SQLite
- PHOTOS_DIR          NAS 共享相册挂载根（只读）
- CACHE_DIR           缩略图缓存目录（应用私有，读写）
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/upjourney.db"
    photos_dir: str = "./data/photos"
    cache_dir: str = "./data/cache"

    thumb_size: int = 400
    full_size: int = 1600
    image_quality: int = 85

    # 管理端密码：留空 = 未配置，管理 API 一律 503（安全默认：公网忘配密码的后果是
    # 管理端不可用，而不是无密码裸奔）。本地开发在 backend/.env 里配一个即可。
    admin_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """测试需要用不同环境重建 Settings 时调用。"""
    get_settings.cache_clear()


def photos_root(settings: Settings | None = None) -> Path:
    return Path((settings or get_settings()).photos_dir).resolve()


def cache_root(settings: Settings | None = None) -> Path:
    return Path((settings or get_settings()).cache_dir).resolve()
