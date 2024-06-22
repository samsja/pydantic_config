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
from pydantic_config import validate_call, parse_argv

@validate_call
def main(hello: str, foo: int):
    print(f"hello: {hello}, foo: {foo}")


if __name__ == "__main__":
    main(**parse_argv())
```

you can call it like this

```bash

python simple_cli.py  --hello world --foo bar
>>> 'hello': 'world', 'foo': 1
```

Under the hood, the cli argument are converted to a (nested) dictionary and passed to the function. Pydantic is used to validate
the argument, eventually coercing the type if needed.

For instance if you passed a wrong parameters:

```bash
python examples/simple_cli.py --hello world --foo --fooo
```

Pydantic config will complain:
```bash
╭─ 1 errors ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --fooo is not a valid cli argument                                                                                            │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Nested Config 

Pydantic Config allow to represent nested config using pydantic [BaseModel](https://docs.pydantic.dev/latest/api/base_model/).

The vision is that most ml code is a suite of nested funciton call, training loop calling model init, calling sub module init etcc.

Allowing to represent the config as a nested model is the most natural way to represent ML code (IMO). It allows as well to locally define argument, tested them independently from other but still having a global config that can be validate ahead of time, allowing to fail early if necessary. 


```python
from pathlib import Path
from pydantic_config import parse_argv, BaseConfig, validate_call


from pathlib import Path
from pydantic_config import parse_argv, BaseConfig, validate_call


class TrainingConfig(BaseConfig):
    lr: float = 3e-4
    batch_size: int


class DataConfig(BaseConfig):
    path: Path

def prepare_data(conf: DataConfig): ...  # prepare data

def train_model(conf: TrainingConfig): ...  # train model

@validate_call
def main(train: TrainingConfig, data: DataConfig):
    prepare_data(data)
    train_model(train)

if __name__ == "__main__":
    main(**parse_argv())

```

You can use it like this

```bash
python examples/nested_cli.py --train.batch_size 32 --data.path ~/datasets
```


## Yet another cli parser / config manager in python ?

Yes sorry, but this one will stay as simple as possible. Arg to dict to pydantic. 

###  Why ?

Because I have been tired of the different cli tool and config manager in the python ecosystem. I want to let [Pydantic](https://docs.pydantic.dev/latest/) handle all of the validation and coercion logic (because it is doing it great), I just need a simple tool that can
generate a dict from the cli arguments and/or a json file and pass it pydantic.

Pydantic_config is what most of the cli/config tool would have been if pydantic would have been released earlier.

Honorable mention to the tool that I used in the past:

* [Typer](https://typer.tiangolo.com/)
* [cyclopts](https://github.com/BrianPugh/cyclopts)
* [click](https://click.palletsprojects.com/en/8.0.x/cli/)
* [fire](https://github.com/google/python-fire)
* [jsonargparse](https://github.com/omni-us/jsonargparse)




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

## List handling

To pass as list, just a repeat the argument

```bash
python main.py --my-list value1 --my-list value2
>>> {"my_list": ["value1", "value2"]}
```

## Development

This project use [rye](https://github.com/astral-sh/rye) to manage python.


## todo list

- [ ] rename since pydantic_config is already used on pypi
- [x] add decorator to wrap function
- [x] add rich for ui
- [x] add no prefix to negate boolean
- [x] nice error message

