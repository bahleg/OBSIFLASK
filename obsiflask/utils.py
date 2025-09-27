"""
Originally a code from embed2discover (https://gitlab.datascience.ch/democrasci/embed2discover)
GPLv3

Some basic functions for logging, 
working with config and prototyping modules of the toolbox
"""

import logging
import logging.handlers as handlers
from rich.logging import RichHandler
from pathlib import Path

from obsiflask.app_state import AppState

MAX_LOG_SIZE = 100 * 1024 * 1024
"""Maximal log size. After exceeding the limit, will be updated according rolling strategy.
"""

logger = logging.getLogger("obsiflask")
"""
Default obsidian-flask logger
"""


def resolve_service_path(s: str) -> Path:
    """
    Returns a path w.r.t. AppState.config.service_dir if set
    Otherwise returns a pure path

    Args:
        s (str): path to resolve

    Returns:
        Path: resolved path
    """
    if AppState.config.service_dir is None:
        return Path(s)
    else:
        return Path(AppState.config.service_dir) / s


def init_logger(
    file_path: Path | None = None,
    use_rich: bool = True,
    remove_other_handlers: bool = True,
    log_level: str = "DEBUG",
    logger_to_init: logging.Logger | None = None,
) -> logging.Logger:
    """
    Makes a logger for a toolbox.

    Args:
        file_path (Path | None): if set, creates a file with logs, defaults to None
        use_rich (bool): if set, will use rich colors in logs, defaults to True
        remove_other_handlers (bool): if set, will delete all other handlers, defaults to True
        log_level (str): logging level
        logger_to_init (logging.Logger | None): logger to init. If not set, will use default logger
    Returns:
        (logging.Logger): logger
    """
    logger_to_init = logger_to_init or logger
    if remove_other_handlers:
        loggers = [logging.getLogger()]  # get the root logger
        loggers = loggers + [
            logging.getLogger(name) for name in logging.root.manager.loggerDict
        ]
        for _logger in loggers:
            _logger.handlers.clear()
    log_format = "[%(thread)d] %(asctime)s | %(message)s"
    formatter = logging.Formatter(log_format)
    if file_path is not None:
        file_handler = handlers.RotatingFileHandler(file_path,
                                                    maxBytes=MAX_LOG_SIZE)
        file_handler.setFormatter(formatter)
        logger_to_init.addHandler(file_handler)
    if use_rich:
        stream_handler = RichHandler()
    else:
        stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger_to_init.addHandler(stream_handler)
    if log_level == "INFO":
        log_level = logging.INFO
    elif log_level == "WARN" or log_level == "WARNING":
        log_level = logging.WARNING
    elif log_level == "DEBUG":
        log_level = logging.DEBUG
    elif log_level == "ERROR":
        log_level = logging.ERROR

    logger_to_init.setLevel(log_level)
    return logger_to_init
