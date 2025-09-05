from lark import Lark, Transformer, v_args, Tree
import ast

grammar = r"""
?start: expr

?expr: expr "and" expr   -> and_
     | expr "or" expr    -> or_
     | "!" expr          -> not_
     | term

?term: method
     | comparison
     | "(" expr ")"

attr: NAME ("." NAME)?    -> attr 

method: attr "." NAME "(" [args] ")"

comparison: value OP value

?value: attr
      | STRING           -> string

args: value ("," value)*

OP: "==" | "!=" | "<=" | ">=" | "<" | ">" | "in" | "not in"

NAME: /\w+/
STRING: /"[^"]*"/

%ignore " "
"""

# Реализация методов
def contains(val, arg): return arg in val
def containsAny(val, *args): return any(a in val for a in args)
def isEmpty(val): return len(val) == 0

@v_args(inline=True)
class FilterTransformer(Transformer):

    def start(self, expr):
        return expr

    def string(self, tok):
        return lambda ctx: ast.literal_eval(tok)

    def attr(self, *parts):
        names = [str(p) for p in parts]
        return lambda ctx: ctx[names[0]][names[1]] if len(names) == 2 else ctx[names[0]]

    def method(self, obj_func, method_name, *args):
        method_name = str(method_name)
        args_funcs = list(args)
        if args and isinstance(args[0], Tree) and args[0].data == "args":
            args_funcs = args[0].children
        else:
            args_funcs = list(args)
        

        
        if method_name == "contains":
            return lambda ctx: contains(obj_func(ctx), *[a(ctx) for a in args_funcs])
        elif method_name == "containsAny":
            return lambda ctx: containsAny(obj_func(ctx), *[a(ctx) for a in args_funcs])
        elif method_name == "isEmpty":
            return lambda ctx: isEmpty(obj_func(ctx))
        else:
            raise ValueError(f"Unknown method {method_name}")

    def comparison(self, left_func, op, right_func):
        op = str(op)
        ops = {
            "==": lambda a,b: a==b,
            "!=": lambda a,b: a!=b,
            "<": lambda a,b: a<b,
            "<=": lambda a,b: a<=b,
            ">": lambda a,b: a>b,
            ">=": lambda a,b: a>=b,
            "in": lambda a,b: a in b,
            "not in": lambda a,b: a not in b
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

# Пример использования
if __name__ == "__main__":
    parser = Lark(grammar, start="start", parser="lalr")

    filters = [
        'file.folder.contains("many_digits")',
        'file.tags.containsAny("even", "odd")',
        'file.ext == "md"',
        'file.name == file.ext',
        '!file.tags.contains("odd")',
        '(file.ext == "md" and file.name != "txt") or file.size > 100',
        '"even" in file.tags',
        '"odd" not in file.tags'
    ]

    ctx = {
        "file": {"folder": "many_digits_folder", "tags": ["even"], "ext": "md", "name": "md", "size": 123}
    }

    for f in filters:
        func = FilterTransformer().transform(parser.parse(f))
        print(f"{f} -> {func(ctx)}")
