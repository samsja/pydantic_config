import pytest
from pydantic_config.errors import CliError
from pydantic_config.parse import parse_args


def test_no_starting_with_correct_prefix():
    argv = ["world"]
    with pytest.raises(CliError):
        parse_args(argv)


## bool


def test_bool():
    argv = ["--hello", "--no-foo", "--no-bar"]
    assert parse_args(argv) == {"hello": True, "foo": False, "bar": False}


def test_bool_not_follow_value():
    argv = ["--no-hello", "world"]
    with pytest.raises(CliError):
        parse_args(argv)


def test_nested_list():
    argv = ["--hello.world", "world", "--foo", "bar", "--hello.world", "universe"]
    assert parse_args(argv) == {"hello": {"world": ["world", "universe"]}, "foo": "bar"}


## old test for legacy


@pytest.mark.parametrize("arg", ["hello", "-hello"])
def test_no_underscor_arg_failed(arg):
    argv = [arg]

    with pytest.raises(CliError):
        parse_args(argv)


def test_correct_arg_passed():
    argv = ["--hello", "world", "--foo", "bar"]
    assert parse_args(argv) == {"hello": "world", "foo": "bar"}


def test_python_underscor_replace():
    argv = ["--hello-world", "hye", "--foo_bar", "bar"]
    assert parse_args(argv) == {"hello_world": "hye", "foo_bar": "bar"}


def test_list():
    argv = ["--hello", "world", "--foo", "bar", "--hello", "universe"]
    assert parse_args(argv) == {"hello": ["world", "universe"], "foo": "bar"}


def test_nested_conflict():
    with pytest.raises(CliError):
        argv = ["--hello.world", "world", "--hello", "galaxy"]
        parse_args(argv)
