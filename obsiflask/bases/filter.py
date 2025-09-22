"""
Filtering logic for vault bases
"""

from lark import Lark

from obsiflask.bases.grammar import FilterTransformer, grammar
from obsiflask.bases.file_info import FileInfo
from obsiflask.app_state import AppState
from obsiflask.messages import add_message


class Filter:
    """
    Abstract class to represent a filter
    """

    def check(file: FileInfo) -> bool:
        """
        Abstract function to check if file meetgs condition

        Args:
            file (FileInfo): file to chec

        Returns:
            bool: True if filter accepts the file
        """
        raise NotImplementedError()


class FilterAnd(Filter):
    """
    "And" filter
    """

    def __init__(self, filters: list[Filter]):
        """
        Constructor

        Args:
            filters (list[Filter]): filter to check with "AND" operator
        """
        super().__init__()
        self.children = filters

    def check(self, file):
        return all([c.check(file) for c in self.children])


class FilterOr(Filter):
    """
    "Or" filter
    """

    def __init__(self, filters: list[Filter]):
        """
        Constructor

        Args:
            filters (list[Filter]): filter to check with "AND" operator
        """
        super().__init__()
        self.children = filters

    def check(self, file):
        return any([c.check(file) for c in self.children])


class TrivialFilter(Filter):
    """
    A filter that accepts everything.
    Written for compatibility
    """

    def check(self, file: FileInfo):
        return True


class FieldFilter:
    """
    Filter that parses formula and check files against this formula
    """

    def __init__(self, expr: str):
        """
        Constructor

        Args:
            expr (str): expression for the filter
        """
        self.parser = Lark(grammar, start="start", parser="lalr")
        self.exception = None
        self.expr = expr
        try:
            self.func = FilterTransformer().transform(self.parser.parse(expr))
        except Exception as e:
            self.exception = e

    def check(self, file: FileInfo):
        if self.exception:
            if AppState.config.vaults[
                    file.vault].base_config.error_on_field_parse:
                raise self.exception
            else:
                add_message(
                    f'Error during filter parsing with experssion {self.expr}. Ignoring filter',
                    type=1,
                    vault=file.vault,
                    details=repr(self.exception))
                return True
        return self.func(file)
