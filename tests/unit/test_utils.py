"""
Originally a code from embed2discover (https://gitlab.datascience.ch/democrasci/embed2discover)
GPLv3
"""

import os
from pathlib import Path

from obsiflask.app_state import AppState, AppConfig
from obsiflask.utils import init_logger, resolve_service_path, get_traceback


def test_resolve_service_path(tmp_path):
    AppState.config = AppConfig({})
    assert resolve_service_path('test') == Path('test')
    AppState.config.service_dir = tmp_path
    assert resolve_service_path('test') == Path(tmp_path / 'test')


def test_logger(tmp_path):
    # test that it does not fail
    logger = init_logger()
    # test that log creates
    logger = init_logger(tmp_path / "log.txt")
    logger.info('test')
    assert os.path.exists(tmp_path / "log.txt")
    # more than number of chars in log message
    assert os.path.getsize(tmp_path / "log.txt") > 4

    # check that nothing bad happens
    init_logger(tmp_path / "log.txt", False)
    init_logger(tmp_path / "log.txt", True, False)


def test_get_traceback():
    try:
        1/0
    except Exception as e:
        exception = True 
        assert len(get_traceback(e))>0
    assert exception