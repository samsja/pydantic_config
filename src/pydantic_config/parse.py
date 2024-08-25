import copy
from typing import Dict, List, TypeAlias
import sys
from pydantic_config.errors import CliError

NestedDict: TypeAlias = Dict[str, "NestedDict"]


def parse_args(args: List[str]) -> NestedDict:
    """
    Parse and validated a list of raw arguments.

    Example
    >>> parse_args(["--hello", "world", "--foo.bar", "galaxy"])
    {"hello": "world", "foo": {"bar": "galaxy"}}
    """

    args_original = args
    args = copy.deepcopy(args)
    suggestion_args = copy.deepcopy(args)

    named_args: Dict[str, str | bool] = {}

    i = 0

    while i < len(args):
        potential_arg_name = args[i]

        if not potential_arg_name.startswith("--"):
            ## arg_name should start with "--" Example "--hello a"
            error_msg = "the first argument should start with '--'"
            suggestion_args[i] = "--" + potential_arg_name
            raise CliError(args_original, [i], error_msg, suggestion_args)
        else:
            # once we have the arg name we look for the arg value
            arg_name = potential_arg_name

            # if we are at the end of the list, we assume the last value is a boolean
            if i == len(args) - 1:
                value = None
                increment = 1
            else:
                arg_value = args[i + 1]

                if arg_value.startswith("--"):
                    ## Example "--hello --foo a". Hello is a bool here
                    value = None
                    increment = 1  # we want to analyse --foo next
                else:
                    ## example "--hello a --foo b"
                    value = arg_value
                    increment = 2  # we want to analyse --foo next

            if value is None:
                # if it start with --no then value is False else True
                value = not (arg_name.startswith("--no-"))

            if value is not None and arg_name.startswith("--no-"):
                error_msg = "Boolean flag starting with '--no-' cannot be follow by a argument value"
                suggestion_args[i + 1] = "--" + arg_name.removeprefix("--no-")
                raise CliError(args_original, [i, i + 1], error_msg, suggestion_args)

            named_args[arg_name] = value

            i += increment

    return named_args


def parse_argv() -> NestedDict:
    """
    Parse argument from argv and return a nested python dictionary.
    """
    try:
        program_name = sys.argv[0]
        args = list(sys.argv)[1:]
        return parse_args(args)
    except CliError as e:
        e.program_name = program_name
        e.render()
        sys.exit(1)
