from markupsafe import escape
import os
import numpy as np
from urllib import parse
import json
import nltk
from copy import copy
from dataclasses import asdict, dataclass
from pathlib import Path
from cmap import Colormap
from flask import render_template, redirect, url_for, request, stream_template
from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
from obsiflask.utils import logger
from obsiflask.graph import Graph, GraphRepr
import networkx as nx
from networkx.algorithms.community import louvain_communities
from obsiflask.messages import add_message
import re
from obsiflask.bases.filter import FieldFilter
from obsiflask.graph import Graph, GraphRepr
from obsiflask.consts import MAX_FILE_SIZE_MARKDOWN

SEARCH_PREVIEW_CHARS = 100
punct = re.compile('\W+')

def generate_formula(
    query: str,
    vault: str,
):
    try:
        filter = FieldFilter(query)
        graph: Graph = AppState.graphs[vault]
        graph_results = graph.build(True)
        for file in graph_results.files:
            if filter.check(file):
                yield str(file.path), ""
    except Exception as e:
        add_message('Error during tag search', 2, vault, details=repr(e))



def generate_tags(
    query: str,
    vault: str,
):
    try:
        query = query.lstrip('#').strip()
        graph: Graph = AppState.graphs[vault]
        graph_results = graph.build(True)
        tag_id = None
        for i in graph_results.tags:
            if graph_results.node_labels[i].lstrip('#').strip() == query:
                tag_id = i
                break
        if tag_id:
            for edge in graph_results.edges:
                if edge[1] == tag_id:
                    yield str(graph_results.files[edge[0]].path), ""
    except Exception as e:
        add_message('Error during tag search', 2, vault, details=repr(e))


def compare_fuzzy(query: str, text: str, fuzzy_window_coef: float,
                  inclusion_percent: float):
    tokenizer = nltk.tokenize.WordPunctTokenizer()
    query = set(tokenizer.tokenize(query))
    text_tokenization = list(tokenizer.span_tokenize(text))
    window_size = max(1, int(fuzzy_window_coef * len(query)))
    for i in range(len(text_tokenization)):
        window = text_tokenization[i:i + window_size]
        text_tokens = set([text[w[0]:w[1]] for w in window])
        if (len(text_tokens & query)) / (max(1,
                                             len(query))) > inclusion_percent:
            min_pos = max(0, window[0][0] - SEARCH_PREVIEW_CHARS)
            max_pos = window[-1][1] + SEARCH_PREVIEW_CHARS
            return f'{escape(text[min_pos:window[0][0]])}<strong>{text[window[0][0]:window[-1][1]]}</strong>{escape(text[window[-1][1]:max_pos])}'


def compare_exact(query: str, text: str):
    if query not in text:
        return None
    index = text.index(query)
    min_pos = max(0, index - SEARCH_PREVIEW_CHARS)
    max_pos = index + len(query) + SEARCH_PREVIEW_CHARS
    return f'{escape(text[min_pos:index])}<strong>{escape(query)}</strong>{escape(text[index+len(query):max_pos])}'


def compare_regex(query_re: re.Pattern, text: str):
    found = query_re.search(text)
    if found:
        span = found.span()
        min_pos = max(0, span[0] - SEARCH_PREVIEW_CHARS)
        max_pos = span[1] + SEARCH_PREVIEW_CHARS
        return f'{escape(text[min_pos:span[0]])}<strong>{escape(text[span[0]:span[1]])}</strong>{escape(text[span[1]:max_pos])}'
    return None


def generate_links(query, vault: str, forward: bool = True, local: bool = True):
    ids_to_search = set()
    query = query.lstrip('./')
    try:
        graph: Graph = AppState.graphs[vault]
        graph_results = graph.build(True)
        for f_id, f in enumerate(graph_results.files):
            for path_version in [query, query+'.md']:
                if str(f.path).lstrip('./') == path_version:
                    ids_to_search.add(f_id)
                if local:
                    if str(f.path.name).lstrip('./') == path_version:
                        ids_to_search.add(f_id)
        for edge in graph_results.edges:
            if forward:
                vertex, vertex2 = edge
            else:
                vertex, vertex2 = edge
            if vertex in ids_to_search:
                    if (vertex2) < len(graph_results.files):
                        # ignore tags
                        yield str(graph_results.files[vertex2].path), ""
    except Exception as e:
        add_message('Error during link search', 2, vault, details=repr(e))

def generate_text(
    query: str,
    vault,
    mode,
    ignore_case=False,
    ignore_punctuation=False,
    only_md: bool = True,
    fuzzy_window_coef: float = 2.0,
    inclusion_percent: float = 0.75,
):
    assert mode in ['exact', 'regex', 'fuzzy',]

    graph: Graph = AppState.graphs[vault]

    try:
        if ignore_case:
            query = query.lower()
            if ignore_punctuation:
                query = punct.sub(' ', query)
        if mode == 'regex':
            query_re = re.compile(query)

        graph_results = graph.build(True)
        for file in graph_results.files:
            if only_md and file.path.suffix != '.md':
                continue
            if os.path.getsize(file.real_path) > MAX_FILE_SIZE_MARKDOWN:
                logger.warning(
                    f'skipping {file.path} due to size limit {MAX_FILE_SIZE_MARKDOWN/1024/1024} MB'
                )
            with open(file.real_path) as inp:
                text = inp.read()
                if ignore_case:
                    text = text.lower()
                if ignore_punctuation:
                    text = punct.sub(' ', text)
                if mode == 'regex':
                    res = compare_regex(query_re, text)
                if mode == 'exact':
                    res = compare_exact(query, text)
                if mode == 'fuzzy':
                    res = compare_fuzzy(query, text, fuzzy_window_coef,
                                        inclusion_percent)
                if res:
                    yield str(file.path), res

    except Exception as e:
        add_message('Error during text search', 2, vault, details=repr(e))


def render_search(vault):
    query = request.args.get("q")
    mode = request.args.get('mode') or 'exact'
    if mode not in ['exact', 'regex', 'tags', 'fuzzy', 'forward', 'backward', 'formula']:
        add_message(f'could not parse mode: {mode}', 2, vault)
        mode = 'exact'
    if request.args.get('ignore_case'):
        ignore_case = True
    else:
        ignore_case = False 

    
    if request.args.get('ignore_punct'):
        ignore_punct = True
    else:
        ignore_punct = False 

    
    if request.args.get('fuzzy_window'):
        fuzzy_window =  float(request.args.get('fuzzy_window'))
    else:
        fuzzy_window = 2.0

    if request.args.get('fuzzy_ratio'):
        fuzzy_ratio =  float(request.args.get('fuzzy_ratio'))
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
            results = generate_tags(query, vault)
        elif mode in ['forward', 'backward']:
            results = generate_links(query, vault, mode=='forward', local=local_link)
        elif mode == 'formula':
            results = generate_formula(query, vault)
        else:
            results = generate_text(query, vault, mode=mode, fuzzy_window_coef=fuzzy_window, inclusion_percent=fuzzy_ratio,
                                    ignore_case=ignore_case, ignore_punctuation=ignore_punct)

    return render_func('search.html',
                       vault=vault,
                       navtree=render_tree(AppState.indices[vault], vault,
                                           True),
                       page_editor=False,
                       home=AppState.config.vaults[vault].home_file,
                       results=results,
                       query=query, ignore_case = ignore_case, ignore_punct = ignore_punct, 
                       mode=mode, local_link=local_link, fuzzy_window=fuzzy_window, fuzzy_ratio=fuzzy_ratio)
