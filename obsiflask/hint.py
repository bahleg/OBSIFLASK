"""
Basic logic for autocomplete task.
Gathers info about recently openned files (and all files as well),
popular tags.

Also there is an implementation of fuzzy search index
"""
from zlib import crc32
from threading import Lock
from collections import deque

from obsiflask.utils import logger

MAX_HINT = 10
"""
Note, this number is approximate. Can be slightly more
"""
_lock = Lock()


class NaiveStringIndex:
    """
    Fuzzy index based on ngrams
    """

    def __init__(self, ngram_order: int, max_ngrams: int,
                 max_ratio_in_ngram: float):
        """
        Constructor

        Args:
            ngram_order (int): ngram order to use
            max_ngrams (int): if number of ngrams is larger, will prune index
            max_ratio_in_ngram (float): removes too frequent ngrams, if they're 
            shared across max_ratio_in_ngram*100% of all the string in the index
        """
        self.ngram_order = ngram_order
        assert ngram_order >= 2
        self.max_prop_in_dict = max_ratio_in_ngram
        assert max_ratio_in_ngram > 0
        self.max_ngrams = max_ngrams
        assert max_ngrams > 0
        self.current_state: int = -1
        self.ngrams_to_strings: dict[str, set[str]] = None

    def update_index(self, strings: set[str]):
        """
        Rebuils index with new strings.
        If nothing was changed, does nothing
        Args:
            strings (set[str]): new strings to rebuild index
        """
        hash_ = crc32(''.join(sorted(strings)).encode('utf-8', 'ignore'))
        if hash_ == self.current_state:
            return
        self.ngrams_to_strings = {}
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

    def search(self, q: str) -> tuple[list[tuple[str, str]], float]:
        """
        Search in the index.
        Returns only the results with the best match, 
        sorted by the difference between the length of the query string and
        the matches string

        Args:
            q (str): string to find

        Returns:
            tuple[list[tuple[str, str]], float]: tuple with two elements:
                the first is a list of found matches, for each there is also provided a difference
                of length between the query string and the collection string
                the second is the ratio of ngrams that were found in the string
        """
        q = q.strip()
        if len(q) < self.ngram_order:
            return [], 0
        candidates = {}
        for ngram_id in range(len(q) - self.ngram_order + 1):
            ngram = q[ngram_id:ngram_id + self.ngram_order]
            for c in self.ngrams_to_strings.get(ngram, []):
                if c not in candidates:
                    candidates[c] = 0
                candidates[c] += 1
        if len(candidates) == 0:
            return [], 0
        best_match = max(candidates.values())
        top_candidates = [(c, abs(len(q) - len(c)))
                          for c, v in candidates.items() if v == best_match]
        top_candidates = sorted(top_candidates, key=lambda x: x[1])[:MAX_HINT]
        return top_candidates, best_match


class HintIndex:
    """
    Hint index for the target vault
    """

    def __init__(self, ngram_order: int, max_ngrams: int,
                 max_ratio_in_ngram: float):
        """index constructor

        Args:
            ngram_order (int): ngram order to use
            max_ngrams (int): if number of ngrams is larger, will prune index
            max_ratio_in_ngram (float): removes too frequent ngrams, if they're 
            shared across max_ratio_in_ngram*100% of all the string in the index
        """
        self.default_files_per_user: dict[str | None, deque[str]] = {}
        # most recent files that are shown to user
        # initially populated by popular files, see graph.py

        self.default_tags: list[str] = []
        # most popular tags for user

        # indicies for autocomplete
        self.string_file_index = NaiveStringIndex(ngram_order, max_ngrams,
                                                  max_ratio_in_ngram)

        self.string_all_file_index = NaiveStringIndex(ngram_order, max_ngrams,
                                                      max_ratio_in_ngram)

        self.string_tag_index = NaiveStringIndex(ngram_order, max_ngrams,
                                                 max_ratio_in_ngram)

    def populate_default_files(self, user: str | None, files: list[str]):
        """
        Initializes the list of default_files_per_user

        Args:
            user (str | None): user 
            files (list[str]): list of files
        """
        with _lock:
            self.default_files_per_user[user] = deque(files, MAX_HINT)

    def update_file(self, fname: str, user: str | None = None):
        """
        Updates a file in the default_files_per_user

        Args:
            fname (str): file name to add
        """
        with _lock:
            if fname in set(self.default_files_per_user[None]):
                self.default_files_per_user[None].remove(fname)
            self.default_files_per_user[None].appendleft(fname)
            if user is not None:
                if fname in set(self.default_files_per_user[user]):
                    self.default_files_per_user[user].remove(fname)
                self.default_files_per_user[user].appendleft(fname)
