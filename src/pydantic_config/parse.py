from __future__ import annotations
import copy
from typing import TypeAlias
import sys
from pydantic_config.errors import CliError

RawValue: TypeAlias = str | bool


class Value:
    """
    Hold a value as well as a priority info
    """

    def __init__(self, value: RawValue, priority: int):
        self.value = value
        self.priority = priority

    def __repr__(self) -> str:
        return f"{self.value} ({self.priority})"


NestedArgs: TypeAlias = dict[str, "NestedArgs"]  # dict[str, "NestedArgs" | Value]


def parse_nested_args(arg_name: str, value: RawValue) -> NestedArgs:
    """
    Take an arg_name and a value and return a nested dictionary.

    Mainly look for nested dot notation in the arg_name and unest it if needed.

    Example:

    >>> parse_nested_args("a.b.c.d", "value")
    {"a": {"b": {"c": {"d": "value"}}}}
    """
    if "." not in arg_name:
        return {arg_name: value}
    else:
        left_name, *rest = arg_name.split(".")
        rest = ".".join(rest)
        return {left_name: parse_nested_args(rest, value)}


def normalize_arg_name(arg_name: str) -> str:
    """remove prefix are replaced - with _"""
    arg_name = copy.deepcopy(arg_name)
    if arg_name.startswith("--no-"):
        arg_name = arg_name.removeprefix("--no-")
    else:
        arg_name = arg_name.removeprefix("--")

    arg_name = arg_name.replace("-", "_")
    return arg_name


def unwrap_value(args: NestedArgs) -> NestedArgs:
    """
    Look for value as leaf in a nested args and cast to its content
    """
    for key, value in args.items():
        if isinstance(value, Value):
            args[key] = value.value
        else:
            unwrap_value(value)
    return args


def parse_args(args: list[str]) -> NestedArgs:
    """
    Parse and validated a list of raw arguments.

    Example
    >>> parse_args(["--hello", "world", "--foo.bar", "galaxy"])
    {"hello": "world", "foo": {"bar": "galaxy"}}
    """

    args_original = args
    args = copy.deepcopy(args)
    suggestion_args = copy.deepcopy(args)

    merged_args = {}

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

            if value is not None and arg_name.startswith("--no-"):
                error_msg = "Boolean flag starting with '--no-' cannot be follow by a argument value"
                suggestion_args[i] = "--" + arg_name.removeprefix("--no-")
                raise CliError(args_original, [i, i + 1], error_msg, suggestion_args)

            if value is None:
                # if it start with --no then value is False else True
                value = not (arg_name.startswith("--no-"))

            arg_name = normalize_arg_name(arg_name)
            value = Value(value, priority=1)  # command line argument are priority over config file
            parsed_arg = parse_nested_args(arg_name, value)
            top_name = list(parsed_arg.keys())[0]

            def merge_dict(name, left, right):
                if name not in left.keys():
                    left[name] = right[name]
                else:
                    arg = left[name]
                    new_arg = right[name]
                    if isinstance(arg, Value):
                        if not isinstance(new_arg, Value):
                            raise CliError(args_original, [i], f"Conflicting value for {name}", [])
                        if isinstance(arg.value, bool):
                            if isinstance(new_arg.value, bool):
                                if new_arg.priority > arg.priority:
                                    left[name] = new_arg
                                elif new_arg.priority < arg.priority:
                                    ...
                                else:
                                    raise CliError(args_original, [i], f"Conflicting boolean flag for {name}", [])
                        if isinstance(new_arg.value, str):
                            if not isinstance(arg.value, str):
                                raise CliError(args_original, [i], f"Conflicting value for {name}", [])
                            if new_arg.priority > arg.priority:
                                left[name] = new_arg
                            elif new_arg.priority < arg.priority:
                                ...
                            else:
                                # if we get mutiple non bool arg we put them into a list
                                if isinstance(arg.value, str):
                                    arg.value = [arg.value]

                                arg.value.append(new_arg.value)
                        else:
                            if isinstance(new_arg.value, bool):
                                raise CliError(args_original, [i], f"Conflicting boolean flag for {name}", [])

                    elif isinstance(arg, dict):
                        if not isinstance(new_arg, dict):
                            raise CliError(args_original, [i], f"Conflicting boolean flag for {name}", [])

                        nested_arg_name = list(right[name].keys())[0]
                        merge_dict(nested_arg_name, left[name], right[name])
                    else:
                        # should never arrive here
                        raise ValueError()

            merge_dict(top_name, merged_args, parsed_arg)

            i += increment

    return unwrap_value(merged_args)


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
