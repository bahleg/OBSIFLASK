import pytest

import obsiflask.messages as messages
from obsiflask.main import run
from obsiflask.config import AppConfig, VaultConfig, AuthConfig
from obsiflask.app_state import AppState
from obsiflask.auth import register_user


@pytest.fixture
def app(tmp_path):
    config = AppConfig(
        vaults={'vault1': VaultConfig(str(tmp_path), message_list_size=3)})
    AppState.messages[('vault1', None)] = []
    app = run(config, True)
    # adding artifical user for tracking messages
    AppState.messages[('vault1', 'user1')] = []
    return app


@pytest.fixture
def app_auth(tmp_path):
    db_path = tmp_path / "auth.db"
    config = AppConfig(
        vaults={'vault1': VaultConfig(str(tmp_path), message_list_size=3)},
        auth=AuthConfig(enabled=True, db_path=db_path))
    AppState.messages[('vault1', None)] = []
    app = run(config, True)

    register_user('user', 'pass', [])
    register_user('user2', 'pass', ['vault1'])

    yield app
    if db_path.exists():
        db_path.unlink()


def test_add_message_and_retrieve(app):
    for k in AppState.messages:
        AppState.messages[k] = []
    messages.add_message("hello", 0, "vault1", user="user1", use_log=False)
    result = messages.get_messages("vault1", user="user1", consider_read=False)
    assert len(result) == 1
    assert result[0].message == "hello"
    assert result[0].type == 0
    assert result[0].vault == "vault1"
    assert result[0].user == "user1"


def test_add_message_and_retrieve_auth(app_auth):
    for k in AppState.messages:
        AppState.messages[k] = []
    messages.add_message("hello", 0, "vault1", user=None, use_log=False)
    result = messages.get_messages("vault1", user='root', consider_read=True)
    assert len(result) == 1
    assert result[0].message == "hello"
    assert result[0].type == 0
    assert result[0].vault == "vault1"
    assert result[0].user == "root"

    result = messages.get_messages("vault1", user='user2', consider_read=True)
    assert len(result) == 1
    assert result[0].message == "hello"
    assert result[0].type == 0
    assert result[0].vault == "vault1"
    assert result[0].user == "user2"

    result = messages.get_messages("vault1", user='user1', consider_read=True)
    assert len(result) == 0


def test_get_messages_marks_as_read(app):
    messages.add_message("m1", 0, "vault1", user=None, use_log=False)
    result = messages.get_messages("vault1", user=None)
    assert all(m.is_read for m in result)


def test_get_messages_unread_filter(app):
    messages.add_message("m1", 0, "vault1", use_log=False)
    # First read
    _ = messages.get_messages("vault1")
    # Second read with unread=True — must return empty
    result = messages.get_messages("vault1", unread=True)
    assert result == []


def test_message_list_size_limit(app):
    # message_list_size = 3 → max 3
    for i in range(10):
        messages.add_message(f"msg{i}", 0, "vault1", use_log=False)

    result = messages.get_messages("vault1", consider_read=False, unread=False)
    assert len(result) == 3  # limited
    # checking last time
    times = [m.time for m in result]
    assert times == sorted(times, reverse=True)


def test_invalid_type_raises(app):
    with pytest.raises(AssertionError):
        messages.add_message("bad", 999, "vault1")
