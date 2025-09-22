"""
Autocomplete logic
"""
import re
import datetime
from obsiflask.consts import DATE_FORMAT
from obsiflask.hint import MAX_HINT
from obsiflask.app_state import AppState
from obsiflask.auth import get_user

MAX_HINT_LEN = 32
"""
If the hint is larger, will trim it
"""

context_pattern = re.compile(r'("[^"]*$|[^\s]+)$')
"""
Pattern like SomeUnfinishedWo
or "Some part of phrase in bracket
"""
hashtag_pattern = re.compile(r'#\w*$')
"""
Pattern #hashtag, or just "#"
"""
d_brackets_pattern = re.compile(r'\[\[[^\]]*$')
"""
Pattern [[some unfinished link
"""
taglist_pattern = re.compile(r'^\s*tags:\s+\[.*?(?:,|\[)?\s*([^\],]*)$')
"""
Pattern like "tags: [element1, element "
"""
taglist_start_pattern = re.compile(r'^\s*tags:\s*$')
"""
Pattern like "tags: 
"""


def make_short(s: str) -> str:
    """
    Helper to reduce the length of the hint to show to user

    Args:
        s (str): string to reduce

    Returns:
        str: processed string
    """
    if len(s) > MAX_HINT_LEN:
        s = s[:MAX_HINT_LEN // 2] + '...' + s[-MAX_HINT_LEN // 2:]
    return s


def context_hint(vault: str, context: str) -> list[dict]:
    """
    Tries to show the user most probable hints depending on the context

    Args:
        vault (str): vault name
        context (str): context of the hint

    Returns:
        list[dict]: resulting hints
    """
    found = context_pattern.search(context)
    if found is None:
        return None
    found_text = found.group().lstrip('"')
    file_results, file_best_match_score = AppState.hints[
        vault].string_file_index.search(found_text)
    file_results = [(f[0], file_best_match_score, f) for f in file_results]
    tags_results, tag_best_match_score = AppState.hints[
        vault].string_tag_index.search(found_text)
    tags_results = [('#' + r[0], tag_best_match_score, r[1])
                    for r in tags_results]
    results = sorted(file_results + tags_results, key=lambda x:
                     (-x[1], x[2]))[:MAX_HINT]
    found_span = len(found_text)
    
    if len(results) == 0:
        return simple_hint(vault, found_span)
    return [{'text': r[0], 'erase': found_span} for r in results]


def hashtag_hint(vault: str, context: str) -> list[dict]:
    """
    Tries to show the user most probable hints depending on the hashtag enetered

    Args:
        vault (str): vault name
        context (str): context of the hint

    Returns:
        list[dict]: resulting hints
    """
    found = hashtag_pattern.search(context)
    if found is None:
        return None
    found_text = found.group()
    if len(found_text) == 1:  # only '#'
        return [{
            'text': '#' + r,
            'erase': 1
        } for r in AppState.hints[vault].default_tags[:MAX_HINT]]

    tags_results, _ = AppState.hints[vault].string_tag_index.search(
        found_text[1:])
    found_text_len = len(found_text)
    if len(tags_results) == 0:
        return [{
            'text': '#' + r,
            'erase': found_text_len
        } for r in AppState.hints[vault].default_tags[:MAX_HINT]]

    return [{
        'text': '#' + r[0],
        'erase': found_text_len
    } for r in tags_results]


def taglist_hint(vault: str, context: str) -> list[dict]:
    """
    Tries to show the user most probable hints depending on the taglist enetered

    Args:
        vault (str): vault name
        context (str): context of the hint

    Returns:
        list[dict]: resulting hints
    """
    found = taglist_pattern.search(context)
    brackets_wrap = lambda x: x
    if found is None:
        # case when the user only entered "tags: ", without list of tags
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
        } for r in AppState.hints[vault].default_tags[:MAX_HINT]]

    tags_results, _ = AppState.hints[vault].string_tag_index.search(
        found_text.strip("'"))
    found_text_len = len(found_text)
    if len(tags_results) == 0:
        return [{
            'text': brackets_wrap(r),
            'erase': found_text_len
        } for r in AppState.hints[vault].default_tags[:MAX_HINT]]

    return [{
        'text': brackets_wrap(r[0]),
        'erase': found_text_len
    } for r in tags_results]


def double_brackets_hint(vault: str, context: str) -> list[dict]:
    """
    Tries to show the user most probable hints for the wikilink autocomplete 

    Args:
        vault (str): vault name
        context (str): context of the hint

    Returns:
        list[dict]: resulting hints
    """
    found = d_brackets_pattern.search(context)
    if found is None:
        return None
    found_text = found.group()
    default_files = [
        r for r in list(AppState.hints[vault].default_files_per_user[get_user()])
        [:MAX_HINT // 2]
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

    file_results, _ = AppState.hints[vault].string_file_index.search(
        found_text[2:])
    file_results = file_results[:MAX_HINT]
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


def simple_hint(vault: str, erase_num: int = 0) -> list[dict]:
    """
    Tries to show default hints for the user 

    Args:
        vault (str): vault name
        erase_num (int): number of characters of the context to erase
        
    Returns:
        list[dict]: resulting hints
    """
    date = datetime.datetime.now().strftime(DATE_FORMAT)
    result = [{'text': date, 'erase': erase_num}]
    for t in AppState.hints[vault].default_tags[:MAX_HINT // 3]:
        result.append({'text': '#' + t, 'erase': erase_num})
    files_added = set()
    for f in list(
            AppState.hints[vault].default_files_per_user[get_user()])[:MAX_HINT //
                                                                3]:
        short = f.split('/')[-1]
        if short not in files_added:
            files_added.add(short)
            result.append({'text': short, 'erase': erase_num})
    for f in list(
            AppState.hints[vault].default_files_per_user[get_user()])[:MAX_HINT //
                                                                3]:
        if f not in files_added:
            result.append({'text': f, 'erase': erase_num})
    return result


def get_hint(vault: str, context: str) -> list[dict[str]]:
    """
    Main logic of autocomplete results providing

    Args:
        vault (str): vault name
        context (str): context of autocomplete

    Returns:
        list[dict[str]]: list of dictionaries,
        where each dictionary has the following keys:
            - "text": text to add
            - "erase": number of chars to remove from the context
            - "short": short alias for the hint to show to user
    """
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
