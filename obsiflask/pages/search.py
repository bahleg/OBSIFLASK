"""
Module contains search logic
"""
import os
import re
from typing import Generator

from markupsafe import escape
import nltk
from flask import render_template, request, stream_template

from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
from obsiflask.utils import logger
from obsiflask.graph import Graph
from obsiflask.messages import add_message, type_to_int
from obsiflask.bases.filter import FieldFilter
from obsiflask.consts import MAX_FILE_SIZE_MARKDOWN

SEARCH_PREVIEW_CHARS = 100
"""
This amount of chars will be shown as a context
"""
re_non_words = re.compile('\W+')
"""
non-alphabetical symbols for "ignore non-words" flag
"""


def generate_formula_check_results(
    formula: str,
    vault: str,
) -> Generator[tuple[str, str], None, None]:
    """
    Returns a generator of results after the formula check

    Args:
        formula (str): formula expression, compatible with Bases formulae
        vault (str): vault name

    Yields:
        [tuple[str, str], None, None]: a generator of results: filename and empty string (no context)
    """
    try:
        filter = FieldFilter(formula)
        graph: Graph = AppState.graphs[vault]
        graph_results = graph.build(True)
        for file in graph_results.files:
            if filter.check(file):
                yield str(file.vault_path), ""
    except Exception as e:
        add_message('Error during tag search',
                    type_to_int['error'],
                    vault,
                    details=repr(e))


def generate_tags_check_results(
    tag: str,
    vault: str,
) -> Generator[tuple[str, str], None, None]:
    """
    Returns a generator of results after the search by tag

    Args:
        tag (str): tag to search
        vault (str): vault name

    Yields:
        Generator[tuple[str, str], None, None]: a generator of results: filename and empty string (no context)
    """
    try:
        query = tag.lstrip('#').strip()
        graph: Graph = AppState.graphs[vault]
        graph_results = graph.build(True)
        tag_id = None
        for i in graph_results.tags:
            if graph_results.node_labels[i].lstrip('#').strip() == query:
                tag_id = i
                break
        if tag_id is not None:
            for edge in graph_results.edges:
                if edge[1] == tag_id:
                    yield str(graph_results.files[edge[0]].vault_path), ""
    except Exception as e:
        add_message('Error during tag search',
                    type_to_int['error'],
                    vault,
                    details=repr(e))


def generate_links_check_results(
        query: str,
        vault: str,
        forward: bool = True,
        local: bool = True) -> Generator[tuple[str, str], None, None]:
    """Returns a generator of results after the search by link (mention)

    Args:
        query (str): link to search
        vault (str): vault name
        forward (bool, optional): backward of forward. Defaults to True.
        local (bool, optional): if local, will also look for local (not absolute) mentions. Defaults to True.

    Yields:
        Generator[tuple[str, str], None, None]: a generator of results: filename and empty string (no context)
    """

    ids_to_search = set()
    query = query.lstrip('./')
    try:
        graph: Graph = AppState.graphs[vault]
        graph_results = graph.build(True)
        for f_id, f in enumerate(graph_results.files):
            for path_version in [query, query + '.md']:
                if str(f.path).lstrip('./') == path_version:
                    ids_to_search.add(f_id)
                if local:
                    if str(f.vault_path.name).lstrip('./') == path_version:
                        ids_to_search.add(f_id)
        for edge in graph_results.edges:
            if forward:
                vertex, vertex2 = edge
            else:
                vertex2, vertex = edge
            if vertex in ids_to_search:
                if (vertex2) < len(graph_results.files):
                    # ignore tags
                    yield str(graph_results.files[vertex2].path), ""
    except Exception as e:
        add_message('Error during link search',
                    type_to_int['error'],
                    vault,
                    details=repr(e))


def generate_text_check_results(
    query: str,
    vault: str,
    mode: str,
    ignore_case: bool = False,
    ignore_non_words: bool = False,
    only_md: bool = True,
    fuzzy_window_coef: float = 2.0,
    inclusion_percent: float = 0.75,
) -> Generator[tuple[str, str], None, None]:
    """
    Returns a generator of results after the text search

    Args:
        query (str): line of text to search
        vault (str): vault name
        mode (str): one of ['exact', 'regex', 'fuzzy']
        ignore_case (bool, optional): flag to ignore case. Defaults to False.
        ignore_non_words (bool, optional): flag to ignore non-word symbols. Defaults to False.
        only_md (bool, optional): if set, will ignore non-markdown files. Defaults to True.
        fuzzy_window_coef (float, optional): multiplcative coefficient of the length of the query to get 
        a window in a fuzzy search. If the query is of 3 words, and the multiplier is 2, then we get a window of 6. 
            Defaults to 2.0.
        inclusion_percent (float, optional): percentage of words in a window to match during fuzzy search. 
            Defaults to 0.75.

    Yields:
        Generator[tuple[str, str], None, None]: a generator of results: filename and a context string 
    """
    assert mode in [
        'exact',
        'regex',
        'fuzzy',
    ]

    graph: Graph = AppState.graphs[vault]

    try:
        if ignore_case:
            query = query.lower()
            if ignore_non_words:
                query = re_non_words.sub(' ', query)

        if mode == 'regex':
            query_re = re.compile(query)

        graph_results = graph.build(True)
        for file in graph_results.files:
            if only_md and file.vault_path.suffix != '.md':
                continue
            if os.path.getsize(file.real_path) > MAX_FILE_SIZE_MARKDOWN:
                logger.warning(
                    f'skipping {file.vault_path} due to size limit {MAX_FILE_SIZE_MARKDOWN/1024/1024} MB'
                )
            with open(file.real_path) as inp:
                text = inp.read()
                if ignore_case:
                    text = text.lower()
                if ignore_non_words:
                    text = re_non_words.sub(' ', text)
                if mode == 'regex':
                    res = compare_regex(query_re, text)
                if mode == 'exact':
                    res = compare_exact(query, text)
                if mode == 'fuzzy':
                    res = compare_fuzzy(query, text, fuzzy_window_coef,
                                        inclusion_percent)
                if res:
                    yield str(file.vault_path), res

    except Exception as e:
        add_message('Error during text search',
                    type_to_int['error'],
                    vault,
                    details=repr(e))


def compare_fuzzy(query: str, text: str, fuzzy_window_coef: float,
                  inclusion_percent: float) -> str | None:
    """
    Fuzzy comparison function.
    Takes the window of size len(query) (in words) * fuzzy_window_coef.
    Returns result if in this window we can find (inclusion_percent * 100) % of query tokens

    Args:
        query (str):  query string
        text (str): text
        fuzzy_window_coef (float): window size coefficient
        inclusion_percent (float): percentage of tokens to detect match

    Returns:
        str | None: matched context  or None if not found
    """
    tokenizer = nltk.tokenize.WordPunctTokenizer()
    query = set(tokenizer.tokenize(query))
    text_tokenization = list(tokenizer.span_tokenize(text))
    window_size = max(1, int(fuzzy_window_coef * len(query)))
    for i in range(len(text_tokenization)):
        window = text_tokenization[i:i + window_size]
        text_tokens = set([text[w[0]:w[1]] for w in window])
        if (len(text_tokens & query)) / (max(1,
                                             len(query))) >= inclusion_percent:
            min_pos = max(0, window[0][0] - SEARCH_PREVIEW_CHARS)
            max_pos = window[-1][1] + SEARCH_PREVIEW_CHARS
            before = escape(text[min_pos:window[0][0]])
            match = text[window[0][0]:window[-1][1]]
            after = escape(text[window[-1][1]:max_pos])
            return f'{before}<strong>{match}</strong>{after}'


def compare_exact(query: str, text: str) -> str | None:
    """Exact comparison function.

    Args:
        query (str):  query string
        text (str): text

    Returns:
        str | None: matched context  or None if not found
    """
    if query not in text:
        return None
    index = text.index(query)
    min_pos = max(0, index - SEARCH_PREVIEW_CHARS)
    max_pos = index + len(query) + SEARCH_PREVIEW_CHARS
    return f'{escape(text[min_pos:index])}<strong>{escape(query)}</strong>{escape(text[index+len(query):max_pos])}'


def compare_regex(query_re: re.Pattern, text: str) -> str | None:
    """Rege comparison function.

    Args:
        query_re (re.Pattern):  regex from query string
        text (str): text

    Returns:
        str | None: matched context or None if not found
    """
    found = query_re.search(text)
    if found:
        span = found.span()
        min_pos = max(0, span[0] - SEARCH_PREVIEW_CHARS)
        max_pos = span[1] + SEARCH_PREVIEW_CHARS
        before = escape(text[min_pos:span[0]])
        match = escape(text[span[0]:span[1]])
        after = escape(text[span[1]:max_pos])
        return f'{before}<strong>{match}</strong>{after}'
    return None


def render_search(vault: str) -> str | Generator[str, None, None]:
    """
    Performs rendering for search procedure

    Args:
        vault (str): vault name

    Returns:
        str | Generator[str, None, None]: rendered template or generator of templates for results
    """
    query = request.args.get("q")
    mode = request.args.get('mode') or 'exact'
    if mode not in [
            'exact', 'regex', 'tags', 'fuzzy', 'forward', 'backward', 'formula'
    ]:
        add_message(f'could not parse mode: {mode}', type_to_int['error'],
                    vault)
        mode = 'exact'
    if request.args.get('ignore_case'):
        ignore_case = True
    else:
        ignore_case = False

    if request.args.get('ignore_non_words'):
        ignore_non_words = True
    else:
        ignore_non_words = False

    if request.args.get('fuzzy_window'):
        fuzzy_window = float(request.args.get('fuzzy_window'))
    else:
        fuzzy_window = 2.0

    if request.args.get('fuzzy_ratio'):
        fuzzy_ratio = float(request.args.get('fuzzy_ratio'))
    else:
        fuzzy_ratio = 0.75

    if request.args.get('local_link'):
        local_link = True
    else:
        local_link = False

    render_func = render_template
    results = []
    if query:
        render_func = stream_template
        if mode == 'tags':
            results = generate_tags_check_results(query, vault)
        elif mode in ['forward', 'backward']:
            results = generate_links_check_results(query,
                                                   vault,
                                                   mode == 'forward',
                                                   local=local_link)
        elif mode == 'formula':
            results = generate_formula_check_results(query, vault)
        else:
            results = generate_text_check_results(
                query,
                vault,
                mode=mode,
                fuzzy_window_coef=fuzzy_window,
                inclusion_percent=fuzzy_ratio,
                ignore_case=ignore_case,
                ignore_non_words=ignore_non_words)

    return render_func('search.html',
                       vault=vault,
                       navtree=render_tree(AppState.indices[vault], vault,
                                           True),
                       page_editor=False,
                       home=AppState.config.vaults[vault].home_file,
                       results=results,
                       query=query,
                       ignore_case=ignore_case,
                       ignore_non_words=ignore_non_words,
                       mode=mode,
                       local_link=local_link,
                       fuzzy_window=fuzzy_window,
                       fuzzy_ratio=fuzzy_ratio)
