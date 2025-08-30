from pathlib import Path
from flask import jsonify
from flobsidian.utils import logger
from flobsidian.file_index import FileIndex
from flobsidian.messages import add_message


def make_save(path, content, index: FileIndex, vault: str):
    path = Path(path)
    parent = Path(path).parent

    try:
        exists = Path(path).exists()
        parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        if not exists:
            index.add_file(Path(path).absolute())
        add_message(f'Saved file: {path.name}', 0, vault)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f'problems with saving file {path}: {e}')
        add_message(f'Cannot save file: {path.name}: {e}', 2, vault, repr(e))
        return f'Cannot save: {e}', 402
