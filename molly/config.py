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
class LmStudioSettings:
    base_url: str
    model: str
    api_key: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class Settings:
    env: str
    log_level: str
    db: DbSettings
    model_adapter: str
    model_context_messages: int
    lmstudio: LmStudioSettings


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

    model_adapter = os.getenv("MOLLY_MODEL_ADAPTER", "dummy").strip().lower()
    model_context_messages = int(os.getenv("MOLLY_MODEL_CONTEXT_MESSAGES", "20").strip())

    lmstudio = LmStudioSettings(
        base_url=os.getenv("MOLLY_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1").strip().rstrip("/"),
        model=os.getenv("MOLLY_LMSTUDIO_MODEL", "local-model").strip(),
        api_key=os.getenv("MOLLY_LMSTUDIO_API_KEY", "lm-studio").strip(),
        temperature=float(os.getenv("MOLLY_LMSTUDIO_TEMPERATURE", "0.7").strip()),
        max_tokens=int(os.getenv("MOLLY_LMSTUDIO_MAX_TOKENS", "350").strip()),
    )

    return Settings(
        env=env,
        log_level=log_level,
        db=db,
        model_adapter=model_adapter,
        model_context_messages=model_context_messages,
        lmstudio=lmstudio,
    )