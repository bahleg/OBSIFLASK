import pytest

from obsiflask.pages.hint import get_hint, make_short, MAX_HINT_LEN
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig, AuthConfig
from obsiflask.auth import register_user, get_users
from obsiflask.main import run



@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={
        'vault':
        VaultConfig(str(tmp_path), autocomplete_max_ratio_in_key=1.01)
    })
    AppState.messages[('vault', None)] = []
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir" / "test.md").write_text("hello world #mylongtag")
    (tmp_path / "dir" / "test2.md").write_text("hello world #anothertag")
    (tmp_path / "dir" / "logo.png").write_text("binary content")

    app = run(config, True)
    AppState.indices['vault'].refresh()
    return app


@pytest.fixture
def app_auth(tmp_path):
    db_path = tmp_path / "db.db"
    config = AppConfig(vaults={
        'vault':
        VaultConfig(str(tmp_path), autocomplete_max_ratio_in_key=1.01)
    },
                       auth=AuthConfig(enabled=True, db_path=db_path))
    AppState.messages[('vault', None)] = []
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir" / "test.md").write_text("hello world #mylongtag")
    (tmp_path / "dir" / "test2.md").write_text("hello world #anothertag")
    app = run(config, True)
    register_user('user', 'pass', ["vault"])

    yield app
    if db_path.exists():
        db_path.unlink()


def test_make_short(app):
    s = '1' * MAX_HINT_LEN + '2' * MAX_HINT_LEN
    assert make_short(
        s) == '1' * (MAX_HINT_LEN // 2) + '...' + '2' * (MAX_HINT_LEN // 2)

    s = '1' * (MAX_HINT_LEN // 2) + '2' * (MAX_HINT_LEN // 2)

    assert make_short(s) == s


def test_default_hints(app):
    result = (get_hint('vault', ''))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 0
    assert len(result) == 7
    assert result[0]['text'].count('-') == 2
    assert set([result[1]['text'],
                result[2]['text']]) == {'#anothertag', '#mylongtag'}
    assert set([result[3]['text'],
                result[4]['text']]) == {'test.md', 'test2.md'}
    assert set([result[5]['text'],
                result[6]['text']]) == {'dir/test.md', 'dir/test2.md'}


def test_default_hints_auth(app_auth, monkeypatch):
    AppState.hints['vault'].update_file('dir2/newfile', 'root')

    for user in ['root', None]:
        monkeypatch.setattr("obsiflask.pages.hint.get_user", lambda: user)
        result = (get_hint('vault', ''))
        for r in result:
            assert r['short'] == r['text']
            assert r['erase'] == 0
        assert len(result) == 9
        assert result[0]['text'].count('-') == 2
        assert set([result[1]['text'],
                    result[2]['text']]) == {'#anothertag', '#mylongtag'}
        assert set([result[3]['text'], result[4]['text'],
                    result[5]['text']]) == {'test.md', 'test2.md', 'newfile'}
        assert set([
            result[6]['text'],
            result[7]['text'],
            result[8]['text'],
        ]) == {'dir/test.md', 'dir/test2.md', 'dir2/newfile'}

    # checking that we didn't affect another user
    monkeypatch.setattr("obsiflask.pages.hint.get_user", lambda: 'user')
    result = (get_hint('vault', ''))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 0
    assert len(result) == 7
    assert result[0]['text'].count('-') == 2
    assert set([result[1]['text'],
                result[2]['text']]) == {'#anothertag', '#mylongtag'}
    assert set([result[3]['text'],
                result[4]['text']]) == {'test.md', 'test2.md'}
    assert set([result[5]['text'],
                result[6]['text']]) == {'dir/test.md', 'dir/test2.md'}


def test_hashtags(app):
    result = (get_hint('vault', '#'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 1
    assert len(result) == 2
    assert set([result[0]['text'],
                result[1]['text']]) == {'#anothertag', '#mylongtag'}

    result = (get_hint('vault', '#mylongta'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == len('#mylongta')
    assert len(result) == 1
    assert set([result[0]['text']]) == {'#mylongtag'}


def test_taglist(app):
    result = (get_hint('vault', 'tags:'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 0
    assert len(result) == 2
    assert set([result[0]['text'],
                result[1]['text']]) == {' [anothertag]', ' [mylongtag]'}

    result = (get_hint('vault', 'tags: [ABCD'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 4
    assert len(result) == 2
    assert set([result[0]['text'],
                result[1]['text']]) == {'anothertag', 'mylongtag'}

    result = (get_hint('vault', 'tags: [mylongta'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == len('mylongta')
    assert len(result) == 1
    assert set([result[0]['text']]) == {'mylongtag'}


def test_links(app):
    result = (get_hint('vault', '[['))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 0
    assert len(result) == 4
    assert set([result[0]['text'],
                result[1]['text']]) == {'test.md]]', 'test2.md]]'}
    assert set([result[2]['text'],
                result[3]['text']]) == {'dir/test.md]]', 'dir/test2.md]]'}

    result = (get_hint('vault', '[[ABCD'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 4
    assert len(result) == 4
    assert set([result[0]['text'],
                result[1]['text']]) == {'test.md]]', 'test2.md]]'}
    assert set([result[2]['text'],
                result[3]['text']]) == {'dir/test.md]]', 'dir/test2.md]]'}

    result = (get_hint('vault', '[[test.m'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == len('test.m')
    assert len(result) == 2
    assert set([result[0]['text']]) == {'test.md]]'}
    assert set([result[1]['text']]) == {'dir/test.md]]'}


def test_embed(app):
    result = (get_hint('vault', '![['))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 0
    assert len(result) == 4
    assert set([result[0]['text'],
                result[1]['text']]) == {'test.md]]', 'test2.md]]'}
    assert set([result[2]['text'],
                result[3]['text']]) == {'dir/test.md]]', 'dir/test2.md]]'}

    result = (get_hint('vault', '![[ABCD'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 4
    assert len(result) == 4
    assert set([result[0]['text'],
                result[1]['text']]) == {'test.md]]', 'test2.md]]'}
    assert set([result[2]['text'],
                result[3]['text']]) == {'dir/test.md]]', 'dir/test2.md]]'}

    result = (get_hint('vault', '![[logo.'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == len('logo.')
    assert len(result) == 2
    assert set([result[0]['text']]) == {'logo.png]]'}
    assert set([result[1]['text']]) == {'dir/logo.png]]'}


def test_context_hints(app):
    result = (get_hint('vault', 'ABCD'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 4
    assert len(result) == 7
    assert result[0]['text'].count('-') == 2
    assert set([result[1]['text'],
                result[2]['text']]) == {'#anothertag', '#mylongtag'}
    assert set([result[3]['text'],
                result[4]['text']]) == {'test.md', 'test2.md'}
    assert set([result[5]['text'],
                result[6]['text']]) == {'dir/test.md', 'dir/test2.md'}

    result = (get_hint('vault', 'anotherta'))
    for r in result:
        assert r['short'] == r['text']
        assert r['erase'] == 9
    assert len(result) == 1
    assert set([result[0]['text']]) == {'#anothertag'}
