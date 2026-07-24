"""Centralized logging configuration for the trading bot."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_directory: Path | None = None) -> logging.Logger:
    """Configure console and file logging for the CLI.

    The file log is written to ``logs/bot.log`` under the project directory by
    default. The console output stays concise so order results remain readable.
    """

    project_root = Path(__file__).resolve().parent.parent
    default_log_directory = project_root / "logs"
    target_directory = log_directory or default_log_directory
    target_directory.mkdir(parents=True, exist_ok=True)

    log_file = target_directory / "bot.log"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
