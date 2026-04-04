"""
MediaFlow — Application logger.
Provides a configured logger that writes to both a rotating file
and an in-app signal so the UI log panel can display entries live.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QObject, Signal


class LogSignalEmitter(QObject):
    """Emits new log lines so the UI can pick them up."""
    new_entry = Signal(str)


class QtLogHandler(logging.Handler):
    """Logging handler that forwards records to a Qt signal."""

    def __init__(self, emitter: LogSignalEmitter) -> None:
        super().__init__()
        self._emitter = emitter

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._emitter.new_entry.emit(msg)
        except RuntimeError:
            pass  # widget already destroyed


# Module-level singleton
_emitter = LogSignalEmitter()


def get_log_emitter() -> LogSignalEmitter:
    return _emitter


def setup_logger(name: str = "mediaflow") -> logging.Logger:
    """Return a fully configured logger (call once at startup)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    # --- file handler -------------------------------------------------------
    log_dir = Path(os.getenv("APPDATA", Path.home())) / "MediaFlow" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = RotatingFileHandler(
        log_dir / f"mediaflow_{today}.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # --- Qt signal handler --------------------------------------------------
    qt_handler = QtLogHandler(_emitter)
    qt_handler.setLevel(logging.DEBUG)
    qt_handler.setFormatter(fmt)
    logger.addHandler(qt_handler)

    # --- console (dev) ------------------------------------------------------
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    return logger
