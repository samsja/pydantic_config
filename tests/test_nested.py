from pydantic_config.parse import NamedArg


def test_nested_arg_parser():
    named_arg = NamedArg("--a.b.c", "value")
    assert named_arg.name == "a"
    assert named_arg.value.value.value == "value"
    assert named_arg.value.value.name == "c"
    assert named_arg.value.name == "b"
