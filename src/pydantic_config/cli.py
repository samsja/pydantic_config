"""
CLI with TOML/YAML/JSON config file support.

Drop-in replacement for tyro.cli with config file support:
    # Instead of:
    from tyro import cli
    # Use:
    from pydantic_config import cli

Usage:
    from pydantic_config import cli, BaseConfig

    class Config(BaseConfig):
        lr: float = 1e-4
        batch_size: int = 32

    config = cli(Config)

Supports loading config files with @ syntax:
    python train.py @ config.toml --lr 1e-3
    python train.py --model @ model.toml --data @ data.toml
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import sys
import types
from typing import TypeVar, Union, get_args, get_origin, overload

import tyro
from tyro.conf import AvoidSubcommands
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseConfig(BaseModel):
    """Base configuration class with strict validation (extra fields forbidden)."""

    model_config = ConfigDict(extra="forbid")


CONFIG_FILE_SIGN = "@"


# ANSI color codes
_RESET = "\033[0m"
_RED = "\033[31m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_BRIGHT_RED = "\033[91m"


def _supports_color() -> bool:
    """Check if the terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not hasattr(sys.stderr, "isatty"):
        return False
    if not sys.stderr.isatty():
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True


def _colorize(text: str, *codes: str) -> str:
    """Apply ANSI color codes to text if colors are supported."""
    if not _supports_color():
        return text
    return "".join(codes) + text + _RESET


class ConfigFileError(Exception):
    """Error loading or parsing a config file."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _print_config_error_and_exit(error: ConfigFileError) -> None:
    """Print a config file error in a nice box format and exit."""
    width = min(80, max(40, shutil.get_terminal_size().columns))
    inner_width = width - 4  # Account for "│ " and " │"

    # Box drawing characters
    top_left, top_right = "╭", "╮"
    bot_left, bot_right = "╰", "╯"
    horiz, vert = "─", "│"

    def wrap_text(text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width, preserving leading indentation."""
        # Preserve leading whitespace
        stripped = text.lstrip()
        indent = text[: len(text) - len(stripped)]

        words = stripped.split()
        lines = []
        current_line = indent
        for word in words:
            if current_line == indent:
                current_line = indent + word
            elif len(current_line) + 1 + len(word) <= max_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = indent + word
        if current_line:
            lines.append(current_line)
        return lines or [indent]

    def box_line(content: str, visible_len: int | None = None) -> str:
        """Create a line inside the box with proper padding."""
        if visible_len is None:
            visible_len = len(content)
        padding = inner_width - visible_len
        return f"{_colorize(vert, _RED)} {content}{' ' * max(0, padding)} {_colorize(vert, _RED)}"

    # Build the error message content
    lines = []

    # Title line
    title = "Config file error"
    title_plain_len = 2 + len(title) + 1
    lines.append(
        _colorize(top_left, _RED)
        + f"{horiz} {_colorize(title, _RED, _BOLD)} "
        + _colorize(horiz * (width - title_plain_len - 2) + top_right, _RED)
    )

    # Content
    message = error.message
    if "Failed to validate config" in message:
        parts = message.split(": ", 1)
        if len(parts) == 2:
            # Source info line
            for line in wrap_text(parts[0] + ":", inner_width):
                lines.append(box_line(line))

            # Horizontal rule
            lines.append(box_line(_colorize(horiz * inner_width, _RED), inner_width))

            # Pydantic error details
            pydantic_lines = parts[1].split("\n")
            for pydantic_line in pydantic_lines:
                if not pydantic_line:
                    continue
                # First line (validation error count)
                if "validation error" in pydantic_line:
                    for wrapped in wrap_text(pydantic_line, inner_width):
                        lines.append(box_line(_colorize(wrapped, _BRIGHT_RED), len(wrapped)))
                # Field name (not indented)
                elif pydantic_line and not pydantic_line.startswith(" "):
                    text = f"  {pydantic_line}"
                    for wrapped in wrap_text(text, inner_width):
                        lines.append(box_line(_colorize(wrapped, _BOLD), len(wrapped)))
                # Error details (indented)
                elif pydantic_line.startswith("  "):
                    text = f"    {pydantic_line.strip()}"
                    for wrapped in wrap_text(text, inner_width):
                        lines.append(box_line(_colorize(wrapped, _DIM), len(wrapped)))
        else:
            for line in wrap_text(message, inner_width):
                lines.append(box_line(line))
    else:
        for line in wrap_text(message, inner_width):
            lines.append(box_line(line))

    # Bottom border
    lines.append(_colorize(f"{bot_left}{horiz * (width - 2)}{bot_right}", _RED))

    # Print to stderr
    for line in lines:
        print(line, file=sys.stderr)

    sys.exit(1)


def _load_config_file(path: str) -> dict:
    """Load a config file (JSON, YAML, or TOML) and return its contents as a dict."""
    try:
        with open(path, "rb") as f:
            if path.endswith(".json"):
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    raise ConfigFileError(f"Invalid JSON in {path}: {e}")

            elif path.endswith(".yaml") or path.endswith(".yml"):
                if importlib.util.find_spec("yaml") is None:
                    raise ConfigFileError(f"Cannot load {path}: pyyaml not installed. Install with: pip install pyyaml")
                import yaml

                try:
                    return yaml.load(f, Loader=yaml.FullLoader)
                except yaml.YAMLError as e:
                    raise ConfigFileError(f"Invalid YAML in {path}: {e}")

            elif path.endswith(".toml"):
                if importlib.util.find_spec("tomli") is None:
                    raise ConfigFileError(f"Cannot load {path}: tomli not installed. Install with: pip install tomli")
                import tomli

                try:
                    return tomli.load(f)
                except tomli.TOMLDecodeError as e:
                    raise ConfigFileError(f"Invalid TOML in {path}: {e}")

            else:
                raise ConfigFileError(f"Unsupported file type: {path}. Supported: .json, .yaml, .yml, .toml")
    except FileNotFoundError:
        raise ConfigFileError(f"Config file not found: {path}")


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts. Values from override take precedence."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _dict_to_instance(cls: type[T], data: dict) -> T:
    """Convert a dictionary to an instance of a Pydantic model."""
    if isinstance(cls, type) and issubclass(cls, BaseModel):
        return cls.model_validate(data)
    raise TypeError(f"Cannot convert dict to {cls}: not a Pydantic BaseModel")


def _process_args(args: list[str]) -> tuple[list[str], dict, dict[str, dict]]:
    """
    Process command line args to extract config file references.

    Returns:
        - remaining_args: args with config file refs removed (for tyro)
        - root_config: merged config from root-level @ files
        - nested_configs: dict mapping arg names to their loaded configs

    Supports:
        - `@ config.toml` (with space, root level)
        - `--model @ model.toml` (with space, nested)
        - `--model @model.toml` (without space, nested)
    """
    remaining_args = []
    root_config: dict = {}
    nested_configs: dict[str, dict] = {}

    i = 0
    while i < len(args):
        arg = args[i]

        # Root level config: `@ config.toml`
        if arg == CONFIG_FILE_SIGN:
            if i + 1 >= len(args):
                raise ConfigFileError("@ must be followed by a config file path")
            config_path = args[i + 1]
            loaded = _load_config_file(config_path)
            root_config = _deep_merge(root_config, loaded)
            i += 2
            continue

        # Handle --arg @ file.toml or --arg @file.toml
        if arg.startswith("--"):
            arg_name = arg[2:]  # Remove --

            # Check if next arg is @ (with space)
            if i + 1 < len(args) and args[i + 1] == CONFIG_FILE_SIGN:
                if i + 2 >= len(args):
                    raise ConfigFileError(f"@ after {arg} must be followed by a config file path")
                config_path = args[i + 2]
                loaded = _load_config_file(config_path)
                nested_configs[arg_name] = loaded
                i += 3
                continue

            # Check if next arg starts with @ (without space): --arg @file.toml
            if i + 1 < len(args) and args[i + 1].startswith(CONFIG_FILE_SIGN) and len(args[i + 1]) > 1:
                config_path = args[i + 1][1:]  # Remove @
                loaded = _load_config_file(config_path)
                nested_configs[arg_name] = loaded
                i += 2
                continue

        # Regular arg, keep it
        remaining_args.append(arg)
        i += 1

    return remaining_args, root_config, nested_configs


def _nest_config(key_path: str, config: dict) -> dict:
    """
    Nest a config dict under a dotted key path.

    Example:
        _nest_config("model.encoder", {"layers": 6})
        -> {"model": {"encoder": {"layers": 6}}}
    """
    parts = key_path.split(".")
    result = config
    for part in reversed(parts):
        result = {part: result}
    return result


def _build_default_from_config(cls: type[T], config: dict, config_path: str | None = None) -> T | None:
    """Build a default instance from config dict for tyro.

    Raises ConfigFileError if the config cannot be validated against the model.
    """
    if not config:
        return None
    try:
        return _dict_to_instance(cls, config)
    except Exception as e:
        source = f" from '{config_path}'" if config_path else ""
        raise ConfigFileError(f"Failed to validate config{source}: {e}") from e


def _is_optional_type(annotation: type) -> tuple[bool, type | None]:
    """Check if a type annotation is Optional[T] (i.e., T | None or Union[T, None]).

    Returns:
        A tuple of (is_optional, inner_type) where inner_type is the non-None type
        if it's optional, or None if not optional.
    """
    origin = get_origin(annotation)

    # Handle Union types (typing.Union) and Python 3.10+ union syntax (types.UnionType)
    # T | None uses types.UnionType in Python 3.10+, while Union[T, None] uses typing.Union
    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        non_none_args = [arg for arg in args if arg is not type(None)]
        # It's Optional if there's exactly one non-None type and None is present
        if len(non_none_args) == 1 and type(None) in args:
            return True, non_none_args[0]

    return False, None


def _get_optional_nested_fields(cls: type) -> dict[str, type]:
    """Get all fields that are Optional[SomeConfig] where SomeConfig is a BaseModel.

    Returns:
        A dict mapping field names to their non-None types.
    """
    optional_fields = {}

    if not (isinstance(cls, type) and issubclass(cls, BaseModel)):
        return optional_fields

    for field_name, field_info in cls.model_fields.items():
        annotation = field_info.annotation
        if annotation is None:
            continue

        is_optional, inner_type = _is_optional_type(annotation)
        if is_optional and inner_type is not None:
            # Check if inner_type is a BaseModel (nested config)
            if isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                optional_fields[field_name] = inner_type

    return optional_fields


def _find_referenced_optional_fields(args: list[str], optional_fields: dict[str, type]) -> set[str]:
    """Find which optional fields are referenced in the CLI args.

    Looks for patterns like --field.subfield or --field-name.subfield (with hyphens).

    Returns:
        Set of field names that are referenced in args.
    """
    referenced = set()

    for arg in args:
        if not arg.startswith("--"):
            continue

        # Remove the -- prefix
        arg_name = arg[2:]

        # Check each optional field
        for field_name in optional_fields:
            # tyro uses hyphens in CLI args, so check both forms
            field_with_hyphen = field_name.replace("_", "-")

            # Check if arg starts with field_name. (dot-separated nested access)
            if arg_name.startswith(f"{field_name}.") or arg_name.startswith(f"{field_with_hyphen}."):
                referenced.add(field_name)
                break

    return referenced


def _build_default_for_optional_fields(
    cls: type[T],
    referenced_fields: set[str],
    optional_fields: dict[str, type],
    existing_default: T | None = None,
) -> T | None:
    """Build a default instance with referenced optional fields populated.

    Args:
        cls: The config class
        referenced_fields: Set of field names that need non-None defaults
        optional_fields: Dict mapping field names to their non-None types
        existing_default: An existing default instance to build upon

    Returns:
        A default instance with the referenced optional fields populated.
    """
    if not referenced_fields:
        return existing_default

    # Start from existing default or create fresh dict
    if existing_default is not None:
        # Convert to dict to modify
        default_dict = existing_default.model_dump()
    else:
        default_dict = {}

    # For each referenced optional field, create a default instance if not already set
    for field_name in referenced_fields:
        if field_name not in default_dict or default_dict[field_name] is None:
            inner_type = optional_fields[field_name]
            # Create a default instance of the inner type
            default_dict[field_name] = inner_type()

    # Build the config instance
    try:
        return cls.model_validate(default_dict)
    except Exception:
        # If validation fails, return existing default
        return existing_default


@overload
def cli(cls: type[T]) -> T: ...


@overload
def cli(cls: type[T], *, args: list[str]) -> T: ...


@overload
def cli(cls: type[T], *, default: T) -> T: ...


@overload
def cli(cls: type[T], *, args: list[str], default: T) -> T: ...


def cli(
    cls: type[T],
    *,
    args: list[str] | None = None,
    default: T | None = None,
    prog: str | None = None,
    description: str | None = None,
) -> T:
    """
    Parse CLI arguments into a typed config object, with support for config files.

    Drop-in replacement for tyro.cli() with additional support for loading
    config files using the @ syntax:
        - `@ config.toml` - Load root-level config
        - `--model @ model.toml` - Load config nested under 'model'
        - `--model @model.toml` - Same as above (no space)

    Args:
        cls: The type to parse into (Pydantic BaseConfig or BaseModel)
        args: Command line args to parse (defaults to sys.argv[1:])
        default: Default instance to use for missing values
        prog: Program name for help text
        description: Description for help text

    Returns:
        Parsed and validated config object

    Example:
        class TrainConfig(BaseConfig):
            lr: float = 1e-4
            batch_size: int = 32

        class Config(BaseConfig):
            train: TrainConfig
            seed: int = 42

        # Can be called as:
        # python train.py @ config.toml --train.lr 1e-3
        # python train.py --train @ train.toml --seed 123

        config = cli(Config)
    """
    use_sys_argv = args is None
    if args is None:
        args = sys.argv[1:]

    try:
        # Process args to extract config files
        remaining_args, root_config, nested_configs = _process_args(args)

        # Merge all configs: root first, then nested configs
        merged_config = root_config
        for key_path, config in nested_configs.items():
            nested = _nest_config(key_path, config)
            merged_config = _deep_merge(merged_config, nested)

        # Build default from merged config
        config_default = None
        if merged_config:
            config_default = _build_default_from_config(cls, merged_config, config_path="merged config")

        # Merge with provided default
        final_default = default
        if config_default is not None:
            final_default = config_default

        # Handle Optional[Config] fields: detect if any are referenced in args
        # and build defaults for them so tyro doesn't require subcommand selection
        optional_fields = _get_optional_nested_fields(cls)
        if optional_fields:
            referenced_fields = _find_referenced_optional_fields(remaining_args, optional_fields)
            if referenced_fields:
                final_default = _build_default_for_optional_fields(
                    cls, referenced_fields, optional_fields, final_default
                )

        # Call tyro with processed args
        # Use AvoidSubcommands to prevent Optional[Config] from creating subcommands
        return tyro.cli(
            cls,
            args=remaining_args,
            default=final_default,
            prog=prog,
            description=description,
            config=(AvoidSubcommands,),
        )
    except ConfigFileError as e:
        # Only print formatted error when running from CLI (sys.argv)
        # When args are explicitly passed, re-raise for programmatic handling
        if use_sys_argv:
            _print_config_error_and_exit(e)
        raise
