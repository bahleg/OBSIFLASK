from zlib import crc32
from threading import Lock
from obsiflask.utils import logger

MAX_HINT = 10
"""
Note, this number is approximate. Can be slightly more
"""
_lock = Lock()


class NaiveStringIndex:

    def __init__(self, ngram_order: int, max_ngrams: int,
                 max_ratio_in_ngram: float):
        self.ngram_order = ngram_order
        assert ngram_order >= 2
        self.max_prop_in_dict = max_ratio_in_ngram
        assert max_ratio_in_ngram > 0
        self.max_ngrams = max_ngrams
        assert max_ngrams > 0
        self.current_state: int = -1
        self.ngrams_to_strings: dict[str, set[str]] = None

    def update_index(self, strings: set[str]):

        hash_ = crc32(''.join(sorted(strings)).encode('utf-8', 'ignore'))
        self.ngrams_to_strings = {}
        if hash_ == self.current_state:
            return
        blacklist = set()

        def prune():
            sorted_keys = sorted(
                self.ngrams_to_strings.keys(),
                key=lambda x: len(self.ngrams_to_strings[x]))[self.max_ngrams:]
            for k in sorted_keys:
                logger.debug(f'Pruning {k} from ngram index')
                del self.ngrams_to_strings[k]
                blacklist.add(k)

        for k in strings:
            for ngram_id in range(len(k) - self.ngram_order + 1):
                ngram = k[ngram_id:ngram_id + self.ngram_order]
                if ngram in blacklist:
                    continue

                if ngram not in self.ngrams_to_strings:
                    self.ngrams_to_strings[ngram] = set()
                self.ngrams_to_strings[ngram].add(k)
                if len(self.ngrams_to_strings[ngram]) / len(
                        strings) > self.max_prop_in_dict:
                    blacklist.add(ngram)
                    del self.ngrams_to_strings[ngram]
                    logger.debug(f'Pruning {ngram} from ngram index')
                if len(self.ngrams_to_strings) > 2 * self.max_ngrams:
                    prune()
        prune()
        self.current_state = hash_
        if len(blacklist) > 0:
            logger.info(
                f'Pruned {len(blacklist)} ngrams during index building')

    def search(self, q):
        q = q.strip()
        if len(q) < self.ngram_order:
            return []
        candidates = {}
        for ngram_id in range(len(q) - self.ngram_order + 1):
            ngram = q[ngram_id:ngram_id + self.ngram_order]
            for c in self.ngrams_to_strings.get(ngram, []):
                if c not in candidates:
                    candidates[c] = 0
                candidates[c] += 1
        if len(candidates) == 0:
            return []
        best_match = max(candidates.values())
        top_candidates = [(c, best_match, abs(len(q) - len(c)))
                          for c, v in candidates.items() if v == best_match]
        top_candidates = sorted(top_candidates, key=lambda x: x[2])
        return top_candidates


class HintIndex:

    def __init__(self, ngram_order, max_ngrams, ngram_max_ratio):
        self.default_files_per_user: dict[str | None, list[str]] = {}
        self.default_tags_per_user: dict[str | None, list[str]] = {}
        self.string_file_index = NaiveStringIndex(ngram_order, max_ngrams,
                                                    ngram_max_ratio)
        self.string_tag_index = NaiveStringIndex(ngram_order, max_ngrams,
                                                   ngram_max_ratio)

    def update_file(self, fname: str):
        with _lock:
            if fname in HintIndex.default_files_per_user[None]:
                HintIndex.default_files_per_user[None].remove(fname)
            HintIndex.default_files_per_user[None] = [
                fname
            ] + HintIndex.default_files_per_user[None]
            HintIndex.default_files_per_user[
                None] = HintIndex.default_files_per_user[None][:MAX_HINT]
