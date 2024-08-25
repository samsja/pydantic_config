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

    i = 0

    while i < len(args):
        potential_arg_name = args[i]

        if not potential_arg_name.startswith("--"):
            raise CliError(args_original, [i])

    return {}


def parse_argv() -> NestedDict:
    """
    Parse argument from argv and return a nested python dictionary.
    """
    try:
        program_name = sys.argv[0]
        args = list(sys.argv)[1:]
        return parse_args(args, program_name)
    except CliError as e:
        e.program_name = program_name
        e.render()
        sys.exit(1)
