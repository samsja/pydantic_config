"""Tests for the cli module."""

import os

import pytest

from pydantic_config import cli, BaseConfig, ConfigFileError
from pydantic_config.cli import (
    _deep_merge,
    _load_config_file,
    _nest_config,
    _process_args,
)


# Helpers


def write_file(path: str, content: str):
    with open(path, "w") as f:
        f.write(content)


# Fixtures


@pytest.fixture
def tmp_toml_file(tmp_path):
    return os.path.join(tmp_path, "config.toml")


@pytest.fixture
def tmp_json_file(tmp_path):
    return os.path.join(tmp_path, "config.json")


@pytest.fixture
def tmp_yaml_file(tmp_path):
    return os.path.join(tmp_path, "config.yaml")


# Config classes


class SimpleConfig(BaseConfig):
    name: str = "default"
    count: int = 0


class NestedInner(BaseConfig):
    lr: float = 1e-4
    batch_size: int = 32


class NestedConfig(BaseConfig):
    train: NestedInner = NestedInner()
    seed: int = 42


class DeepNestedInner(BaseConfig):
    hidden_size: int = 256
    num_layers: int = 4


class DeepNestedMiddle(BaseConfig):
    encoder: DeepNestedInner = DeepNestedInner()
    decoder: DeepNestedInner = DeepNestedInner()


class DeepNestedConfig(BaseConfig):
    model: DeepNestedMiddle = DeepNestedMiddle()
    train: NestedInner = NestedInner()
    name: str = "experiment"


# Tests: _load_config_file


def test_load_json(tmp_json_file):
    write_file(tmp_json_file, '{"name": "test", "count": 5}')
    result = _load_config_file(tmp_json_file)
    assert result == {"name": "test", "count": 5}


def test_load_toml(tmp_toml_file):
    write_file(tmp_toml_file, 'name = "test"\ncount = 5')
    result = _load_config_file(tmp_toml_file)
    assert result == {"name": "test", "count": 5}


def test_load_yaml(tmp_yaml_file):
    write_file(tmp_yaml_file, "name: test\ncount: 5")
    result = _load_config_file(tmp_yaml_file)
    assert result == {"name": "test", "count": 5}


def test_load_file_not_found():
    with pytest.raises(ConfigFileError, match="not found"):
        _load_config_file("/nonexistent/file.toml")


def test_load_invalid_json(tmp_json_file):
    write_file(tmp_json_file, '{"invalid json')
    with pytest.raises(ConfigFileError, match="Invalid JSON"):
        _load_config_file(tmp_json_file)


def test_load_invalid_toml(tmp_toml_file):
    write_file(tmp_toml_file, "invalid = [toml")
    with pytest.raises(ConfigFileError, match="Invalid TOML"):
        _load_config_file(tmp_toml_file)


def test_load_unsupported_extension(tmp_path):
    txt_file = os.path.join(tmp_path, "config.txt")
    write_file(txt_file, "some content")
    with pytest.raises(ConfigFileError, match="Unsupported file type"):
        _load_config_file(txt_file)


# Tests: _deep_merge


def test_deep_merge_simple():
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_nested():
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    override = {"a": {"y": 20, "z": 30}}
    result = _deep_merge(base, override)
    assert result == {"a": {"x": 1, "y": 20, "z": 30}, "b": 3}


def test_deep_merge_deep_nested():
    base = {"a": {"b": {"c": 1, "d": 2}}}
    override = {"a": {"b": {"d": 20, "e": 30}}}
    result = _deep_merge(base, override)
    assert result == {"a": {"b": {"c": 1, "d": 20, "e": 30}}}


# Tests: _nest_config


def test_nest_config_single_level():
    result = _nest_config("model", {"layers": 6})
    assert result == {"model": {"layers": 6}}


def test_nest_config_multi_level():
    result = _nest_config("model.encoder", {"layers": 6})
    assert result == {"model": {"encoder": {"layers": 6}}}


def test_nest_config_deep():
    result = _nest_config("a.b.c.d", {"value": 1})
    assert result == {"a": {"b": {"c": {"d": {"value": 1}}}}}


# Tests: _process_args


def test_process_args_no_config_files():
    args = ["--name", "test", "--count", "5"]
    remaining, root, nested = _process_args(args)
    assert remaining == ["--name", "test", "--count", "5"]
    assert root == {}
    assert nested == {}


def test_process_args_root_config_with_space(tmp_toml_file):
    write_file(tmp_toml_file, 'name = "from_file"')
    args = ["@", tmp_toml_file, "--count", "5"]
    remaining, root, nested = _process_args(args)
    assert remaining == ["--count", "5"]
    assert root == {"name": "from_file"}
    assert nested == {}


def test_process_args_nested_config_with_space(tmp_toml_file):
    write_file(tmp_toml_file, "lr = 0.001\nbatch_size = 64")
    args = ["--train", "@", tmp_toml_file, "--seed", "123"]
    remaining, root, nested = _process_args(args)
    assert remaining == ["--seed", "123"]
    assert root == {}
    assert nested == {"train": {"lr": 0.001, "batch_size": 64}}


def test_process_args_nested_config_without_space(tmp_toml_file):
    write_file(tmp_toml_file, "lr = 0.001\nbatch_size = 64")
    args = ["--train", f"@{tmp_toml_file}", "--seed", "123"]
    remaining, root, nested = _process_args(args)
    assert remaining == ["--seed", "123"]
    assert root == {}
    assert nested == {"train": {"lr": 0.001, "batch_size": 64}}


def test_process_args_multiple_nested_configs(tmp_path):
    train_file = os.path.join(tmp_path, "train.toml")
    model_file = os.path.join(tmp_path, "model.toml")
    write_file(train_file, "lr = 0.001")
    write_file(model_file, "hidden_size = 512")

    args = ["--train", "@", train_file, "--model", "@", model_file]
    remaining, root, nested = _process_args(args)
    assert remaining == []
    assert nested == {"train": {"lr": 0.001}, "model": {"hidden_size": 512}}


def test_process_args_deeply_nested_key(tmp_toml_file):
    write_file(tmp_toml_file, "hidden_size = 512")
    args = ["--model.encoder", "@", tmp_toml_file]
    remaining, root, nested = _process_args(args)
    assert remaining == []
    assert nested == {"model.encoder": {"hidden_size": 512}}


# Tests: cli basic


def test_cli_simple_args():
    config = cli(SimpleConfig, args=["--name", "test", "--count", "5"])
    assert config.name == "test"
    assert config.count == 5


def test_cli_defaults():
    config = cli(SimpleConfig, args=[])
    assert config.name == "default"
    assert config.count == 0


def test_cli_partial_override():
    config = cli(SimpleConfig, args=["--count", "10"])
    assert config.name == "default"
    assert config.count == 10


# Tests: cli with config files


def test_cli_root_config_file(tmp_toml_file):
    write_file(tmp_toml_file, 'name = "from_toml"\ncount = 99')
    config = cli(SimpleConfig, args=["@", tmp_toml_file])
    assert config.name == "from_toml"
    assert config.count == 99


def test_cli_root_config_with_override(tmp_toml_file):
    write_file(tmp_toml_file, 'name = "from_toml"\ncount = 99')
    config = cli(SimpleConfig, args=["@", tmp_toml_file, "--count", "1"])
    assert config.name == "from_toml"
    assert config.count == 1


def test_cli_nested_config_with_space(tmp_toml_file):
    write_file(tmp_toml_file, "lr = 0.001\nbatch_size = 64")
    config = cli(NestedConfig, args=["--train", "@", tmp_toml_file])
    assert config.train.lr == 0.001
    assert config.train.batch_size == 64
    assert config.seed == 42


def test_cli_nested_config_without_space(tmp_toml_file):
    write_file(tmp_toml_file, "lr = 0.001\nbatch_size = 64")
    config = cli(NestedConfig, args=["--train", f"@{tmp_toml_file}"])
    assert config.train.lr == 0.001
    assert config.train.batch_size == 64


def test_cli_nested_config_with_override(tmp_toml_file):
    write_file(tmp_toml_file, "lr = 0.001\nbatch_size = 64")
    config = cli(NestedConfig, args=["--train", "@", tmp_toml_file, "--train.lr", "0.1"])
    assert config.train.lr == 0.1
    assert config.train.batch_size == 64


def test_cli_json_config(tmp_json_file):
    write_file(tmp_json_file, '{"name": "from_json", "count": 42}')
    config = cli(SimpleConfig, args=["@", tmp_json_file])
    assert config.name == "from_json"
    assert config.count == 42


def test_cli_yaml_config(tmp_yaml_file):
    write_file(tmp_yaml_file, "name: from_yaml\ncount: 77")
    config = cli(SimpleConfig, args=["@", tmp_yaml_file])
    assert config.name == "from_yaml"
    assert config.count == 77


# Tests: cli deep nesting


def test_cli_deep_nested_config(tmp_path):
    encoder_file = os.path.join(tmp_path, "encoder.toml")
    write_file(encoder_file, "hidden_size = 512\nnum_layers = 8")

    config = cli(DeepNestedConfig, args=["--model.encoder", "@", encoder_file])
    assert config.model.encoder.hidden_size == 512
    assert config.model.encoder.num_layers == 8
    assert config.model.decoder.hidden_size == 256
    assert config.model.decoder.num_layers == 4


def test_cli_multiple_nested_configs(tmp_path):
    encoder_file = os.path.join(tmp_path, "encoder.toml")
    train_file = os.path.join(tmp_path, "train.toml")
    write_file(encoder_file, "hidden_size = 512\nnum_layers = 8")
    write_file(train_file, "lr = 0.0001\nbatch_size = 128")

    config = cli(
        DeepNestedConfig,
        args=["--model.encoder", "@", encoder_file, "--train", "@", train_file],
    )
    assert config.model.encoder.hidden_size == 512
    assert config.model.encoder.num_layers == 8
    assert config.train.lr == 0.0001
    assert config.train.batch_size == 128


def test_cli_root_and_nested_config(tmp_path):
    root_file = os.path.join(tmp_path, "root.toml")
    encoder_file = os.path.join(tmp_path, "encoder.toml")
    write_file(root_file, 'name = "experiment_1"')
    write_file(encoder_file, "hidden_size = 1024")

    config = cli(
        DeepNestedConfig,
        args=["@", root_file, "--model.encoder", "@", encoder_file],
    )
    assert config.name == "experiment_1"


# Tests: error handling


def test_cli_missing_config_file():
    with pytest.raises(ConfigFileError, match="not found"):
        cli(SimpleConfig, args=["@", "/nonexistent/config.toml"])


def test_cli_invalid_config_file(tmp_toml_file):
    write_file(tmp_toml_file, "invalid = [toml")
    with pytest.raises(ConfigFileError, match="Invalid TOML"):
        cli(SimpleConfig, args=["@", tmp_toml_file])


def test_cli_missing_file_after_at():
    with pytest.raises(ConfigFileError, match="must be followed"):
        cli(SimpleConfig, args=["@"])


def test_cli_discriminated_union_missing_type_uses_default(tmp_toml_file):
    """Test that missing discriminator field is auto-injected from default."""
    from typing import Annotated, Literal

    from pydantic import Field

    class DataConfigA(BaseConfig):
        type: Literal["a"] = "a"
        value: int = 1

    class DataConfigB(BaseConfig):
        type: Literal["b"] = "b"
        value: int = 2

    class ConfigWithUnion(BaseConfig):
        data: Annotated[DataConfigA | DataConfigB, Field(discriminator="type")] = DataConfigA()

    # Config file missing the 'type' discriminator - should use default "a"
    write_file(tmp_toml_file, "[data]\nvalue = 100")

    config = cli(ConfigWithUnion, args=["@", tmp_toml_file])
    assert config.data.type == "a"
    assert config.data.value == 100


def test_cli_discriminated_union_with_type(tmp_toml_file):
    """Test that discriminated union works when type field is provided."""
    from typing import Annotated, Literal
    from pydantic import Field

    class DataConfigA(BaseConfig):
        type: Literal["a"] = "a"
        value: int = 1

    class DataConfigB(BaseConfig):
        type: Literal["b"] = "b"
        value: int = 2

    class ConfigWithUnion(BaseConfig):
        data: Annotated[DataConfigA | DataConfigB, Field(discriminator="type")] = DataConfigA()

    # Config file with the required 'type' discriminator
    write_file(tmp_toml_file, '[data]\ntype = "b"\nvalue = 100')

    config = cli(ConfigWithUnion, args=["@", tmp_toml_file])
    assert config.data.type == "b"
    assert config.data.value == 100


def test_cli_discriminated_union_switch_variant_via_cli():
    """Test that discriminated union variant can be switched via CLI args (no config file)."""
    from typing import Annotated, Literal

    from pydantic import Field

    class DataConfigA(BaseConfig):
        type: Literal["a"] = "a"
        value: int = 1

    class DataConfigB(BaseConfig):
        type: Literal["b"] = "b"
        value: int = 2
        extra: int = 99

    class ConfigWithUnion(BaseConfig):
        data: Annotated[DataConfigA | DataConfigB, Field(discriminator="type")] = DataConfigA()
        name: str = "hello"

    config = cli(ConfigWithUnion, args=["--data.type", "b", "--data.extra", "42", "--name", "world"])
    assert config.data.type == "b"
    assert config.data.extra == 42
    assert config.name == "world"


# Tests: BaseConfig validators


def test_none_str_to_none():
    class ConfigWithOptional(BaseConfig):
        name: str | None = "default"

    config = cli(ConfigWithOptional, args=["--name", "None"])
    assert config.name is None


def test_none_str_to_none_in_toml(tmp_toml_file):
    class ConfigWithOptional(BaseConfig):
        name: str | None = "default"

    write_file(tmp_toml_file, 'name = "None"')
    config = cli(ConfigWithOptional, args=["@", tmp_toml_file])
    assert config.name is None


def test_none_str_passes_regular_values():
    class ConfigWithOptional(BaseConfig):
        name: str | None = "default"

    config = cli(ConfigWithOptional, args=["--name", "hello"])
    assert config.name == "hello"


def test_discriminator_type_injected_from_default(tmp_toml_file):
    """When a TOML file overrides a discriminated union field without specifying 'type',
    the default type tag should be injected automatically."""
    from typing import Annotated, Literal

    from pydantic import Field

    class DataConfigA(BaseConfig):
        type: Literal["a"] = "a"
        value: int = 1

    class DataConfigB(BaseConfig):
        type: Literal["b"] = "b"
        value: int = 2

    class ConfigWithUnion(BaseConfig):
        data: Annotated[DataConfigA | DataConfigB, Field(discriminator="type")] = DataConfigA()

    write_file(tmp_toml_file, "[data]\nvalue = 100")
    config = cli(ConfigWithUnion, args=["@", tmp_toml_file])
    assert config.data.type == "a"
    assert config.data.value == 100


def test_discriminator_type_explicit_overrides_default(tmp_toml_file):
    """When the TOML file explicitly provides a 'type', it should be used."""
    from typing import Annotated, Literal

    from pydantic import Field

    class DataConfigA(BaseConfig):
        type: Literal["a"] = "a"
        value: int = 1

    class DataConfigB(BaseConfig):
        type: Literal["b"] = "b"
        value: int = 2

    class ConfigWithUnion(BaseConfig):
        data: Annotated[DataConfigA | DataConfigB, Field(discriminator="type")] = DataConfigA()

    write_file(tmp_toml_file, '[data]\ntype = "b"\nvalue = 100')
    config = cli(ConfigWithUnion, args=["@", tmp_toml_file])
    assert config.data.type == "b"
    assert config.data.value == 100


# Tests: bare flags for Optional[BaseModel] fields


def test_bare_flag_enables_optional_config():
    """--compile as a bare flag should enable CompileConfig with defaults."""

    class CompileConfig(BaseConfig):
        fullgraph: bool = False

    class Config(BaseConfig):
        compile: CompileConfig | None = None
        name: str = "test"

    config = cli(Config, args=["--compile", "--name", "hello"])
    assert config.compile is not None
    assert config.compile.fullgraph is False
    assert config.name == "hello"


def test_bare_flag_at_end_of_args():
    """--compile at end of args should still work."""

    class CompileConfig(BaseConfig):
        fullgraph: bool = False

    class Config(BaseConfig):
        name: str = "test"
        compile: CompileConfig | None = None

    config = cli(Config, args=["--name", "hello", "--compile"])
    assert config.compile is not None
    assert config.name == "hello"


def test_bare_flag_nested_path():
    """--model.compile should work for nested Optional configs."""

    class CompileConfig(BaseConfig):
        fullgraph: bool = False

    class ModelConfig(BaseConfig):
        compile: CompileConfig | None = None
        name: str = "default"

    class Config(BaseConfig):
        model: ModelConfig = ModelConfig()

    config = cli(Config, args=["--model.compile", "--model.name", "mymodel"])
    assert config.model.compile is not None
    assert config.model.compile.fullgraph is False
    assert config.model.name == "mymodel"


def test_bare_flag_with_sub_field_override_via_toml(tmp_toml_file):
    """Sub-field overrides for Optional configs are best done via TOML."""

    class CompileConfig(BaseConfig):
        fullgraph: bool = False

    class ModelConfig(BaseConfig):
        compile: CompileConfig | None = None

    class Config(BaseConfig):
        model: ModelConfig = ModelConfig()

    write_file(tmp_toml_file, "[model.compile]\nfullgraph = true")
    config = cli(Config, args=["@", tmp_toml_file])
    assert config.model.compile is not None
    assert config.model.compile.fullgraph is True


def test_bare_flag_multiple_optional_configs():
    """Multiple bare flags should all work."""

    class ACConfig(BaseConfig):
        freq: int = 1

    class CompileConfig(BaseConfig):
        fullgraph: bool = False

    class ModelConfig(BaseConfig):
        ac: ACConfig | None = None
        compile: CompileConfig | None = None

    class Config(BaseConfig):
        model: ModelConfig = ModelConfig()

    config = cli(Config, args=["--model.compile", "--model.ac"])
    assert config.model.compile is not None
    assert config.model.ac is not None
    assert config.model.ac.freq == 1


def test_bare_flag_kebab_case():
    """--model.ac-offloading should work (kebab-case for snake_case field)."""

    class OffloadConfig(BaseConfig):
        pin_memory: bool = True

    class ModelConfig(BaseConfig):
        ac_offloading: OffloadConfig | None = None

    class Config(BaseConfig):
        model: ModelConfig = ModelConfig()

    config = cli(Config, args=["--model.ac-offloading"])
    assert config.model.ac_offloading is not None
    assert config.model.ac_offloading.pin_memory is True


def test_optional_config_none_by_default():
    """Without the bare flag, Optional config should remain None."""

    class CompileConfig(BaseConfig):
        fullgraph: bool = False

    class Config(BaseConfig):
        compile: CompileConfig | None = None
        name: str = "test"

    config = cli(Config, args=["--name", "hello"])
    assert config.compile is None


def test_optional_sub_field_override():
    """--wandb.project foo should implicitly enable the optional wandb config."""

    class WandbConfig(BaseConfig):
        project: str = "default"
        name: str = "run"

    class Config(BaseConfig):
        wandb: WandbConfig | None = None
        seed: int = 42

    config = cli(Config, args=["--wandb.project", "my-project", "--wandb.name", "my-run"])
    assert config.wandb is not None
    assert config.wandb.project == "my-project"
    assert config.wandb.name == "my-run"


def test_optional_sub_field_nested():
    """--model.compile.fullgraph True should work for deeply nested optional configs."""

    class CompileConfig(BaseConfig):
        fullgraph: bool = False
        dynamic: bool = True

    class ModelConfig(BaseConfig):
        compile: CompileConfig | None = None
        name: str = "default"

    class Config(BaseConfig):
        model: ModelConfig = ModelConfig()

    config = cli(Config, args=["--model.compile.fullgraph", "True"])
    assert config.model.compile is not None
    assert config.model.compile.fullgraph is True
    assert config.model.compile.dynamic is True


def test_optional_sub_field_with_bare_flag_and_regular_args():
    """Mixing sub-field overrides with regular args should work."""

    class WandbConfig(BaseConfig):
        project: str = "default"

    class Config(BaseConfig):
        wandb: WandbConfig | None = None
        name: str = "test"
        seed: int = 42

    config = cli(Config, args=["--name", "hello", "--wandb.project", "proj", "--seed", "123"])
    assert config.name == "hello"
    assert config.seed == 123
    assert config.wandb is not None
    assert config.wandb.project == "proj"


# Tests: dict[str, Any] fields (handled via config files, not CLI)


def test_dict_any_field_with_default(tmp_toml_file):
    """dict[str, Any] fields should work when a default is provided via config file."""
    from typing import Any

    class SamplingConfig(BaseConfig):
        temperature: float = 1.0
        extra_body: dict[str, Any] = {}

    class Config(BaseConfig):
        sampling: SamplingConfig = SamplingConfig()
        name: str = "test"

    write_file(tmp_toml_file, '[sampling]\ntemperature = 0.5')
    config = cli(Config, args=["@", tmp_toml_file, "--name", "hello"])
    assert config.sampling.temperature == 0.5
    assert config.sampling.extra_body == {}
    assert config.name == "hello"


def test_dict_any_field_set_via_toml(tmp_toml_file):
    """dict[str, Any] fields should be settable via config files."""
    from typing import Any

    class EnvConfig(BaseConfig):
        id: str = "default"
        extra_kwargs: dict[str, Any] = {}

    class Config(BaseConfig):
        env: EnvConfig = EnvConfig()

    write_file(tmp_toml_file, '[env]\nid = "custom"\n\n[env.extra_kwargs]\nseq_len = 512\nverbose = true')
    config = cli(Config, args=["@", tmp_toml_file])
    assert config.env.id == "custom"
    assert config.env.extra_kwargs == {"seq_len": 512, "verbose": True}


def test_dict_any_in_discriminated_union(tmp_toml_file):
    """dict[str, Any] in a non-default discriminated union variant should not crash."""
    from typing import Annotated, Any, Literal, TypeAlias

    from pydantic import Field

    class DefaultMode(BaseConfig):
        type: Literal["default"] = "default"
        scale: float = 1.0

    class CustomMode(BaseConfig):
        type: Literal["custom"] = "custom"
        import_path: str = "my_module.fn"
        kwargs: dict[str, Any] = {}

    ModeConfig: TypeAlias = Annotated[DefaultMode | CustomMode, Field(discriminator="type")]

    class Config(BaseConfig):
        mode: ModeConfig = DefaultMode()
        name: str = "test"

    # Default mode works without touching the dict field
    config = cli(Config, args=["--name", "hello"])
    assert config.mode.type == "default"

    # Custom mode via TOML with dict kwargs
    write_file(tmp_toml_file, '[mode]\ntype = "custom"\nimport_path = "my.fn"\n\n[mode.kwargs]\nalpha = 0.5')
    config = cli(Config, args=["@", tmp_toml_file])
    assert config.mode.type == "custom"
    assert config.mode.kwargs == {"alpha": 0.5}


# Tests: dict[str, Any] fields via JSON CLI args


def test_dict_field_via_json_cli():
    """--extra-kwargs '{"key": 123}' should parse JSON and set the dict field."""
    from typing import Any

    class Config(BaseConfig):
        extra_kwargs: dict[str, Any] = {}
        name: str = "test"

    config = cli(Config, args=["--extra-kwargs", '{"sandbox_client_max_workers": 128}', "--name", "hello"])
    assert config.extra_kwargs == {"sandbox_client_max_workers": 128}
    assert config.name == "hello"


def test_dict_field_via_json_cli_nested():
    """JSON dict args should work for nested config fields."""
    from typing import Any

    class EnvConfig(BaseConfig):
        id: str = "default"
        extra_env_kwargs: dict[str, Any] = {}

    class Config(BaseConfig):
        env: EnvConfig = EnvConfig()

    config = cli(Config, args=["--env.extra-env-kwargs", '{"timeout": 60, "verbose": true}'])
    assert config.env.extra_env_kwargs == {"timeout": 60, "verbose": True}


def test_dict_field_via_json_cli_with_toml(tmp_toml_file):
    """JSON dict CLI args should merge with TOML dict values."""
    from typing import Any

    class Config(BaseConfig):
        extra: dict[str, Any] = {}
        name: str = "test"

    write_file(tmp_toml_file, 'name = "from-toml"\n\n[extra]\nold_key = "old_value"')
    config = cli(Config, args=["@", tmp_toml_file, "--extra", '{"new_key": "new_value"}'])
    assert config.extra == {"old_key": "old_value", "new_key": "new_value"}
    assert config.name == "from-toml"


# Tests: real-world scenarios


def test_ml_training_config(tmp_path):
    """Simulate a typical ML training configuration."""

    class OptimizerConfig(BaseConfig):
        lr: float = 1e-4
        weight_decay: float = 0.01

    class ModelConfig(BaseConfig):
        hidden_size: int = 256
        num_layers: int = 4
        dropout: float = 0.1

    class DataConfig(BaseConfig):
        batch_size: int = 32
        num_workers: int = 4

    class TrainConfig(BaseConfig):
        model: ModelConfig = ModelConfig()
        optimizer: OptimizerConfig = OptimizerConfig()
        data: DataConfig = DataConfig()
        seed: int = 42
        max_epochs: int = 100

    model_file = os.path.join(tmp_path, "model.toml")
    optim_file = os.path.join(tmp_path, "optimizer.toml")

    write_file(model_file, "hidden_size = 512\nnum_layers = 8\ndropout = 0.2")
    write_file(optim_file, "lr = 0.001\nweight_decay = 0.1")

    config = cli(
        TrainConfig,
        args=[
            "--model", "@", model_file,
            "--optimizer", "@", optim_file,
            "--data.batch-size", "64",
            "--max-epochs", "50",
        ],
    )

    assert config.model.hidden_size == 512
    assert config.model.num_layers == 8
    assert config.model.dropout == 0.2
    assert config.optimizer.lr == 0.001
    assert config.optimizer.weight_decay == 0.1
    assert config.data.batch_size == 64
    assert config.max_epochs == 50
    assert config.seed == 42


def test_override_nested_in_config_file(tmp_toml_file):
    """Test that CLI args can override specific nested fields from config."""

    class InnerConfig(BaseConfig):
        a: int = 1
        b: int = 2
        c: int = 3

    class OuterConfig(BaseConfig):
        inner: InnerConfig = InnerConfig()
        name: str = "test"

    write_file(tmp_toml_file, "a = 10\nb = 20\nc = 30")

    config = cli(OuterConfig, args=["--inner", "@", tmp_toml_file, "--inner.b", "200"])

    assert config.inner.a == 10
    assert config.inner.b == 200
    assert config.inner.c == 30
