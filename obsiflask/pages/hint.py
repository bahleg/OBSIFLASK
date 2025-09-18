import datetime
from collections import deque
from threading import Lock
from obsiflask.consts import DATE_FORMAT

MAX_HINT = 10
"""
Note, this number is approximate. Can be slightly more
"""
MAX_HINT_LEN = 32


class HintIndex:
    lock = Lock()
    default_files_per_user: dict[tuple[str, str | None], list[str]] = {}
    default_tags_per_user: dict[tuple[str, str | None], list[str]] = {}

    def update_file(vault: str, fname: str):
        with HintIndex.lock:
            if fname in HintIndex.default_files_per_user[(vault, None)]:
                HintIndex.default_files_per_user[(vault, None)].remove(fname)
            HintIndex.default_files_per_user[(
                vault,
                None)] = [fname] + HintIndex.default_files_per_user[(vault, None)]
            HintIndex.default_files_per_user[(
                vault, None)] = HintIndex.default_files_per_user[(vault,
                                                                None)][:MAX_HINT]


def make_short(s: str):
    if len(s) > MAX_HINT_LEN:
        s = s[:MAX_HINT_LEN // 2] + '...' + s[-MAX_HINT_LEN // 2:]
    return s


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
    result = simple_hint(vault)
    for r in result:
        r['short'] = make_short(r['text'])
    return result
