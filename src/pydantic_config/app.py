from typing import Callable, Tuple, Type, TypeAlias
from pydantic_config import BaseConfig
from pydantic_config.parse import parse_argv


EntryPoint: TypeAlias = Tuple[Callable, Type[BaseConfig]]


class App:
    def __init__(self):
        self.entry_points: list[EntryPoint] = []

    def __call__(self):
        self.call("default")

    def call(self, name: str):
        if name in self.entry_points:
            config_class, callable = self.entry_points[name]
            parsed_config = config_class(**parse_argv())
            callable(parsed_config.model_dump())
        else:
            raise ValueError(f"Entry point {name} not found")
