# Pydantic Config

A drop-in replacement for `tyro.cli` with TOML/YAML/JSON config file support.

```python
# Instead of:
from tyro import cli

# Use:
from pydantic_config import cli
```

Built on top of [tyro](https://brentyi.github.io/tyro/) for type-safe CLI parsing and [Pydantic](https://docs.pydantic.dev/) for validation.

## Install

```bash
pip install git+https://github.com/samsja/pydantic_config
```

For TOML support (recommended):
```bash
pip install "pydantic_config[toml] @ git+https://github.com/samsja/pydantic_config"
```

## Quick Start

```python
from pydantic_config import cli, BaseConfig

class Config(BaseConfig):
    lr: float = 1e-4
    batch_size: int = 32
    seed: int = 42

if __name__ == "__main__":
    config = cli(Config)
    print(config)
```

Run it:
```bash
python train.py --lr 0.001 --batch-size 64
# Config(lr=0.001, batch_size=64, seed=42)
```

## Config Files with @ Syntax

Load config from TOML/YAML/JSON files using the `@` syntax:

```bash
# Load root config (with space after @)
python train.py @ config.toml

# Override specific values
python train.py @ config.toml --lr 0.001
```

Example `config.toml`:
```toml
lr = 0.0003
batch_size = 32
seed = 42
```

## Nested Configs

The real power comes with nested configurations - perfect for ML projects:

```python
from pydantic_config import cli, BaseConfig

class OptimizerConfig(BaseConfig):
    lr: float = 1e-4
    weight_decay: float = 0.01

class ModelConfig(BaseConfig):
    hidden_size: int = 256
    num_layers: int = 4

class TrainConfig(BaseConfig):
    model: ModelConfig = ModelConfig()
    optimizer: OptimizerConfig = OptimizerConfig()
    max_epochs: int = 100

if __name__ == "__main__":
    config = cli(TrainConfig)
```

### Loading Nested Configs from Files

Load specific nested configs from separate files:

```bash
# Load model config from file (with space)
python train.py --model @ model.toml --optimizer.lr 0.001

# Load model config from file (without space)
python train.py --model @model.toml --optimizer.lr 0.001

# Load multiple nested configs
python train.py --model @ model.toml --optimizer @ optimizer.toml

# Mix root config with nested overrides
python train.py @ base.toml --model @ model.toml --max-epochs 50
```

Example `model.toml`:
```toml
hidden_size = 512
num_layers = 8
```

### CLI Override Priority

CLI arguments always override config file values:

```bash
# config.toml has lr=0.0003
python train.py @ config.toml --lr 0.001
# Result: lr=0.001 (CLI wins)
```

## BaseConfig

`BaseConfig` is a Pydantic `BaseModel` with `extra="forbid"`:

```python
from pydantic_config import BaseConfig

class Config(BaseConfig):
    lr: float = 1e-4
```

You can also use regular Pydantic `BaseModel`:

```python
from pydantic import BaseModel
from pydantic_config import cli

class Config(BaseModel):
    lr: float = 1e-4

config = cli(Config)
```

## CLI Syntax

The CLI syntax follows tyro conventions:

```bash
# Basic arguments
python train.py --lr 0.001 --batch-size 64

# Nested arguments use dots
python train.py --model.hidden-size 512 --optimizer.lr 0.001

# Boolean flags
python train.py --verbose
python train.py --no-verbose

# Lists (tyro style)
python train.py --layers 64 128 256
```

### Config File Loading

```bash
# Root level (loads entire config)
python train.py @ config.toml

# Nested (loads into specific key)
python train.py --model @ model.toml
python train.py --model @model.toml  # also works without space
```

Supported formats: `.toml`, `.yaml`, `.yml`, `.json`

## Development

This project uses [uv](https://github.com/astral-sh/uv):

```bash
uv venv
uv sync --extra all
```

Run tests:
```bash
uv run pytest -v
```
