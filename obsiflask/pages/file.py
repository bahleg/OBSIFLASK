"""
The module provides a download link for files in the vault
"""
from pathlib import Path
from tempfile import mkstemp
from flask import send_file, request

from obsiflask.app_state import AppState
from obsiflask.encrypt.obfuscate import obf_open
from obsiflask.consts import TEXT_FILES_SFX


def get_file(real_path: str, vault: str):
    """
    Retruns a download response for the path

    Args:
        real_path (str): absolute path
        vault (str): vault name
    """
    tmp = None
    try:
        if 'deobfuscate' in request.args and AppState.config.vaults[
                vault].obfuscation_suffix in Path(real_path).suffixes:
            tmp = mkstemp()[1]
            if Path(real_path).suffix in TEXT_FILES_SFX:
                mode = ''
            else:
                mode = 'b'
            with obf_open(real_path, vault, 'r' + mode) as inp:
                content = inp.read()
            with open(tmp, 'w' + mode) as out:
                out.write(content)
            file = tmp
        else:
            file = real_path
        return send_file(file,
                         as_attachment=True,
                         download_name=Path(real_path).name)
    finally:
        if tmp:
            Path(tmp).unlink()
