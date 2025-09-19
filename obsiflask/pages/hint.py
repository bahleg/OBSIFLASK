import re
from zlib import crc32
import datetime
from threading import Lock
from obsiflask.consts import DATE_FORMAT
from obsiflask.utils import logger

MAX_HINT = 10
"""
Note, this number is approximate. Can be slightly more
"""
MAX_HINT_LEN = 32

"""
TODO: 
    3. tags: []
    5. tests
"""
context_pattern = re.compile(r'("[^"]*$|[^\s]+)$')
hashtag_pattern = re.compile(r'#\w*$')
d_brackets_pattern = re.compile(r'\[\[[^\]]*$')


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
        return []  # no results is also a result
    found_span = len(found_text)
    return [{'text': r[0], 'erase': found_span} for r in results]


def hashtag_hint(vault: str, context: str):
    found = hashtag_pattern.search(context)
    if found is None:
        return None
    found_text = found.group()
    if len(found_text) == 1:  # only '#'
        return [{
            'text': '#' + r,
            'erase': 1
        } for r in HintIndex.default_tags_per_user[(vault, None)][:MAX_HINT]]

    tags_results = HintIndex.string_tag_indices_per_vault[vault].search(
        found_text[1:])
    found_text_len = len(found_text)
    if len(tags_results) == 0:
        return [{
            'text': '#' + r,
            'erase': found_text_len
        } for r in HintIndex.default_tags_per_user[(vault, None)][:MAX_HINT]]

    return [{
        'text': '#' + r[0],
        'erase': found_text_len
    } for r in tags_results]


def double_brackets_hint(vault: str, context: str):
    found = d_brackets_pattern.search(context)
    if found is None:
        return None
    found_text = found.group()
    default_files = [
        r for r in HintIndex.default_files_per_user[(vault,
                                                     None)][:MAX_HINT // 2]
    ]
    default_files_set = set(default_files)
    default_files_add = []
    for r in default_files:  # actually, the check should be
        short = r.split('/')[-1]
        if short not in default_files_set:
            default_files_add.append(short)
            default_files_set.add(short)
    default_files = default_files_add+default_files
    if len(found_text) == 2:  # only '[['
        return [{'text': r + ']]', 'erase': 0} for r in default_files]

    file_results = HintIndex.string_file_indices_per_vault[vault].search(
        found_text[2:])[:MAX_HINT]
    found_text_len = len(found_text)-2
    if len(file_results) == 0:
        return [{
            'text': r + ']]',
            'erase': found_text_len
        } for r in default_files]
    return [{'text': r[0]+']]', 'erase': found_text_len} for r in file_results]


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
    result = None
    for hinter in [hashtag_hint, double_brackets_hint, context_hint]:
        result = hinter(vault, context)
        if result is not None:
            break
    if result is None or len(result) == 0:
        result = simple_hint(vault)
    for r in result:
        r['short'] = make_short(r['text'])
    return result
