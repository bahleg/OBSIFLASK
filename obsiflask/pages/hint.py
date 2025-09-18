import re
from zlib import crc32
import datetime
from threading import Lock
from obsiflask.consts import DATE_FORMAT

MAX_HINT = 10
"""
Note, this number is approximate. Can be slightly more
"""
MAX_HINT_LEN = 32

NGRAM_SIZE = 4
"""
TODO: 
    0. Return tabs
    1. Pruning
    2. "#" 
    3. tags: []
    4. [[]]
    5. tests
"""
context_pattern = re.compile(r'("[^"]*$|[^\s]+)$')


class NaiveStringIndex:

    def __init__(self):

        self.current_state: int = -1
        self.ngrams_to_strings: dict[str, set[str]] = None

    def update_index(self, strings: set[str]):
        hash_ = crc32(''.join(sorted(strings)).encode('utf-8', 'ignore'))
        self.ngrams_to_strings = {}
        if hash_ == self.current_state:
            return
        for k in strings:
            for ngram_id in range(len(k) - NGRAM_SIZE + 1):
                ngram = k[ngram_id:ngram_id + NGRAM_SIZE]
                if ngram not in self.ngrams_to_strings:
                    self.ngrams_to_strings[ngram] = set()
                self.ngrams_to_strings[ngram].add(k)
        self.current_state = hash_

    def search(self, q):
        q = q.strip()
        if len(q) < NGRAM_SIZE:
            return []
        candidates = {}
        for ngram_id in range(len(q) - NGRAM_SIZE + 1):
            ngram = q[ngram_id:ngram_id + NGRAM_SIZE]
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
    lock = Lock()
    default_files_per_user: dict[tuple[str, str | None], list[str]] = {}
    default_tags_per_user: dict[tuple[str, str | None], list[str]] = {}
    string_file_indices_per_vault: dict[str, NaiveStringIndex] = {}
    string_tag_indices_per_vault: dict[str, NaiveStringIndex] = {}

    def update_file(vault: str, fname: str):
        with HintIndex.lock:
            if fname in HintIndex.default_files_per_user[(vault, None)]:
                HintIndex.default_files_per_user[(vault, None)].remove(fname)
            HintIndex.default_files_per_user[(
                vault,
                None)] = [fname
                          ] + HintIndex.default_files_per_user[(vault, None)]
            HintIndex.default_files_per_user[(
                vault,
                None)] = HintIndex.default_files_per_user[(vault,
                                                           None)][:MAX_HINT]


def make_short(s: str):
    if len(s) > MAX_HINT_LEN:
        s = s[:MAX_HINT_LEN // 2] + '...' + s[-MAX_HINT_LEN // 2:]
    return s


def context_hint(vault: str, context: str):
    found = context_pattern.search(context)
    if found is None:
        return None
    found_text = found.group().lstrip('"')
    file_results = HintIndex.string_file_indices_per_vault[vault].search(
        found_text)
    tags_results = HintIndex.string_tag_indices_per_vault[vault].search(
        found_text)
    tags_results = [('#' + r[0], r[1], r[2]) for r in tags_results]
    results = sorted(file_results + tags_results, key=lambda x:
                     (-x[1], x[2]))[:MAX_HINT]
    if len(results) == 0:
        return None
    found_span = len(found_text)
    return [{'text': r[0], 'erase': found_span} for r in results]


def simple_hint(vault: str):
    date = datetime.datetime.now().strftime(DATE_FORMAT)
    result = [{'text': date, 'erase': 0}]
    for t in HintIndex.default_tags_per_user[(vault, None)][:MAX_HINT // 3]:
        result.append({'text': '#' + t, 'erase': 0})
    files_added = set()
    for f in HintIndex.default_files_per_user[(vault, None)][:MAX_HINT // 3]:
        short = f.split('/')[-1]
        if short not in files_added:
            files_added.add(short)
            result.append({'text': short, 'erase': 0})
    for f in HintIndex.default_files_per_user[(vault, None)][:MAX_HINT // 3]:
        if f not in files_added:
            result.append({'text': f, 'erase': 0})
    return result


def get_hint(vault: str, context: str):

    result = context_hint(vault, context)
    if result is None:
        result = simple_hint(vault)
    for r in result:
        r['short'] = make_short(r['text'])
    return result
