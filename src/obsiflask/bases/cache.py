from threading import Lock
from obsiflask.singleton import Singleton
import time


class BaseCache:
    cache_lock = Lock()
    cache: dict[tuple[str, str, str], tuple[str, int]] = {
    }  # (vault, base key, view name) -> (cache, time)

    @staticmethod
    def prune():
        with BaseCache.cache_lock:
            to_delete = set()
            for k, v in BaseCache.cache.items():
                vault = k[0]
                old_time = v[1]
                delta = time.time() - old_time
                if Singleton.config.vaults[
                        vault].base_config.cache_time < delta:
                    to_delete.add(k)
            for k in to_delete:
                del BaseCache.cache[k]

    @staticmethod
    def add_to_cache(vault, base_path, view, result):
        time_s = time.time()
        BaseCache.prune()
        BaseCache.cache[(vault, base_path, view)] = (result, time_s)

    @staticmethod
    def get_from_cache(vault, base_path, view):
        BaseCache.prune()
        res = BaseCache.cache.get((vault, base_path, view), [None, None])
        if res[1] is not None: 
            return res[0], True 
        return None, False
