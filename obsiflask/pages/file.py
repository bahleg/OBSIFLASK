"""
The module provides a download link for files in the vault
"""
from pathlib import Path
from flask import send_file


def get_file(real_path: str):
    """
    Retruns a download response for the path

    Args:
        real_path (str): absolute path
    """
    return send_file(real_path,
                     as_attachment=True,
                     download_name=Path(real_path).name)
