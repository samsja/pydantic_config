import pytest

from pydantic_config.parse import (
    DuplicateKeyError,
    parse_argv_as_list,
    CliArgError,
)


@pytest.mark.parametrize("arg", ["hello", "-hello"])
def test_no_underscor_arg_failed(arg):
    argv = ["main.py", arg]

    with pytest.raises(CliArgError):
        parse_argv_as_list(argv)


def test_correct_arg_passed():
    argv = ["main.py", "--hello", "world", "--foo", "bar"]
    assert parse_argv_as_list(argv) == {"hello": "world", "foo": "bar"}


def test_duplicate_keys_fail():
    argv = ["main.py", "--hello", "world", "--hello", "universe"]
    with pytest.raises(DuplicateKeyError):
        parse_argv_as_list(argv)


def test_python_underscor_replace():
    argv = ["main.py", "--hello-world", "hye", "--foo_bar", "bar"]
    assert parse_argv_as_list(argv) == {"hello_world": "hye", "foo_bar": "bar"}


def test_bool():
    argv = ["main.py", "--hello", "--no-foo", "--no-bar"]
    assert parse_argv_as_list(argv) == {"hello": True, "foo": False, "bar": False}
