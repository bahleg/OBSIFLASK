import pytest

import obsiflask.messages as messages


class DummyVaultConfig:

    def __init__(self, size=5):
        self.message_list_size = size


class DummyConfig:

    def __init__(self):
        self.vaults = {"vault1": DummyVaultConfig(size=3)}


@pytest.fixture(autouse=True)
def setup_appstate(monkeypatch):
    messages.AppState.messages = {
        ('vault1', 'user1'): [],
        ('vault1', None): []
    }
    messages.AppState.config = DummyConfig()
    yield


def test_add_message_and_retrieve():
    messages.add_message("hello", 0, "vault1", user="user1", use_log=False)
    result = messages.get_messages("vault1", user="user1", consider_read=False)
    assert len(result) == 1
    assert result[0].message == "hello"
    assert result[0].type == 0
    assert result[0].vault == "vault1"
    assert result[0].user == "user1"


def test_get_messages_marks_as_read():
    messages.add_message("m1", 0, "vault1", user=None, use_log=False)
    result = messages.get_messages("vault1", user=None)
    assert all(m.is_read for m in result)


def test_get_messages_unread_filter():
    messages.add_message("m1", 0, "vault1", use_log=False)
    # First read
    _ = messages.get_messages("vault1")
    # Second read with unread=True — must return empty
    result = messages.get_messages("vault1", unread=True)
    assert result == []


def test_message_list_size_limit(monkeypatch):
    # message_list_size = 3 → max 3
    for i in range(10):
        messages.add_message(f"msg{i}", 0, "vault1", use_log=False)

    result = messages.get_messages("vault1", consider_read=False, unread=False)
    assert len(result) == 3  # limited
    # checking last time
    times = [m.time for m in result]
    assert times == sorted(times, reverse=True)


def test_invalid_type_raises():
    with pytest.raises(AssertionError):
        messages.add_message("bad", 999, "vault1")
