"""
Logic for parsing bases
"""
from typing import Callable

from omegaconf import OmegaConf
from lark import Lark

from obsiflask.app_state import AppState
from obsiflask.bases.view import View
from obsiflask.bases.filter import Filter, FilterAnd, FilterOr, FieldFilter, TrivialFilter
from obsiflask.messages import add_message
from obsiflask.bases.grammar import FilterTransformer, grammar
from obsiflask.utils import get_traceback

class Base:
    """
    A general class for bases handling
    """

    def __init__(self, path: str):
        """
        Constructor

        Args:
            path (str): path to base w.r.t. vault
        """
        self.formulas = {}
        self.properties = {}
        self.global_filter: Filter = None
        self.views: dict[str, View] = {}


def parse_filter(filter_dict: dict, vault) -> Filter:
    """
    Parsing filter

    Args:
        filter_dict (dict): yaml-based config 
        vault (str): vault name

    Returns:
        Filter: resulting filter
    """
    if isinstance(filter_dict, str):
        result = FieldFilter(filter_dict)
        return result
    if len(filter_dict) > 1:
        if AppState.config.vaults[vault].base_config.error_on_yaml_parse:
            raise NotImplementedError(
                f'unsupported filter format: {filter_dict}')
        else:
            key = list(filter_dict.keys())[0]
            add_message(
                f'unsupported filter format: {filter_dict}. Using only first key',
                1, vault)
    else:
        key = list(filter_dict.keys())[0]
    if key == 'and':
        return FilterAnd([parse_filter(f, vault) for f in filter_dict['and']])
    elif key == 'or':
        return FilterOr([parse_filter(f, vault) for f in filter_dict['or']])
    else:
        if AppState.config.vaults[vault].base_config.error_on_yaml_parse:
            raise NotImplementedError(f'unsupported filter key: \"{key}\"')
        else:
            add_message(f'unsupported filter key: \"{key}\". Disabling.', 1,
                        vault)
            return TrivialFilter()


def parse_view(view: dict, vault: str, formulas: list[Callable],
               properties: dict, base_path: str) -> View:
    """
    View parsing

    Args:
        view (dict): yam-based
        vault (str): vault name
        formulas (list[Callable]): list of callables for each formula
        properties (dict): dictionary of properties
        base_path (str): real path 

    Returns:
        View: resulting view
    """
    result = View(formulas, properties, base_path)
    result.type = view['type']
    if result.type not in ['table', 'cards']:
        if AppState.config.vaults[vault].base_config.error_on_yaml_parse:
            raise NotImplementedError(f'unsupported view type: {result.type}')
        else:
            add_message(
                f'unsupported view type: {result.type}. Changing to table', 1,
                vault)
            result.type = 'table'
    result.name = view['name']
    if 'filters' in view:
        result.filter = parse_filter(view['filters'], vault)
    else:
        result.filter = TrivialFilter()
    result.order = view['order']
    if 'sort' in view:
        for s in view['sort']:
            result.sorts.append((s['property'], s['direction']))
    return result


def parse_base(real_path: str, vault: str) -> Base:
    """
    Base parsing logic

    Args:
        real_path (str): path to base
        vault (str): vault name

    Returns:
        Base: resulting base
    """
    base = Base(real_path)
    yaml = OmegaConf.load(real_path)
    if 'filters' in yaml:
        base.global_filter = parse_filter(yaml['filters'], vault)
    else:
        base.global_filter = TrivialFilter()

    base.properties = yaml.get('properties', {})
    for key, formula in yaml.get('formulas', {}).items():
        parser = Lark(grammar, start="start", parser="lalr")
        try:
            func = FilterTransformer().transform(parser.parse(formula))

        except Exception as e:
            if AppState.config.vaults[vault].base_config.error_on_field_parse:
                raise ValueError(
                    f'Problems with formula {formula} parsing: {e}')
            else:
                add_message(
                    f'Problems with formula {formula} parsing. Skipping', 1,
                    vault, get_traceback(e))
                func = lambda x: ''
        base.formulas[key] = func

    for view in yaml.get('views', []):
        base.views[view['name']] = parse_view(view, vault, base.formulas,
                                              base.properties, real_path)
        base.views[view['name']].global_filter = base.global_filter
    return base
