from pathlib import Path
from obsiflask.app_state import AppState
from flask import send_file, abort


def get_file(real_path):
    return send_file(real_path,
                     as_attachment=True,
                     download_name=Path(real_path).name)
