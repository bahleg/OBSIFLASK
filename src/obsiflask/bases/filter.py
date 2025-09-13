from pathlib import Path
import re
from obsiflask.bases.grammar import FilterTransformer, grammar
from lark import Lark
from obsiflask.bases.file_info import FileInfo
from functools import partial
from obsiflask.app_state import AppState
from obsiflask.messages import add_message

filter_binary_op = re.compile('([^\s]+)\s+([^\s]+)\s+([^\s]+)')


class Variable:
    pass


class Filter:

    def check(file: FileInfo) -> bool:
        raise NotImplementedError()


class FilterAnd(Filter):

    def __init__(self, filters):
        super().__init__()
        self.children = filters

    def check(self, file):
        return all([c.check(file) for c in self.children])


class FilterOr(Filter):

    def __init__(self, filters):
        super().__init__()
        self.children = filters

    def check(self, file):
        return any([c.check(file) for c in self.children])


class TrivialFilter(Filter):

    def check(self, file: FileInfo):
        return True


class FieldFilter:

    def __init__(self, expr):
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


if __name__ == '__main__':
    files = list(Path('..').glob('./**/*md'))
    print(len(files))
    files = [FileInfo(f, Path('..').resolve()) for f in files]
    for filter in """file.folder.contains("many_digits")
        file.tags.containsAny("even", "odd")
        file.ext == "md"
        !next.isEmpty()""".splitlines():
        print('Filter', filter)
        filter = filter.strip()
        filter = FieldFilter(filter)
        filtered = [f for f in files if filter.filter(f)]
        print(len(filtered))
