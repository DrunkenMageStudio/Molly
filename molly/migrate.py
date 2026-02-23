from __future__ import annotations

import os
from alembic import command
from alembic.config import Config


def alembic_config() -> Config:
    # Repo root = parent of the "molly" package folder
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(repo_root, "alembic.ini")
    return Config(ini_path)


def upgrade_head() -> None:
    command.upgrade(alembic_config(), "head")