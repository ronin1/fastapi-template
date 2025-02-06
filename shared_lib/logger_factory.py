import logging
import os
import socket


host_name = socket.gethostname()


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Get the log level and its corresponding color code
        level_color = {
            'DEBUG': '\033[36m',  # Cyan
            'INFO': '\033[32m',   # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',   # Red
            'CRITICAL': '\033[31;1m'  # Bold Red
        }.get(record.levelname, '\033[0m')  # Default: no color

        # Format the log message
        log_message = f"{level_color}{record.levelname:8} {record.name} - {record.message}\033[0m"
        return log_message


def log_config() -> dict | None:
    fmt = os.getenv("LOG_FORMAT", "")
    if fmt is None or fmt == "":
        return None

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": os.getenv("MIN_LOG_LEVEL", "INFO"),
            },
        },
    }


def min_log_level() -> int:
    min_log = os.getenv("MIN_LOG_LEVEL", "INFO").upper()
    if min_log == "DEBUG":
        return logging.DEBUG
    if min_log == "INFO":
        return logging.INFO
    if min_log == "WARNING":
        return logging.WARNING
    if min_log == "ERROR":
        return logging.ERROR
    if min_log == "CRITICAL":
        return logging.CRITICAL
    return logging.NOTSET


class CustomFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    def filter(self, record):
        record.msg = f"@{host_name} - {record.msg}"
        return True

_custom_filter = CustomFilter()


def _setup_logger() -> logging.Logger:
    lgr = logging.getLogger('uvicorn.error')
    lgr.addFilter(_custom_filter)
    return lgr.getChild(host_name)


root_logger = _setup_logger()


def get_logger(name) -> logging.Logger:
    ch = root_logger.getChild(name)
    ch.addFilter(_custom_filter)
    return ch
