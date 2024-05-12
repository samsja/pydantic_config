import pytest

from pydantic_cli.parse import (
    DuplicateKeyError,
    semi_parse_argv,
    CliArgError,
)


@pytest.mark.parametrize("arg", ["hello", "-hello"])
def test_no_underscor_arg_failed(arg):
    argv = ["main.py", arg]

    with pytest.raises(CliArgError):
        semi_parse_argv(argv)


def test_correct_arg_passed():
    argv = ["main.py", "--hello", "world", "--foo", "bar"]
    assert semi_parse_argv(argv) == {"hello": "world", "foo": "bar"}


def test_duplicate_keys_fail():
    argv = ["main.py", "--hello", "world", "--hello", "universe"]
    with pytest.raises(DuplicateKeyError):
        semi_parse_argv(argv)


def test_python_underscor_replace():
    argv = ["main.py", "--hello-world", "hye", "--foo_bar", "bar"]
    assert semi_parse_argv(argv) == {"hello_world": "hye", "foo_bar": "bar"}
