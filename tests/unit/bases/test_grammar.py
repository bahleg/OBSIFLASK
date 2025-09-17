import pytest
from lark import Lark

from obsiflask.bases.grammar import grammar, FilterTransformer


class DummyCtx:

    def __init__(self, props):
        self._props = props

    def get_prop(self, path):
        # path can be a tuple or list of str
        key = ".".join(path)
        return self._props.get(key, None)


@pytest.fixture
def parser():
    return Lark(grammar, parser="lalr", transformer=FilterTransformer())


def eval_expr(parser, expr, ctx_dict):
    tree = parser.parse(expr)
    return tree(DummyCtx(ctx_dict))


def test_number_and_string(parser):
    assert eval_expr(parser, "5", {}) == 5
    assert eval_expr(parser, "3.14", {}) == 3.14
    assert eval_expr(parser, '"hello"', {}) == "hello"


def test_arithmetic(parser):
    assert eval_expr(parser, "2+3*4", {}) == 14
    assert eval_expr(parser, "(2+3)*4", {}) == 20
    assert eval_expr(parser, "-5", {}) == -5
    assert eval_expr(parser, "10/2", {}) == 5


def test_logical_ops(parser):
    ctx = {"a": 1, "b": 2}
    assert eval_expr(parser, "1==1 and 2==2", ctx) is True
    assert eval_expr(parser, "1==2 or 2==2", ctx) is True
    assert eval_expr(parser, "! (1==2)", ctx) is True


def test_binop_in_notin(parser):
    ctx = {"lst": [1, 2, 3]}
    assert eval_expr(parser, "1 in lst", ctx) is True
    assert eval_expr(parser, "5 not in lst", ctx) is True


def test_attr_access(parser):
    ctx = {"file.name": "note.md"}
    assert eval_expr(parser, "file.name == \"note.md\"", ctx) is True


def test_contains_method(parser):
    ctx = {"tags": ["python", "obsidian"]}
    assert eval_expr(parser, "tags.contains(\"python\")", ctx) is True
    assert eval_expr(parser, "tags.contains(\"java\")", ctx) is False


def test_contains_any_method(parser):
    ctx = {"tags": ["python", "obsidian"]}
    assert eval_expr(parser, "tags.containsAny(\"java\", \"python\")",
                     ctx) is True
    assert eval_expr(parser, "tags.containsAny(\"c++\", \"java\")",
                     ctx) is False


def test_is_empty_method(parser):
    assert eval_expr(parser, "tags.isEmpty()", {"tags": []}) is True
    assert eval_expr(parser, "tags.isEmpty()", {"tags": ["x"]}) is False


def test_starts_with_method(parser):
    ctx = {"name": "hello.md"}
    assert eval_expr(parser, "name.startsWith(\"he\")", ctx) is True
    assert eval_expr(parser, "name.startsWith(\"zz\")", ctx) is False


def test_has_tag_method(parser):

    class FakeVal:

        def get_prop(self, path):
            return ["tag1", "tag2"]

    ctx = {"file": FakeVal()}
    assert eval_expr(parser, "file.hasTag(\"tag1\")", ctx) is True
    assert eval_expr(parser, "file.hasTag(\"nope\")", ctx) is False


def test_unknown_method_raises(parser):
    with pytest.raises(ValueError):
        eval_expr(parser, "name.unknownMethod()", {"name": "x"})
