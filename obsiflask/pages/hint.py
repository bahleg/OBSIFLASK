import re
import datetime
from obsiflask.consts import DATE_FORMAT
from obsiflask.hint import MAX_HINT
from obsiflask.app_state import AppState

MAX_HINT_LEN = 32

context_pattern = re.compile(r'("[^"]*$|[^\s]+)$')
hashtag_pattern = re.compile(r'#\w*$')
d_brackets_pattern = re.compile(r'\[\[[^\]]*$')
taglist_pattern = re.compile(r'^\s*tags:\s+\[.*?(?:,|\[)?\s*([^\],]*)$')
taglist_start_pattern = re.compile(r'^\s*tags:\s*$')


def make_short(s: str):
    if len(s) > MAX_HINT_LEN:
        s = s[:MAX_HINT_LEN // 2] + '...' + s[-MAX_HINT_LEN // 2:]
    return s


def context_hint(vault: str, context: str):
    found = context_pattern.search(context)
    if found is None:
        return None
    found_text = found.group().lstrip('"')
    file_results = AppState.hints[vault].string_file_index.search(
        found_text)
    tags_results = AppState.hints[vault].string_tag_index.search(
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
        } for r in AppState.hints[vault].default_tags_per_user[(vault, None)][:MAX_HINT]]

    tags_results = AppState.hints[vault].string_tag_index.search(
        found_text[1:])
    found_text_len = len(found_text)
    if len(tags_results) == 0:
        return [{
            'text': '#' + r,
            'erase': found_text_len
        } for r in AppState.hints[vault].default_tags_per_user[(vault, None)][:MAX_HINT]]

    return [{
        'text': '#' + r[0],
        'erase': found_text_len
    } for r in tags_results]


def taglist_hint(vault: str, context: str):
    found = taglist_pattern.search(context)
    brackets_wrap = lambda x: x
    if found is None:
        found2 = taglist_start_pattern.search(context)
        if found2 is None:
            return None
        else:
            found_text = ''
            brackets_wrap = lambda x: f' [{x}]'
    else:
        found_text = found.group(1).strip()
    if len(found_text) == 0:  # new list element
        return [{
            'text': brackets_wrap(r),
            'erase': 0
        } for r in AppState.hints[vault].default_tags_per_user[(vault, None)][:MAX_HINT]]

    tags_results = AppState.hints[vault].string_tag_index.search(
        found_text.strip("'"))
    found_text_len = len(found_text)
    if len(tags_results) == 0:
        return [{
            'text': brackets_wrap(r),
            'erase': found_text_len
        } for r in AppState.hints[vault].default_tags_per_user[(vault, None)][:MAX_HINT]]

    return [{
        'text': brackets_wrap(r[0]),
        'erase': found_text_len
    } for r in tags_results]


def double_brackets_hint(vault: str, context: str):
    found = d_brackets_pattern.search(context)
    if found is None:
        return None
    found_text = found.group()
    default_files = [
        r for r in AppState.hints[vault].default_files_per_user[(vault,
                                                     None)][:MAX_HINT // 2]
    ]
    default_files_set = set(default_files)
    default_files_add = []
    for r in default_files:  # actually, the check should be
        short = r.split('/')[-1]
        if short not in default_files_set:
            default_files_add.append(short)
            default_files_set.add(short)
    default_files = default_files_add + default_files
    if len(found_text) == 2:  # only '[['
        return [{'text': r + ']]', 'erase': 0} for r in default_files]

    file_results = AppState.hints[vault].string_file_index.search(
        found_text[2:])[:MAX_HINT]
    found_text_len = len(found_text) - 2
    if len(file_results) == 0:
        return [{
            'text': r + ']]',
            'erase': found_text_len
        } for r in default_files]
    return [{
        'text': r[0] + ']]',
        'erase': found_text_len
    } for r in file_results]


def simple_hint(vault: str):
    date = datetime.datetime.now().strftime(DATE_FORMAT)
    result = [{'text': date, 'erase': 0}]
    for t in AppState.hints[vault].default_tags_per_user[(vault, None)][:MAX_HINT // 3]:
        result.append({'text': '#' + t, 'erase': 0})
    files_added = set()
    for f in AppState.hints[vault].default_files_per_user[(vault, None)][:MAX_HINT // 3]:
        short = f.split('/')[-1]
        if short not in files_added:
            files_added.add(short)
            result.append({'text': short, 'erase': 0})
    for f in AppState.hints[vault].default_files_per_user[(vault, None)][:MAX_HINT // 3]:
        if f not in files_added:
            result.append({'text': f, 'erase': 0})
    return result


def get_hint(vault: str, context: str):
    result = None
    for hinter in [
            hashtag_hint, double_brackets_hint, taglist_hint, context_hint
    ]:
        result = hinter(vault, context)
        if result is not None:
            break
    if result is None or len(result) == 0:
        result = simple_hint(vault)
    for r in result:
        r['short'] = make_short(r['text'])
    return result
