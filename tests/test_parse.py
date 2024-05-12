import pytest

from pydantic_config.parse import parse_nested_arg, semi_parse_argv, CliArgError


@pytest.mark.parametrize("arg", ["hello", "-hello"])
def test_no_underscor_arg_failed(arg):
    argv = ["main.py", arg]

    with pytest.raises(CliArgError):
        semi_parse_argv(argv)


def test_correct_arg_passed():
    argv = ["main.py", "--hello", "world", "--foo", "bar"]
    assert semi_parse_argv(argv) == {"hello": "world", "foo": "bar"}


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
            {"main.hello": "world", "main.foo": "bar", "main.foo.bar": "baz"},
            {"main": {"hello": "world", "foo": {"bar": "baz"}}},
        ),
        (
            {
                "main.hello": "world",
                "main.foo.bar": "baz",
                "main.foo.bar.qux": "quux",
                "main.foo.bar.qux.corge": "grault",
            },
            {"main": {"hello": "world", "foo": {"bar": {"qux": {"corge": "grault"}}}}},
        ),
    ],
)
def test_parse_nested_multi_level_arg(input_dict, expected_output):
    assert parse_nested_arg(input_dict) == expected_output
