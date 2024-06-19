from collections import defaultdict
from typing import Dict, List, TypeAlias
import sys

from pydantic_config.error import CliArgError, DuplicateKeyError

from pydantic_config.nested_dict import merge_nested_dict


NestedDict: TypeAlias = Dict[str, "NestedDict"]


def semi_parse_argv(argv: List[str]) -> Dict[str, str]:
    """
    this parse sys.argv into a dict of key value without any reduce.

    Example:

    >>> semi_parse_argv(["main.py","--hello", "world"]) == {"hello", "world"}

    it replace "_" with "-" as well and might raise CliArgError or CliValueError if
    cli argument are not passed correcltys

    """
    argv.pop(0)  # first argument beeing the name of the program

    semi_parse_arg = dict()

    while len(argv) > 0:
        arg_name = argv.pop(0)

        if not arg_name.startswith("--"):
            raise CliArgError(f"{arg_name} is not a valid argument, try {arg_name}")

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
            raise DuplicateKeyError(f"{arg_name_wo_trailing_dash} is duplicated")
        semi_parse_arg[arg_name_wo_trailing_dash] = value

    return semi_parse_arg


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
                nested_args[root_arg_name] = merge_nested_dict(
                    nested_args[root_arg_name], value_nested
                )
            else:
                nested_args[root_arg_name][nested_arg_name] = value

            del args[arg_name]

    return {**args, **nested_args}


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
    return parse_argv_as_list(list(sys.argv)) # need list otherwise it consume sys.argv for other tool like wandb
