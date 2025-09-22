import pytest
from obsiflask.pages.root import (change_rights, change_vaults, check_vaults,
                                  delete_user, drop_pass, gen_pass,
                                  render_root)

from obsiflask.main import run
from obsiflask.config import AppConfig, VaultConfig, AuthConfig
from obsiflask.auth import register_user, get_username_info, check_password_hash


@pytest.fixture
def app(tmp_path):

    config = AppConfig(
        vaults={'vault1': VaultConfig(str(tmp_path))},
        auth=AuthConfig(enabled=True,
                        db_path=tmp_path / "db.db",
                        rootname="root",
                        default_root_pass="mypass",
                        user_config_dir=tmp_path / "users"),
    )
    app = run(config, True, True)
    register_user('bob', 'pass', [], False)
    return app


def test_change_rights(app):
    with app.test_request_context():
        change_rights(get_username_info('root'), 'root')
        assert get_username_info('root')['is_root']
        assert not get_username_info('bob')['is_root']
        change_rights(get_username_info('root'), 'bob')
        assert get_username_info('bob')['is_root']
        change_rights(get_username_info('bob'), 'root')
        assert get_username_info('root')['is_root']
        change_rights(get_username_info('root'), 'bob')
        assert not get_username_info('bob')['is_root']


def test_drop_pass(app):
    with app.test_request_context():
        drop_pass(get_username_info('root'), 'root')
        assert check_password_hash(
            get_username_info('root')['password_hash'], 'mypass')

        change_rights(get_username_info('root'), 'bob')
        assert get_username_info('bob')['is_root']
        drop_pass(get_username_info('bob'), 'root')
        assert check_password_hash(
            get_username_info('root')['password_hash'], 'mypass')

        drop_pass(get_username_info('root'), 'bob')
        assert not check_password_hash(
            get_username_info('bob')['password_hash'], 'pass')


def test_change_vaults(app):
    with app.test_request_context():
        change_vaults(get_username_info('root'), 'root', '[]')
        assert get_username_info('root')['vaults'] == '[]'
        change_rights(get_username_info('root'), 'bob')
        change_vaults(get_username_info('bob'), 'bob', '[]')
        assert get_username_info('bob')['vaults'] == '[]'

        change_vaults(get_username_info('root'), 'root', '["vault1"]')
        assert get_username_info('root')['vaults'] == '["vault1"]'
        change_vaults(get_username_info('bob'), 'root', '[]')
        assert get_username_info('root')['vaults'] == '["vault1"]'


def test_delete_user(app):
    with app.test_request_context():
        delete_user(get_username_info('root'), 'root')
        assert get_username_info('root') is not None
        assert get_username_info('bob') is not None
        delete_user(get_username_info('root'), 'bob')
        assert get_username_info('bob') is None


def test_gen_pass_generates_unique():
    p1 = gen_pass()
    p2 = gen_pass()
    assert isinstance(p1, str)
    assert isinstance(p2, str)
    assert p1 != p2


def test_check_vaults():
    with pytest.raises(ValueError):
        check_vaults('["badvault"]')
    with pytest.raises(ValueError):
        check_vaults('[')
    with pytest.raises(ValueError):
        check_vaults('[{"hello": 1}]')
    assert check_vaults('["vault1"]') == ["vault1"]


def test_render_root(app, monkeypatch):
    monkeypatch.setattr('obsiflask.auth.get_user', lambda: 'root')
    monkeypatch.setattr("obsiflask.pages.root.render_template",
                        lambda *a, **kw: {"rendered": kw})

    # checking only get
    with app.test_request_context():
        render_root()
