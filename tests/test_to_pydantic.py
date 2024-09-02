import pytest
from pydantic_config.parse import parse_args
from pydantic_config import BaseConfig
from pydantic import validate_call


def test_cli_to_pydantic():
    class Foo(BaseConfig):
        hello: str
        world: int

    argv = ["--hello", "world", "--world", "1"]

    arg_parsed = parse_args(argv)
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
        "--nested.nested.hello",
        "world",
        "--nested.nested.world",
        "1",
        "--nested.foo",
        "hello",
        "--bar",
        "hello",
    ]
    arg_parsed = parse_args(argv)

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

    arg_parsed = parse_args(["--a", "b", "--config.hello", "hello", "--config.world", "1"])
    foo(**arg_parsed)

    with pytest.raises(AssertionError):
        arg_parsed = parse_args(["--a", "b", "--config.hello", "nooo", "--config.world", "1"])
        foo(**arg_parsed)
