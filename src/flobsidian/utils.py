"""
Some basic functions for logging, 
working with config and prototyping modules of the toolbox
"""

from abc import ABC, abstractmethod
import logging
import logging.handlers as handlers
from typing import Any
from dataclasses import dataclass, field
import traceback

from pathy import FluidPath
import dpath
from omegaconf import OmegaConf, DictConfig
import matplotlib.pylab as plt
import seaborn as sns
from optuna import Trial
from rich.logging import RichHandler

MAX_LOG_SIZE = 100 * 1024 * 1024
"""Maximal log size. After exceeding the limit, will be updated according rolling strategy.
"""

logger = logging.getLogger("flobsidian")
"""
Default obsidian-flask logger
"""


def init_logger(
    file_path: str = None,
    use_rich: bool = True,
    remove_other_handlers: bool = True,
    log_level: str = "DEBUG",
    logger_to_init: logging.Logger = None,
) -> logging.Logger:
    """
    Makes a logger for a toolbox.
    Uses "springs" logger settings as a base

    Args:
        file_path (str): if set, creates a file with logs, defaults to None
        use_rich (bool): if set, will use rich colors in logs, defaults to True
        remove_other_handlers (bool): if set, will delete all other handlers, defaults to True
        log_level (str): logging level
        logger_to_init (logging.Logger): logger to init. If not set, will use default logger
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
