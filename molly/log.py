from __future__ import annotations

import logging


def setup_logging(level: str) -> None:
    # Minimal, predictable logging. We can get fancy later.
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )