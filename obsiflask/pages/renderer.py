"""
Logic for markdown rendering
"""
import json
import re
from pathlib import Path
from threading import Lock
from urllib import parse

import mistune
from flask import render_template, redirect, url_for
import frontmatter
from markupsafe import Markup

from obsiflask.app_state import AppState
from obsiflask.file_index import FileIndex
from obsiflask.utils import logger, get_traceback
from obsiflask.consts import wikilink, re_tag_embed, hashtag
from obsiflask.encrypt.obfuscate import obf_open
from obsiflask.encrypt.meld_decrypt import read_encoded_data
from obsiflask.messages import add_message, type_to_int
from obsiflask.auth import get_user
_lock = Lock()

meld_code = re.compile('🔐β(.+?)🔐', re.MULTILINE)

def url_for_tag(vault: str, tag: str) -> str:
    """
    Generates an url for tags. 
    Note: it's improper way to generate urls, but since the graph is created before application 
    started, this hardcode is reasonable

    Args:
        vault (str): vault name
        tag (str): tag

    Returns:
        str: url for search tag
    """
    return f'/search/{vault}?q={tag.lstrip('  #')}&mode=tags'


def plugin_mermaid(md):
    """
    mermaid handler
    """
    if not isinstance(md.renderer, mistune.HTMLRenderer):
        return

    orig_block_code = md.renderer.block_code

    def block_code(code, info=None):
        if info == "mermaid":
            return f'<div class="mermaid">{Markup.escape(code)}</div>'
        return orig_block_code(code, info)

    md.renderer.block_code = block_code


def plugin_heading_anchor(md):
    """Adds anchor and id to headers"""

    renderer = md.renderer

    if not hasattr(renderer, "heading_anchor_orig"):
        renderer.heading_anchor_orig = renderer.heading

        def heading(text, level):
            slug = parse.quote(text)
            return f'<h{level} id="{slug}">{text} <a href="#{slug}" style="text-decoration:none; font-size:small" class="anchor">🔗</a></h{level}>\n'

        renderer.heading = heading


def parse_frontmatter(text: str, name: str, vault: str) -> str:
    """
    Frontmatter processor.
    Returns a markdown, 
    where frontmatter properties are put into special "properties" section

    Args:
        text (str): text to parse
        name (str): name of file for logging
        vault (str): vault name

    Returns:
        str: processed file
    """
    try:
        metadata, content = frontmatter.parse(text)

        if len(metadata) > 0:
            buf = ['---\n', '### Properties\n']
            for k, v in metadata.items():
                if k == 'tags':
                    if isinstance(v, str):
                        v = [v]
                    new_v = []
                    for el in v:
                        el = el.lstrip('#')
                        new_v.append(f'[==#{el}==]({url_for_tag(vault, el)})')
                    v = new_v
                buf.append(f' * **{k}**: {v}\n')
            buf.append('---\n')
            content = ''.join(buf) + content
        return content
    except Exception as e:
        logger.error(f'Could not parse frontmatter at {name}: {e}')
        return text


def make_link(link: re.Match, path: Path, index: FileIndex) -> str:
    """
    Resolves wiki links

    Args:
        link (re.Match): found regex for wikilink
        path (Path): file path. needs for wikilink resolution
        index (FileIndex): file index

    Returns:
        str: corrected link
    """
    alias = link.group(2)
    name = link.group(1).strip()
    if not alias:
        alias = name
        if '#' in name:
            suffix = name.rsplit('#', 1)[1]
            if suffix:
                alias = suffix
    if '/' in alias:
        alias = alias.split('/')[-1]
    if '.md' in alias:
        alias = alias.replace('.md', '')
    link = index.resolve_wikilink(name, path, True)

    if link:
        return f'[{alias}]({link})'
    logger.warning(f'link with [[ {name} |{alias} ]] not found')
    if str(Path(path).parent) in ['', '.']:
        local_path = Path(path)
    else:
        local_path = Path(path).relative_to(index.path)
    
    if '#' in name:
        name = name.rsplit('#')[0]
    if not name.endswith('.md'):
        name = name+'.md'
    return f'[*NOT FOUND* **{alias}** *NOT FOUND*]({url_for('fastfileop', op='file', curfile=local_path, dst=name, vault=index.vault)})'
    
def parse_encryption(text: str) -> str:
    matches = meld_code.finditer(text)
    offset = 0
    buf = []
    for m_id, m in enumerate(matches):
        buf.append(text[offset:m.span()[0]])
        buf.append(f'<a href="#" onclick="decodeMeld(\'{m.group(1)}\'); return false;">🔐</a>')
        offset = m.span()[1]
    buf.append(text[offset:])
    return ''.join(buf)

def parse_embedding(text: str, full_path: Path, index: FileIndex,
                    vault: str) -> str:
    """
    A handler for resolving embedding tags in markdown

    Args:
        text (str): text to process
        full_path (Path): file path
        index (FileIndex): file index
        vault (str): vault name

    Returns:
        str: markdown
    """
    matches = re_tag_embed.finditer(text)
    offset = 0
    buf = []
    for m_id, m in enumerate(matches):
        buf.append(text[offset:m.span()[0]])
        path = m.group(1)
        link_path = index.resolve_wikilink(path,
                                           full_path,
                                           False,
                                           escape=False,
                                           relative=False)
        relative_link = str(link_path).startswith('http://') or str(
            link_path).startswith('https://')

        if link_path is not None:
            if not relative_link:
                link_path = (Path(index.path) / link_path).relative_to(
                    index.path)

            if '.' in path and path.split('.')[-1] in {
                    'png', 'bmp', 'jpg', 'jpeg'
            }:
                if not relative_link:
                    link_path = url_for('get_file',
                                        vault=vault,
                                        subpath=Markup.escape(link_path))
                buf.append(f'<img src="{link_path}" style="max-width:100%;">')
            elif '.' in path and path.split('.')[-1] in {'base'}:
                link_path = url_for('base', vault=vault, subpath=link_path)
                id_name = 'embed_' + str(m_id)
                buf.append(
                    f'<hr/><iframe id={id_name} src="{link_path}?raw=1"  style="width:95%"></iframe><hr/>'
                )
                buf.append('<script>setupIframeResize("#")</script>'.replace(
                    '#', id_name))
            else:
                link_path = url_for('get_file', vault=vault, subpath=link_path)
                buf.append(f'[{path}]({link_path})')
        else:
            buf.append(f'???{path}???')
        offset = m.span()[1]
    buf.append(text[offset:])
    return ''.join(buf)


def parse_hashtags(text, vault):
    matches = hashtag.finditer(text)
    offset = 0
    buf = []
    for m_id, m in enumerate(matches):
        buf.append(text[offset:m.span()[0]])
        tag = m.group(1).lstrip('#')
        buf.append(f'[==#{tag}==]({url_for_tag(vault, tag)})')
        offset = m.span()[1]
    buf.append(text[offset:])
    return ''.join(buf)


def preprocess(full_path: Path, index: FileIndex, vault: str) -> str:
    """
    An entrypoint for preprocessing markdown logic

    Args:
        full_path (Path): path to file
        index (FileIndex): file index
        vault (str): vault name

    Returns:
        str: preprocessed document
    """
    with _lock:
        with obf_open(full_path, vault) as inp:
            text = inp.read()
    markdown = mistune.create_markdown(escape=False,
                                       plugins=[
                                           'table', 'strikethrough',
                                           'task_lists', 'mark',
                                           plugin_mermaid,
                                           plugin_heading_anchor, 'url', 'math'
                                       ])
    text = parse_hashtags(text, vault)
    text = parse_frontmatter(text, Path(full_path).name, vault)
    text = parse_encryption(text)
    text = parse_embedding(text, full_path, index, vault)
    offset = 0
    matches = wikilink.finditer(text)
    buf = []
    for m in matches:
        buf.append(text[offset:m.span()[0]])
        buf.append(make_link(m, full_path, index))
        offset = m.span()[1]
    buf.append(text[offset:])
    html = markdown(''.join(buf))
    return html

def preprocess_mdenc(path: str, real_path: str, vault: str)-> str:
    try:
        with open(real_path, "r") as file:
            data = json.load(file)
            if data["version"] != "2.0":
                raise ValueError("Only v2.0 supported!")
            if "encodedData" not in data:
                raise ValueError("Missing 'encodedData' key in JSON file")
                
            return f'<a href="#" onclick="decodeMeld(\'{data["encodedData"]}\'); return false;">🔐</a>'
    except Exception as e:
        add_message(f'could not parse encrypted message from {path}: {e}', type=type_to_int['error'], 
                    vault=vault, details=get_traceback(e), user=get_user())


        

def render_renderer(vault: str, path: str, real_path: Path) -> str:
    """
    Logic for rendering

    Args:
        vault (str): vault name
        path (str): path w.r.t. vault
        real_path (Path): full path in the filesystem

    Returns:
        str: rendered html 
    """
    if str(path).endswith('.base'):
        return redirect(url_for('base', vault=vault, subpath=path))
    elif str(path).endswith('.excalidraw') or str(path).endswith('.excalidraw.md'):
        return redirect(url_for('excalidraw', vault=vault, subpath=path))
    elif Path(real_path).exists() and Path(real_path).is_dir():
        return redirect(url_for('get_folder', vault=vault, subpath=path))
    elif str(path).endswith('.mdenc'):
        return render_template('renderer.html',
                           markdown_text=preprocess_mdenc(path, real_path, vault),
                           path=path,
                           vault=vault,
                           is_editor=False,
                           home=AppState.config.vaults[vault].home_file,
                           curdir=Path(path).parent,
                           curfile=path)
    elif not str(path).endswith('.md'):
        return redirect(url_for('get_file', vault=vault, subpath=path))
    
    return render_template('renderer.html',
                           markdown_text=preprocess(real_path,
                                                    AppState.indices[vault],
                                                    vault),
                           path=path,
                           vault=vault,
                           is_editor=False,
                           home=AppState.config.vaults[vault].home_file,
                           curdir=Path(path).parent,
                           curfile=path)
