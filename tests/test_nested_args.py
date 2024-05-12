import pytest
from pydantic_cli.error import CliArgError, DuplicateKeyError
from pydantic_cli.parse import parse_nested_arg


def test_parse_nested_arg():
    input_dict = {"main.hello": "world", "main.foo": "bar"}
    expected_output = {"main": {"hello": "world", "foo": "bar"}}
    assert parse_nested_arg(input_dict) == expected_output


def test_parse_nested_arg_failure_due_to_main():
    input_dict = {"main.": "world", "main.foo": "bar"}
    with pytest.raises(CliArgError):
        parse_nested_arg(input_dict)


@pytest.mark.parametrize(
    "input_dict, expected_output",
    [
        (
            {"main.hello": "world", "main.foo.bar": "baz"},
            {"main": {"hello": "world", "foo": {"bar": "baz"}}},
        ),
        (
            {
                "main.hello": "world",
                "main.foo.bar.qux.corge": "grault",
                "main.foo.bar.a": "b",
            },
            {
                "main": {
                    "hello": "world",
                    "foo": {"bar": {"qux": {"corge": "grault"}, "a": "b"}},
                }
            },
        ),
    ],
)
def test_parse_nested_multi_level_arg(input_dict, expected_output):
    assert parse_nested_arg(input_dict) == expected_output


def test_parse_nested_multi_level_arg_failure_due_to_duplicate_key():
    input_dict = {"main.hello": "world", "main.hello.foo": "bar"}
    with pytest.raises(DuplicateKeyError):
        parse_nested_arg(input_dict)
