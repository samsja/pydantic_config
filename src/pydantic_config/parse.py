from __future__ import annotations
import copy
from typing import Dict, List, TypeAlias
import sys
from pydantic_config.errors import CliError

RawValue: TypeAlias = str | bool

NestedArgs: TypeAlias = Dict[str, "NestedArgs"]


class NamedArg:
    """
    Take an arg_name and a value and return a nested dictionary.

    Mainly look for nested dot notation in the arg_name and unest it if needed.

    Example:

    """

    def __init__(self, arg_name: str, value: RawValue | NamedArg, priority: bool = False):
        arg_name = arg_name.removeprefix("--")
        arg_name = arg_name.replace("-", "_")
        self.priority = priority

        self.name, self.value = self.process_nested_args(arg_name, value)

    def process_nested_args(self, arg_name: str, value: RawValue) -> tuple[str, RawValue | NamedArg]:
        """
        Take an arg_name and a value and return a nested dictionary.

        Mainly look for nested dot notation in the arg_name and unest it if needed.

        Example:

        """
        if "." not in arg_name:
            return arg_name, value
        else:
            new_value: RawValue | NamedArg = value
            # a.b.c.d
            nested_args_name = arg_name.split(".")
            nested_args_name.reverse()
            # here we go in reverse and create first d:value then c:(d:value) ...
            for name in nested_args_name[:-1]:
                new_value = NamedArg(name, new_value)
            # until the end where we return a , b:(c:(d:value))
            return arg_name[0], new_value

    def __repr__(self) -> str:
        return f"{self.name} : {str(self.value)}"


def parse_args(args: List[str]) -> NestedArgs:
    """
    Parse and validated a list of raw arguments.

    Example
    >>> parse_args(["--hello", "world", "--foo.bar", "galaxy"])
    {"hello": "world", "foo": {"bar": "galaxy"}}
    """

    args_original = args
    args = copy.deepcopy(args)
    suggestion_args = copy.deepcopy(args)

    parsed_named_args: list[NamedArg] = []

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

            parsed_named_args.append(NamedArg(arg_name, value))

            i += increment

    return parsed_named_args


def parse_argv() -> NestedArgs:
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
