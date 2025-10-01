"""
The module provides a download link for files in the vault
"""
from pathlib import Path
from tempfile import mkstemp
from flask import send_file

from obsiflask.app_state import AppState


def get_file(real_path: str, vault: str):
    """
    Retruns a download response for the path

    Args:
        real_path (str): absolute path
    """
    tmp = None
    try:
        if AppState.config.vaults[vault].obfuscation_suffix in Path(
                real_path).suffixes:
            tmp = mkstemp()[1]
            with open(real_path, 'rb') as inp:
                bts = inp.read()
            with open(tmp, 'wb') as out:
                out.write(bts)
            file = tmp
        else:
            file = real_path
        return send_file(file,
                         as_attachment=True,
                         download_name=Path(real_path).name)
    finally:
        if tmp:
            Path(tmp).unlink()
