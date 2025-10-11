"""
The module describes rendering logic for Excalidraw editor page
"""

from pathlib import Path
from threading import Lock
import re
import json

from flask import render_template, abort, request, redirect, url_for
from lzstring import LZString

from obsiflask.pages.save import make_save
from obsiflask.app_state import AppState
from obsiflask.utils import logger, get_traceback
from obsiflask.encrypt.obfuscate import obf_open
from obsiflask.messages import add_message, type_to_int
from obsiflask.auth import get_user

re_spaces = re.compile('\s+', re.MULTILINE | re.DOTALL)
codeblock_json = re.compile('```json(.*?)```', re.MULTILINE | re.DOTALL)
codeblock_compressed_json = re.compile('```compressed-json(.*?)```',
                                       re.MULTILINE | re.DOTALL)

default_excalidraw = """{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "gridSize": 20,
    "gridStep": 5,
    "gridModeEnabled": false,
    "viewBackgroundColor": "#ffffff",
    "lockedMultiSelections": {}
  },
  "files": {}
}"""

default_plugin_excalidraw = """---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: 'Decompress current Excalidraw file'. For more info check in plugin settings under 'Saving'


# Excalidraw Data

## Text Elements
(Compressed version) ^1vCotd7g

%%
## Drawing
```json
{}
```
%%"""
lock = Lock()


def prepare_content_to_write(vault: str, real_path: str, content: str) -> str:
    if str(real_path).endswith('.excalidraw'):
        return content
    with lock:
        with obf_open(real_path, vault) as inp:
            text = inp.read()
    buf = []
    json_match = codeblock_json.search(text)
    if json_match:
        buf.append(text[:json_match.span(1)[0]]+' ')
        buf.append(content)
        buf.append(text[json_match.span(1)[1]:])
        return ''.join(buf)

    json_match = codeblock_compressed_json.search(text)
    if json_match:
        buf.append(text[:json_match.span(1)[0]]+' ')
        lz = LZString()
        buf.append(lz.compressToBase64(content))
        buf.append(text[json_match.span(1)[1]:])
        return ''.join(buf)
    logger.warning(
        f'Could not find excalidraw plugin content. Removing it. Ignore if the file is created now',
    )
    return default_plugin_excalidraw.format(content)


def handle_open(vault: str, real_path: str, is_plugin_based: bool):
    with lock:
        with obf_open(real_path, vault) as inp:
            text = inp.read()
    if len(text.strip()) == 0:
        logger.warning(
            f'Exalidraw content is empty for {real_path}. Ignore if the file is created now',
        )

        text = default_excalidraw
    elif is_plugin_based:
        json_match = codeblock_json.search(text)
        if json_match:
            text = json_match.group(1)
        else:
            compressed_json_match = codeblock_compressed_json.search(
                re_spaces.sub('', text))
            if compressed_json_match:
                try:
                    lz = LZString()
                    text = lz.decompressFromBase64(
                        compressed_json_match.group(1))
                except Exception as e:
                    add_message('Could not decompress text',
                                type_to_int['error'],
                                vault,
                                get_traceback(e),
                                user=get_user())
            else:
                add_message('Bad format for excalidraw.md',
                            type_to_int['error'],
                            vault,
                            text,
                            user=get_user())
                text = default_excalidraw
    try:
        json.loads(text)
    except Exception as e:

        add_message('Exalidraw content is not json',
                    type_to_int['error'],
                    vault,
                    get_traceback(e),
                    user=get_user())
        text = default_excalidraw
    return text


def render_excalidraw(vault: str, path: str, real_path: str) -> str:
    """
  Rendering logic

  Args:
      vault (str): vault name
      path (str): path w.r.t. vault
      real_path (str): filesystem path

  Returns:
      str: html rendered code
  """
    if request.method == 'PUT':
        data = request.get_json()
        content = prepare_content_to_write(vault, real_path, data.get('content', ''))
        return make_save(real_path, content, AppState.indices[vault], vault)
    text = None
    try:
        plugin = path.endswith('.excalidraw.md')
        text = handle_open(vault, real_path, plugin)

    except Exception as e:
        logger.warning(f'attempt to load non-text file: {real_path}: {e}')
    if text is None:
        return abort(400)
    return render_template('excalidraw_editor.html',
                           excalidraw_json=text,
                           path=path,
                           vault=vault,
                           page_editor=True,
                           home=AppState.config.vaults[vault].home_file,
                           curdir=Path(path).parent,
                           curfile=path)
