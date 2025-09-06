from flask import render_template, redirect, url_for
import mistune
import re
from flobsidian.pages.index_tree import render_tree
from flobsidian.singleton import Singleton
from flobsidian.file_index import FileIndex
from pathlib import Path
from urllib import parse
from flobsidian.utils import logger
import frontmatter
from markupsafe import Markup

re_tag_extra = re.compile(r'!\[\[([^\]]+)\]\]')
wikilink = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def plugin_mermaid(md):
    if not isinstance(md.renderer, mistune.HTMLRenderer):
        return

    orig_block_code = md.renderer.block_code

    def block_code(code, info=None):
        if info == "mermaid":
            return f'<div class="mermaid">{Markup.escape(code)}</div>'
        return orig_block_code(code, info)

    md.renderer.block_code = block_code


def parse_frontmatter(text, name):
    try:
        metadata, content = frontmatter.parse(text)

        if len(metadata) > 0:
            buf = ['---\n', '### Properties\n']
            for k, v in metadata.items():
                buf.append(f' * **{k}**: {v}\n')
            buf.append('---\n')
            content = ''.join(buf) + content
        return content
    except Exception as e:
        logger.error(f'Could not parse frontmatter at {name}: {e}')
        return text


def make_link(link, path: Path, index: FileIndex):
    alias = link.group(2)
    name = link.group(1).strip()
    if not alias:
        alias = name
    if '/' in alias:
        alias = alias.split('/')[-1]
    if '.md' in alias:
        alias = alias.replace('.md')

    link = index.resolve_wikilink(name, path, True)

    if link:
        return f'[{alias}]({link})'
    logger.warning(f'link with [[ {name} |{alias} ]] not found')
    return f"???{alias}???"


def pre_parse(text, full_path, index):
    text = parse_frontmatter(text, Path(full_path).name)

    text = re_tag_extra.sub(r'<img src="\1" style="max-width:100%;">', text)
    offset = 0
    matches = wikilink.finditer(text)
    buf = []
    for m in matches:
        buf.append(text[offset:m.span()[0]])
        buf.append(make_link(m, full_path, index))
        offset = m.span()[1]
    buf.append(text[offset:])

    return ''.join(buf)


def get_markdown(real_path, index):
    with open(real_path) as inp:
        text = inp.read()
    markdown = mistune.create_markdown(
        escape=False,
        plugins=['table', 'strikethrough', 'task_lists', plugin_mermaid])
    html = markdown(pre_parse(text, real_path, index))
    return html


def render_renderer(vault, path, real_path):
    if str(path).endswith('.base'):
        return redirect(url_for('base', vault=vault, subpath=path))
    if str(path).endswith('.excalidraw'):
        return redirect(url_for('excalidraw', vault=vault, subpath=path))
    if Path(real_path).exists() and Path(real_path).is_dir():
        return redirect(url_for('get_folder', vault=vault, subpath=path))
    if not str(path).endswith('.md'):
        return redirect(url_for('get_file', vault=vault, subpath=path))
    return render_template(
        'renderer.html',
        markdown_text=get_markdown(real_path, Singleton.indices[vault]),
        path=path,
        vault=vault,
        navtree=render_tree(Singleton.indices[vault], vault, False),
        is_editor=False,
        home=Singleton.config.vaults[vault].home_file,
        curdir=Path(path).parent,
        curfile=path)
