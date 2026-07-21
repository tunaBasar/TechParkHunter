from functools import lru_cache

from app.config import Settings
from app.storage.db import DatabaseManager
from app.storage.json_store import JsonStore


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_json_store() -> JsonStore:
    settings = get_settings()
    return JsonStore(data_dir=f"{settings.DATA_DIR}/companies")


@lru_cache
def get_db() -> DatabaseManager:
    settings = get_settings()
    return DatabaseManager(db_path=settings.DATABASE_URL)
