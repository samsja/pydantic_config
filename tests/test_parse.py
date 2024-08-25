import pytest
from pydantic_config.errors import CliError
from pydantic_config.parse import parse_args


@pytest.mark.parametrize("arg", ["hello", "-hello"])
def test_no_underscor_arg_failed(arg):
    argv = ["main.py", arg]

    with pytest.raises(CliError):
        parse_args(argv)


def test_correct_arg_passed():
    argv = ["main.py", "--hello", "world", "--foo", "bar"]
    assert parse_args(argv) == {"hello": "world", "foo": "bar"}


def test_python_underscor_replace():
    argv = ["main.py", "--hello-world", "hye", "--foo_bar", "bar"]
    assert parse_args(argv) == {"hello_world": "hye", "foo_bar": "bar"}


def test_bool():
    argv = ["main.py", "--hello", "--no-foo", "--no-bar"]
    assert parse_args(argv) == {"hello": True, "foo": False, "bar": False}


def test_list():
    argv = ["main.py", "--hello", "world", "--foo", "bar", "--hello", "universe"]
    assert parse_args(argv) == {"hello": ["world", "universe"], "foo": "bar"}


def test_nested_list():
    argv = ["main.py", "--hello.world", "world", "--foo", "bar", "--hello.world", "universe"]
    assert parse_args(argv) == {"hello": {"world": ["world", "universe"]}, "foo": "bar"}


def test_nested_conflict():
    with pytest.raises(CliError):
        argv = ["main.py", "--hello.world", "world", "--hello", "galaxy"]
        parse_args(argv)
