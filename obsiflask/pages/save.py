"""
The module represents a page to save file
"""
from pathlib import Path

from flask import jsonify

from obsiflask.file_index import FileIndex
from obsiflask.messages import add_message, type_to_int
from obsiflask.app_state import AppState


def make_save(path: str, content: str, index: FileIndex,
              vault: str) -> tuple[str, int]:
    """
    Saves the file and returns results for flask

    Args:
        path (str): path to save file
        content (str): content to save
        index (FileIndex): vault file index
        vault (str): vault name

    Returns:
        tuple[str,int]: result message and code
    """
    path = Path(path)
    parent = Path(path).parent

    try:
        exists = Path(path).exists()
        parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        if not exists:
            index.refresh()
        AppState.hints[vault].update_file(str(Path(path).resolve().relative_to(index.path)))
        add_message(f'Saved file: {path.name}', 0, vault)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        add_message(f'Cannot save file: {path.name}: {e}',
                    type_to_int['error'], vault, repr(e))
        return f'Cannot save: {e}', 400
