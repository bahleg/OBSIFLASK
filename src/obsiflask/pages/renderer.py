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
from flobsidian.consts import wikilink

re_tag_embed = re.compile(r'!\[\[([^\]]+)\]\]')


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
        alias = alias.replace('.md', '')

    link = index.resolve_wikilink(name, path, True)

    if link:
        return f'[{alias}]({link})'
    logger.warning(f'link with [[ {name} |{alias} ]] not found')
    return f"???{alias}???"


def parse_embedding(text, full_path, index: FileIndex, vault):
    matches = re_tag_embed.finditer(text)
    offset = 0
    buf = []
    for m_id, m in enumerate(matches):
        buf.append(text[offset:m.span()[0]])
        path = m.group(1)
        link_path = index.resolve_wikilink(path,
                                           full_path,
                                           False,
                                           escape=False, relative=False)
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
                                        subpath=link_path)
                buf.append(f'<img src="{link_path}" style="max-width:100%;">')
            elif '.' in path and path.split('.')[-1] in {'base'}:
                link_path = url_for('base', vault=vault, subpath=link_path)
                id_name = 'embed_' + str(m_id)
                buf.append(
                    f'<hr/><iframe id={id_name} src="{link_path}?raw=1"  style="width:95%"></iframe><hr/>'
                )
                buf.append("""
                           <script>
function resizeIframe_#() {
    const iframe = document.getElementById('#');
    try {
        const doc = iframe.contentDocument || iframe.contentWindow.document;
        iframe.style.height = doc.body.scrollHeight + 'px';
    } catch (e) {
        console.warn("Невозможно получить доступ к iframe (cross-origin)");
    }
}
document.getElementById('#').addEventListener('load', resizeIframe_#);</script>
                           
                           """.replace('#', id_name))
            else:
                link_path = url_for('get_file', vault=vault, subpath=link_path)
                buf.append(f'[{path}]({link_path})')
        else:
            buf.append(f'???{path}???')
        offset = m.span()[1]
    buf.append(text[offset:])
    return ''.join(buf)


def pre_parse(text, full_path, index, vault):
    text = parse_frontmatter(text, Path(full_path).name)
    text = parse_embedding(text, full_path, index, vault)
    offset = 0
    matches = wikilink.finditer(text)
    buf = []
    for m in matches:
        buf.append(text[offset:m.span()[0]])
        buf.append(make_link(m, full_path, index))
        offset = m.span()[1]
    buf.append(text[offset:])

    return ''.join(buf)


def get_markdown(real_path, index, vault):
    with open(real_path) as inp:
        text = inp.read()
    markdown = mistune.create_markdown(
        escape=False,
        plugins=['table', 'strikethrough', 'task_lists', plugin_mermaid])
    html = markdown(pre_parse(text, real_path, index, vault))
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
    return render_template('renderer.html',
                           markdown_text=get_markdown(real_path,
                                                      Singleton.indices[vault],
                                                      vault),
                           path=path,
                           vault=vault,
                           navtree=render_tree(Singleton.indices[vault], vault,
                                               False),
                           is_editor=False,
                           home=Singleton.config.vaults[vault].home_file,
                           curdir=Path(path).parent,
                           curfile=path)
