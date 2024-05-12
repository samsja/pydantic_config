import pytest

from pydantic_config.parse import semi_parse_argv, CliArgError


@pytest.mark.parametrize("arg", ["hello", "-hello"])
def test_no_underscor_arg_failed(arg):
    argv = ["main.py", arg]

    with pytest.raises(CliArgError):
        semi_parse_argv(argv)
