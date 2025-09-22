import pytest
import json

from obsiflask.minihydra import load_config
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig, AuthConfig, UserConfig
from obsiflask.main import run
from obsiflask.auth import (save_user_config, make_user_adjustments, get_user,
                            get_username_info, get_user_config, get_db,
                            try_create_db, get_users, get_username_info,
                            login_perform, update_user, delete_user,
                            register_user, check_password_hash, check_rights,
                            MAX_SESSION_RECORDS, add_session_record)


@pytest.fixture
def app(tmp_path):
    config = AppConfig(vaults={'vault': VaultConfig(str(tmp_path))},
                       auth=AuthConfig(enabled=True,
                                       db_path=tmp_path / "db.db",
                                       rootname="myroot",
                                       default_root_pass="mypass",
                                       user_config_dir=tmp_path / "users"))
    app = run(config, True)

    return app


@pytest.fixture
def app_no_auth(tmp_path):
    config = AppConfig(vaults={'vault': VaultConfig(str(tmp_path))},
                       auth=AuthConfig(enabled=False))
    app = run(config, True)

    return app


def test_save_user_config(tmp_path, app):
    cfg = UserConfig()
    cfg.bootstrap_theme = "test"
    save_user_config('test', cfg)
    cfg2 = load_config(tmp_path / "users" / "test.yml", UserConfig)
    assert cfg == cfg2


def test_get_user_config(tmp_path, app, monkeypatch):
    monkeypatch.setattr('obsiflask.auth.get_user', lambda: None)
    cfg = UserConfig()
    cfg.bootstrap_theme = "test"
    make_user_adjustments('test')
    AppState.user_configs['test'] = cfg
    assert get_user_config() == AppState.config.default_user_config
    monkeypatch.setattr('obsiflask.auth.get_user', lambda: 'test')
    assert get_user_config() == cfg


def test_get_db(tmp_path):
    config = AppConfig(vaults={'vault': VaultConfig(str(tmp_path))},
                       auth=AuthConfig(enabled=True,
                                       db_path=tmp_path / "db.db",
                                       rootname="myroot",
                                       default_root_pass="mypass",
                                       user_config_dir=tmp_path / "users"))
    AppState.config = config
    with pytest.raises(Exception):
        get_db()
    assert get_db(True) is not None
    assert get_db() is not None


def test_create_db(tmp_path):
    config = AppConfig(vaults={'vault': VaultConfig(str(tmp_path))},
                       auth=AuthConfig(enabled=True,
                                       db_path=tmp_path / "db.db",
                                       rootname="myroot",
                                       default_root_pass="mypass",
                                       user_config_dir=tmp_path / "users"))
    AppState.config = config
    if (tmp_path / "db.db").exists():
        (tmp_path / "db.db").unlink()
    try_create_db()
    users = get_users()
    assert len(users) == 1
    assert users[0]['username'] == 'myroot'


def test_register_user_update_user_delete_user_get_users(app):
    register_user('test_new', 'pass', ['vault'], False)
    users = get_users()
    found = False
    for u in users:
        if u['username'] == 'test_new':
            assert u['vaults'] == json.dumps(['vault'])
            assert not u['is_root']
            assert check_password_hash(u['password_hash'], 'pass')
            found = True
    assert found
    user = get_username_info('test_new')
    assert user['is_root'] == False

    update_user('test_new', 'is_root', True)
    user = get_username_info('test_new')
    assert user['is_root'] == True
    delete_user('test_new')
    users = get_users()
    assert len(users) == 1
    assert users[0]['username'] == 'myroot'


def test_get_user_get_username_info_login_perform(app, monkeypatch):
    AppState.config.auth.enabled = False
    assert get_user() is None
    AppState.config.auth.enabled = True

    with pytest.raises(Exception):
        get_user()
    register_user('test_new', 'pass', ['vault'], False)
    with app.test_request_context():
        login_perform('test_new', 'pass')
        assert get_user() == 'test_new'
    monkeypatch.setattr('obsiflask.auth.get_user', lambda: 'test_new')
    assert get_username_info()['username'] == 'test_new'
    assert get_username_info('myroot')['username'] == 'myroot'


def test_check_rights_no_auth(app_no_auth):
    assert check_rights(None, auth_enabled_required=False) is None
    assert check_rights(None, auth_enabled_required=True) is not None


def test_check_rights_no_auth(app):
    with app.test_request_context():
        assert check_rights(None,
                            allow_non_auth=True,
                            ignore_in_session_hist=True) is None
        assert check_rights(None,
                            allow_non_auth=False,
                            ignore_in_session_hist=True) is not None
        register_user('test_new', 'pass', [], False)

        login_perform('myroot', 'mypass')
        assert check_rights(None,
                            user_required=True,
                            ignore_in_session_hist=True) is None
        assert check_rights(None,
                            root_required=True,
                            ignore_in_session_hist=True) is None
        assert check_rights('vault',
                            user_required=True,
                            ignore_in_session_hist=True) is None

        login_perform('test_new', 'pass')
        assert check_rights(None,
                            user_required=True,
                            ignore_in_session_hist=True) is None
        assert check_rights(None,
                            root_required=True,
                            ignore_in_session_hist=True) is not None
        assert check_rights('vault',
                            user_required=True,
                            ignore_in_session_hist=True) is not None


def test_sessions(app):
    with app.test_request_context():
        for i in range(MAX_SESSION_RECORDS + 1):
            add_session_record(str(i))
    # the first was prunned
    assert len(AppState.session_tracker) == MAX_SESSION_RECORDS
    assert set([k[0] for k in AppState.session_tracker
                ]) == set(map(str, range(1, MAX_SESSION_RECORDS + 1)))
