from pathlib import Path
import re

filter_binary_op = re.compile('([^\s]+)\s+([^\s]+)\s+([^\s]+)')


class Variable:
    pass


class FileInfo:

    def __init__(self, path: Path, index_path: Path):
        self.path = Path(path).resolve().relative_to(index_path.resolve())


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


class FieldFilter(filter):

    def __init__(self, formula: str):
        super().__init__()
        self.formula = formula  # for tracking
        if formula.startswith('"'):
            formula.strip('"')
            self.custom_property = True
        else:
            self.custom_property = False

        self.neg = formula.startswith('!')
        formula = formula.lstrip('!', 1)
        if not self.custom_property:
            assert formula.startswith('file.')
            formula = formula.split('file.', 1)[1]
