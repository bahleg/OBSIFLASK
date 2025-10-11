import pytest
import json
import re

from obsiflask.pages.index_tree import render_tree
from obsiflask.config import AppConfig, VaultConfig
from obsiflask.main import run


@pytest.fixture
def app(tmp_path):
    (tmp_path / "dir").mkdir()
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "template.md").write_text('write')

    (tmp_path / "dir" / "file.md").write_text('write')
    (tmp_path / "dir" / "file.obf.md").write_text('write')
    (tmp_path / "dir" / "file.txt").write_text('write')
    config = AppConfig(
        vaults={
            'vault':
            VaultConfig(str(tmp_path), template_dir=(tmp_path / "templates")),
        },
        log_level='INFO',
    )

    app = run(config, True)
    return app


def test_render_tree_root(app):
    with app.test_request_context('?global=1'):
        elements = json.loads(render_tree('vault', '').data)
        assert len(elements) == 3  # note, the order is sorted
        assert elements[0]['title'] == '<ROOT>'
        assert elements[0]['lazy'] == False

        assert elements[1]['title'] == 'dir'
        assert elements[1]['lazy'] == True

        assert elements[2]['title'] == 'templates'
        assert elements[1]['lazy'] == True

        for f in elements:
            assert f['folder'] == True
            menu_titles = set([
                re.sub('[^\w\s]', '', t['title']).strip().lower()
                for t in f['data']['menu']
            ])
            assert menu_titles == {
                'open folder', 'create empty file', 'create new folder',
                'duplicate', 'rename', 'delete', 'file operations',
                'new file from templatemd'
            }


def test_folder(app):
    with app.test_request_context():
        elements = json.loads(render_tree('vault', 'dir/').data)
        assert len(elements) == 3
        assert elements[0]['title'] == 'file.md'
        assert elements[1]['title'] == 'file.obf.md'
        assert elements[2]['title'] == 'file.txt'

        for f in elements:
            assert f.get('folder') != True
            assert f.get('lazy') != True

        menu_titles = set([
            re.sub('[^\w\s]', '', t['title']).strip().lower()
            for t in elements[0]['data']['menu']
        ])
        assert menu_titles == {
            'duplicate', 'rename', 'delete', 'file operations', 'download',
            'show', 'edit'
        }

        # download deobfuscated options for obf file
        menu_titles = set([
            re.sub('[^\w\s]', '', t['title']).strip().lower()
            for t in elements[1]['data']['menu']
        ])
        assert menu_titles == {
            'edit', 'show', 'duplicate', 'rename', 'delete', 'file operations',
            'download', 'download wrt obfuscation'
        }

        # less options for non-md file
        menu_titles = set([
            re.sub('[^\w\s]', '', t['title']).strip().lower()
            for t in elements[2]['data']['menu']
        ])
        assert menu_titles == {
            'duplicate',
            'rename',
            'delete',
            'file operations',
            'download',
        }
    # no delete/rename for current file
    with app.test_request_context('?curfile=dir/file.md'):
        elements = json.loads(render_tree('vault', 'dir/').data)
        menu_titles = set([
            re.sub('[^\w\s]', '', t['title']).strip().lower()
            for t in elements[0]['data']['menu']
        ])
        assert menu_titles == {
            'duplicate', 'file operations', 'download', 'show', 'edit'
        }
