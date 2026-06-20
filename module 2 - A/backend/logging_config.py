"""
MODULE 2 — PART B: Structured Logging
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from core.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.handlers = [handler]

    # Silence noisy third-party loggers
    logging.getLogger("paddleocr").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
