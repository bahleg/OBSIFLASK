import time
import pytest

from obsiflask.bases.cache import BaseCache
from obsiflask.app_state import AppState


class DummyVaultConfig:
    def __init__(self, cache_time):
        self.base_config = type("BC", (), {"cache_time": cache_time})


@pytest.fixture(autouse=True)
def clean_cache(monkeypatch):
    #  clean cache before each test
    BaseCache.cache.clear()
    AppState.config = type("Config", (), {"vaults": {}})
    yield
    BaseCache.cache.clear()


def test_add_and_get_from_cache(monkeypatch):
    AppState.config.vaults["v1"] = DummyVaultConfig(cache_time=60)

    BaseCache.add_to_cache("v1", "path1", "viewA", "result123")
    res, hit = BaseCache.get_from_cache("v1", "path1", "viewA")

    assert hit is True
    assert res == "result123"


def test_cache_miss(monkeypatch):
    AppState.config.vaults["v1"] = DummyVaultConfig(cache_time=60)

    res, hit = BaseCache.get_from_cache("v1", "pathX", "viewY")

    assert hit is False
    assert res is None


def test_prune_removes_expired(monkeypatch):
    # cache_time = 0.1 секунды
    AppState.config.vaults["v1"] = DummyVaultConfig(cache_time=0.1)

    BaseCache.add_to_cache("v1", "path1", "viewA", "res1")
    time.sleep(0.2)  

    BaseCache.prune()

    res, hit = BaseCache.get_from_cache("v1", "path1", "viewA")
    assert hit is False
    assert res is None


def test_prune_keeps_valid(monkeypatch):
    AppState.config.vaults["v1"] = DummyVaultConfig(cache_time=2)

    BaseCache.add_to_cache("v1", "path1", "viewA", "res1")
    time.sleep(0.1)

    BaseCache.prune()
    res, hit = BaseCache.get_from_cache("v1", "path1", "viewA")

    assert hit is True
    assert res == "res1"
