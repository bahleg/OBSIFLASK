from lark import Lark, Transformer, v_args, Tree
import ast

grammar = r"""
?start: expr

?expr: expr "and" expr   -> and_
     | expr "or" expr    -> or_
     | "!" expr          -> not_
     | binop
     | arith


attr: NAME ("." NAME)*    -> attr 

?method: NAME ("." NAME)* "(" [args] ")"

?binop: arith OP arith

?arith: arith "+" term   -> add_
      | arith "-" term   -> sub_
      | term

?term: term "*" factor   -> mult_
     | term "/" factor   -> div_
     | factor

?factor: method
       | attr
       | NUMBER           -> number
       | STRING           -> string
       | "(" expr ")"

?value: attr
      | STRING           -> string
      | NUMBER           -> number

args: value ("," value)*

OP: "==" | "!=" | "<=" | ">=" | "<" | ">" | "in" | "not in" 

NAME: /\w+/
STRING: /"[^"]*"/
NUMBER: /\d+(\.\d+)?/

%ignore " "
"""


# Реализация методов
def contains(val, arg):
    return arg in val


def containsAny(val, *args):
    return any(a in val for a in args)


def isEmpty(val):
    return len(val) == 0

def startsWith(val,  *args):
    if len(args) != 1:
        raise ValueError('startsWith requires 1 argument')
    return str(val).startswith(str(args[0]))

def hasTag(val, *args):
    if len(args) != 1:
        raise ValueError('hasTag requires 1 argument')
    tag = args[0].lstrip('#')
    return tag in val.get_prop(['tags'])
    
@v_args(inline=True)
class FilterTransformer(Transformer):

    def attr(self, *attr):
        return lambda ctx: ctx.get_prop(attr)

    def start(self, expr):
        return expr

    def number(self, tok):
        val = float(tok) if "." in tok else int(tok)
        return lambda ctx: val

    def string(self, tok):
        return lambda ctx: ast.literal_eval(tok)

    def method(self, *args):
        names = []
        method_args = []
        for a in args:
            if a is None:  # empty args
                continue
            if isinstance(a, Tree) and a.data == 'args':
                args_funcs = a.children
                method_args.extend(args_funcs)
            elif a.type == 'NAME':
                names.append(str(a))
        method_name = str(names[-1])
        attr = lambda ctx: ctx.get_prop(names[:-1])
        if method_name == "contains":
            return lambda ctx: contains(attr(ctx), *
                                        [a(ctx) for a in method_args])
        elif method_name == "containsAny":
            return lambda ctx: containsAny(attr(ctx), *
                                           [a(ctx) for a in method_args])
        elif method_name == "isEmpty":
            return lambda ctx: isEmpty(attr(ctx))
        elif method_name == 'startsWith':
            return lambda ctx: startsWith(attr(ctx), *
                                           [a(ctx) for a in method_args])
        elif method_name == 'hasTag':
            return lambda ctx: hasTag(attr(ctx), *
                                           [a(ctx) for a in method_args])
        else:
            raise ValueError(f"Unknown method {method_name}")

    def binop(self, left_func_or_tree, op, right_func_or_tree):
        if isinstance(left_func_or_tree, Tree):
            left_names = left_func_or_tree.children
            left_func = lambda ctx: ctx.get_prop(left_names)
        else:
            left_func = left_func_or_tree

        if isinstance(right_func_or_tree, Tree):
            right_names = right_func_or_tree.children
            right_func = lambda ctx: ctx.get_prop(right_names)
        else:
            right_func = right_func_or_tree

        op = str(op)
        ops = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "in": lambda a, b: a in b,
            "not in": lambda a, b: a not in b,
        }
        if op not in ops:
            raise ValueError(f"Unsupported op {op}")
        return lambda ctx: ops[op](left_func(ctx), right_func(ctx))

    def not_(self, func):
        return lambda ctx: not func(ctx)

    def and_(self, a, b):
        return lambda ctx: a(ctx) and b(ctx)

    def or_(self, a, b):
        return lambda ctx: a(ctx) or b(ctx)

    def add_(self, a, b):
        return lambda ctx: a(ctx) + b(ctx)

    def mult_(self, a, b):
        return lambda ctx: a(ctx) * b(ctx)

    def sub_(self, a, b):
        return lambda ctx: a(ctx) - b(ctx)

    def div_(self, a, b):
        return lambda ctx: a(ctx) / b(ctx)


# Пример использования
if __name__ == "__main__":
    parser = Lark(grammar, start="start", parser="lalr")

    filters = [
        'file.folder.contains("many_digits")',
        'file.tags.containsAny("even", "odd")', 'file.ext == "md"',
        'file.name == file.ext', '!file.tags.contains("odd")',
        '(file.ext == "md" and file.name != "txt") or file.size > 100',
        '"even" in file.tags', '"odd" not in file.tags'
    ]

    ctx = {
        "file": {
            "folder": "many_digits_folder",
            "tags": ["even"],
            "ext": "md",
            "name": "md",
            "size": 123
        }
    }

    for f in filters:
        func = FilterTransformer().transform(parser.parse(f))
        print(f"{f} -> {func(ctx)}")
