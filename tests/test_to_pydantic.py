from pydantic_config.parse import parse_argv_as_list
from pydantic_config import BaseConfig


def test_cli_to_pydantic():
    class Foo(BaseConfig):
        hello: str
        world: int

    argv = ["main.py", "--hello", "world", "--world", "1"]

    arg_parsed = parse_argv_as_list(argv)
    assert arg_parsed == {"hello": "world", "world": "1"}

    arg_validated = Foo(**arg_parsed)
    assert arg_validated.hello == "world"
    assert arg_validated.world == 1


def test_complex_pydantic():
    class NestedNestedModel(BaseConfig):
        hello: str = "world"
        world: int

    class NestedModel(BaseConfig):
        nested: NestedNestedModel
        foo: str

    class MainModel(BaseConfig):
        nested: NestedModel
        bar: str

    argv = [
        "main.py",
        "--nested.nested.hello",
        "world",
        "--nested.nested.world",
        "1",
        "--nested.foo",
        "hello",
        "--bar",
        "hello",
    ]
    arg_parsed = parse_argv_as_list(argv)

    arg_validated = MainModel(**arg_parsed)

    assert arg_validated.nested.nested.hello == "world"
    assert arg_validated.nested.nested.world == 1
    assert arg_validated.nested.foo == "hello"
    assert arg_validated.bar == "hello"
