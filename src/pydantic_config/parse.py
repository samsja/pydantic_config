from __future__ import annotations
import copy
import json
from typing import TypeAlias
import sys
import importlib

from pydantic_config.errors import CliError, InvalidConfigFileError

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


CONFIG_FILE_SIGN = "@"


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
        elif isinstance(value, dict):
            unwrap_value(value)
        else:
            raise ValueError(f"Invalid value type {type(value)}")
    return args


def load_config_file(path: str, priority: int) -> NestedArgs:
    """
    Load a config file and return a nested dictionary.
    """

    content = None
    try:
        with open(path, "rb") as f:
            if path.endswith(".json"):
                try:
                    content = json.load(f)
                except json.JSONDecodeError as e:
                    raise InvalidConfigFileError(e)
            elif importlib.util.find_spec("yaml") is not None and path.endswith(".yaml") or path.endswith(".yml"):
                import yaml

                try:
                    content = yaml.load(f, Loader=yaml.FullLoader)
                except yaml.YAMLError as e:
                    raise InvalidConfigFileError(e)
            elif importlib.util.find_spec("tomli") is not None and path.endswith(".toml"):
                import tomli

                try:
                    content = tomli.load(f)
                except tomli.TOMLDecodeError as e:
                    raise InvalidConfigFileError(e)
            else:
                raise InvalidConfigFileError(f"Unsupported file type: {path}")
    except FileNotFoundError:
        raise InvalidConfigFileError(f"File {path} not found")

    def wrap_value(nested_dict):
        if isinstance(nested_dict, dict):
            for key, value in nested_dict.items():
                nested_dict[key] = wrap_value(value)
            return nested_dict
        else:
            return Value(nested_dict, priority)

    return wrap_value(content)


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

        if i == 0 and args[i].startswith(CONFIG_FILE_SIGN):
            ## if we start with a config value we don't need a key name
            ## example python train.py @llama_7b.json
            config_name = args[i].removeprefix(CONFIG_FILE_SIGN)
            try:
                value = load_config_file(config_name, priority=0)
            except InvalidConfigFileError as e:
                raise CliError(
                    args_original,
                    [0],
                    f"Invalid config file [bold]{config_name}[/bold]. Original error: {e.original_error}",
                    [],
                )

            merged_args.update(value)
            i += 1

        if not potential_arg_name.startswith("--") and not potential_arg_name.startswith(CONFIG_FILE_SIGN):
            ## arg_name should start with "--" Example "--hello a"
            error_msg = "the first argument should start with '--'"
            suggestion_args[i] = "--" + potential_arg_name
            raise CliError(args_original, [i], error_msg, suggestion_args)

        if not potential_arg_name.startswith(CONFIG_FILE_SIGN):
            # once we have the arg name we look for the arg value
            arg_name = potential_arg_name

            # if we are at the end of the list, we assume the last value is a boolean
            if i == len(args) - 1:
                value = None
                increment = 1
            else:
                arg_value = args[i + 1]
                need_to_load_config_file = False

                if arg_value.startswith("--"):
                    ## Example "--hello --foo a". Hello is a bool here
                    value = None
                    increment = 1  # we want to analyse --foo next
                # elif arg_value == CONFIG_FILE_SIGN: # example " --hello @ config.json --foo"
                #     if i == len(args) - 1:
                #         raise CliError(args_original, [i], "Cannot end with @", [])
                #     else:
                #         value = args[i + 2]
                #         increment = 3 # we want to analyse --foo next
                #         need_to_load_config_file = True
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
            if isinstance(value, str) and value.startswith(CONFIG_FILE_SIGN):
                value = value.removeprefix(CONFIG_FILE_SIGN)
                need_to_load_config_file = True

            if need_to_load_config_file:
                try:
                    value = load_config_file(value, priority=0)
                except InvalidConfigFileError as e:
                    raise CliError(
                        args_original,
                        [i, i + 1],
                        f"Invalid config file [bold]{value.removeprefix(CONFIG_FILE_SIGN)}[/bold]. Original error: {e.original_error}",
                        [],
                    )
            else:
                value = Value(value, priority=1)  # command line are priority over config file

            parsed_arg = parse_nested_args(arg_name, value)

            def merge_dict(name, left, right):
                if name not in left.keys():
                    left[name] = right[name]
                else:
                    arg = left[name]
                    new_arg = right[name]
                    if isinstance(arg, Value):
                        if not isinstance(new_arg, Value):
                            raise CliError(args_original, [i], f"Conflicting value for {name}", [])

                        if not isinstance(new_arg.value, dict):
                            if isinstance(arg.value, dict):
                                raise CliError(args_original, [i], f"Conflicting value for {name}", [])
                            if new_arg.priority > arg.priority:
                                left[name] = new_arg
                            elif new_arg.priority < arg.priority:
                                ...
                            else:
                                # if we get mutiple non bool arg we put them into a list
                                if isinstance(arg.value, bool) or isinstance(new_arg.value, bool):
                                    raise CliError(args_original, [i], f"Conflicting boolean flag for {name}", [])
                                else:
                                    arg.value = [arg.value]

                                arg.value.append(new_arg.value)

                    elif isinstance(arg, dict):
                        if not isinstance(new_arg, dict):
                            raise CliError(args_original, [i], f"Conflicting boolean flag for {name}", [])

                        for nested_arg_name in right[name].keys():
                            merge_dict(nested_arg_name, left[name], right[name])
                    else:
                        # should never arrive here
                        raise ValueError()

            for name in parsed_arg.keys():
                merge_dict(name, merged_args, parsed_arg)

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
