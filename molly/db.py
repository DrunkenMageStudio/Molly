from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class DbConnInfo:
    host: str
    port: int
    name: str
    user: str
    password: str


def build_db_url(cfg: DbConnInfo) -> str:
    # SQLAlchemy URL format for MariaDB/MySQL via PyMySQL:
    # mysql+pymysql://user:pass@host:port/dbname
    return f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.name}"


def create_db_engine(cfg: DbConnInfo) -> Engine:
    # pool_pre_ping helps keep connections sane over long runtimes
    return create_engine(build_db_url(cfg), pool_pre_ping=True, future=True)


def ping_db(engine: Engine) -> None:
    # Raises if connection/auth/db is wrong.
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))