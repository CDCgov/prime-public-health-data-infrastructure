import logging
from config import get_required_config


class TracebackInfoFilter(logging.Filter):
    """Clear or restore the exception on log records"""

    def __init__(self, clear=True):
        self.clear = clear

    def filter(self, record):
        if self.clear:
            record._exc_info_hidden, record.exc_info = record.exc_info, None
            # clear the exception traceback text cache, if created.
            record.exc_text = None
        elif hasattr(record, "_exc_info_hidden"):
            record.exc_info = record._exc_info_hidden
            del record._exc_info_hidden
        return True


class PhdiAppFormatter(logging.Formatter):
    def formatStack(self, stack_info):
        pass

    def formatException(self, exc_info):
        pass


def init_logger(log_suffix: str = "default"):
    file_log_handler = logging.handlers.RotatingFileHandler(
        filename=f"PhdiLog-{log_suffix}.log",
        encoding="UTF-8",
        backupCount=5,
        maxBytes=1000000,
    )

    log_level = ""
    try:
        log_level = get_required_config("LOG_LEVEL")
    except Exception:
        # Default to WARNING log level if not overridden.
        log_level = logging.WARNING

    file_log_handler.setFormatter(
        PhdiAppFormatter(
            "{asctime} - {filename}:{lineno} - {levelname} - {message}", style="{"
        )
    )

    logger = logging.getLogger(__name__)
    logger.addHandler(file_log_handler)
    logger.setLevel(log_level)
    return logger
