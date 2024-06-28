from enum import Enum
import pytest
from pydantic_config.parse import parse_argv_as_list
from pydantic_config import BaseConfig, validate_call


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


def test_validate_function():
    class Config(BaseConfig):
        hello: str
        world: int

    @validate_call
    def foo(a: str, config: Config):
        assert config.hello == "hello"
        assert config.world == 1
        assert a == "b"

    arg_parsed = parse_argv_as_list(["main.py", "--a", "b", "--config.hello", "hello", "--config.world", "1"])
    foo(**arg_parsed)

    with pytest.raises(AssertionError):
        arg_parsed = parse_argv_as_list(["main.py", "--a", "b", "--config.hello", "nooo", "--config.world", "1"])
        foo(**arg_parsed)

    with pytest.raises(SystemExit) as e:
        arg_parsed = parse_argv_as_list(["main.py", "--a", "b", "--config.world", "1"])
        foo(**arg_parsed)
    assert e.value.code == 1


def test_enum():
    class Bar(Enum):
        a = "a"
        b = "b"

    class Foo(BaseConfig):
        bar: Bar

    with pytest.raises(ValueError):
        arg_parsed = parse_argv_as_list(["main.py", "--bar", "c"])
        Foo(**arg_parsed)

    arg_parsed = parse_argv_as_list(["main.py", "--bar", "a"])
    foo = Foo(**arg_parsed)
    assert foo.bar == Bar.a

    arg_parsed = parse_argv_as_list(["main.py", "--bar", "b"])
    foo = Foo(**arg_parsed)
    assert foo.bar == Bar.b
