from typing import Dict, List


class PydantiCliError(ValueError): ...


class CliArgError(PydantiCliError): ...


class CliValueError(PydantiCliError): ...


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
        print(argv)

        if not arg_name.startswith("--"):
            raise CliArgError(f"{arg_name} is not a valid argument, try {arg_name}")

        if len(argv) == 0:
            raise CliValueError(
                f"You are missing a value after --{arg_name} SOMETHING "
            )

        value = argv.pop(0)

        if value.startswith("-"):
            raise CliValueError(f"--{arg_name} {value} is not correct")

        arg_name = arg_name[2:]  # remove the leading --
        arg_name = arg_name.replace(
            "-", "_"
        )  # python variable name cannot have - inside, but it is commonly used in cli

        semi_parse_arg[arg_name] = value

    return semi_parse_arg


def parse_argv(argv: List[str]):
    """
    this function is used to parse the sys.argv and return dict (or nested dict)
    string representation of the arguments
    """

    args = semi_parse_argv(argv)
    return args
