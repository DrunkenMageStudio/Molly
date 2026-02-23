from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class DbSettings:
    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(frozen=True)
class Settings:
    env: str
    log_level: str
    db: DbSettings
    model_adapter = os.getenv("MOLLY_MODEL_ADAPTER", "dummy").strip().lower()
    model_context_messages = int(os.getenv("MOLLY_MODEL_CONTEXT_MESSAGES", "20").strip())


def load_settings() -> Settings:
    load_dotenv()

    env = os.getenv("MOLLY_ENV", "dev").strip()
    log_level = os.getenv("MOLLY_LOG_LEVEL", "INFO").strip().upper()

    db = DbSettings(
        host=os.getenv("MOLLY_DB_HOST", "127.0.0.1").strip(),
        port=int(os.getenv("MOLLY_DB_PORT", "3306").strip()),
        name=os.getenv("MOLLY_DB_NAME", "molly").strip(),
        user=os.getenv("MOLLY_DB_USER", "molly").strip(),
        password=os.getenv("MOLLY_DB_PASSWORD", "").strip(),
    )

    return Settings(env=env, log_level=log_level, db=db)