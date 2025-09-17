"""
A caching mechanism for bases. Will be removed in future

"""
from threading import Lock
import time

from obsiflask.app_state import AppState


class BaseCache:
    """
    This class represents global variables for caching base results
    """
    cache_lock = Lock()
    cache: dict[tuple[str, str, str], tuple[str, int]] = {}

    @staticmethod
    def prune():
        """
        Pruning old base results
        """
        with BaseCache.cache_lock:
            to_delete = set()
            for k, v in BaseCache.cache.items():
                vault = k[0]
                old_time = v[1]
                delta = time.time() - old_time
                if AppState.config.vaults[
                        vault].base_config.cache_time < delta:
                    to_delete.add(k)
            for k in to_delete:
                del BaseCache.cache[k]

    @staticmethod
    def add_to_cache(vault: str, base_path: str, view: str, result: str):
        """
        Adds base cache to base

        Args:
            vault (str): vault name
            base_path (str): path to base w.r.t. vault
            view (str): view name
            result (str): result to save
        """
        time_s = time.time()
        BaseCache.prune()
        BaseCache.cache[(vault, base_path, view)] = (result, time_s)

    @staticmethod
    def get_from_cache(vault: str, base_path: str,
                       view: str) -> tuple[str | None, bool]:
        """returns results from cache

        Args:
            vault (str): vault name
            base_path (str): path to base w.r.t. vault
            view (str): view name

        Returns:
            tuple[str | None, bool]: string or None for the first variable in return, 
            flag if it was in cache for the second argument
        """
        BaseCache.prune()
        res = BaseCache.cache.get((vault, base_path, view), (None, None))
        if res[1] is not None:
            return res[0], True
        return None, False
