"""
A smoke test checking all the *py file import without errors
"""
from pathlib import Path
import importlib


def test_imports():
    import obsiflask
    path = Path(obsiflask.__file__).parent
    for file in path.glob('./**/*py'):
        module_name = '.'.join(file.relative_to(path).with_suffix("").parts)
        importlib.import_module('obsiflask.'+module_name)
