# Pydantic config

Pydantic is a dead simple config manager that built on top of pydantic.

It can parse some configuration either from cli or from a yaml/json/toml file and validate it against a pydantic model.

## Install

```bash
pip install git+https://github.com/samsja/pydantic_config
```

## Example

This is the code to define the cli (in a file name `simple_cli.py`)

```python
from pydantic_config import parse_argv, BaseConfig


class Config(BaseConfig):
    hello: str 
    foo: int

def main(conf: Config):

    print(conf.model_dump())


if __name__ == "__main__":
    
    config = Config(**parse_argv())
    main(config)

```

you can call it like this

```bash

python simple_cli.py  --hello world --foo bar
>>> {'hello': 'world', 'foo': 1}
```


## Nested argument Example

```python
from pathlib import Path
from pydantic_config import parse_argv, BaseConfig


class TrainingConfig(BaseConfig):
    lr: float = 3e-4
    batch_size: int

class DataConfig(BaseConfig):
    path: Path

class Config(BaseConfig):
    train: TrainingConfig
    data: DataConfig



def prepare_data(conf: DataConfig):
    ... # prepare data

def train(conf: TrainingConfig):
    ... # train model

def main(conf: Config):

    prepare_data(conf.data)
    train(conf.train)


if __name__ == "__main__":
    
    config = Config(**parse_argv())
    main(config)

```

You can use it like this

```bash
python examples/nested_cli.py --train.batch_size 32 --data.path ~/datasets
```

## CLI syntax

Pydantic config accept argument with two leading minus `-`.

```bash
python main.py --arg value --arg2 value2
```

### Python varaible,  `-` and `_`

Any other `-` will be converted to an underscoed `_`. As in python variable name use underscode but cli args are usaully using
minus as seperator.

This two are therefore equivalent
```bash
python main.py --my-arg value
python main.py --my_arg value
```

### Nested argument

Pydantic config support nested argument using the `.` delimiter

```bash
python main.py --hello.foo bar --xyz value
python main.py --hello.foo.a abc --hello.foo.b bar
```

this hierarchy will be translated into nested python dictionaries

### Boolean handling

If you pass an argument without a value, pydantic_config will assume it is a boolean and set the value to `True`.

```bash
python main.py --my-arg
```

Unless you pass `--no-my-arg`, which will set the value to `False`.

```bash
python main.py --no-my-arg
```

## Why ?

Because I have been tired of the different cli tool and config manager in the python ecosystem. I want to let [Pydantic](https://docs.pydantic.dev/latest/) handle all of the validation and coercion logic (because it is doing it great), I just need a simple tool that can
generate a dict from the cli arguments and/or a json file and pass it pydantic.

Pydantic_config is what most of the cli/config tool would have been if pydantic would have been released earlier.

Honorable mention to the tool that I used in the past:

* [Typer](https://typer.tiangolo.com/)
* [cyclopts](https://github.com/BrianPugh/cyclopts)
* [click](https://click.palletsprojects.com/en/8.0.x/cli/)
* [fire](https://github.com/google/python-fire)
* [jsonargparse](https://github.com/omni-us/jsonargparse)




## Yet another cli parser in python ?

Yes sorry, but this one will stay as simple as possible. Arg to dict to pydantic. 


## Development

This project use [rye](https://github.com/astral-sh/rye) to manage python.


## todo list

- [ ] rename since pydantic_config is already used on pypi
- [x] add decorator to wrap function
- [x] add rich for ui
- [x] add no prefix to negate boolean
- [x] nice error message

