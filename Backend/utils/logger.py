import sys
import logging
import threading
import io
from typing import Optional

# Module-level lock to prevent race conditions during logger setup
_lock = threading.Lock()


def _build_utf8_handler() -> logging.StreamHandler:
    """
    Create a StreamHandler with UTF-8 encoding without mutating global sys.stdout.
    Uses sys.stdout.buffer (a raw binary stream) wrapped in TextIOWrapper.
    Falls back to reconfigure() or plain sys.stdout gracefully.
    """
    # Best approach: wrap the raw buffer, leaving global sys.stdout untouched
    if hasattr(sys.stdout, "buffer"):
        try:
            utf8_stream = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            return logging.StreamHandler(stream=utf8_stream)
        except Exception:
            pass

    # Fallback: reconfigure only if available (Python 3.7+), on sys.stdout directly
    handler = logging.StreamHandler(stream=sys.stdout)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    return handler


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)

    # Lock ensures only one thread sets up handlers (prevents duplicates)
    with _lock:
        if not logger.handlers:
            # Set logger to DEBUG so handlers can selectively filter levels
            logger.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                "%(asctime)s | %(filename)s:%(lineno)d | %(levelname)s | %(message)s",
                datefmt="%d-%m-%Y %H:%M:%S",  # Fixed: added %S for second precision
            )

            handler = _build_utf8_handler()
            handler.setLevel(logging.INFO)  # Handler controls the effective output level
            handler.setFormatter(formatter)

            logger.addHandler(handler)
            logger.propagate = False

    return logger


class CustomLogger:
    def __init__(self, name: Optional[str] = None) -> None:
        # Accept name so different modules get tagged loggers
        self.logger = get_logger(name)

    def info(self, message: str) -> None:
        self.logger.info(message, stacklevel=2)

    def warning(self, message: str) -> None:
        self.logger.warning(message, stacklevel=2)

    def error(self, message: str) -> None:
        self.logger.error(message, stacklevel=2)

    def debug(self, message: str) -> None:
        self.logger.debug(message, stacklevel=2)

    def critical(self, message: str) -> None:
        # Added: was completely missing
        self.logger.critical(message, stacklevel=2)

    def exception(self, message: str) -> None:
        # Added: logs ERROR + full exception traceback automatically
        self.logger.exception(message, stacklevel=2)

    def set_level(self, level: int) -> None:
        """Dynamically change the effective log level at runtime."""
        for handler in self.logger.handlers:
            handler.setLevel(level)
