"""
Originally a code from embed2discover (https://gitlab.datascience.ch/democrasci/embed2discover)
GPLv3
"""

import os
import re

from obsiflask.utils import init_logger


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

