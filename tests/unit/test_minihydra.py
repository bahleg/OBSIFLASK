"""
Originally a code from embed2discover (https://gitlab.datascience.ch/democrasci/embed2discover)
GPLv3
"""
from dataclasses import dataclass, MISSING

from pytest import raises

from obsiflask.minihydra import TARGET_KEY, init, load_config  


def test_load_config(tmp_path):

    @dataclass
    class MyTestA:
        a: int = MISSING
        b: int = 456
        add_entries: list[int] | None = None
        ext_path: list[str] | None = None
        ext_dirs: list[str] | None = None

    with open(tmp_path / "yaml.yml", "w") as out:
        out.write("a: 123")
    assert load_config(tmp_path / "yaml.yml").a == 123
    assert load_config(tmp_path / "yaml.yml", MyTestA).a == 123
    assert load_config(tmp_path / "yaml.yml", MyTestA).b == 456
    with open(tmp_path / "yaml.yml", "w") as out:
        out.write("a: 123\nc: 456")
    with raises(Exception):
        load_config(tmp_path / "yaml.yml", MyTestA)

    ext = (tmp_path / "add_yaml")
    ext.mkdir()
    with open(ext / "1.yml", 'w') as out:
        out.write('add_entries: [1, 2]')
    with open(ext / "2.yml", 'w') as out:
        out.write('add_entries: [3, 4]')


def test_init():
    from tests.unit.test_minihydra_helper import TestObject

    resulting_obj = init({
        TARGET_KEY: "tests.unit.test_minihydra_helper.TestObject",
        "a": 123,
        "b": 456
    })
    assert resulting_obj.a == 123
    assert resulting_obj.b == 456
    resulting_obj = init(
        {
            TARGET_KEY: "tests.unit.test_minihydra_helper.TestObject",
            "a": 123,
            "b": 456
        },
        TestObject,
    )
    assert resulting_obj.a == 123
    assert resulting_obj.b == 456
    with raises(AssertionError):
        resulting_obj = init(
            {
                TARGET_KEY: "tests.unit.test_minihydra_helper.TestObject",
                "a": 123,
                "b": 456
            },
            str,
        )
    resulting_obj = init(
        {
            TARGET_KEY: "tests.unit.test_minihydra_helper.TestObject",
            "a": 123,
            "b": {
                TARGET_KEY: "tests.unit.test_minihydra_helper.TestObject",
                "a": 789,
                "b": 1011,
            },
        },
        TestObject,
    )
    assert resulting_obj.a == 123
    assert resulting_obj.b.a == 789
    assert resulting_obj.b.b == 1011