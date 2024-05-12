from pydantic_config.parse import parse_argv

from pydantic import BaseModel


def test_cli_to_pydantic():
    class Foo(BaseModel):
        hello: str
        world: int

    argv = ["main.py", "--hello", "world", "--world", "1"]

    arg_parsed = parse_argv(argv)
    assert arg_parsed == {"hello": "world", "world": "1"}

    arg_validated = Foo(**arg_parsed)
    assert arg_validated.hello == "world"
    assert arg_validated.world == 1


def test_complex_pydantic():
    class NestedNestedModel(BaseModel):
        hello: str = "world"
        world: int

    class NestedModel(BaseModel):
        nested: NestedNestedModel
        foo: str

    class MainModel(BaseModel):
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
    arg_parsed = parse_argv(argv)

    arg_validated = MainModel(**arg_parsed)

    assert arg_validated.nested.nested.hello == "world"
    assert arg_validated.nested.nested.world == 1
    assert arg_validated.nested.foo == "hello"
    assert arg_validated.bar == "hello"
