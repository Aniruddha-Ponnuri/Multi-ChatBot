"""
Robust UTF-8 logger utility for Python >= 3.9.

Thread-safe, avoids mutating global sys.stdout, and handles
all edge-cases for encoding, propagation, and runtime level control.
"""

from __future__ import annotations  # Enables str | None syntax on Python 3.9

import io
import logging
import sys
import threading
import warnings
from types import TracebackType

# Module-level lock to prevent race conditions during logger setup
_lock = threading.Lock()

# Sentinel to detect if we're inside an active exception context
_NO_ACTIVE_EXCEPTION = "exception() called outside of an active exception context."


def _build_utf8_handler() -> logging.StreamHandler:  # type: ignore[type-arg]
    """
    Create a StreamHandler that writes UTF-8 to stdout.

    Strategy (in order of preference):
    1. Wrap sys.stdout.buffer in a fresh TextIOWrapper — avoids mutating
       the global sys.stdout while still writing UTF-8 to the underlying buffer.
    2. If sys.stdout.buffer is unavailable (e.g. IDLE, some test harnesses),
       fall back to a plain sys.stdout handler without reconfiguring it.

    NOTE: We intentionally do NOT call sys.stdout.reconfigure() as it mutates
    global state, which is unsafe in multi-threaded or multi-logger scenarios.
    """
    if hasattr(sys.stdout, "buffer"):
        try:
            utf8_stream = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
                write_through=True,  # Ensures every write flushes immediately
            )
            return logging.StreamHandler(stream=utf8_stream)
        except Exception as exc:  # noqa: BLE001
            # Surface the failure so it's not silently swallowed
            warnings.warn(
                f"Failed to create UTF-8 StreamHandler via buffer: {exc!r}. "
                "Falling back to sys.stdout.",
                RuntimeWarning,
                stacklevel=2,
            )

    # Fallback: plain sys.stdout (encoding depends on the environment)
    return logging.StreamHandler(stream=sys.stdout)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return (or create) a named logger with a UTF-8 StreamHandler.

    Args:
        name: Logger name. Defaults to the root logger name of this module.
              Pass `__name__` from the calling module for per-module loggers.

    Returns:
        A configured logging.Logger instance.
    """
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)

    with _lock:
        # Re-check inside the lock to avoid TOCTOU race between threads
        if logger.handlers:
            return logger

        # Disable propagation BEFORE adding handlers to avoid
        # a brief window where root logger duplicates messages
        logger.propagate = False

        # Set logger to DEBUG so handlers can selectively filter levels
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(filename)s:%(lineno)d | %(levelname)s | %(message)s",
            datefmt="%d-%m-%Y %H:%M:%S",
        )

        handler = _build_utf8_handler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


class CustomLogger:
    """
    Thin wrapper around logging.Logger providing a clean, consistent API.

    Usage:
        log = CustomLogger(__name__)
        log.info("Server started")
        log.set_level(logging.DEBUG)   # enable verbose output at runtime
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Args:
            name: Logger name (pass __name__ for per-module tagging).
                  Defaults to the logger module's own name if omitted.
        """
        self.logger = get_logger(name)

    # ------------------------------------------------------------------
    # Standard log-level methods
    # ------------------------------------------------------------------

    def debug(self, message: str) -> None:
        self.logger.debug(message, stacklevel=2)

    def info(self, message: str) -> None:
        self.logger.info(message, stacklevel=2)

    def warning(self, message: str) -> None:
        self.logger.warning(message, stacklevel=2)

    def error(self, message: str) -> None:
        self.logger.error(message, stacklevel=2)

    def critical(self, message: str) -> None:
        self.logger.critical(message, stacklevel=2)

    def exception(self, message: str) -> None:
        """
        Log an ERROR message with the full exception traceback.

        MUST be called from within an active ``except`` block.
        Emits a warning and falls back to logger.error() if called outside
        an exception context to avoid confusing 'NoneType: None' tracebacks.
        """
        exc_info = sys.exc_info()
        active: bool = exc_info[0] is not None

        if not active:
            warnings.warn(
                _NO_ACTIVE_EXCEPTION,
                stacklevel=2,
                category=UserWarning,
            )
            self.logger.error(message, stacklevel=2)
            return

        self.logger.exception(message, stacklevel=2)

    # ------------------------------------------------------------------
    # Runtime configuration
    # ------------------------------------------------------------------

    def set_level(self, level: int) -> None:
        """
        Dynamically change the effective log level at runtime.

        Updates BOTH the logger and all its handlers so that the new
        level is fully respected (fixing the original bug where only
        handlers were updated, leaving the logger's own level unchanged).

        Args:
            level: A logging level constant, e.g. logging.DEBUG.
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    # ------------------------------------------------------------------
    # Context manager support — handy for request/task scoping
    # ------------------------------------------------------------------

    def __enter__(self) -> CustomLogger:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Log uncaught exceptions before propagating them."""
        if exc_type is not None:
            self.logger.exception(
                "Unhandled exception in CustomLogger context",
                exc_info=(exc_type, exc_val, exc_tb),
                stacklevel=2,
            )
        return False  # Never suppress the exception
