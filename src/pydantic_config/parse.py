from collections import defaultdict
import json
from typing import Dict, List, TypeAlias
import sys

from rich import print as rich_print

from pydantic_config._ui import _get_error_panel


class PydantiCliError(ValueError): ...


class CliArgError(PydantiCliError): ...


class CliValueError(PydantiCliError): ...


class DuplicateKeyError(PydantiCliError): ...


NestedDict: TypeAlias = Dict[str, "NestedDict"]

CONFIG_FILE_SYMBOL = "@"


def merge_nested_dict(left_dict: NestedDict, right_dict: NestedDict) -> NestedDict:
    """
    this function take two nested dict and merge them together.
    """

    if not isinstance(left_dict, dict) or not isinstance(right_dict, dict):
        raise TypeError("left_dict and right_dict must be dict")

    shared_key = [key for key in left_dict.keys() if key in right_dict.keys()]

    current_dict_non_shared = {k: v for k, v in left_dict.items() if k not in shared_key}
    new_branch_non_shared = {k: v for k, v in right_dict.items() if k not in shared_key}

    merged_dict = {**current_dict_non_shared, **new_branch_non_shared}

    for key in shared_key:
        if not isinstance(left_dict[key], dict) or not isinstance(right_dict[key], dict):
            raise DuplicateKeyError(f"{key} is duplicated")

        merged_dict[key] = merge_nested_dict(left_dict[key], right_dict[key])

    return merged_dict


def load_config_file(file_path: str) -> NestedDict:
    """
    take a file path load the content into a python dict.

    For now expect the file to be a json file.

    Later will add yaml and toml support.
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise CliValueError(f"File {file_path} not found")
    except json.JSONDecodeError:
        raise CliValueError(f"Error when parsing {file_path} as json")


def semi_parse_argv(argv: List[str]) -> Dict[str, str]:
    """
    this parse sys.argv into a dict of key value without any reduce.

    Example:

    >>> semi_parse_argv(["main.py","--hello", "world"]) == {"hello", "world"}

    it replace "_" with "-" as well and might raise CliArgError or CliValueError if
    cli argument are not passed correcltys
    """

    argv_copy = argv.copy()

    argv.pop(0)  # first argument beeing the name of the program

    semi_parse_arg = dict()

    while len(argv) > 0:
        arg_name = argv.pop(0)

        if not arg_name.startswith("--"):
            cli_passed = "python " + " ".join(argv_copy)
            if arg_name.startswith("-"):
                arg_suggestion = arg_name.replace("-", "--")
            else:
                arg_suggestion = f"--{arg_name}"

            bold_arg_name = f"[bold]{arg_suggestion}[/bold]"
            cli_suggestion = cli_passed.replace(arg_name, bold_arg_name)
            raise CliArgError(f"{arg_name} is not a valid. You should try: \n \n{cli_suggestion}")

        if len(argv) == 0:  # if we end with smth like python cmd.py ---aa a --hello
            bool_arg = True
        else:
            bool_arg = argv[0].startswith("--")

        if bool_arg:
            if arg_name.startswith("--no-"):
                value = False
                arg_name = arg_name.replace("--no-", "--")
            else:
                value = True

        else:
            value = argv.pop(0)

        arg_name_wo_trailing_dash = arg_name[2:]  # remove the leading --
        arg_name_wo_trailing_dash = arg_name_wo_trailing_dash.replace("-", "_")
        # python variable name cannot have - inside, but it is commonly used in cli

        if arg_name_wo_trailing_dash in semi_parse_arg:
            if isinstance(semi_parse_arg[arg_name_wo_trailing_dash], list):
                semi_parse_arg[arg_name_wo_trailing_dash].append(value)
            else:
                semi_parse_arg[arg_name_wo_trailing_dash] = [semi_parse_arg[arg_name_wo_trailing_dash], value]
        else:
            semi_parse_arg[arg_name_wo_trailing_dash] = value

    return semi_parse_arg


def merge_args_and_load_config(args: Dict[str, str], nested_args: NestedDict) -> NestedDict:
    """
    handle merging of top lever args and nested args.
    Optionaly load config file if necessary.

    cli override config file. Otherwise conflict will raise an error.
    """
    # assert interesction of the keyu of args and nested_args is null
    conflicting_keys = list(set(args.keys()) & set(nested_args.keys()))
    if conflicting_keys:
        for conflicting_key in conflicting_keys:
            if args[conflicting_key].startswith(CONFIG_FILE_SYMBOL):
                args_from_config = load_config_file(args[conflicting_key][len(CONFIG_FILE_SYMBOL) :])
                args_from_cli = nested_args[conflicting_key]
                args_from_config.update(args_from_cli)

                del args[conflicting_key]
                nested_args[conflicting_key] = args_from_config
            else:
                first_arg_name = list(nested_args[conflicting_key].keys())[0]
                raise CliArgError(
                    f"Conflicting argument: {conflicting_key}. You cannot use both --{conflicting_key} and --{conflicting_key}.{first_arg_name} at the same time"
                )
    for key in list(args.keys()):  # list because we might edit the dict
        if isinstance(args[key], str) and args[key].startswith(CONFIG_FILE_SYMBOL):
            args[key] = load_config_file(args[key][len(CONFIG_FILE_SYMBOL) :])

    return {**args, **nested_args}


def parse_nested_arg(args: Dict[str, str]) -> NestedDict:
    """
    take a dict, extract key that contain "." and create a nested dict inside the arg.

    Example:

    >>> parse_nested_arg({"hello.world": "foo"}) == {"hello": {"world": "foo"}}
    """
    nested_args = defaultdict(dict)

    for arg_name, value in list(args.items()):  # we need list because we modify args
        if "." in arg_name:
            splits = arg_name.split(".")

            if any(part == "" for part in splits):
                raise CliArgError(f"{arg_name} is not a valid")
            root_arg_name = splits[0]

            nested_arg_name = splits[1]

            if len(splits[1:]) > 1:  # if there is more than one nested level
                value_nested = parse_nested_arg({".".join(splits[1:]): value})
                nested_args[root_arg_name] = merge_nested_dict(nested_args[root_arg_name], value_nested)
            else:
                nested_args[root_arg_name][nested_arg_name] = value

            del args[arg_name]

    return merge_args_and_load_config(args, nested_args)


def parse_argv_as_list(argv: List[str]) -> NestedDict:
    """
    this function is used to parse the sys.argv and return dict (or nested dict)
    string representation of the arguments.
    """
    return parse_nested_arg(semi_parse_argv(argv))


def parse_argv() -> NestedDict:
    """
    Parse argument from argv and return a nested dict of string arguments that can be
    used to instantiate a pydantic model.
    """
    try:
        return parse_argv_as_list(list(sys.argv))  # need list otherwise it consume sys.argv for other tool like wandb
    except CliArgError as e:
        msg = f"[white]{e}[/white]"
        panel = _get_error_panel(msg, 1)
        rich_print(panel)
        sys.exit(1)
